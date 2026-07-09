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
