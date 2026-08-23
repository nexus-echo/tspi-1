"""Official TSPI severity + dosing protocol (TSPI-AI Clinical Decision Engine v3.0).

Loads data/tspi_severity_dosing.json. Maps a Network Severity Score (NSS 0-100) to a
Level (0-3), returns the per-module dose for that level, and the special KS protocol.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).resolve().parent.parent.parent / "data" / "tspi_severity_dosing.json"


@lru_cache
def _cfg() -> dict:
    return json.loads(_DATA.read_text(encoding="utf-8"))


def level_for_nss(nss: int) -> dict:
    for lv in _cfg()["levels"]:
        if lv["nss_min"] <= nss <= lv["nss_max"]:
            return lv
    return _cfg()["levels"][-1]


def dose_string(level: dict) -> str:
    d = level["dose"]
    return f"{d['caps']} caps x {d['times_per_day']}/day ({d['daily_total']}/day)"


def ks_protocol() -> dict:
    return _cfg()["ks_protocol"]


def reassessment_days() -> list[int]:
    return _cfg()["reassessment_days"]


def safety_note() -> str:
    return _cfg()["safety"]


# --- bowel-regulation modules (dose by bowel performance, not severity level) ---
import re as _re


def _norm(s: str) -> str:
    return _re.sub(r"[^a-z0-9]", "", (s or "").lower())


def bowel_group() -> set[str]:
    """Normalized names/codes of modules that use bowel dosing (from config)."""
    return {_norm(x) for x in _cfg().get("bowel_protocol", {}).get("group", [])}


def is_bowel(code_or_name: str) -> bool:
    n = _norm(code_or_name)
    return any(b in n or n in b for b in bowel_group())


def bowel_dose(code_or_name: str = "") -> str:
    """KS gets its detailed titration; other bowel modules use the generic dose."""
    bp = _cfg().get("bowel_protocol", {})
    if _norm(code_or_name) == "ks":
        ks = ks_protocol()
        return f"KS protocol (bowel-based): start {ks['start']['normal']}; {ks['goal']}"
    return f"Bowel protocol: {bp.get('generic_dose', '1-4 caps at bedtime + on waking')}; {bp.get('goal', '')}"
