"""Stage 1 — Normalize raw findings into standardized biological signals.

Generic by design: accepts ANY analyte/unit. Where a reference range is present we can
derive a flag; for unknown tests we fall back to semantic interpretation (RAG) later.
"""
from __future__ import annotations

from app.schemas import BiologicalSignal, LabResult, PatientInput

# Illustrative seed map (symptom/lab keyword -> biological concept).
# Phase 1: expand into a maintained rules table; Phase 2: RAG handles the long tail.
_SEED_CONCEPTS: dict[str, str] = {
    "crp": "systemic inflammation",
    "hba1c": "glucose / insulin dysregulation",
    "glucose": "glucose / insulin dysregulation",
    "hemoglobin": "anemia / oxygen transport",
    "mcv": "red cell size (microcytic/macrocytic)",
    "tsh": "thyroid axis",
    "ft3": "thyroid axis",
    "ige": "immune hypersensitivity / barrier",
    "vitamin d": "immune-metabolic support",
    "fatigue": "mitochondrial / energy",
    "stress": "autonomic / HPA",
}


def _flag(lab: LabResult) -> str | None:
    if lab.flag:
        return lab.flag
    if isinstance(lab.value, (int, float)):
        if lab.ref_high is not None and lab.value > lab.ref_high:
            return "high"
        if lab.ref_low is not None and lab.value < lab.ref_low:
            return "low"
    return None


def normalize(patient: PatientInput) -> list[BiologicalSignal]:
    signals: list[BiologicalSignal] = []

    for lab in patient.labs:
        flag = _flag(lab)
        concept = _SEED_CONCEPTS.get(lab.analyte.strip().lower(), f"lab:{lab.analyte}")
        direction = {"high": "up", "low": "down"}.get(flag or "", "abnormal")
        signals.append(
            BiologicalSignal(
                concept=concept,
                direction=direction,  # type: ignore[arg-type]
                source=f"{lab.analyte}={lab.value}{lab.unit or ''} ({flag or 'n/a'})",
            )
        )

    text = patient.symptoms.lower()
    for keyword, concept in _SEED_CONCEPTS.items():
        if keyword in text and keyword not in {"crp", "hba1c", "mcv", "tsh", "ft3"}:
            signals.append(
                BiologicalSignal(concept=concept, direction="abnormal", source=f"symptom:{keyword}")
            )

    # TODO(Phase 2): for concepts starting "lab:" (unknown tests), call RAG to interpret.
    return signals
