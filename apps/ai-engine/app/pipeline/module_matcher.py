"""Stage 5 — Match catalog modules to dysfunctional axes (driver axes first).

Pulls modules from axis_module_map, prefers multi-axis coverage, and applies a hard
safety/contraindication filter. Unresolved modules are flagged, never invented.
"""
from __future__ import annotations

from app.knowledge.repository import KnowledgeRepo
from app.schemas import AxisScore, ModulePick


def match(axis_scores: list[AxisScore], repo: KnowledgeRepo, medications: list[str]) -> list[ModulePick]:
    drivers = [a for a in axis_scores if a.is_driver] or axis_scores
    picks: dict[str, ModulePick] = {}

    for axis in drivers:
        for mod in repo.modules_for_axis(axis.axis_code):
            code = mod["code"]
            if code in picks:
                if axis.axis_code not in picks[code].target_axes:
                    picks[code].target_axes.append(axis.axis_code)
                continue
            # Safety gate (placeholder): Phase 1 checks real contraindications vs meds.
            if repo.is_contraindicated(code, medications):
                continue
            picks[code] = ModulePick(
                module_code=code,
                module_name=mod.get("name"),
                target_axes=[axis.axis_code],
                mechanism=mod.get("mechanism"),
                dose=mod.get("dose"),
                clinical_role=mod.get("role"),
                safety=mod.get("safety"),
                resolved=mod.get("resolved", True),
            )

    return list(picks.values())
