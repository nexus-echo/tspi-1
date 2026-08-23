"""Stage 3b — Network Severity Score (NSS v0.3) + System Priority Score (SPS).

FINAL ruling of 5 Aug 2026 (`...Final Review...pdf`, §14 + Final Developer Lock):

    "Data Completeness must NOT numerically reduce the severity of an observed abnormality.
     Final Severity = Severity x Data Completeness is PROHIBITED."

Severity represents the biological magnitude supported by the available evidence. Confidence,
Data Completeness and Evidence Quality describe the RELIABILITY and COVERAGE of the assessment —
they are reported SEPARATELY and must never act as severity multipliers. (This supersedes the
25 Jul weighting used in v0.2.)

NSS is therefore computed as the severity aggregate of the axes that satisfy the required
assessment state, times a bounded network-burden factor:

    included (headline "Observed NSS") = axes with status in
        {PROVISIONALLY_ASSESSED, ASSESSED, HIGH_CONFIDENCE_ASSESSED}   (and scorable)
    excluded                            = NOT_ASSESSED, AXIS_CANDIDATE  (never scored)

    ObservedNSS = mean(Severity_i over included) x NetworkFactor
    AssessmentStatus = PROVISIONAL if any included axis is only PROVISIONALLY_ASSESSED,
                       else ASSESSED

Every NSS output also reports Assessment Coverage, Overall Confidence, Biological Uncertainty,
Assessment Status and the Algorithm Version — so reliability is visible without ever bending the
severity number. A critical-value alert is NEVER diluted by this score (handled in red_flags.py).
"""
from __future__ import annotations

import json
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from app.evidence import label_confidence, label_uncertainty
from app.schemas import AxisScore, Severity

_CFG_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "nss_config.json"

_SEV_SCORE = {
    Severity.optimal: 0.0,
    Severity.subclinical: 33.0,
    Severity.functional_impairment: 66.0,
    Severity.pathological: 100.0,
}

# Assessment states (mirror app.evidence.AxisStatus values) that may enter scoring.
_FINAL_STATES = {"ASSESSED", "HIGH_CONFIDENCE_ASSESSED"}
_INCLUDED_STATES = {"PROVISIONALLY_ASSESSED", "ASSESSED", "HIGH_CONFIDENCE_ASSESSED"}


@lru_cache
def _cfg() -> dict:
    try:
        return json.loads(_CFG_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"abnormal_axis_threshold": 50,
                "network_factor": [{"min_abnormal_axes": 0, "max_abnormal_axes": 99, "factor": 1.0}],
                "nss_algorithm_version": "TSPI-NSS-v0.3"}


def algorithm_version() -> str:
    return _cfg().get("nss_algorithm_version", "TSPI-NSS-v0.3")


def _status(a: AxisScore) -> str:
    s = getattr(a, "status", None)
    return getattr(s, "value", s) or ""


def _axis_value(a: AxisScore) -> float:
    v = getattr(a, "score", None)
    return float(v) if v is not None else _SEV_SCORE[a.severity]


def _confidence(a: AxisScore) -> float:
    c = getattr(a, "confidence", None)
    return float(c) if isinstance(c, (int, float)) and c >= 0 else 0.0


def _completeness(a: AxisScore) -> float:
    c = getattr(a, "data_completeness", None)
    return float(c) if isinstance(c, (int, float)) and c >= 0 else 0.0


def _uncertainty(a: AxisScore) -> float:
    u = getattr(a, "biological_uncertainty", None)
    return float(u) if isinstance(u, (int, float)) and u >= 0 else 0.0


def _included(axis_scores: list[AxisScore]) -> list[AxisScore]:
    """Axes eligible for the (provisional-or-above) Observed NSS. Candidates/unassessed are excluded,
    and HYPOTHESIS-only axes never score (scoring_effect False)."""
    return [a for a in axis_scores
            if getattr(a, "scoring_effect", True) and _status(a) in _INCLUDED_STATES]


