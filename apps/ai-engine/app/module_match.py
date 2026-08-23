"""Phase 10 — TSPI Module Match v1.0 (approved formula, TSPI 3 Q10).

    30% Axis match + 25% Network match + 15% Evidence grade + 10% Patient phenotype fit
  + 10% Safety + 5% Treatment-step compatibility + 5% Historical response

Critical expert corrections encoded here:

  * SAFETY IS A GATE, NOT A SCORE. An absolute contraindication / major interaction sets
    module_status = EXCLUDED and module_match_score = not_calculated. We do NOT merely
    subtract 10 points.
  * MATCHING != PRESCRIBING. Modules map broadly, so a severe patient can match dozens.
    Selection ceiling: 1-3 core + 0-3 supporting (typical max 6); 7-8 needs senior approval;
    >8 needs explicit justification.
  * Mechanism DE-DUPLICATION: keep the highest-ranked representative of a duplicated mechanism.
  * Every matched-but-unselected module carries a structured reason_not_selected.

Weights live in data/module_match_config.json (configurable + version-controlled, not hard-coded).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_CFG = Path(__file__).resolve().parent.parent / "data" / "module_match_config.json"

VERSION = "TSPI-Module-Match-v1.0"


class ReasonNotSelected:
    CONTRAINDICATED = "CONTRAINDICATED"
    MAJOR_INTERACTION = "MAJOR_INTERACTION"
    DUPLICATE_MECHANISM = "DUPLICATE_MECHANISM"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    INSUFFICIENT_PATIENT_DATA = "INSUFFICIENT_PATIENT_DATA"
    NOT_STEP_COMPATIBLE = "NOT_STEP_COMPATIBLE"
    EXCESSIVE_MODULE_BURDEN = "EXCESSIVE_MODULE_BURDEN"
    LOWER_RANKED_THAN_SELECTED_ALTERNATIVE = "LOWER_RANKED_THAN_SELECTED_ALTERNATIVE"
    PHYSICIAN_EXCLUDED = "PHYSICIAN_EXCLUDED"
    DIAGNOSTIC_WORKUP_REQUIRED_FIRST = "DIAGNOSTIC_WORKUP_REQUIRED_FIRST"


_GRADE_VALUE = {"A": 1.0, "B": 0.75, "C": 0.5, "D": 0.25}


@lru_cache
def _cfg() -> dict:
    try:
        return json.loads(_CFG.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def weights() -> dict:
    return _cfg().get("weights", {"axis_match": 0.30, "network_match": 0.25, "evidence_grade": 0.15,
                                  "phenotype_fit": 0.10, "safety": 0.10,
                                  "step_compatibility": 0.05, "historical_response": 0.05})


def limits() -> dict:
    return _cfg().get("selection_limits", {"core_min": 1, "core_max": 3, "supporting_max": 3,
                                           "typical_total_max": 6, "senior_approval_above": 6,
                                           "justification_required_above": 8})


def _axis_match(mod, active_axes: dict[str, float]) -> float:
    """Fraction of the patient's active-axis burden this module covers (primary axes count more)."""
    if not active_axes:
        return 0.0
    hit = 0.0
    for ax, burden in active_axes.items():
        if ax in mod["target_axes"]:
            role_w = 1.0 if ax in mod.get("primary_axes", []) else 0.6
            hit += burden * role_w
    total = sum(active_axes.values()) or 1.0
    return min(1.0, hit / total)


def _evidence_grade(mod) -> tuple[float, str]:
    """31 Jul §8: 'not graded' is NOT 'weakest'. Ungraded -> NEUTRAL contribution + flag,
    never silently scored as D. Lowers overall confidence/coverage, not biological severity."""
    g = (mod.get("evidence_grade") or "").upper() or None
    if g in _GRADE_VALUE:
        return _GRADE_VALUE[g], g
    return 0.5, "EVIDENCE_NOT_GRADED"       # neutral, explicitly flagged (not defaulted to D)


