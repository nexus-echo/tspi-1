"""Stage 1 — Normalize raw findings into standardized biological signals.

Generic by design: accepts ANY analyte/unit. Where a reference range is present we can
derive a flag; for unknown tests we fall back to semantic interpretation (RAG) later.
"""
from __future__ import annotations

from app.evidence import EvidenceStatus
from app.markers import (
    DirectionRule,
    ValueSourceType,
    interpret as marker_interpret,
    lookup as marker_lookup,
    resolve_context,
)
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
    present = {lab.analyte.strip().lower() for lab in patient.labs}

    for lab in patient.labs:
        flag = _flag(lab)
        direction = {"high": "up", "low": "down"}.get(flag or "", "abnormal")
        marker = marker_lookup(lab.analyte)

        # Default concept + evidence status (unchanged fallback for unknown labs)
        concept = _SEED_CONCEPTS.get(lab.analyte.strip().lower(), f"lab:{lab.analyte}")
        ev_status = EvidenceStatus.MEASURED

        if marker is not None:
            # Marker Registry is authoritative: value_source_type is SEPARATE from direction (25 Jul Q5a)
            ev_status = (EvidenceStatus.DERIVED
                         if marker.value_source_type is ValueSourceType.DERIVED
                         else EvidenceStatus.MEASURED)
            val = lab.value if isinstance(lab.value, (int, float)) else None
            interp = marker_interpret(marker, val, lab.ref_low, lab.ref_high)
            if interp["direction"] and interp["direction"] != "abnormal":
                direction = interp["direction"]

            if marker.direction_rule is DirectionRule.CONTEXT_DEPENDENT:
                # Ferritin et al.: the axis depends on co-present markers, never a single fixed axis.
                rule = resolve_context(marker, direction, present)
                if rule is None or rule.axis is None:
                    continue                       # ambiguous (e.g. high ferritin alone) -> assert nothing
                concept = rule.concept or marker.concept or concept
            else:
                concept = marker.concept or concept

        signals.append(
            BiologicalSignal(
                concept=concept,
                direction=direction,  # type: ignore[arg-type]
                source=f"{lab.analyte}={lab.value}{lab.unit or ''} ({flag or 'n/a'})",
                evidence_status=ev_status,
                value_source_type=(marker.value_source_type.value if marker else "MEASURED"),
            )
        )

    text = patient.symptoms.lower()
    for keyword, concept in _SEED_CONCEPTS.items():
        if keyword in text and keyword not in {"crp", "hba1c", "mcv", "tsh", "ft3"}:
            signals.append(
                BiologicalSignal(concept=concept, direction="abnormal",
                                 source=f"symptom:{keyword}",
                                 # symptoms are first-class biological evidence (not narrative text)
                                 evidence_status=EvidenceStatus.CLINICAL_INFERENCE)
            )

    # TODO(Phase 2): for concepts starting "lab:" (unknown tests), call RAG to interpret.
    return signals
