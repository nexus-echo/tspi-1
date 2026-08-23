"""Phase 7 — Red-Flag screening. MANDATORY, and it runs BEFORE any network/axis/module reasoning.

Expert rule (TSPI 3, Q5):
    "Red-Flag Screening is mandatory and must run before any TSPI Network, Axis or Module
     recommendation... The initial production system should not rely on the LLM to determine Red
     Flags from unrestricted prose alone. The Red-Flag engine should be deterministic, based on
     structured inputs and clinically reviewed rules."

So: NO LLM is involved here. Matching is deterministic over structured inputs (labs, conditions)
and explicit clinically-reviewed phrase rules. Conservative by design -- screening may only
ESCALATE care, never withhold it.

Critical values are a SEPARATE layer (Round-2 Q2): a critical alert must never be diluted by
averaging it into a score. NSS 28 + critical potassium is still an emergency.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).resolve().parent.parent / "data" / "red_flag_rules.json"

CLASS_1 = "CLASS_1_EMERGENCY"
CLASS_2 = "CLASS_2_URGENT"
CLASS_3 = "CLASS_3_STANDARD_WORKUP"
_SEVERITY_ORDER = {CLASS_1: 3, CLASS_2: 2, CLASS_3: 1}


@lru_cache
def _rules() -> dict:
    try:
        return json.loads(_DATA.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"action_classes": {}, "symptom_rules": [], "condition_rules": [],
                "critical_value_rules": []}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def _unit_ok(lab_unit: str | None, units: list[str]) -> bool:
    """If the rule names units, the lab's unit must match one (prevents mg/dL vs mmol/L errors)."""
    if not units:
        return True
    return _norm(lab_unit or "").replace(" ", "") in {u.replace(" ", "") for u in units}


def _match_phrases(text: str, phrases: list[str]) -> str | None:
    for p in phrases:
        if p and p in text:
            return p
    return None


def screen(patient) -> dict:
    """Deterministic red-flag screen. Returns the gate decision + findings."""
    r = _rules()
    findings: list[dict] = []

    text = _norm(getattr(patient, "symptoms", "") or "")
    conditions = [_norm(c) for c in (getattr(patient, "conditions", None) or [])]
    cond_text = " ; ".join(conditions)

    # 1) symptom phrase rules (deterministic, clinically-reviewed phrases -- not free LLM reading)
    for rule in r.get("symptom_rules", []):
        hit = _match_phrases(text, [_norm(m) for m in rule.get("match_any", [])])
        if hit:
            findings.append({"red_flag_code": rule["red_flag_code"], "name": rule["name_en"],
                             "action_class": rule["action_class"], "source": "symptom",
                             "matched": hit, "symptom_area": rule.get("symptom_area")})

    # 2) condition rules (structured input)
    for rule in r.get("condition_rules", []):
        hit = _match_phrases(cond_text, [_norm(m) for m in rule.get("match_any", [])])
        if hit:
            findings.append({"red_flag_code": rule["red_flag_code"], "name": rule["name_en"],
                             "action_class": rule["action_class"], "source": "condition",
                             "matched": hit})

    # 3) CRITICAL VALUE layer -- separate, never averaged into any score
    critical: list[dict] = []
    for lab in (getattr(patient, "labs", None) or []):
        analyte = _norm(getattr(lab, "analyte", ""))
        value = getattr(lab, "value", None)
        if not isinstance(value, (int, float)):
            continue
        for rule in r.get("critical_value_rules", []):
            if rule["analyte"] not in analyte:
                continue
            if not _unit_ok(getattr(lab, "unit", None), rule.get("units", [])):
                continue
            lo, hi = rule.get("critical_low"), rule.get("critical_high")
            breach = None
            if lo is not None and value < lo:
                breach = f"{analyte}={value} below critical low {lo}"
            elif hi is not None and value > hi:
                breach = f"{analyte}={value} above critical high {hi}"
            if breach:
                f = {"red_flag_code": rule["red_flag_code"], "name": rule["name_en"],
                     "action_class": rule["action_class"], "source": "critical_value",
                     "matched": breach}
                findings.append(f)
                critical.append(f)

    if not findings:
        return {"screened": True, "red_flags": [], "critical_values": [],
                "action_class": None, "required_action": None,
                "release_block": False, "module_plan_allowed": True,
                "module_plan_requires_clinician_override": False,
                "cause_specific_module_plan": "allowed",
                "registry_version": r.get("dataset_version"),
                "registry_authoritative": r.get("authoritative", False)}

    # highest severity wins
    worst = max(findings, key=lambda f: _SEVERITY_ORDER.get(f["action_class"], 0))["action_class"]
    cfg = r.get("action_classes", {}).get(worst, {})
    return {
        "screened": True,
        "red_flags": findings,
        "critical_values": critical,
        "action_class": worst,
        "required_action": cfg.get("required_action"),
        "release_block": bool(cfg.get("release_block", False)),
        "module_plan_allowed": bool(cfg.get("module_plan_allowed", True)),
        "module_plan_requires_clinician_override": bool(
            cfg.get("module_plan_requires_clinician_override", False)),
        "cause_specific_module_plan": cfg.get("cause_specific_module_plan", "allowed"),
        "supportive_plan": cfg.get("supportive_plan"),
        "registry_version": r.get("dataset_version"),
        "registry_authoritative": r.get("authoritative", False),
    }
