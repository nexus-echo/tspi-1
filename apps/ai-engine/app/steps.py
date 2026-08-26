"""Canonical 9 Restoration Steps registry (S1–S9). Read-only reference used by the report layer
and module→step context."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).resolve().parent.parent / "data" / "restoration_steps.json"


@lru_cache
def steps() -> list[dict]:
    try:
        return json.loads(_DATA.read_text(encoding="utf-8")).get("steps", [])
    except FileNotFoundError:
        return []


@lru_cache
def name(code: str) -> str | None:
    for s in steps():
        if s["code"] == code:
            return s["name_en"]
    return None
