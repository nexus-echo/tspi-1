"""P7 — OAuth auth provider + per-request clinician identity for the (public) MCP surface.

Fail-closed: if TSPI_MCP_AUTH is set but its config is incomplete, startup raises rather than
running an UNAUTHENTICATED public MCP. Local stdio (auth=none) keeps the static-identity pilot model.
"""
from __future__ import annotations

from .config import settings


def build_auth():
    """Return a FastMCP auth provider from env, or None for local stdio (no incoming auth)."""
    mode = (settings.mcp_auth or "none").lower()
    if mode == "none":
        return None
    if mode == "jwt":
        if not (settings.jwt_jwks_uri and settings.jwt_issuer):
            raise RuntimeError("TSPI_MCP_AUTH=jwt requires TSPI_JWT_JWKS_URI and TSPI_JWT_ISSUER.")
        from fastmcp.server.auth.providers.jwt import JWTVerifier
        return JWTVerifier(jwks_uri=settings.jwt_jwks_uri, issuer=settings.jwt_issuer,
                           audience=settings.jwt_audience)
    if mode == "workos":
        if not (settings.workos_authkit_domain and settings.mcp_base_url):
            raise RuntimeError("TSPI_MCP_AUTH=workos requires TSPI_WORKOS_AUTHKIT_DOMAIN and TSPI_MCP_BASE_URL.")
        from fastmcp.server.auth.providers.workos import AuthKitProvider

        return AuthKitProvider(
            authkit_domain=settings.workos_authkit_domain,
            base_url=settings.mcp_base_url,
            resource_base_url=settings.mcp_base_url,
            resource_name="TSPI AI Brain",
        )

    raise RuntimeError(f"Unknown TSPI_MCP_AUTH mode: {mode!r} (use none|jwt|workos).")


def current_identity_ext() -> dict:
    """Full identity for THIS request from the validated OAuth token (else the static pilot
    identity for stdio). Includes human-identity fields (name/email) for report attribution.
    Never trusts anything the LLM can set — everything comes from the signed token's claims."""
    tok = None
    try:
        from fastmcp.server.dependencies import get_access_token
        tok = get_access_token()
    except Exception:  # noqa: BLE001 — no request/token context (e.g. stdio)
        tok = None

    if tok is not None:
        claims = getattr(tok, "claims", None) or {}
        user = claims.get(settings.claim_user) or getattr(tok, "subject", None) or settings.clinician_id
        role = claims.get(settings.claim_role) or settings.clinician_role
        clinic = claims.get(settings.claim_clinic) or settings.clinic_id
        email = claims.get(settings.claim_email)
        first = claims.get(settings.claim_first_name)
        last = claims.get(settings.claim_last_name)
    else:
        user, role, clinic = settings.clinician_id, settings.clinician_role, settings.clinic_id
        email = first = last = None

    name = " ".join(p for p in (first, last) if p) or None
    return {
        "user": str(user),
        "role": str(role),
        "clinic": (str(clinic) if clinic else None),
        "email": (str(email) if email else None),
        "first_name": (str(first) if first else None),
        "last_name": (str(last) if last else None),
        "name": name,
    }


def current_identity() -> tuple[str, str, str | None]:
    """(user_id, role, clinic_id) — the core triple used for RBAC/tenant checks. Thin wrapper over
    current_identity_ext() so there is a single source of truth."""
    i = current_identity_ext()
    return i["user"], i["role"], i["clinic"]
