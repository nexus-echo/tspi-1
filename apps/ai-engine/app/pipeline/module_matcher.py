"""Stage 5 — Match catalog modules to active axes, then SELECT a prescribable plan.

Phase 10 pipeline:
    candidates -> SAFETY GATE (hard exclusion) -> Module Match v1.0 scoring
               -> mechanism de-duplication -> selection ceiling -> reasons for everything else

"Matching does not mean prescribing" (expert Q10): a severe patient may match dozens of modules,
so the ceiling (1-3 core + 0-3 supporting) is what makes the plan clinically realistic.
"""
from __future__ import annotations

from app import module_match, safety
from app.knowledge.repository import KnowledgeRepo
from app.module_match import ReasonNotSelected
from app.schemas import AxisScore, ModulePick


def _active_axes(axis_scores: list[AxisScore]) -> dict[str, float]:
    """Patient's active-axis burden (0-1 per axis), evidence-weighted. Drivers first."""
    out: dict[str, float] = {}
    for a in axis_scores:
        if not getattr(a, "scoring_effect", True):
            continue                      # HYPOTHESIS-only axes never drive module selection
        score = a.score if a.score is not None else 0.0
        conf = getattr(a, "confidence", 1.0) or 1.0
        burden = (score / 100.0) * conf
        if a.is_driver:
            burden *= 1.25
        if burden > 0:
            out[a.axis_code] = round(min(1.0, burden), 4)
    return out


def _absolute_contraindication(repo: KnowledgeRepo, code: str, medications: list[str],
                               conditions: list[str]) -> str | None:
    """Hard safety gate. Returns a reason when the module must be EXCLUDED outright."""
    if repo.is_contraindicated(code, medications):
        return ReasonNotSelected.CONTRAINDICATED
    return None


def match(axis_scores: list[AxisScore], repo: KnowledgeRepo, medications: list[str],
          conditions: list[str] | None = None, step_position: int | None = None) -> dict:
    """Returns {'selected': [ModulePick], 'considered': [ModulePick], 'selection': {...}}."""
    conditions = conditions or []
    active = _active_axes(axis_scores)

    # 1) collect candidates from the official axis->module map
    picks: dict[str, ModulePick] = {}
    raw: dict[str, dict] = {}
    for axis in sorted(active, key=lambda c: active[c], reverse=True):
        for mod in repo.modules_for_axis(axis):
            code = mod["code"]
            role = mod.get("role", "primary")
            if code in picks:
                if axis not in picks[code].target_axes:
                    picks[code].target_axes.append(axis)
                picks[code].axis_roles[axis] = role
                raw[code]["target_axes"].append(axis)
                if role == "primary":
                    raw[code]["primary_axes"].append(axis)
                continue
            contra = repo.module_contraindications(code)
            picks[code] = ModulePick(
                module_code=code, module_name=mod.get("name"), target_axes=[axis],
                mechanism=mod.get("mechanism"), clinical_role=mod.get("role"),
                safety=mod.get("safety"), resolved=mod.get("resolved", True),
                phytocore_code=mod.get("phytocore"), dose_type=mod.get("dose_type", "severity"),
                status=mod.get("status", "active"), axis_roles={axis: role},
                contraindications=contra,
            )
            raw[code] = {"module_code": code, "target_axes": [axis],
                         "primary_axes": [axis] if role == "primary" else [],
                         "dose_type": mod.get("dose_type", "severity"),
                         "contraindications": contra,
                         "evidence_grade": mod.get("evidence_grade")}

    # 2) SAFETY GATE + scoring
    candidates: list[dict] = []
    for code, pick in picks.items():
        blocked = _absolute_contraindication(repo, code, medications, conditions)
        if blocked:
            pick.module_status = "EXCLUDED"
            pick.safety_outcome = safety.SafetyOutcome.CONTRAINDICATED.value  # categorical, not a score
            pick.module_match_score = None          # not_calculated -- NOT a -10 penalty
            pick.reason_not_selected = blocked
            candidates.append({"module_code": code, "module_status": "EXCLUDED",
                               "module_match_score": -1, "dedupe_key": None, "_pick": pick})
            continue
        # cleared the absolute gate: monitor if the module carries any contraindication note
        pick.safety_outcome = (safety.SafetyOutcome.PASS_WITH_MONITORING.value
                               if pick.contraindications else safety.SafetyOutcome.PASS.value)
        sc = module_match.score_module(raw[code], active, step_position=step_position)
        pick.module_match_score = sc["module_match_score"]
        pick.match_breakdown = sc["breakdown"]
        pick.match_notes = sc["notes"]
        candidates.append({"module_code": code, "module_status": "ELIGIBLE",
                           "module_match_score": sc["module_match_score"],
                           "dedupe_key": module_match.dedupe_key(raw[code]), "_pick": pick})

    # 3) de-dupe + ceiling
    result = module_match.select(candidates)

    selected: list[ModulePick] = []
    considered: list[ModulePick] = []
    for c in result["selected"]:
        p = c["_pick"]
        p.tier = c.get("tier")
        selected.append(p)
    for c in result["considered"]:
        p = c["_pick"]
        p.reason_not_selected = c.get("reason_not_selected") or p.reason_not_selected
        p.duplicate_of = c.get("duplicate_of")
        considered.append(p)

    selection = {k: v for k, v in result.items() if k not in ("selected", "considered")}
    return {"selected": selected, "considered": considered, "selection": selection}
