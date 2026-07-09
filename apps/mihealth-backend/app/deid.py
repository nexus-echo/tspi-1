"""De-identification boundary: build the EXACT TSPI payload and prove no PII leaks.

This is the single most important function in MiHealth — the only place patient data crosses
into the brain. It emits only the contract-allowed fields (case_id + age band + sex + clinical
facts: symptoms, labs, imaging, medications, conditions, lifestyle) and a guard raises if any
PII-bearing field ever appears. `summarize()` powers the pre-flight completeness check so a
near-empty (symptom-only) call can be caught before it produces a thin report.
"""
from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.models import Consent, Document, ImagingFinding, Intake, LabResult, Patient

# Exactly the keys the TSPI /report contract accepts.
ALLOWED_KEYS = {
    "case_id", "age_band", "sex", "symptoms", "labs", "imaging",
    "medications", "conditions", "lifestyle", "consent",
}
# Field names that must NEVER appear in an outbound payload.
PII_KEYS = {"first_name", "last_name", "name", "dob", "date_of_birth", "phone",
            "email", "address", "owner_user_id", "patient_id", "id"}


def _latest_consents(db: Session, patient_id: str) -> dict[str, bool]:
    rows = (
        db.query(Consent).filter(Consent.patient_id == patient_id)
        .order_by(Consent.created_at.desc()).all()
    )
    out: dict[str, bool] = {}
    for r in rows:
        out.setdefault(r.scope, r.granted)
    return out


def _confirmed_labs(db: Session, patient_id: str) -> list[LabResult]:
    return (
        db.query(LabResult)
        .filter(LabResult.patient_id == patient_id, LabResult.confirmed == True)  # noqa: E712
        .order_by(LabResult.analyte).all()
    )


def _imaging(db: Session, patient_id: str) -> list[ImagingFinding]:
    return (
        db.query(ImagingFinding)
        .filter(ImagingFinding.patient_id == patient_id)
        .order_by(ImagingFinding.created_at).all()
    )


def _latest_intake(db: Session, patient_id: str) -> Intake | None:
    return (
        db.query(Intake).filter(Intake.patient_id == patient_id)
        .order_by(Intake.created_at.desc()).first()
    )


def build_payload(db: Session, patient: Patient) -> dict:
    intake = _latest_intake(db, patient.id)
    labs = _confirmed_labs(db, patient.id)
    imaging = _imaging(db, patient.id)
    consents = _latest_consents(db, patient.id)

    payload = {
        "case_id": patient.case_id,                 # NOT the uuid, NOT a name
        "age_band": patient.age_band,               # derived; never DOB
        "sex": patient.sex.value if hasattr(patient.sex, "value") else str(patient.sex),
        "symptoms": intake.symptoms_text if intake else "",
        "labs": [
            {
                "analyte": l.analyte,
                "value": _coerce(l.value),
                "unit": l.unit,
                "ref_low": l.ref_low,
                "ref_high": l.ref_high,
                "flag": l.flag,
            }
            for l in labs
        ],
        "imaging": [f.text for f in imaging if f.text],
        "medications": list(intake.medications) if intake else [],
        "conditions": list(intake.conditions) if intake else [],
        "lifestyle": dict(intake.lifestyle) if intake else {},
        "consent": consents,
    }
    _assert_clean(payload)
    return payload


def summarize(db: Session, patient: Patient) -> dict:
    """Pre-flight completeness check (MiHealth §5 checklist). Returns counts + warnings
    and a hard `blocker` when a lab report was uploaded but no labs are confirmed."""
    intake = _latest_intake(db, patient.id)
    confirmed = _confirmed_labs(db, patient.id)
    lab_docs = (
        db.query(Document)
        .filter(Document.patient_id == patient.id, Document.doc_type == "lab").count()
    )
    symptoms = (intake.symptoms_text if intake else "").strip()
    tokens = [t for t in re.split(r"[,;\n]", symptoms) if t.strip()]
    conditions = list(intake.conditions) if intake else []
    medications = list(intake.medications) if intake else []
    imaging = [f for f in _imaging(db, patient.id) if f.text]
    consents = _latest_consents(db, patient.id)

    warnings: list[str] = []
    blocker: str | None = None

    if lab_docs > 0 and len(confirmed) == 0:
        blocker = (f"{lab_docs} lab report(s) uploaded but 0 confirmed labs — confirm the "
                   "extracted lab values before generating (otherwise the report is symptom-only).")
    elif len(confirmed) == 0:
        warnings.append("No labs will be sent — report will be symptom-only and likely incomplete.")
    if not symptoms:
        warnings.append("No symptoms entered.")
    elif len(tokens) < 2:
        warnings.append("Only one symptom listed — include ALL presenting complaints, comma-separated.")
    if not consents.get("ai_analysis"):
        warnings.append("ai_analysis consent not granted (generation will be blocked).")

    return {
        "confirmed_labs": len(confirmed),
        "lab_documents": lab_docs,
        "symptom_count": len(tokens),
        "conditions": len(conditions),
        "medications": len(medications),
        "imaging": len(imaging),
        "ai_analysis_consent": bool(consents.get("ai_analysis")),
        "warnings": warnings,
        "blocker": blocker,
        "ready": blocker is None and bool(consents.get("ai_analysis")),
    }


def _coerce(value: str):
    """Send numeric lab values as numbers (TSPI accepts float|str)."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def _assert_clean(payload: dict) -> None:
    extra = set(payload.keys()) - ALLOWED_KEYS
    if extra:
        raise ValueError(f"De-id guard: disallowed keys in payload: {extra}")
    leaked = set(payload.keys()) & PII_KEYS
    if leaked:
        raise ValueError(f"De-id guard: PII keys present: {leaked}")
    for lab in payload.get("labs", []):
        bad = set(lab.keys()) & PII_KEYS
        if bad:
            raise ValueError(f"De-id guard: PII in lab row: {bad}")
