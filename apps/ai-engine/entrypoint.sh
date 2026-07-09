#!/bin/sh
set -e

echo "[entrypoint] waiting for database..."
python - <<'PY'
import os, time
from sqlalchemy import create_engine
url = os.environ.get("DATABASE_URL")
if url:
    for _ in range(60):
        try:
            create_engine(url).connect().close()
            print("[entrypoint] database is up"); break
        except Exception:
            time.sleep(2)
    else:
        print("[entrypoint] WARNING: database not reachable; continuing")
PY

echo "[entrypoint] seeding knowledge base (idempotent)..."
python -m scripts.seed_db || echo "[entrypoint] seed skipped/failed (continuing)"

echo "[entrypoint] applying DB migrations (alembic upgrade head)..."
python -m alembic upgrade head || echo "[entrypoint] migrations skipped/failed (continuing)"

if [ "${RUN_EMBED_ON_START}" = "true" ]; then
  echo "[entrypoint] embedding knowledge (RUN_EMBED_ON_START=true)..."
  python -m scripts.embed_knowledge || echo "[entrypoint] embed skipped/failed (continuing)"
fi

echo "[entrypoint] starting uvicorn (${WEB_CONCURRENCY:-2} workers)..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "${WEB_CONCURRENCY:-2}"