def score_module(mod: dict, active_axes: dict[str, float], step_position: int | None = None,
                 historical: float | None = None, network_available: bool = False) -> dict:
    """Return the v1.0 breakdown for ONE module that has already passed the safety gate."""
    w = weights()
    axis = _axis_match(mod, active_axes)
    # 31 Jul §5 + Directive 9: the Network layer is mechanistic VALIDATION, never a candidate
    # source. Absent network data is NOT_ASSESSED, never 0, and must not be silently renormalised.
    network = 0.0                                     # placeholder weight only while unvalidated
    network_validation_status = "VALIDATED" if network_available else "NOT_ASSESSED"
    grade_val, grade = _evidence_grade(mod)
    phenotype = 0.5                                   # Phase 8 pending: neutral, not invented
    safety = 1.0 - min(1.0, 0.25 * len(mod.get("contraindications", [])))
    step = 1.0 if step_position is None else 1.0      # Phase: step map pending -> neutral
    hist = 0.5 if historical is None else historical

    total = (w["axis_match"] * axis + w["network_match"] * network +
             w["evidence_grade"] * grade_val + w["phenotype_fit"] * phenotype +
             w["safety"] * safety + w["step_compatibility"] * step +
             w["historical_response"] * hist)
    # Validated Score Coverage: how much of the weighting model is actually validated (not
    # NOT_ASSESSED). We surface the provisional score AND its coverage, never renormalise.
    validated_coverage = 1.0 - (w["network_match"] if network_validation_status == "NOT_ASSESSED" else 0.0)
    return {
        "module_match_score": round(100 * total, 1),
        "provisional": network_validation_status == "NOT_ASSESSED",
        "validated_score_coverage": round(100 * validated_coverage, 1),
        "network_validation_status": network_validation_status,
        "breakdown": {"axis_match": round(axis, 3), "network_match": network,
                      "evidence_grade": grade_val, "phenotype_fit": phenotype,
                      "safety": round(safety, 3), "step_compatibility": step,
                      "historical_response": hist},
        "evidence_grade_letter": grade,
        "network_match_available": network_available,
        "notes": [n for n in [
            ("evidence not yet graded -> neutral contribution, not defaulted to D"
             if grade == "EVIDENCE_NOT_GRADED" else None),
            None if network_available else "network validation NOT_ASSESSED (Network master pending)",
            "phenotype_fit neutral (Clinical Phenotype Engine pending)",
        ] if n],
    }


def dedupe_key(mod: dict) -> str:
    """Modules sharing a dominant axis pattern + bowel role are treated as one mechanism."""
    primary = ",".join(sorted(mod.get("primary_axes", []))[:3])
    return f"{mod.get('dose_type', 'severity')}|{primary}"


def select(candidates: list[dict]) -> dict:
    """Rank -> de-duplicate -> apply the ceiling. Returns selected + considered(with reasons).

    `candidates` are dicts with at least: module_code, module_match_score, module_status,
    dedupe_key. EXCLUDED modules never enter ranking (safety gate already removed them).
    """
    lim = limits()
    excluded = [c for c in candidates if c.get("module_status") == "EXCLUDED"]
    eligible = sorted([c for c in candidates if c.get("module_status") != "EXCLUDED"],
                      key=lambda c: c["module_match_score"], reverse=True)

    selected: list[dict] = []
    considered: list[dict] = list(excluded)
    seen_mech: dict[str, str] = {}

    for c in eligible:
        key = c.get("dedupe_key")
        if key in seen_mech:
            c["reason_not_selected"] = ReasonNotSelected.DUPLICATE_MECHANISM
            c["duplicate_of"] = seen_mech[key]
            considered.append(c)
            continue
        if len(selected) >= lim["typical_total_max"]:
            c["reason_not_selected"] = ReasonNotSelected.EXCESSIVE_MODULE_BURDEN
            considered.append(c)
            continue
        c["tier"] = "core" if len(selected) < lim["core_max"] else "supporting"
        seen_mech[key] = c["module_code"]
        selected.append(c)

    total = len(selected)
    return {
        "match_version": VERSION,
        "selected": selected,
        "considered": considered,
        "counts": {"matched": len(candidates), "excluded_by_safety_gate": len(excluded),
                   "selected": total,
                   "core": sum(1 for s in selected if s.get("tier") == "core"),
                   "supporting": sum(1 for s in selected if s.get("tier") == "supporting")},
        "requires_senior_approval": total > lim["senior_approval_above"],
        "requires_explicit_justification": total > lim["justification_required_above"],
        "limits": lim,
        "note": "Matching is not prescribing. The physician retains authority; this is a ceiling, "
                "not an absolute prescribing law.",
    }
