"""Candidate Laboratory Cut-off Registry (pilot).

Classifies a measured value into a disturbance band (OPTIMAL / SUBCLINICAL / FUNCTIONAL /
PATHOLOGICAL / CRITICAL) and a high/low flag. PROVISIONAL — pilot cut-offs from standard adult
references; unknown marker -> NOT_CLASSIFIABLE. A CRITICAL band is a safety signal, not an axis
severity score (red-flag layer handles escalation).
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).resolve().parent.parent / "data" / "lab_cutoffs.json"


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


@lru_cache
def _index() -> dict[str, dict]:
    try:
        doc = json.loads(_DATA.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    return {_norm(c["marker"]): c for c in doc.get("cutoffs", [])}


def classify(marker: str, value: float | None) -> dict:
    """Return {band, flag, classifiable}. flag: 'high' | 'low' | None."""
    row = _index().get(_norm(marker))
    if row is None or not isinstance(value, (int, float)):
        return {"band": "NOT_CLASSIFIABLE", "flag": None, "classifiable": False}
    v = float(value)
    # critical first (safety)
    if row.get("critical_low") is not None and v <= row["critical_low"]:
        return {"band": "CRITICAL", "flag": "low", "classifiable": True}
    if row.get("critical_high") is not None and v >= row["critical_high"]:
        return {"band": "CRITICAL", "flag": "high", "classifiable": True}
    # high side (worse as value rises)
    for band, key in (("PATHOLOGICAL", "pathological_high"), ("FUNCTIONAL", "functional_high"),
                      ("SUBCLINICAL", "subclinical_high")):
        t = row.get(key)
        if t is not None and v >= t:
            return {"band": band, "flag": "high", "classifiable": True}
    # low side (worse as value falls)
    for band, key in (("PATHOLOGICAL", "pathological_low"), ("FUNCTIONAL", "functional_low"),
                      ("SUBCLINICAL", "subclinical_low")):
        t = row.get(key)
        if t is not None and v <= t:
            return {"band": band, "flag": "low", "classifiable": True}
    return {"band": "OPTIMAL", "flag": None, "classifiable": True}
