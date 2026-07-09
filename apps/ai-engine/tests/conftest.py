"""Make tests hermetic: SQLite DB, no live LLM, deterministic hash embedder —
regardless of the developer's .env (which may point at Postgres / DeepSeek / Ollama).
Env vars set here take precedence over .env in pydantic-settings.
"""
import os

os.environ["DATABASE_URL"] = ""        # force SQLite for tests
os.environ["TSPI_ENV"] = "test"        # disable live LLM calls
os.environ["EMBEDDING_BACKEND"] = "hash"   # no network embedder in tests
os.environ["EMBEDDING_DIM"] = "384"
