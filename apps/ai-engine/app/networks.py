"""Living Biological Network layer (candidate, pilot).

Loads the 180-network master and provides lookups. Networks EXPLAIN axes (mechanistic context for
the report's pathophysiology section); they do not drive module ranking. Mapping is CANDIDATE until
expert sign-off, so entries carry mapping_status and are surfaced as provisional.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).resolve().parent.parent / "data" / "tspi_networks_180.json"


@lru_cache
def _all() -> list[dict]:
    try:
        return json.loads(_DATA.read_text(encoding="utf-8")).get("networks", [])
    except FileNotFoundError:
        return []


@lru_cache
def by_axis() -> dict[str, list[dict]]:
    idx: dict[str, list[dict]] = {}
    for n in _all():
        ax = n.get("primary_axis_code")
        if ax:
            idx.setdefault(ax, []).append(n)
    return idx


def networks_for_axis(axis_code: str, limit: int = 4) -> list[dict]:
    out = []
    for n in by_axis().get(axis_code, [])[:limit]:
        out.append({"network_code": n.get("network_code"), "legacy_id": n.get("legacy_display_id"),
                    "name": n.get("network_name_en"), "primary_axis": n.get("primary_axis_code"),
                    "mapping_status": n.get("mapping_status", "CANDIDATE")})
    return out


def count() -> int:
    return len(_all())
