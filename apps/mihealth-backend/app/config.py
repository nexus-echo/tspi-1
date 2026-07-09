"""MiHealth service settings (env-driven). Prototype defaults are safe for local Docker."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+psycopg2://mihealth:mihealth@localhost:5432/mihealth"

    # Auth
    jwt_secret: str = "dev-only-change-me"          # override in .env for anything real
    jwt_algorithm: str = "HS256"
    pii_encryption_key: str = ""                    # if blank, derived from jwt_secret (dev only)
    access_token_minutes: int = 30
    refresh_token_days: int = 7

    # TSPI brain (consumed as a service)
    tspi_base_url: str = "http://localhost:8000"

    # File storage + OCR (Phase C)
    upload_dir: str = "uploads"                     # local disk for prototype; mount a volume in Docker
    ocr_use_llm: bool = False                       # if True + provider reachable, structure labs via LLM
    ollama_base_url: str = "http://localhost:11434"  # local-first OCR structuring (per decision)
    ollama_model: str = "qwen2.5:14b"
    tesseract_cmd: str = ""                          # full path to tesseract.exe if not on PATH

    # Seed admin (created on startup if no users exist)
    seed_admin_email: str = "admin@mihealth.app"
    seed_admin_password: str = "admin12345"
    seed_admin_name: str = "Default Admin"

    # CORS
    cors_origins: str = "http://localhost:5173"


settings = Settings()
