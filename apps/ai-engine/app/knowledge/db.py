"""Database engine + session.

- No DATABASE_URL  -> zero-config SQLite dev DB (data/tspi.db).
- DATABASE_URL set -> PostgreSQL (recommended for dev/prod parity).

On Postgres we also try to enable the `pgvector` extension so the SAME database holds both the
relational catalog and the embeddings. pgvector is optional for Phase 0 (relational only); if it
is not installed on the local Postgres we warn and continue.
"""
from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.knowledge.models import Base

_DEFAULT_SQLITE = f"sqlite:///{Path(__file__).resolve().parent.parent.parent / 'data' / 'tspi.db'}"
DB_URL = settings.database_url or _DEFAULT_SQLITE
IS_POSTGRES = DB_URL.startswith("postgres")

_engine = create_engine(
    DB_URL,
    future=True,
    pool_pre_ping=IS_POSTGRES,
    connect_args=({"check_same_thread": False} if DB_URL.startswith("sqlite") else {}),
)
SessionLocal = sessionmaker(bind=_engine, class_=Session, expire_on_commit=False, future=True)


def engine():
    return _engine


def init_db() -> None:
    """Create relational tables (both engines). On Postgres, try to enable pgvector."""
    if IS_POSTGRES:
        try:
            with _engine.begin() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except Exception as e:  # noqa: BLE001 — pgvector optional for Phase 0
            logging.getLogger(__name__).warning(
                "pgvector not enabled (%s). Relational catalog still loads; "
                "install pgvector for embeddings/RAG.", e)
    Base.metadata.create_all(_engine)


def get_session() -> Session:
    return SessionLocal()
