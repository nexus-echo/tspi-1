"""Stage 6 — Sequence modules into phases: foundation BEFORE manifestation.

Step 1 = reset the terrain (microbiome, inflammation, nutrient sensing, autonomic, blood).
Step 2 = targeted correction of the manifestation. Step 3 = endocrine/neuro fine-tuning.
"""
from __future__ import annotations

from app.schemas import ModulePick

# Axes that belong to the foundation reset (Step 1).
_FOUNDATION_AXES = {"A1", "A2", "A9", "A15", "A16", "A17", "A18", "A26", "A34"}
# Higher-order / manifestation axes handled later.
_FINE_TUNE_AXES = {"A33", "A39"}


def sequence(modules: list[ModulePick]) -> list[ModulePick]:
    for m in modules:
        axes = set(m.target_axes)
        if axes & _FOUNDATION_AXES:
            m.phase = "step_1"
        elif axes & _FINE_TUNE_AXES:
            m.phase = "step_3"
        else:
            m.phase = "step_2"
    order = {"step_1": 0, "step_2": 1, "step_3": 2}
    return sorted(modules, key=lambda m: order[m.phase])
