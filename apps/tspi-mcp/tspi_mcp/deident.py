"""De-identification gate.

Governance invariant (all TSPI expert rulings): **PII must never reach the engine or the LLM.**
The MCP tool schemas deliberately have NO name / DOB / MRN / contact fields, which steers the
model to collect only de-identified data. This module is the second line of defence: it scans
free-text fields for identifiers and either redacts them (lenient) or rejects the call (strict).

It is intentionally conservative and self-contained (no engine import) so it can be unit-tested
and can never itself leak data.
"""
from __future__ import annotations

import re

# Fields the engine legitimately accepts. Anything else is dropped before forwarding.
ALLOWED_FIELDS = {
    "case_id", "age_band", "sex", "symptoms", "structured_symptoms", "labs", "imaging",
    "medications", "conditions", "lifestyle", "omics", "consent",
}

# Field names that indicate a caller is trying to pass identity — always rejected.
FORBIDDEN_FIELDS = {
    "name", "patient_name", "full_name", "first_name", "last_name", "surname",
    "dob", "date_of_birth", "birthdate", "mrn", "hn", "national_id", "ssn",
    "passport", "phone", "mobile", "tel", "email", "address", "photo",
}

_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")
_LONG_ID = re.compile(r"\b\d{7,}\b")                      # long digit runs (MRN / national id)
_DOB = re.compile(r"\b(?:19|20)\d{2}[-/.](?:0?[1-9]|1[0-2])[-/.](?:0?[1-9]|[12]\d|3[01])\b"
                  r"|\b(?:0?[1-9]|[12]\d|3[01])[-/.](?:0?[1-9]|1[0-2])[-/.](?:19|20)\d{2}\b")
_NAME_HINT = re.compile(r"\b(?:name|patient|mr|mrs|ms|dr)[.:]\s+[A-Z][a-z]+", re.IGNORECASE)

_REDACTIONS = (
    ("email", _EMAIL),
    ("date_of_birth", _DOB),     # before phone: a date like 1980-05-01 must not be read as a phone
    ("phone", _PHONE),
    ("identifier", _LONG_ID),
    ("name", _NAME_HINT),
)


class PIIError(ValueError):
    """Raised in strict mode when identifiable information is detected."""


def _scrub_text(text: str) -> tuple[str, list[str]]:
    findings: list[str] = []
    out = text
    for label, rx in _REDACTIONS:
        if rx.search(out):
            findings.append(label)
            out = rx.sub(f"[REDACTED_{label.upper()}]", out)
    return out, findings


def _walk(value):
    """Recursively scrub strings inside dict/list structures. Returns (clean, findings)."""
    findings: list[str] = []
    if isinstance(value, str):
        clean, f = _scrub_text(value)
        return clean, f
    if isinstance(value, dict):
        clean_d = {}
        for k, v in value.items():
            cv, f = _walk(v)
            clean_d[k] = cv
            findings += f
        return clean_d, findings
    if isinstance(value, list):
        clean_l = []
        for v in value:
            cv, f = _walk(v)
            clean_l.append(cv)
            findings += f
        return clean_l, findings
    return value, findings


def deidentify(payload: dict, *, strict: bool) -> tuple[dict, list[str]]:
    """Return a de-identified copy of `payload` plus a list of what was removed.

    - Drops any field not in ALLOWED_FIELDS.
    - Rejects any FORBIDDEN_FIELDS outright.
    - Scrubs identifiers from all remaining free-text.
    In strict mode, ANY finding raises PIIError (fail-closed).
    """
    forbidden_present = sorted(set(payload) & FORBIDDEN_FIELDS)
    if forbidden_present:
        raise PIIError(
            "Identity fields are not allowed in TSPI input: "
            f"{', '.join(forbidden_present)}. Submit de-identified data only "
            "(case_id + age_band + sex + clinical findings)."
        )

    kept = {k: v for k, v in payload.items() if k in ALLOWED_FIELDS}
    clean, findings = _walk(kept)
    findings = sorted(set(findings))

    if findings and strict:
        raise PIIError(
            "Possible patient identifiers detected in the input "
            f"({', '.join(findings)}). Remove them and resend — TSPI must never receive PII. "
            "Use a case code instead of any name/date/number that could identify the patient."
        )
    return clean, findings
