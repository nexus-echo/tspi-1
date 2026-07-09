# TSPI AI Brain — Deployment (Docker Compose)

Full stack in three containers: **api** (FastAPI), **db** (PostgreSQL + pgvector), **ollama**
(local LLM/embeddings). The app de-identifies, scores (NSS/SPS), generates the report, and gates
delivery on doctor validation.

## Quick start
```bash
cd tspi_ai_brain
cp .env.docker.example .env          # add DEEPSEEK_API_KEY; review EMBEDDING_* and POSTGRES_PASSWORD
docker compose up -d --build         # builds api, starts db + ollama

# one-time model + vectors (Phase 2 RAG)
docker compose exec ollama ollama pull bge-m3
docker compose exec api python -m scripts.embed_knowledge
docker compose exec api python -m scripts.verify_phase2   # expect ALL PASS

open http://localhost:8000/docs       # OpenAPI / Swagger
```
On startup the **api** container waits for Postgres, **seeds the knowledge base** (idempotent),
then runs uvicorn with `WEB_CONCURRENCY` workers. The Postgres/Ollama data persist in named volumes.

## Services
| Service | Image | Purpose | Port |
|---|---|---|---|
| `api` | built from `Dockerfile` | FastAPI engine (`/report`, `/validate`, `/learning/*`, …) | 8000 |
| `db` | `pgvector/pgvector:pg16` | relational catalog **+** embeddings (one DB) | 5432 (internal) |
| `ollama` | `ollama/ollama` | local embeddings (`bge-m3`) and optional local LLM | 11434 (internal) |

## Configuration (`.env`)
- **LLM:** `LLM_PRIMARY=deepseek` + `DEEPSEEK_API_KEY` (the report writer). Ollama is an in-stack fallback.
- **Embeddings:** `EMBEDDING_BACKEND=ollama` + `OLLAMA_EMBEDDING_MODEL=bge-m3` + `EMBEDDING_DIM=1024`
  (local/private). Or `api` (OpenAI-compatible) — set `EMBEDDING_API_KEY`/`EMBEDDING_MODEL`/`EMBEDDING_DIM`.
- **Infra** (set by compose, don't put in `.env`): `DATABASE_URL`, `OLLAMA_BASE_URL`.
- `WEB_CONCURRENCY` (workers), `RUN_EMBED_ON_START` (embed on boot if the model is pre-pulled),
  `REQUIRE_DOCTOR_VALIDATION` (default true).

> Switching the embedding model changes the vector dimension — set `EMBEDDING_DIM` to match and
> re-run `embed_knowledge` (it drops & rebuilds `kb_embeddings`).

## Scaling (≈1000 reports/day)
- Raise `WEB_CONCURRENCY` (2–4 workers per core) and/or run multiple `api` replicas behind a load
  balancer. The app is stateless; all state is in Postgres.
- **Ollama wants a GPU** for good throughput — uncomment the `deploy.resources` GPU block (needs
  `nvidia-container-toolkit`). Without a GPU, prefer the **`api` embedding backend** (managed) and
  use DeepSeek for the LLM, so the box stays CPU-only.
- pgvector: add an index for large catalogs (only needed once the catalog grows):
  `CREATE INDEX ON kb_embeddings USING hnsw (embedding vector_cosine_ops);`

## Production hardening
- **TLS / reverse proxy:** put Caddy / Nginx / Traefik in front of `api:8000` for HTTPS + rate limiting.
- **Managed Postgres** (RDS/Cloud SQL/Supabase with pgvector): drop the `db` service and point
  `DATABASE_URL` at it. Same code.
- **Secrets:** use Docker/cloud secrets, not a plaintext `.env`, in production. Rotate keys.
- **Backups:** snapshot the `tspi_pgdata` volume / managed-DB backups (reports + audit log live here).
- **Schema migrations:** add **Alembic** before the first prod schema change (today tables are
  auto-created on boot, fine for greenfield).
- **Observability:** scrape `/health`; ship logs; track LLM/embedding latency + token cost.
- **Compliance (health data):** keep de-identification on (default), TLS everywhere, restrict DB
  network, retain the `audit_log`. For HIPAA, route DeepSeek/embeddings via a BAA-covered endpoint.

## Cloud (serverless) alternative
For a managed deploy (Cloud Run / ECS Fargate): use the same image with **managed Postgres+pgvector**
and the **`api` embedding backend** + DeepSeek (no Ollama container, since Ollama needs a persistent
GPU host). See `TSPI_Deployment_and_Cost_Plan.md` for the cost model.

## Common commands
```bash
docker compose logs -f api                 # app logs
docker compose exec api python -m scripts.validate_phase0   # 27/27
docker compose exec api python -m pytest -q                  # 17 tests
docker compose down                        # stop (keeps volumes)
docker compose down -v                     # stop + WIPE data
```

## Troubleshooting
- **api restarts / DB errors:** ensure `db` is healthy (`docker compose ps`); the entrypoint retries 60×2s.
- **`verify_phase2` SKIP:** `DATABASE_URL` isn't Postgres — it's set by compose; check the `api` env.
- **embed fails:** pull the model first (`ollama pull bge-m3`) and confirm `EMBEDDING_DIM` matches it.
- **report is short/bulleted (not prose):** the LLM call failed → it fell back to the deterministic
  report. Check `DEEPSEEK_API_KEY` / `LLM_PRIMARY`.
