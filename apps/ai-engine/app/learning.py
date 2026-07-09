"""Phase 4 — outcome learning loop + temporal trajectory analysis.

- recalibrate(): reads stored outcomes, decides whether each marker improved or worsened, and
  nudges the corresponding axis WEIGHT (worsening -> more emphasis; improving -> relax toward
  neutral), bounded [0.5, 2.0]. Feeds the weight-aware NSS/SPS engine.
- temporal(): per-marker trajectory for one case across its outcomes.

This is the LEARNING MECHANISM. The exact update rule + marker→axis map should be ratified by the
clinical team (like the official NSS formula); the defaults here are sensible and clearly bounded.
"""
from __future__ import annotations

import re
from collections import defaultdict

from app import store

# marker -> axis (extend with the official marker dictionary)
_MARKER_AXIS = {
    "crp": "A1", "hscrp": "A1", "esr": "A1",
    "hba1c": "A5", "glucose": "A5", "fastingglucose": "A5",
    "hemoglobin": "A26", "hb": "A26", "mcv": "A26", "ferritin": "A26",
    "tsh": "A33", "ft3": "A33", "ft4": "A33",
    "ige": "A2", "vitamind": "A15",
}
_LOWER_IS_BETTER = {"crp", "hscrp", "esr", "hba1c", "glucose", "fastingglucose", "ige"}
_HIGHER_IS_BETTER = {"hemoglobin", "hb", "ferritin", "vitamind"}

_LR = 0.1          # learning rate
_WMIN, _WMAX = 0.5, 2.0


def _norm(m: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (m or "").lower())


def _improved(marker_norm: str, change: float) -> bool | None:
    if marker_norm in _LOWER_IS_BETTER:
        return change < 0
    if marker_norm in _HIGHER_IS_BETTER:
        return change > 0
    return None  # unknown direction -> don't learn from it


def recalibrate(learning_rate: float = _LR) -> dict:
    outs = store.unlearned_outcomes()                # incremental: only new outcomes
    agg: dict[str, list[int]] = defaultdict(lambda: [0, 0])   # axis -> [improved, worsened]
    for o in outs:
        m = _norm(o["marker"])
        axis = _MARKER_AXIS.get(m)
        if not axis:
            continue
        imp = _improved(m, o["delta"])
        if imp is None:
            continue
        agg[axis][0 if imp else 1] += 1

    store.mark_learned([o["id"] for o in outs])   # consumed (incl. unknown markers)
    weights = store.get_axis_weights()
    updated: dict[str, dict] = {}
    for axis, (imp, wor) in agg.items():
        n = imp + wor
        if n == 0:
            continue
        signal = (wor - imp) / n                        # -1 (all improved) .. +1 (all worsened)
        new_w = min(_WMAX, max(_WMIN, weights.get(axis, 1.0) + learning_rate * signal))
        store.set_axis_weight(axis, round(new_w, 3), samples=n)
        updated[axis] = {"weight": round(new_w, 3), "improved": imp, "worsened": wor}
    return {"updated": updated, "learning_rate": learning_rate, "axes_changed": len(updated)}


def temporal(case_id: str) -> dict:
    outs = store.outcomes_for_case(case_id)
    by_marker: dict[str, list[dict]] = defaultdict(list)
    for o in outs:
        by_marker[o["marker"]].append(o)

    series = []
    for marker, rows in by_marker.items():
        first, last = rows[0]["baseline"], rows[-1]["followup"]
        change = last - first
        imp = _improved(_norm(marker), change)
        trend = "flat" if abs(change) < 1e-9 else (
            "improving" if imp else "worsening" if imp is False else "changed")
        series.append({"marker": marker, "first": first, "last": last,
                       "change": round(change, 3), "trend": trend, "points": len(rows)})
    return {"case_id": case_id, "markers": series}
