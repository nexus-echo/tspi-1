"""Phase 8 — Clinical Phenotype Engine.

The expert's central correction (Part 1 + Q4):

    "Symptoms are biological evidence... TSPI-AI must not wait for specialist tests before it can
     analyse. A normal test narrows the differential; it does not erase the symptom. But the AI
     must not swing from hallucinating labs to hallucinating networks from symptoms."

So this engine is deliberately PROBABILISTIC and DIFFERENTIAL:

  * one symptom -> MANY candidate axes (never 1:1)
  * base weights 0.25 / 0.50 / 0.75 / 1.00, adjusted by co-symptoms, triggers, clusters
  * symptom BURDEN is reported separately from attribution CONFIDENCE
  * normal tests reduce probability of structural disease, never erase the symptom
  * missing discriminators become adaptive follow-up QUESTIONS, not guesses

Deterministic: dictionary-driven matching over structured symptoms (or, for back-compat, a
keyword scan of free text). No LLM decides an axis here.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from app import phenotype_registry

_DATA = Path(__file__).resolve().parent.parent / "data"

MAX_WEIGHT = 1.0


@lru_cache
def _dict() -> dict:
    try:
        return json.loads((_DATA / "symptom_dictionary.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"symptoms": [], "clusters": []}


@lru_cache
def _negative_rules() -> dict:
    try:
        return json.loads((_DATA / "negative_test_rules.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"rules": []}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def _identify(patient) -> list[dict]:
    """Match symptoms from structured input first; fall back to a deterministic keyword scan."""
    found: dict[str, dict] = {}
    text = _norm(getattr(patient, "symptoms", "") or "")
    structured = getattr(patient, "structured_symptoms", None) or []

    # structured symptoms (preferred)
    for sx in structured:
        blob = _norm(" ".join(filter(None, [
            sx.symptom_code or "", sx.canonical_name_en or "", sx.display_name_th or "",
            " ".join(sx.associated_symptoms or [])])))
        for entry in _dict().get("symptoms", []):
            if entry["symptom_code"] == sx.symptom_code or any(
                    _norm(m) in blob for m in entry.get("match_any", [])):
                found.setdefault(entry["symptom_code"], {"entry": entry, "structured": sx,
                                                         "matched_on": "structured"})
        for a in (sx.associated_symptoms or []):
            for entry in _dict().get("symptoms", []):
                if any(_norm(m) in _norm(a) for m in entry.get("match_any", [])):
                    found.setdefault(entry["symptom_code"],
                                     {"entry": entry, "structured": None, "matched_on": "associated"})

    # free text fallback
    for entry in _dict().get("symptoms", []):
        if entry["symptom_code"] in found:
            continue
        for m in entry.get("match_any", []):
            if _norm(m) and _norm(m) in text:
                found[entry["symptom_code"]] = {"entry": entry, "structured": None,
                                                "matched_on": "free_text"}
                break
    return list(found.values())


def _triggers(patient, hits) -> set[str]:
    t = set()
    text = _norm(getattr(patient, "symptoms", "") or "")
    for h in hits:
        sx = h.get("structured")
        if sx:
            for x in (sx.triggering_factors or []):
                t.add(_norm(x))
            if sx.stress_relationship:
                t.add("stress")
            if sx.meal_relationship:
                t.add("meal")
    if "stress" in text or "worse when stressed" in text:
        t.add("stress")
    return t


def _negative_findings(patient, hits) -> list[dict]:
    """Interpret normal tests: narrow the differential, never erase the symptom."""
    blob = _norm(getattr(patient, "symptoms", "") or "")
    for h in hits:
        sx = h.get("structured")
        if sx:
            blob += " " + _norm(" ".join(sx.negative_findings or []))
    out = []
    for rule in _negative_rules().get("rules", []):
        if any(_norm(m) in blob for m in rule.get("match_any", [])):
            out.append({
                "test": rule["test"],
                "reduces_probability_of": rule.get("reduces_probability_of", []),
                "does_not_exclude": rule.get("does_not_exclude", []),
                "axes_still_possible": rule.get("axes_still_possible", []),
                "interpretation": ("Narrows the differential. Does NOT prove the biological "
                                   "network is normal (structural normality != functional "
                                   "network normality)."),
            })
    return out


def _burden(hits) -> int:
    """Clinical symptom burden 0-100 — deliberately SEPARATE from attribution confidence."""
    if not hits:
        return 0
    total = 0.0
    for h in hits:
        sx = h.get("structured")
        sev = (sx.severity / 10.0) if (sx and sx.severity is not None) else 0.5
        total += sev
    return int(min(100, round(100 * total / max(1, len(hits)) * min(1.0, 0.5 + 0.25 * len(hits)))))


def evaluate(patient) -> dict:
    """Build the clinical phenotype + differential axis candidates from symptoms."""
    hits = _identify(patient)
    if not hits:
        return {"symptoms_identified": [], "phenotypes": [],
                "phenotype_path": "Symptom -> Phenotype -> Axis (25 Jul Q3, Option A)",
                "phenotype_registry_version": phenotype_registry.registry_version(),
                "phenotype_registry_authoritative": phenotype_registry.is_authoritative(),
                "clusters": [], "axis_candidates": {},
                "differential": [], "adaptive_questions": [], "negative_findings": [],
                "symptom_burden": 0, "dictionary_version": _dict().get("dataset_version"),
                "dictionary_authoritative": _dict().get("authoritative", False)}

    codes = {h["entry"]["symptom_code"] for h in hits}
    triggers = _triggers(patient, hits)

    # 1) base weights: one symptom -> MANY candidate axes
    cand: dict[str, dict] = {}
    for h in hits:
        e = h["entry"]
        for c in e.get("candidates", []):
            ax = c["axis_code"]
            slot = cand.setdefault(ax, {"weight": 0.0, "evidence": [], "symptoms": []})
            slot["weight"] = min(MAX_WEIGHT, slot["weight"] + c["base_weight"] * 0.6)
            slot["evidence"].append(f"{e['name_en']} ({c['weight_class']} {c['base_weight']})")
            slot["symptoms"].append(e["symptom_code"])

    # 2) context adjustment: co-symptoms + triggers
    applied_rules = []
    for h in hits:
        for rule in h["entry"].get("context_rules", []):
            need = set(rule.get("if_co_symptoms", []))
            trig = _norm(rule.get("if_trigger", "")) if rule.get("if_trigger") else None
            ok = (need and need <= codes) or (trig and trig in triggers)
            if not ok:
                continue
            for ax, boost in (rule.get("boost") or {}).items():
                slot = cand.setdefault(ax, {"weight": 0.0, "evidence": [], "symptoms": []})
                slot["weight"] = min(MAX_WEIGHT, slot["weight"] + boost)
                slot["evidence"].append(rule.get("note", "context boost"))
            applied_rules.append(rule.get("note") or rule)

    # 3) clusters
    clusters = []
    for cl in _dict().get("clusters", []):
        present = codes & set(cl["members"])
        if len(present) >= cl.get("min_members", 2):
            clusters.append({"cluster_code": cl["cluster_code"], "name": cl["name_en"],
                             "members_present": sorted(present),
                             "networks_hint": cl.get("networks_hint", [])})
            for ax, w in (cl.get("axes") or {}).items():
                slot = cand.setdefault(ax, {"weight": 0.0, "evidence": [], "symptoms": []})
                slot["weight"] = min(MAX_WEIGHT, max(slot["weight"], w))
                slot["evidence"].append(f"cluster: {cl['name_en']}")

    # 3b) NAMED PHENOTYPE layer (25 Jul Q3, Option A): Symptom -> Phenotype -> Axis.
    #     Matched phenotypes PROPOSE candidate axes with weights. They are CANDIDATE until a
    #     domain expert approves them, so they augment the differential but never assert alone.
    phenotypes = phenotype_registry.match(codes)
    for ph in phenotypes:
        for ax, w in (ph.get("axis_evidence_weights") or {}).items():
            slot = cand.setdefault(ax, {"weight": 0.0, "evidence": [], "symptoms": []})
            # weight the phenotype contribution by its own match confidence
            slot["weight"] = min(MAX_WEIGHT, max(slot["weight"], round(w * ph["confidence"], 3)))
            slot["evidence"].append(
                f"phenotype: {ph['phenotype_name_en']} ({ph['status']}, conf {ph['confidence']})")

    # 4) negative tests narrow, never erase
    negatives = _negative_findings(patient, hits)

    # 5) differential -- ranked candidates, never a single forced mechanism
    differential = sorted(
        ({"axis_code": ax, "weight": round(v["weight"], 3),
          "likelihood": ("high" if v["weight"] >= 0.6 else
                         "moderate" if v["weight"] >= 0.35 else "low"),
          "supporting_symptoms": sorted(set(v["symptoms"])),
          "evidence": v["evidence"][:4]}
         for ax, v in cand.items()),
        key=lambda d: d["weight"], reverse=True)

    # 6) adaptive questions for the missing discriminators
    questions: list[str] = []
    for h in hits:
        for q in h["entry"].get("adaptive_questions", []):
            if q not in questions:
                questions.append(q)

    must_exclude = sorted({m for h in hits for m in h["entry"].get("must_exclude_first", [])})

    return {
        "symptoms_identified": [{"symptom_code": h["entry"]["symptom_code"],
                                 "name": h["entry"]["name_en"],
                                 "matched_on": h["matched_on"]} for h in hits],
        "phenotypes": phenotypes,
        "phenotype_path": "Symptom -> Phenotype -> Axis (25 Jul Q3, Option A)",
        "phenotype_registry_version": phenotype_registry.registry_version(),
        "phenotype_registry_authoritative": phenotype_registry.is_authoritative(),
        "clusters": clusters,
        "axis_candidates": {ax: round(v["weight"], 3) for ax, v in cand.items()},
        "differential": differential,
        "adaptive_questions": questions[:12],
        "negative_findings": negatives,
        "must_exclude_first": must_exclude,
        "context_rules_applied": applied_rules,
        "symptom_burden": _burden(hits),
        "interpretation": ("Symptom patterns indicate the POSSIBILITY of network involvement. "
                           "They do not confirm any single mechanism."),
        "dictionary_version": _dict().get("dataset_version"),
        "dictionary_authoritative": _dict().get("authoritative", False),
    }
