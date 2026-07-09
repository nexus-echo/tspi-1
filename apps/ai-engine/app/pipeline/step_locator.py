"""Stage 4 — Locate the patient on the 9 Steps of Wellness and size the Prakati gap.

Heuristic: the more foundational axes are pathological, the lower (earlier) the patient
sits on the ladder. Step 9 = Prakati (the goal). Refine with clinical rules in Phase 1.
"""
from __future__ import annotations

from app.schemas import AxisScore, Severity

# Foundational axes (rough) -> early steps must be addressed first.
_FOUNDATION_AXES = {"A15", "A17", "A18", "A1", "A2", "A9", "A5", "A8"}


def locate(axis_scores: list[AxisScore]) -> tuple[int, str]:
    pathological_foundation = [
        a for a in axis_scores
        if a.axis_code in _FOUNDATION_AXES and a.severity == Severity.pathological
    ]
    n = len(pathological_foundation)
    # More foundational damage -> start lower on the 9-step ladder.
    position = 1 if n >= 3 else 2 if n == 2 else 3 if n == 1 else 4
    gap = "large" if n >= 3 else "moderate" if n >= 1 else "small"
    return position, gap
