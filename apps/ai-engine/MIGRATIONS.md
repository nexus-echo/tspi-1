# Database Migrations (Alembic)

**Why this exists:** `Base.metadata.create_all()` only *creates missing tables* — it never
*alters* an existing one. So adding a column to a model (e.g. `OutcomeRow.learned`) doesn't reach
a database that already has that table. **Alembic** tracks model changes and applies the `ALTER`s.

## Fix your current Postgres (the `learned` column)
Your existing DB has `outcomes` without `learned`. Apply the shipped migration:
```bash
# local
DATABASE_URL=postgresql+psycopg://tspi:...@localhost:5432/tspi  alembic upgrade head
# docker
docker compose exec api alembic upgrade head
```
This runs `alembic/versions/0001_add_learned_to_outcomes.py`, which **idempotently** adds the
column (and backfills existing rows with `false`). Safe to run anytime, on any DB.

> One-liner alternative (not recommended long-term):
> `ALTER TABLE outcomes ADD COLUMN learned boolean NOT NULL DEFAULT false;`

## Going forward — whenever you change a model
1. Edit the SQLAlchemy model in `app/knowledge/models.py`.
2. Autogenerate a migration (Alembic diffs models vs the live DB):
   ```bash
   alembic revision --autogenerate -m "describe the change"
   # docker: docker compose exec api alembic revision --autogenerate -m "..."
   ```
3. **Review** the generated file in `alembic/versions/` (autogenerate is great but not perfect —
   check renames, data backfills, server defaults).
4. Apply it:
   ```bash
   alembic upgrade head
   ```

## On deploy
The container entrypoint runs **`alembic upgrade head`** automatically (after seeding, before
uvicorn), so deploys self-migrate. New/dev databases are still bootstrapped by `create_all`
(builds missing tables); Alembic then applies any pending `ALTER`s — the migrations are written
idempotently so both paths are safe.

## Useful commands
```bash
alembic current            # which revision the DB is at
alembic history            # all migrations
alembic upgrade head       # apply all pending
alembic downgrade -1       # roll back one
alembic stamp head         # mark DB as up-to-date WITHOUT running (adopting Alembic on an existing DB)
```

## Notes
- **URL / `.env`**: `alembic/env.py` reads `DATABASE_URL` through the app's `Settings`, so it loads
  your `.env` **exactly like the app** (run `alembic` from the project dir where `.env` lives). A real
  env var (e.g. Docker `environment:`) still takes precedence; falls back to the SQLite dev DB. No
  URL is hard-coded in `alembic.ini`.
- **Scope**: env.py targets `app.knowledge.models.Base.metadata` (catalog + reports + audit +
  outcomes + axis_weights). The pgvector-managed **`kb_embeddings`** table is intentionally
  excluded from autogenerate (managed by `app/knowledge/vectors.py` / `scripts/embed_knowledge`).
- **Adopting Alembic on an already-running DB**: run `alembic stamp head` once to record the
  current state, then use `revision --autogenerate` for future changes.
