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
    # Role + clinic the MCP acts as (forwarded to the engine when it enforces auth). The MCP is a
    # clinician-facing surface, so the default role is 'clinician'.
    clinician_role: str = os.getenv("TSPI_CLINICIAN_ROLE", "clinician")
    clinic_id: str | None = os.getenv("TSPI_CLINIC_ID") or None
    # De-identification: when strict, any detected PII in input HARD-FAILS the call.
    # When not strict, PII is redacted and a warning is returned instead.
    strict_deident: bool = _bool("TSPI_STRICT_DEIDENT", True)
    # Transport: "stdio" (local Claude Desktop) or "streamable-http" (remote connectors).
    transport: str = os.getenv("TSPI_MCP_TRANSPORT", "stdio")
    http_timeout_s: float = float(os.getenv("TSPI_HTTP_TIMEOUT", "60"))

    # --- P7: OAuth for the public/remote MCP surface ---
    # none  = no incoming auth (local stdio only; NEVER expose publicly)
    # jwt   = validate bearer JWTs from any OIDC issuer (JWKS)  [works with Auth0/Keycloak/Azure/…]
    # workos= WorkOS AuthKit (DCR) — the simplest fully-automatic remote-connector flow
    mcp_auth: str = os.getenv("TSPI_MCP_AUTH", "none")
    mcp_base_url: str | None = os.getenv("TSPI_MCP_BASE_URL") or None      # public https URL of this MCP
    jwt_jwks_uri: str | None = os.getenv("TSPI_JWT_JWKS_URI") or None
    jwt_issuer: str | None = os.getenv("TSPI_JWT_ISSUER") or None
    jwt_audience: str | None = os.getenv("TSPI_JWT_AUDIENCE") or None
    workos_authkit_domain: str | None = os.getenv("TSPI_WORKOS_AUTHKIT_DOMAIN") or None
    # Token claim names carrying the clinician identity (mapped to X-TSPI-* for the engine).
    claim_user: str = os.getenv("TSPI_CLAIM_USER", "sub")
    claim_role: str = os.getenv("TSPI_CLAIM_ROLE", "role")
    claim_clinic: str = os.getenv("TSPI_CLAIM_CLINIC", "clinic_id")


settings = Settings()
