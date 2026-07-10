"""Stage 5 — Match catalog modules to dysfunctional axes (driver axes first).

Pulls modules from the OFFICIAL axis->module map, carries each module's per-axis primary/secondary
role, dose_type, phytocore code and contraindications, and applies a hard safety filter (which,
per governance, never drops a module — it flags). Unresolved modules are flagged, never invented.
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
            role = mod.get("role", "primary")
            if code in picks:
                p = picks[code]
                if axis.axis_code not in p.target_axes:
                    p.target_axes.append(axis.axis_code)
                p.axis_roles[axis.axis_code] = role
                continue
            if repo.is_contraindicated(code, medications):     # no-op by design (we flag, not drop)
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
                phytocore_code=mod.get("phytocore"),
                dose_type=mod.get("dose_type", "severity"),
                status=mod.get("status", "active"),
                axis_roles={axis.axis_code: role},
                contraindications=repo.module_contraindications(code),
            )

    return list(picks.values())
