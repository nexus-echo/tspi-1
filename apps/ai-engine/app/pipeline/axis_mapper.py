"""Stage 2 — Map biological signals to the 39 axes (async; RAG fallback for unknown labs).

Rules first; for concepts the rules can't map, fall back to async RAG (no-op unless vectors are
available). Severity is a placeholder pending the official Phase-1 scoring rules.
"""
from __future__ import annotations

from app.knowledge import retrieval
from app.knowledge.repository import KnowledgeRepo
from app.schemas import AxisScore, BiologicalSignal, KeyCode, Severity

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

_RAG_MIN_SCORE = 0.2


def _add(scored: dict, code: str, repo: KnowledgeRepo, severity: Severity,
         source: str, inferred: bool) -> None:
    if code in scored:
        scored[code].evidence.append(source)
        return
    meta = repo.axis(code)
    scored[code] = AxisScore(
        axis_code=code,
        axis_name=meta.get("name", code),
        domain_code=meta.get("domain_code"),
        key=KeyCode(meta["key"]) if meta.get("key") else None,
        severity=severity,
        inferred=inferred,
        evidence=[source],
    )


async def map_axes(signals: list[BiologicalSignal], repo: KnowledgeRepo) -> list[AxisScore]:
    scored: dict[str, AxisScore] = {}

    for sig in signals:
        axes = _CONCEPT_TO_AXES.get(sig.concept)
        if axes:
            sev = Severity.pathological if sig.direction in {"up", "down"} else Severity.functional_impairment
            for code in axes:
                _add(scored, code, repo, sev, sig.source, inferred=False)
            continue

        # RAG fallback (async; no-op unless vectors available)
        for hit in await retrieval.aretrieve(sig.concept, kind="axis", k=1):
            if hit.get("score", 0) >= _RAG_MIN_SCORE and hit.get("ref_code"):
                _add(scored, hit["ref_code"], repo, Severity.functional_impairment,
                     f"{sig.source} ~RAG({hit['score']})", inferred=True)

    return list(scored.values())
