"""Phase 11 — legacy -> current axis converter (Blocker 1).

The delivered module file still uses LEGACY axis numbering. The domain experts were explicit
(and reconfirmed on 25 Jul): a blind numeric shift is forbidden, because some legacy numbers
were reused for a different concept (e.g. legacy "Metabolic Balance" is NOT current A27).
Mapping must be SEMANTIC and expert-approved.

This converter therefore:
  * matches by legacy NAME (semantic), never by number alone;
  * AUTO-APPLIES Tier A (EXACT_SEMANTIC_MAPPING / RENAMED_REFINED) — safe, 1:1, concept-preserving;
  * QUARANTINES Tier B/C (split / context-dependent / same-number-different-meaning /
    deprecated-to-network / no-equivalent) with a candidate + reason for expert review;
  * stamps provenance on every converted reference so nothing is silently changed.

The converted registry stays `production_allowed=false` until a domain expert signs off the
quarantined items — consistent with the standing Blocker-1 rule.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).resolve().parent.parent / "data" / "legacy_axis_map.json"

AUTO_TIERS = {"A"}
AUTO_TYPES = {"EXACT_SEMANTIC_MAPPING", "RENAMED_REFINED"}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


@lru_cache
def _map_doc() -> dict:
    try:
        return json.loads(_DATA.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"mappings": []}


@lru_cache
def _by_name() -> dict[str, dict]:
    return {_norm(m["legacy_name"]): m for m in _map_doc().get("mappings", [])}


def map_version() -> str:
    return _map_doc().get("dataset_version", "0.0.0")


def _extract_name(ref: str) -> str:
    """Pull the semantic name from a legacy reference like 'Axis 16 - Liver Detoxification'."""
    ref = str(ref)
    # drop a leading 'Axis 16 -', 'AXIS 37', 'A16:', bare numbers, dashes
    ref = re.sub(r"(?i)\baxis\b", " ", ref)
    ref = re.sub(r"[-–—:]", " ", ref)
    ref = re.sub(r"\b\d+\b", " ", ref)
    return ref.strip()


def convert_axis_ref(ref: str) -> dict:
    """Convert ONE legacy axis reference. Returns a provenance record; never raises."""
    name = _extract_name(ref)
    m = _by_name().get(_norm(name))
    if not m:
        return {"legacy_ref": ref, "current_code": None, "candidate_code": None,
                "conversion_type": "NO_DIRECT_EQUIVALENT", "tier": "C",
                "auto_applied": False, "review_required": True,
                "note": "no semantic match in legacy_axis_map — expert must map manually"}

    ctype = m.get("conversion_type", "NO_DIRECT_EQUIVALENT")
    tier = m.get("tier", "C")
    auto = tier in AUTO_TIERS and ctype in AUTO_TYPES and bool(m.get("current_code"))
    return {
        "legacy_ref": ref,
        "current_code": m.get("current_code") if auto else None,
        "candidate_code": m.get("current_code") or m.get("candidate_code"),
        "conversion_type": ctype,
        "tier": tier,
        "auto_applied": auto,
        "review_required": not auto,
        "network_code": m.get("network_code"),
        "note": m.get("note"),
    }


def convert_target_axes(refs: list[str]) -> dict:
    """Convert a module's whole target_axes list. Splits into applied vs quarantined."""
    records = [convert_axis_ref(r) for r in refs]
    applied = [r["current_code"] for r in records if r["auto_applied"]]
    quarantined = [r for r in records if not r["auto_applied"]]
    return {
        "target_axes_current": sorted(set(applied)),
        "provenance": records,
        "quarantined": quarantined,
        "fully_resolved": len(quarantined) == 0,
    }


def convert_registry(modules: list[dict], legacy_field: str = "legacy_target_axes") -> dict:
    """Convert a legacy module registry. Returns converted modules + a quarantine review sheet.

    Each module dict must carry a list under `legacy_field`. Modules with any quarantined ref
    are marked `production_allowed=false` and listed in the review sheet.
    """
    converted, review_rows = [], []
    for mod in modules:
        refs = mod.get(legacy_field) or mod.get("target_axes") or []
        res = convert_target_axes([str(r) for r in refs])
        out = dict(mod)
        out["target_axes"] = res["target_axes_current"]
        out["axis_conversion"] = res["provenance"]
        out["production_allowed"] = res["fully_resolved"]
        out["axis_master_version"] = _map_doc().get("framework_version")
        converted.append(out)
        for q in res["quarantined"]:
            review_rows.append({"module_code": mod.get("module_code"),
                                "module_name": mod.get("name_en") or mod.get("module_name"),
                                **q})
    return {
        "map_version": map_version(),
        "framework_version": _map_doc().get("framework_version"),
        "production_allowed": all(m["production_allowed"] for m in converted) if converted else False,
        "modules": converted,
        "review_sheet": review_rows,
        "summary": {
            "modules_total": len(converted),
            "modules_fully_resolved": sum(1 for m in converted if m["production_allowed"]),
            "modules_needing_review": sum(1 for m in converted if not m["production_allowed"]),
            "quarantined_refs": len(review_rows),
        },
    }
