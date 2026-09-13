"""Async HTTP client for the standalone TSPI FastAPI engine.

This is the ONLY thing that talks to the engine, and it talks to it exactly as any other REST
client would — the engine is unchanged and standalone. Errors are turned into actionable
messages the chat model can relay to the clinician.
"""
from __future__ import annotations

from typing import Any

import httpx

from .config import settings


class EngineError(RuntimeError):
    """A failed engine call, with an actionable message."""


def _headers() -> dict[str, str]:
    # Service token authenticates the MCP to the engine; X-TSPI-* forward the clinician identity
    # the engine trusts for RBAC + audit. Identity is PER-REQUEST from the validated OAuth token
    # (P7) when the MCP is remote/authenticated, else the static pilot identity (stdio).
    from .identity import current_identity_ext
    ident = current_identity_ext()
    h = {"Accept": "application/json"}
    if settings.engine_token:
        h["Authorization"] = f"Bearer {settings.engine_token}"
    h["X-TSPI-User-Id"] = ident["user"]
    h["X-TSPI-Role"] = ident["role"]
    h["X-TSPI-Source"] = "mcp"
    if ident["clinic"]:
        h["X-TSPI-Clinic-Id"] = ident["clinic"]
    # Human-identity for report attribution (who created/approved). Optional; omitted if absent.
    if ident["name"]:
        h["X-TSPI-Name"] = ident["name"]
    if ident["email"]:
        h["X-TSPI-Email"] = ident["email"]
    return h


def _explain(status: int, body: str) -> str:
    if status == 403:
        return ("The engine refused the request (403). The most common cause is missing consent: "
                "set consent_ai_analysis=true after confirming the patient consented.")
    if status == 404:
        return "The engine could not find that record (404). Check the report_id / case_id."
    if status == 422:
        return f"The engine rejected the input as invalid (422): {body[:400]}"
    return f"The engine returned HTTP {status}: {body[:400]}"


async def _request(method: str, path: str, *, json: Any = None,
                   params: dict | None = None) -> Any:
    url = f"{settings.engine_url.rstrip('/')}{path}"
    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout_s) as client:
            resp = await client.request(method, url, json=json, params=params, headers=_headers())
    except httpx.ConnectError as e:
        raise EngineError(
            f"Cannot reach the TSPI engine at {settings.engine_url}. Is it running? "
            f"(set TSPI_ENGINE_URL if it lives elsewhere.) Details: {e}"
        ) from e
    except httpx.HTTPError as e:
        raise EngineError(f"Network error calling the TSPI engine: {e}") from e

    if resp.status_code >= 400:
        raise EngineError(_explain(resp.status_code, resp.text))
    if not resp.content:
        return {}
    try:
        return resp.json()
    except ValueError:
        return {"raw": resp.text}


async def get(path: str, params: dict | None = None) -> Any:
    return await _request("GET", path, params=params)


async def post(path: str, json: Any = None, params: dict | None = None) -> Any:
    return await _request("POST", path, json=json, params=params)
