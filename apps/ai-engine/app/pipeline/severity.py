"""Stage 3b -- Network Severity Score (NSS) + System Priority Score (SPS), weight-aware.

Severity is inflammation-driven (official). Phase 4 adds optional per-axis WEIGHTS (learned by
the outcome loop); a missing/1.0 weight is neutral, so with no learning the scores are identical
to Phase 1-3. The NSS *formula* remains a documented heuristic pending the official one.
"""
from __future__ import annotations

from collections import defaultdict

from app.schemas import AxisScore, Severity

_SEV_W = {
    Severity.optimal: 0.0,
    Severity.subclinical: 0.33,
    Severity.functional_impairment: 0.66,
    Severity.pathological: 1.0,
}
_INFLAMMATORY_AXES = {"A1", "A2", "A3", "A4"}


def _w(weights: dict[str, float] | None, code: str) -> float:
    return (weights or {}).get(code, 1.0)


def compute_nss(axis_scores: list[AxisScore], weights: dict[str, float] | None = None) -> int:
    """0-100. Weighted burden + inflammatory amplifier. weights default to 1.0 (neutral)."""
    if not axis_scores:
        return 0
    num = sum(_SEV_W[a.severity] * _w(weights, a.axis_code) for a in axis_scores)
    den = sum(_w(weights, a.axis_code) for a in axis_scores) or 1.0
    burden = num / den
    infl = max(
        [_SEV_W[a.severity] for a in axis_scores if a.axis_code in _INFLAMMATORY_AXES] or [0.0]
    )
    nss = round(100 * (0.6 * burden + 0.4 * infl))
    return max(0, min(100, nss))


def compute_sps(axis_scores: list[AxisScore], weights: dict[str, float] | None = None) -> list[dict]:
    """Rank the 12 Systems by weighted summed axis severity. Highest priority first."""
    by_system: dict[str, float] = defaultdict(float)
    for a in axis_scores:
        by_system[a.domain_code or "D?"] += _SEV_W[a.severity] * _w(weights, a.axis_code)
    ranked = sorted(by_system.items(), key=lambda kv: kv[1], reverse=True)
    return [{"system": s, "priority_score": round(v, 2)} for s, v in ranked]
