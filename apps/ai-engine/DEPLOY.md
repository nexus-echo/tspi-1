# TSPI AI Brain — Deployment (Docker Compose)

The repo has **one** compose file at the root (`../../docker-compose.yml`) that builds **two**
application services: **tspi-api** (FastAPI engine) and **tspi-mcp** (public MCP surface).

There is deliberately **no database or Ollama container**:
- **Database** — SQLite locally (zero-config), **Supabase Postgres + pgvector** in prod, selected
  purely by `DATABASE_URL`.
- **Ollama** — an **external** service in both environments (localhost locally, a GPU box over
  Tailscale in prod), selected by `OLLAMA_BASE_URL`.

## Quick start (local docker)
```bash
cd tspi_new                             # repo root (where docker-compose.yml lives)
cp apps/ai-engine/.env.example apps/ai-engine/.env    # fill in values (see [local] annotations)
cp apps/tspi-mcp/.env.example  apps/tspi-mcp/.env
docker compose up -d --build            # builds tspi-api + tspi-mcp

open http://localhost:8002/docs         # engine OpenAPI / Swagger
# MCP surface: http://localhost:8080
```
With `DATABASE_URL` unset the engine uses the built-in SQLite DB. Point `OLLAMA_BASE_URL` at your
own Ollama (use `http://host.docker.internal:11434` to reach a host Ollama from the container).
On startup the engine seeds the knowledge base (idempotent), runs Alembic migrations, then serves
uvicorn with `WEB_CONCURRENCY` workers.

## Services
| Service | Build context | Purpose | Port | Public? |
|---|---|---|---|---|
| `tspi-api` | `apps/ai-engine` | FastAPI engine (`/report`, `/validate`, `/learning/*`, …) | 8002→8000 | **No** (private in prod) |
| `tspi-mcp` | `apps/tspi-mcp` | MCP server for AI chat clients | 8080 | **Yes** + OAuth in prod |

External (not containers): the DB (SQLite/Supabase via `DATABASE_URL`) and Ollama (via `OLLAMA_BASE_URL`).

## Configuration (`apps/ai-engine/.env`)
Every var is annotated `[local]` / `[prod]` in `.env.example`. The prod-critical switches:
- **Database:** set `DATABASE_URL` to the Supabase **pooler** conn (port 6543). The DB password
  lives inside this URL — there is no separate `POSTGRES_PASSWORD` (no bundled Postgres).
- **LLM:** `LLM_PRIMARY=ollama` in prod (PHI-bearing report LLM stays local); DeepSeek is unused
  on the PHI path and its key can be omitted.
- **Embeddings:** `EMBEDDING_BACKEND=ollama` + `OLLAMA_EMBEDDING_MODEL=bge-m3` + `EMBEDDING_DIM=1024`.
- **Auth/PHI:** `AUTH_ENABLED=true` + `SERVICE_TOKENS=…` and `ENCRYPTION_KEY=<fernet>` (PHI stored
  encrypted); `PILOT_MODE=true` for the pilot.

> Switching the embedding model changes the vector dimension — set `EMBEDDING_DIM` to match and
> re-run `embed_knowledge` (it drops & rebuilds `kb_embeddings`).

## Production (Coolify + Supabase + Tailscale)
The full production runbook — creating the Coolify services, Supabase pgvector setup, keeping the
engine private, MCP OAuth, and the go-live checklist — lives in
`../../docs/01-plans/TSPI_Deploy_Runbook_Coolify.md`. Key points:
- Expose **only** `tspi-mcp` (public + OAuth) and the MiHealth web app. Keep `tspi-api` private.
- Use managed Postgres+pgvector (Supabase) and Tailscale Ollama — same image, env-driven.
- Secrets go in Coolify's secret store, not a committed `.env`. Rotate keys. Configure backups.
- pgvector index for large catalogs (once the catalog grows):
  `CREATE INDEX ON kb_embeddings USING hnsw (embedding vector_cosine_ops);`

## Common commands
```bash
docker compose logs -f tspi-api                              # app logs
docker compose exec tspi-api python -m scripts.validate_phase0
docker compose exec tspi-api python -m pytest -q             # test suite
docker compose exec tspi-api python -m scripts.embed_knowledge   # build vectors (Ollama reachable)
docker compose down                                         # stop
```

## Troubleshooting
- **embed fails:** pull the model first (`ollama pull bge-m3`) and confirm `EMBEDDING_DIM` matches it.
- **report is short/bulleted (not prose):** the LLM call failed → it fell back to the deterministic
  report. Check `OLLAMA_BASE_URL` / `LLM_PRIMARY` (or `DEEPSEEK_API_KEY` if using DeepSeek locally).
- **engine can't reach Ollama from a container:** use `http://host.docker.internal:11434` (local)
  or the Tailscale IP (prod), not `localhost`.
