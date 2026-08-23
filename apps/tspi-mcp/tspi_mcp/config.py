"""Configuration for the TSPI MCP server (env-driven).

Nothing here changes the engine — these are client-side settings for how the MCP layer reaches
the engine and how strict the governance gates are.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    return default if v is None else v.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # Where the standalone FastAPI engine lives (unchanged, standalone REST service).
    engine_url: str = os.getenv("TSPI_ENGINE_URL", "http://localhost:8000")
    # Optional bearer token the MCP server presents to the engine (Phase B: real auth).
    engine_token: str | None = os.getenv("TSPI_ENGINE_TOKEN") or None
    # The authenticated clinician using this chat session (recorded on approvals + audit).
    clinician_id: str = os.getenv("TSPI_CLINICIAN_ID", "unknown-clinician")
    # De-identification: when strict, any detected PII in input HARD-FAILS the call.
    # When not strict, PII is redacted and a warning is returned instead.
    strict_deident: bool = _bool("TSPI_STRICT_DEIDENT", True)
    # Transport: "stdio" (local Claude Desktop) or "streamable-http" (remote connectors).
    transport: str = os.getenv("TSPI_MCP_TRANSPORT", "stdio")
    http_timeout_s: float = float(os.getenv("TSPI_HTTP_TIMEOUT", "60"))


settings = Settings()
