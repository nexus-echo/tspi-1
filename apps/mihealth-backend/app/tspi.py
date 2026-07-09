"""HTTP client to the de-identified TSPI brain (consumed as a service).

All calls degrade gracefully: connection failures AND non-2xx responses are converted into
BrainUnavailable (with the brain's message), so the API returns a clean 502 instead of a 500.
"""
from __future__ import annotations

import httpx

from app.config import settings


class BrainUnavailable(RuntimeError):
    pass


class ConsentRejected(RuntimeError):
    pass


def _url(path: str) -> str:
    return f"{settings.tspi_base_url.rstrip('/')}/{path.lstrip('/')}"


def _request(method: str, path: str, *, json: dict | None = None, timeout: float = 60.0,
             allow_403: bool = False) -> httpx.Response:
    try:
        resp = httpx.request(method, _url(path), json=json, timeout=timeout)
    except httpx.HTTPError as e:
        raise BrainUnavailable(f"TSPI brain unreachable at {_url(path)}: {e}") from e
    if allow_403 and resp.status_code == 403:
        return resp
    if resp.status_code >= 400:
        body = (resp.text or "")[:300]
        raise BrainUnavailable(f"TSPI {method} {path} returned {resp.status_code}: {body}")
    return resp


def generate_report(payload: dict) -> dict:
    """POST /report -> CaseReport. Raises ConsentRejected on 403."""
    resp = _request("POST", "/report", json=payload, timeout=120.0, allow_403=True)
    if resp.status_code == 403:
        try:
            detail = resp.json().get("detail", "Consent rejected by TSPI")
        except Exception:
            detail = "Consent rejected by TSPI"
        raise ConsentRejected(detail)
    return resp.json()


def validate(tspi_report_id: str, doctor_id: str, decision: str, edits: dict | None) -> dict:
    return _request("POST", "/validate", json={
        "report_id": tspi_report_id, "doctor_id": doctor_id,
        "decision": decision, "edits": edits,
    }).json()


def outcome(tspi_report_id: str, marker: str, baseline: float, followup: float) -> dict:
    return _request("POST", "/outcome", json={
        "report_id": tspi_report_id, "marker": marker,
        "baseline": baseline, "followup": followup,
    }).json()


def recalibrate() -> dict:
    return _request("POST", "/learning/recalibrate", timeout=120.0).json()


def weights() -> dict:
    return _request("GET", "/learning/weights", timeout=30.0).json()


def extract_document(data: bytes, filename: str, mime: str, doc_type: str = "lab") -> dict:
    """POST /extract (multipart) -> candidate labs + imaging narrative from the TSPI engine.

    The engine reads the file with LOCAL models (vision for images/scanned PDFs, text for text
    PDFs) and returns confirmed=False candidates. Raises BrainUnavailable on any failure so the
    caller can fall back to local OCR.
    """
    files = {"file": (filename or "upload", data, mime or "application/octet-stream")}
    try:
        resp = httpx.post(_url("/extract"), files=files, data={"doc_type": doc_type}, timeout=180.0)
    except httpx.HTTPError as e:
        raise BrainUnavailable(f"TSPI extract unreachable: {e}") from e
    if resp.status_code >= 400:
        raise BrainUnavailable(f"TSPI /extract returned {resp.status_code}: {(resp.text or '')[:200]}")
    return resp.json()
