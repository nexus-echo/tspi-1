"""Marker Registry — the single source of truth for how a lab marker relates to the axes.

Implements the model CONFIRMED by the domain-expert answers of 25 Jul 2026
(`answer tspi 25.07.2026.pdf`, Q1 + Q5):

  * value_source_type (MEASURED | DERIVED) is SEPARATE from the direction rule (Q5a).
    DERIVED markers (HOMA-IR, eGFR, ratios) carry a calculation_rule and are read as
    EvidenceStatus.DERIVED, never as a directly measured value.
  * direction_rule is one of LOWER_BETTER | HIGHER_BETTER | TARGET_RANGE | CONTEXT_DEPENDENT.
    "Optimal Range" and "U-shape" are the SAME family (Q5b): U-shape is a CURVE under
    TARGET_RANGE, not a separate direction.
  * Ferritin's inflammatory axis is A1, NOT A34 (Q1 — A34 was a typo). Ferritin is
    context-dependent: low -> A26 (iron/hematopoiesis); high WITH inflammation -> A1;
    high ALONE -> no axis asserted (acute-phase reactant, ambiguous).

This registry replaces the two ad-hoc placeholder maps (normalizer `_SEED_CONCEPTS`,
learning `_MARKER_AXIS`). Data lives in data/marker_registry.json and is version-flagged.
"""
from __future__ import annotations

import json
import re
from enum import Enum
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

_DATA = Path(__file__).resolve().parent.parent / "data" / "marker_registry.json"


class ValueSourceType(str, Enum):
    MEASURED = "MEASURED"   # read directly from a lab/device/report
    DERIVED = "DERIVED"     # computed from measured inputs via a defined formula


class DirectionRule(str, Enum):
    LOWER_BETTER = "LOWER_BETTER"          # higher value = worse (CRP, HbA1c)
    HIGHER_BETTER = "HIGHER_BETTER"        # lower value = worse (eGFR)
    TARGET_RANGE = "TARGET_RANGE"          # both low AND high are worse (TSH, Na, K)
    CONTEXT_DEPENDENT = "CONTEXT_DEPENDENT"  # meaning depends on other findings (ferritin)


class CurveType(str, Enum):
    LINEAR = "LINEAR"
    U_SHAPE = "U_SHAPE"        # symmetric: worse equally as you leave the range either way
    J_SHAPE = "J_SHAPE"        # asymmetric: one tail worse than the other
    ASYMMETRIC = "ASYMMETRIC"


class ContextRule(BaseModel):
    when: str                          # human-readable condition, e.g. "low"
    requires_marker: str | None = None  # e.g. "crp" must be present/high
    axis: str | None = None            # axis asserted when the condition holds
    concept: str | None = None         # concept bridge for the normalizer, when axis holds
    note: str | None = None


class MarkerDef(BaseModel):
    marker_name: str
    aliases: list[str] = []
    primary_axis: str | None = None
    secondary_axes: list[str] = []
    direction_rule: DirectionRule
    value_source_type: ValueSourceType = ValueSourceType.MEASURED
    calculation_rule: str | None = None          # single-form DERIVED formula (legacy)
    calculation_rules: dict[str, str] = {}       # unit-specific formulas, keyed by unit (31 Jul §6.1)
    formula_version: str | None = None
    unit_validation_required: bool = False       # units MUST be validated before calculation
    required_inputs: list[str] = []              # only when DERIVED
    curve_type: CurveType | None = None          # only when TARGET_RANGE
    lower_optimal: float | None = None
    upper_optimal: float | None = None
    unit: str | None = None
    context_rules: list[ContextRule] = []        # only when CONTEXT_DEPENDENT
    concept: str | None = None                   # bridge to the normalizer's concept space
    evidence_grade: str | None = None
    note: str | None = None


def _norm(m: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (m or "").lower())


@lru_cache
def _registry_raw() -> dict:
    try:
        return json.loads(_DATA.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"markers": []}


@lru_cache
def _index() -> dict[str, MarkerDef]:
    idx: dict[str, MarkerDef] = {}
    for row in _registry_raw().get("markers", []):
        m = MarkerDef(**row)
        for key in [m.marker_name, *m.aliases]:
            idx[_norm(key)] = m
    return idx


def registry_version() -> str:
    return _registry_raw().get("dataset_version", "0.0.0")


