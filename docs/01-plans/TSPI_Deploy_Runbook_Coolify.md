# TSPI — Production Deploy Runbook (Coolify + Supabase + Tailscale Ollama)

*Pilot deployment of the AI platform (this repo) + MiHealth portal (separate repo) on a Hostinger VPS
running Coolify, with Supabase Postgres and a local GPU Ollama reached over Tailscale.*

## Target topology
```
                 PUBLIC (Coolify/Traefik + Let's Encrypt TLS)
   mihealth-web ───────────────┐                 tspi-mcp ──────────── (OAuth: workos|jwt)
        │                       │                    │
        ▼ /api                  │                    ▼  X-TSPI-* identity from token
   mihealth-api ────────────────┼──────────────► tspi-api  (ENGINE — PRIVATE, no public route)
        │  (PHI: portal)        │  de-identified     │  (PHI stored ENCRYPTED here; LLM sees placeholders)
        ▼                       │                    ▼
   Supabase: mihealth DB        │            Supabase: tspi DB (pgvector, encrypted)
                                └──────── Tailscale ───────► Ollama (GPU box) : embeddings/extraction/LLM
```
**Only `mihealth-web` and `tspi-mcp` are public.** `tspi-api` and both DBs stay private.

---

## 0. One-time prep

**Generate secrets** (keep in Coolify secrets, never in git):
```bash
# engine service tokens (comma-separated; one per caller)
python -c "import secrets; print('svc-mihealth-'+secrets.token_urlsafe(24)); print('svc-mcp-'+secrets.token_urlsafe(24))"
# PHI encryption key (Fernet)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# JWT/portal secret
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

**Supabase:**
1. Create **two projects** (or two DBs): `tspi` and `mihealth`.
2. In the **`tspi`** DB SQL editor: `create extension if not exists vector;` (pgvector).
3. Note the **pooler** connection string (port 6543, `pgbouncer`) for each — use it for `DATABASE_URL`.
4. `tspi` DB now holds PHI → confirm encryption-at-rest is on (Supabase default) and restrict access.

**Tailscale:** ensure the VPS and the Ollama GPU box are on the same tailnet; the Ollama IP is
`http://100.121.11.25:11434` (pull models once: `ollama pull bge-m3`, `ollama pull qwen2.5vl`).

**Identity provider (for public MCP OAuth):** pick one and have its values ready —
WorkOS AuthKit (`TSPI_MCP_AUTH=workos`, domain + base_url) **or** any OIDC issuer
(`TSPI_MCP_AUTH=jwt`, JWKS URI + issuer + audience). Clinician tokens must carry `role` (and
`clinic_id`) claims.

---

## 1. Coolify — create 4 services (2 repos)

| Service | Repo / build context | Port | Public? |
|---|---|---|---|
| **tspi-api** | this repo → `apps/ai-engine` (Dockerfile) | 8000 | **No** (internal) |
| **tspi-mcp** | this repo → `apps/tspi-mcp` (Dockerfile) | 8080 | **Yes** + OAuth |
| **mihealth-api** | mihealth repo → `backend` | 8001 | No (behind web) |
| **mihealth-web** | mihealth repo → `frontend` | 5173 | **Yes** |

In Coolify: add the two Git sources, create each service from its Dockerfile/build context, set the
env below, attach a domain + TLS only to the two public ones, set **resource limits** and
**healthchecks**, and enable **auto-deploy on push**.

## 2. Env per service (Coolify secrets)

**tspi-api (engine, private):**
```
TSPI_ENV=prod
DATABASE_URL=postgresql+psycopg://<tspi pooler conn>        # pgvector DB
OLLAMA_BASE_URL=http://100.121.11.25:11434
EMBEDDING_BACKEND=ollama
EMBEDDING_DIM=1024
OLLAMA_EMBEDDING_MODEL=bge-m3
LLM_PRIMARY=ollama            # PHI-bearing report LLM must be local; DeepSeek only for de-identified
AUTH_ENABLED=true
SERVICE_TOKENS=<svc-mihealth-…>,<svc-mcp-…>
ENCRYPTION_KEY=<fernet key>   # REQUIRED — PHI is stored here
PILOT_MODE=true
REPORT_LANGUAGE_DEFAULT=en
WEB_CONCURRENCY=2
```

**tspi-mcp (public, OAuth):**
```
TSPI_ENGINE_URL=http://tspi-api:8000        # private engine
TSPI_ENGINE_TOKEN=<svc-mcp-…>
TSPI_MCP_TRANSPORT=streamable-http
TSPI_MCP_PORT=8080
TSPI_MCP_AUTH=workos                        # or jwt
TSPI_WORKOS_AUTHKIT_DOMAIN=https://<project>.authkit.app
TSPI_MCP_BASE_URL=https://mcp.<your-domain>
# (jwt alt) TSPI_JWT_JWKS_URI=… TSPI_JWT_ISSUER=… TSPI_JWT_AUDIENCE=tspi-mcp
```

**mihealth-api (portal, PHI):**
```
DATABASE_URL=postgresql+psycopg2://<mihealth pooler conn>
TSPI_BASE_URL=http://tspi-api:8000          # private engine
TSPI_SERVICE_TOKEN=<svc-mihealth-…>          # + forward X-TSPI-* identity (see note in §5)
JWT_SECRET=<portal secret>
CORS_ORIGINS=https://<mihealth web domain>
```

**mihealth-web:** `VITE_API_TARGET=https://<mihealth-api domain or internal>`.

## 3. First-boot

- The engine entrypoint auto-runs `seed_db` + `alembic upgrade head` (incl. `0004`/`0005`).
- Optional one-off embeddings: set `RUN_EMBED_ON_START=true` once (models must be pulled) or run
  `python -m scripts.embed_knowledge` in the container.
- Verify: `https://mcp.<domain>` returns MCP metadata; `tspi-api` `/health` (internal) is ok.

## 4. Connect a clinician's chat client
Add the MCP as a **custom connector** in Claude.ai / ChatGPT using `https://mcp.<domain>`; the OAuth
flow signs the clinician in via your IdP. Tools appear; the identity flows through as `X-TSPI-*`.

## 5. Pre-go-live checklist
- [ ] `tspi-api` and both DBs have **no public route** (private network only).
- [ ] `AUTH_ENABLED=true` + `SERVICE_TOKENS` set; MCP/MiHealth present a valid token.
- [ ] `ENCRYPTION_KEY` set (PHI encrypted at rest); identity never appears in engine logs.
- [ ] `TSPI_MCP_AUTH` = workos|jwt (public MCP **refuses to start** unauthenticated).
- [ ] TLS on both public services; `PILOT_MODE=true` (reports watermarked, no auto patient release).
- [ ] Local Ollama reachable over Tailscale; PHI-bearing LLM stays local.
- [ ] Backups configured (Supabase + Coolify volumes); resource limits + healthchecks set.
- [ ] Follow-up (P8): clinician gold-standard cases + shadow-pilot monitoring.

## 6. Rollback
Coolify keeps previous deployments — redeploy the prior image per service. DB migrations `0004`/`0005`
are additive/nullable; a rollback of code is safe without a down-migration for the pilot.

---

**Note (MiHealth → engine auth):** when `AUTH_ENABLED=true`, MiHealth's engine client
(`backend/app/tspi.py`) must send `Authorization: Bearer <TSPI_SERVICE_TOKEN>` + `X-TSPI-User-Id/-Role/
-Clinic-Id` (same pattern the MCP uses). That's a small change in the mihealth repo — do it before
enabling engine auth in prod.
