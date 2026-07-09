"""Alembic environment for tspi_ai_brain.

Targets `app.knowledge.models.Base.metadata` (all ORM tables: catalog + reports + audit +
outcomes + axis_weights). The pgvector-managed `kb_embeddings` table is intentionally excluded
from autogenerate. DATABASE_URL is read via the app's Settings, so it picks up `.env` exactly
like the app does (and a real env var, e.g. Docker, still wins).
"""
from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config, pool
from alembic import context

from app.knowledge.models import Base  # registers every ORM model on Base.metadata

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    # Reuse the app's settings so Alembic loads DATABASE_URL from .env exactly like the app does.
    # Precedence: real env var (e.g. Docker) > .env file > sqlite default.
    try:
        from app.config import settings
        if settings.database_url:
            return settings.database_url
    except Exception:
        pass
    return os.environ.get("DATABASE_URL") or "sqlite:///./data/tspi.db"


def include_object(obj, name, type_, reflected, compare_to):
    # kb_embeddings is managed by app/knowledge/vectors.py (pgvector), not the ORM.
    if type_ == "table" and name == "kb_embeddings":
        return False
    return True


def run_migrations_offline() -> None:
    context.configure(url=get_url(), target_metadata=target_metadata,
                      literal_binds=True, compare_type=True, include_object=include_object)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata,
                          compare_type=True, include_object=include_object)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
