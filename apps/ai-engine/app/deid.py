"""P4 — de-identification / re-identification boundary (engine side).

Centralises ALL PII handling in one place so clients never re-implement it. The rule kept
absolutely: **the brain and the LLM only ever see de-identified data + placeholders.** PII enters
here, is stored **encrypted** keyed by the de-identified `case_id`, and is re-attached ONLY at report
render time — never in the LLM prompt, never in a chat transcript.
"""
from __future__ import annotations

import json
import re

from app import store
from app.config import settings

# Placeholder tokens the report template uses; re-id substitutes these at render.
_FIELDS = ["full_name", "dob", "mrn", "phone", "email", "address"]

_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")
_LONGID = re.compile(r"\b\d{7,}\b")
_DOB = re.compile(r"\b(?:19|20)\d{2}[-/.](?:0?[1-9]|1[0-2])[-/.](?:0?[1-9]|[12]\d|3[01])\b")


class PIILeak(RuntimeError):
    """Raised if identifiable information is about to reach the LLM."""


def _fernet():
    key = settings.encryption_key
    if not key:
        return None
    from cryptography.fernet import Fernet
    return Fernet(key.encode() if isinstance(key, str) else key)


# ---------------------------------------------------------------- store / load (encrypted)
def store_identity(case_id: str, identity: dict) -> None:
    payload = json.dumps({k: identity.get(k) for k in _FIELDS if identity.get(k)}, ensure_ascii=False)
    f = _fernet()
    if f:
        store.save_identity(case_id, f.encrypt(payload.encode()).decode(), encrypted=True)
    else:
        store.save_identity(case_id, payload, encrypted=False)   # dev fallback (flagged; not for prod)


def get_identity(case_id: str) -> dict | None:
    row = store.get_identity(case_id)
    if not row:
        return None
    blob, enc = row["blob"], row["encrypted"]
    if enc:
        f = _fernet()
        if not f:
            return None                          # encrypted at rest but no key here -> cannot read
        blob = f.decrypt(blob.encode()).decode()
    try:
        return json.loads(blob)
    except ValueError:
        return None


# ---------------------------------------------------------------- scrub / guard
def scrub_text(text: str) -> tuple[str, list[str]]:
    findings, out = [], text or ""
    for label, rx in (("email", _EMAIL), ("date_of_birth", _DOB), ("phone", _PHONE),
                      ("identifier", _LONGID)):
        if rx.search(out):
            findings.append(label)
            out = rx.sub(f"[REDACTED_{label.upper()}]", out)
    return out, findings


def assert_prompt_deidentified(prompt: str, case_id: str) -> None:
    """Guard: the stored identity's values must NOT appear in an LLM prompt. Fail closed."""
    ident = get_identity(case_id) or {}
    low = prompt.lower()
    for k, v in ident.items():
        if v and str(v).strip() and str(v).lower() in low:
            raise PIILeak(f"PII ({k}) detected in LLM prompt for case {case_id}. Blocked.")
    # also catch raw identifiers that slipped into free text
    _, findings = scrub_text(prompt)
    if findings:
        raise PIILeak(f"Identifier(s) {findings} detected in LLM prompt for case {case_id}. Blocked.")


# ---------------------------------------------------------------- re-identify (render only)
def placeholders(identity: dict) -> dict[str, str]:
    return {f"{{{{patient.{k}}}}}": str(identity.get(k) or "") for k in _FIELDS}


def reidentify(text: str, case_id: str) -> str:
    ident = get_identity(case_id)
    if not ident or not text:
        return text
    for token, value in placeholders(ident).items():
        text = text.replace(token, value)
    return text


# ---------------------------------------------------------------- intake (strip before pipeline)
def intake(patient):
    """If the caller sent PII, store it encrypted + strip it so only de-identified data proceeds.
    Also scrubs free-text symptoms. Returns the de-identified patient object."""
    ident = getattr(patient, "patient_identity", None)
    if ident is not None:
        store_identity(patient.case_id, ident.model_dump() if hasattr(ident, "model_dump") else dict(ident))
        patient.patient_identity = None
        store.audit("pii_intake", case_id=patient.case_id, detail={"stored": True})
    # scrub any identifiers that leaked into free-text symptoms
    if getattr(patient, "symptoms", None):
        clean, findings = scrub_text(patient.symptoms)
        if findings:
            patient.symptoms = clean
            store.audit("pii_scrub", case_id=patient.case_id, detail={"fields": findings})
    return patient
