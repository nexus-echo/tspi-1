"""Phenotype Registry (Phase 8.3b) — the NAMED, VERSIONED phenotype layer.

Domain-expert ruling of 25 Jul 2026 (Q3, Option A): a phenotype is a NAMED clinical pattern
(e.g. "Upper-Digestive Dysfunction"), and the reasoning path is

        Symptom  ->  Phenotype  ->  Axis        (NOT Symptom -> Axis directly)

The dev team proposes the starter list; every entry is status=CANDIDATE until a domain expert
approves it. A matched phenotype PROPOSES candidate axes with weights — it never asserts an axis
on its own, and its evidence is CLINICAL_INFERENCE (symptom-derived), never MEASURED.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel

_DATA = Path(__file__).resolve().parent.parent / "data" / "phenotype_registry.json"


class Phenotype(BaseModel):
    phenotype_code: str
    phenotype_name_en: str
    phenotype_name_th: str | None = None
    required_features: list[str] = []
    supporting_features: list[str] = []
    exclusion_features: list[str] = []
    red_flag_overrides: list[str] = []
    candidate_axis_codes: list[str] = []
    axis_evidence_weights: dict[str, float] = {}
    minimum_feature_count: int = 1
    confidence_rule: str | None = None
    network_hint: list[str] = []
    status: str = "CANDIDATE"
    version: str = "0.0.0"
    approved_by: str | None = None


@lru_cache
def _doc() -> dict:
    try:
        return json.loads(_DATA.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"phenotypes": []}


@lru_cache
def _phenotypes() -> list[Phenotype]:
    return [Phenotype(**p) for p in _doc().get("phenotypes", [])]


def registry_version() -> str:
    return _doc().get("dataset_version", "0.0.0")


def is_authoritative() -> bool:
    return bool(_doc().get("authoritative", False))


def match(symptom_codes: set[str]) -> list[dict]:
    """Return the phenotypes that fire for this set of symptom codes.

    A phenotype fires when: every required feature is present, no exclusion feature is present,
    and the count of matched (required + supporting) features >= minimum_feature_count.
    Confidence = matched / (required + supporting), reported separately from any score.
    """
    out: list[dict] = []
    for ph in _phenotypes():
        req = set(ph.required_features)
        sup = set(ph.supporting_features)
        exc = set(ph.exclusion_features)
        if req and not req <= symptom_codes:
            continue
        if exc & symptom_codes:
            continue
        matched = (req | sup) & symptom_codes
        if len(matched) < ph.minimum_feature_count:
            continue
        denom = len(req | sup) or 1
        confidence = round(len(matched) / denom, 3)
        out.append({
            "phenotype_code": ph.phenotype_code,
            "phenotype_name_en": ph.phenotype_name_en,
            "phenotype_name_th": ph.phenotype_name_th,
            "matched_features": sorted(matched),
            "candidate_axis_codes": ph.candidate_axis_codes,
            "axis_evidence_weights": ph.axis_evidence_weights,
            "confidence": confidence,
            "network_hint": ph.network_hint,
            "red_flag_overrides": ph.red_flag_overrides,
            "status": ph.status,
            "version": ph.version,
        })
    out.sort(key=lambda d: d["confidence"], reverse=True)
    return out