def _severity_mean(axes: list[AxisScore]) -> float:
    return (sum(_axis_value(a) for a in axes) / len(axes)) if axes else 0.0


def network_factor(abnormal_count: int) -> float:
    for band in _cfg().get("network_factor", []):
        if band["min_abnormal_axes"] <= abnormal_count <= band["max_abnormal_axes"]:
            return float(band["factor"])
    return 1.0


def compute_nss(axis_scores: list[AxisScore], weights: dict[str, float] | None = None) -> int:
    """Observed NSS = mean severity over qualifying axes x network factor. No reliability weighting."""
    included = _included(axis_scores)
    if not included:
        return 0                      # no qualifying evidence != healthy; surfaced as NOT_ASSESSED
    threshold = _cfg().get("abnormal_axis_threshold", 50)
    abnormal = sum(1 for a in included if _axis_value(a) >= threshold)
    observed = _severity_mean(included) * network_factor(abnormal)
    return max(0, min(100, round(observed)))


def _mean(vals: list[float]) -> float:
    return (sum(vals) / len(vals)) if vals else 0.0


def nss_detail(axis_scores: list[AxisScore], weights: dict[str, float] | None = None) -> dict:
    """Full auditable NSS object. Reliability dimensions are REPORTED, never applied to severity."""
    included = _included(axis_scores)
    final_axes = [a for a in included if _status(a) in _FINAL_STATES]
    threshold = _cfg().get("abnormal_axis_threshold", 50)
    abnormal = sum(1 for a in included if _axis_value(a) >= threshold)
    nf = network_factor(abnormal)
    observed = max(0, min(100, round(_severity_mean(included) * nf)))

    if not included:
        status = "NOT_ASSESSED"
    elif any(_status(a) == "PROVISIONALLY_ASSESSED" for a in included):
        status = "PROVISIONAL"          # relies on at least one provisional axis
    else:
        status = "ASSESSED"

    # Assessment Coverage: of the axes we have evidence for, how many reached scoring threshold.
    coverage = round(100 * len(included) / max(1, len(axis_scores)))
    conf = _mean([_confidence(a) for a in included])
    unc = _mean([_uncertainty(a) for a in included])

    return {
        "algorithm_version": algorithm_version(),
        "observed_nss": observed,
        "final_nss": observed,                      # headline number (back-compat alias)
        "assessment_status": status,                # NOT_ASSESSED | PROVISIONAL | ASSESSED
        "assessment_coverage": coverage,            # % of evidenced axes that qualified
        "overall_confidence": round(conf, 2),
        "overall_confidence_label": label_confidence(conf),
        "biological_uncertainty": round(unc, 2),
        "biological_uncertainty_label": label_uncertainty(unc),
        "included_axis_count": len(included),
        "final_axis_count": len(final_axes),
        "excluded_candidate_or_unassessed": len(axis_scores) - len(included),
        "abnormal_axes_at_threshold": abnormal,
        "abnormal_axis_threshold": threshold,
        "network_factor": nf,
        "severity_rule": ("Severity reflects biological magnitude only. Confidence and Data "
                          "Completeness are reported separately and NEVER reduce severity "
                          "(5 Aug final ruling)."),
        "contributors": [
            {"axis": a.axis_code, "severity": _axis_value(a), "status": _status(a),
             "confidence": _confidence(a), "data_completeness": _completeness(a)}
            for a in included
        ],
    }


def compute_sps(axis_scores: list[AxisScore], weights: dict[str, float] | None = None) -> list[dict]:
    """Rank the 12 Systems by qualifying axis burden. Prioritisation may use learned weights;
    it does NOT feed back into severity."""
    def _w(code: str) -> float:
        return (weights or {}).get(code, 1.0)
    by_system: dict[str, float] = defaultdict(float)
    for a in _included(axis_scores):
        by_system[a.domain_code or "D?"] += (_axis_value(a) / 100.0) * _w(a.axis_code)
    ranked = sorted(by_system.items(), key=lambda kv: kv[1], reverse=True)
    return [{"system": s, "priority_score": round(v, 2)} for s, v in ranked]
