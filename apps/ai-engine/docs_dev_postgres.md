# Dev on PostgreSQL + pgvector (one DB for plain + vector)

**Yes — for dev you can (and should) use Postgres for both the relational catalog and the vector
embeddings.** One container, the `pgvector` extension, dev/prod parity. SQLite stays as a
zero-config fallback for quick local runs and CI.

## How it works
- `app/knowledge/db.py` reads `DATABASE_URL`. If it points to Postgres, the app uses Postgres and
  auto-runs `CREATE EXTENSION IF NOT EXISTS vector` on init. If unset, it uses SQLite (`data/tspi.db`).
- The **relational tables** (keys, steps, domains, axes, sub_axes, products, …) are identical on
  both engines — no code change to switch.
- The **embeddings** live in the SAME Postgres DB via `app/knowledge/vectors.py`
  (`kb_embeddings` table, `Vector` column). pgvector is imported lazily, so the SQLite path never
  needs it. (Populating embeddings = Phase 2 / RAG.)

## One-time setup
```bash
cd tspi_ai_brain
pip install -r requirements.txt          # now includes psycopg + pgvector

docker compose up -d db                   # Postgres 16 + pgvector on localhost:5432

# point the app at Postgres (.env)
echo 'DATABASE_URL=postgresql+psycopg://tspi:tspi@localhost:5432/tspi' >> .env

python -m scripts.seed_db                 # loads the official knowledge into Postgres
python -m scripts.validate_phase0         # expect 27/27 PASS on Postgres too
uvicorn app.main:app --reload             # /report now runs on Postgres
```

## Switching back to SQLite
Just remove/blank `DATABASE_URL` (no Docker needed). Useful for fast unit tests and CI.

## Why this is the right call
- **Parity:** dev behaves like prod — you catch Postgres-only issues (types, constraints, vector
  search) before deploy, not after.
- **One database:** exact lookups *and* semantic search in the same place — no second system to run,
  back up, or keep in sync.
- **No rewrite later:** production is the same image/extension, just a managed Postgres URL.

## Notes
- The pgvector dimension defaults to 1536; set it to match your embedding model when Phase 2 lands.
- For CI, keep SQLite (fast, no service) OR spin up the `pgvector/pgvector:pg16` service container.
