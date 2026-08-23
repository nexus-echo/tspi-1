"""Stage 2 — Map biological signals to the 39 axes (async; RAG fallback for unknown labs).

Phase 6: every assessed axis now carries the four required dimensions (Evidence Status/Grade,
Confidence, Data Completeness, Biological Uncertainty) and an explicit AxisStatus. Axes we cannot
assess are returned separately as NOT_ASSESSED with a reason -- never omitted, never defaulted,
never read as "normal".

RAG-inferred axes are HYPOTHESIS: they are surfaced for the differential but contribute NOTHING
to any score (expert hard rule).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.evidence import (
    EvidenceItem,
    EvidenceStatus,
    EvidenceWeight,
    axis_status,
    biological_uncertainty,
    confidence as calc_confidence,
    contributes_to_score,
    data_completeness,
    label_confidence,
    label_uncertainty,
)
from app.knowledge import retrieval
from app.knowledge.repository import KnowledgeRepo
from app.schemas import AxisScore, BiologicalSignal, KeyCode, NotAssessedAxis, Severity

_CONCEPT_TO_AXES: dict[str, list[str]] = {
    "systemic inflammation": ["A1"],
    "glucose / insulin dysregulation": ["A5"],
    "anemia / oxygen transport": ["A26", "A8"],
    "red cell size (microcytic/macrocytic)": ["A26"],
    "thyroid axis": ["A33"],
    "immune hypersensitivity / barrier": ["A2", "A18"],
    "immune-metabolic support": ["A15"],
    "mitochondrial / energy": ["A8"],
    "autonomic / HPA": ["A34"],
}

# Evidence a full assessment of an axis would expect. Placeholder until the official
# per-axis `minimum_evidence` / accepted_markers arrive (expert Q9).
_EXPECTED = [EvidenceWeight.CORE, EvidenceWeight.SUPPORTING, EvidenceWeight.OPTIONAL]

_RAG_MIN_SCORE = 0.2
_DATA = Path(__file__).resolve().parent.parent.parent / "data" / "tspi_axes_39.json"


@lru_cache
def _axis_master() -> dict:
    try:
        d = json.loads(_DATA.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    return {a["axis_id"]: a for a in d.get("axes", [])}


def _weight_class(sig: BiologicalSignal) -> EvidenceWeight:
    """A measured lab is CORE evidence; a symptom is SUPPORTING."""
    return EvidenceWeight.CORE if sig.evidence_status is EvidenceStatus.MEASURED else EvidenceWeight.SUPPORTING


def _add(scored: dict, code: str, repo: KnowledgeRepo, severity: Severity,
         sig_source: str, status: EvidenceStatus, weight: EvidenceWeight, inferred: bool) -> None:
    item = EvidenceItem(source=sig_source, status=status, weight_class=weight)
    if code in scored:
        scored[code].evidence.append(sig_source)
        scored[code].evidence_items.append(item)
        return
    meta = repo.axis(code)
    master = _axis_master().get(code, {})
    # Prefer the DB catalog; fall back to the frozen axis master (the ontology source of truth).
    name = meta.get("name") or code
    if name == code and master:
        name = master.get("name", code)
    domain = meta.get("domain_code") or (f"D{master['domain_num']}" if master.get("domain_num") else None)
    scored[code] = AxisScore(
        axis_code=code,
        axis_name=name,
        domain_code=domain,
        key=KeyCode(meta["key"]) if meta.get("key") else None,
        severity=severity,
        inferred=inferred,
        evidence=[sig_source],
        evidence_items=[item],
    )


_SEV_SCORE = {Severity.optimal: 0.0, Severity.subclinical: 33.0,
              Severity.functional_impairment: 66.0, Severity.pathological: 100.0}


def _finalize(a: AxisScore) -> AxisScore:
    """Compute the four dimensions + status for one assessed axis."""
    completeness = data_completeness(a.evidence_items, _EXPECTED)
    conf = calc_confidence(a.evidence_items, completeness)
    st, reason = axis_status(a.evidence_items, completeness)
    usable = [i for i in a.evidence_items if contributes_to_score(i.status)]

    a.data_completeness = completeness
    a.confidence = conf
    a.confidence_label = label_confidence(conf)
    a.status = st
    a.reason = reason
    a.scoring_effect = bool(usable)
    a.evidence_status = (max(usable, key=lambda i: i.status is EvidenceStatus.MEASURED).status
                         if usable else EvidenceStatus.HYPOTHESIS)
    # more candidate explanations when evidence is thin/indirect
    candidates = 1 if a.evidence_status is EvidenceStatus.MEASURED else 3
    a.biological_uncertainty = biological_uncertainty(
        candidate_models=candidates, completeness=completeness,
        discriminating_evidence_missing=completeness < 0.6)
    a.uncertainty_label = label_uncertainty(a.biological_uncertainty)
    # HYPOTHESIS-only -> no score at all (must never raise anything)
    a.score = _SEV_SCORE[a.severity] if a.scoring_effect else None
    if not a.scoring_effect:
        a.reason = "HYPOTHESIS_ONLY_NOT_SCORED"
    a.missing_evidence = [] if completeness >= 1.0 else ["confirmatory marker(s) for this axis"]
    return a


def _not_assessed(assessed: set[str], repo: KnowledgeRepo) -> list[NotAssessedAxis]:
    """Every axis we could NOT assess, stated explicitly (never silently absent)."""
    out: list[NotAssessedAxis] = []
    for code, meta in sorted(_axis_master().items(), key=lambda kv: kv[1]["axis_num"]):
        if code in assessed:
            continue
        out.append(NotAssessedAxis(
            axis_code=code,
            axis_name=meta.get("name", code),
            domain_code=f"D{meta.get('domain_num')}" if meta.get("domain_num") else None,
            reason="required markers unavailable",
            required_evidence=["accepted markers / clinical features for this axis"],
        ))
    return out


def _severity_from_weight(w: float) -> Severity:
    """Phenotype weight -> axis severity. Deliberately conservative: symptoms indicate the
    POSSIBILITY of involvement; they never assert a pathological mechanism on their own."""
    if w >= 0.6:
        return Severity.functional_impairment
    return Severity.subclinical


async def map_axes(signals: list[BiologicalSignal], repo: KnowledgeRepo,
                   phenotype_result: dict | None = None
                   ) -> tuple[list[AxisScore], list[NotAssessedAxis]]:
    """Returns (assessed_axes, not_assessed_axes).

    Phase 8: the clinical phenotype contributes CLINICAL_INFERENCE evidence, so an axis can be
    assessed from symptoms alone -- no specialist biomarker required (expert Part 1).
    """
    scored: dict[str, AxisScore] = {}

    for sig in signals:
        axes = _CONCEPT_TO_AXES.get(sig.concept)
        if axes:
            sev = Severity.pathological if sig.direction in {"up", "down"} else Severity.functional_impairment
            for code in axes:
                _add(scored, code, repo, sev, sig.source, sig.evidence_status,
                     _weight_class(sig), inferred=False)
            continue

        # RAG fallback -> HYPOTHESIS: shown in the differential, contributes nothing to scoring.
        for hit in await retrieval.aretrieve(sig.concept, kind="axis", k=1):
            if hit.get("score", 0) >= _RAG_MIN_SCORE and hit.get("ref_code"):
                _add(scored, hit["ref_code"], repo, Severity.functional_impairment,
                     f"{sig.source} ~RAG({hit['score']})", EvidenceStatus.HYPOTHESIS,
                     EvidenceWeight.OPTIONAL, inferred=True)

    # Phase 8 — symptoms are first-class biological evidence.
    for ax, weight in ((phenotype_result or {}).get("axis_candidates") or {}).items():
        if weight <= 0:
            continue
        _add(scored, ax, repo, _severity_from_weight(weight),
             f"clinical phenotype (weight {round(weight, 2)})",
             EvidenceStatus.CLINICAL_INFERENCE, EvidenceWeight.SUPPORTING, inferred=False)

    assessed = [_finalize(a) for a in scored.values()]
    return assessed, _not_assessed(set(scored), repo)