def lookup(name: str) -> MarkerDef | None:
    return _index().get(_norm(name))


def interpret(marker: MarkerDef, value: float | None,
              ref_low: float | None = None, ref_high: float | None = None) -> dict:
    """Turn a value into {abnormal, direction, badness} using the marker's direction rule.

    `badness` is a 0..1 hint (0 = optimal, 1 = clearly pathological) — NOT a final score;
    it only helps rank how far from good the value is. Never fabricates precision.
    """
    if value is None:
        return {"abnormal": None, "direction": "abnormal", "badness": None}

    lo = marker.lower_optimal if marker.lower_optimal is not None else ref_low
    hi = marker.upper_optimal if marker.upper_optimal is not None else ref_high

    if marker.direction_rule is DirectionRule.LOWER_BETTER:
        if hi is not None and value > hi:
            return {"abnormal": True, "direction": "up", "badness": 0.8}
        return {"abnormal": False, "direction": "normal", "badness": 0.1}

    if marker.direction_rule is DirectionRule.HIGHER_BETTER:
        if lo is not None and value < lo:
            return {"abnormal": True, "direction": "down", "badness": 0.8}
        return {"abnormal": False, "direction": "normal", "badness": 0.1}

    if marker.direction_rule is DirectionRule.TARGET_RANGE:
        # both tails are abnormal; U-shape treats them symmetrically
        if lo is not None and value < lo:
            return {"abnormal": True, "direction": "down", "badness": 0.7}
        if hi is not None and value > hi:
            return {"abnormal": True, "direction": "up", "badness": 0.7}
        return {"abnormal": False, "direction": "normal", "badness": 0.1}

    # CONTEXT_DEPENDENT — direction alone is not interpretable without other findings
    direction = "abnormal"
    if hi is not None and value > hi:
        direction = "up"
    elif lo is not None and value < lo:
        direction = "down"
    return {"abnormal": None, "direction": direction, "badness": None}


def resolve_context(marker: MarkerDef, direction: str, present_markers: set[str]) -> "ContextRule | None":
    """Return the first matching context rule (or None) for a CONTEXT_DEPENDENT marker."""
    present = {_norm(p) for p in present_markers}
    for rule in marker.context_rules:
        if rule.when != direction:
            continue
        if rule.requires_marker and _norm(rule.requires_marker) not in present:
            continue
        return rule
    return None


def resolve_context_axes(marker: MarkerDef, direction: str, present_markers: set[str]) -> list[str]:
    """For CONTEXT_DEPENDENT markers, pick the axis using the co-present markers.

    Ferritin is the canonical case: low -> A26; high WITH an inflammatory marker -> A1
    (NOT A34); high alone -> [] (assert nothing).
    """
    present = {_norm(p) for p in present_markers}
    for rule in marker.context_rules:
        if rule.when != direction:
            continue
        if rule.requires_marker and _norm(rule.requires_marker) not in present:
            continue
        return [rule.axis] if rule.axis else []
    return []


def direction_is_better(name: str, change: float) -> bool | None:
    """Replacement for learning.py's LOWER/HIGHER sets.

    Returns True if `change` (delta) is an improvement, False if worsening, None if the
    marker's direction is not context-free (so learning must NOT infer a direction).
    """
    m = lookup(name)
    if not m:
        return None
    if m.direction_rule is DirectionRule.LOWER_BETTER:
        return change < 0
    if m.direction_rule is DirectionRule.HIGHER_BETTER:
        return change > 0
    # TARGET_RANGE and CONTEXT_DEPENDENT: direction of "better" depends on where the value
    # sits relative to the optimal band, so a raw delta is not interpretable -> never learn blindly.
    return None


def axis_for(name: str) -> str | None:
    m = lookup(name)
    return m.primary_axis if m else None


def formula_for_unit(marker: MarkerDef, unit: str | None) -> str | None:
    """Return the DERIVED formula for a given unit, or None if the unit is unsupported.

    31 Jul §6.1: derived markers are unit-specific and units MUST be validated before
    calculation (e.g. HOMA-IR ÷405 for mg/dL vs ÷22.5 for mmol/L). Returning None means
    'refuse to calculate' — the engine must not silently pick a formula for an unknown unit.
    """
    if marker.calculation_rules:
        if unit is None and marker.unit_validation_required:
            return None
        return marker.calculation_rules.get(unit)
    return marker.calculation_rule
