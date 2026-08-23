"""Phase 6 — TSPI Evidence & Confidence model.

Implements the four dimensions the domain experts require on EVERY conclusion
(TSPI 3 — Complete Domain Expert Response, Q7):

    1. Evidence Status  -- HOW the statement was produced (MEASURED..NOT_AVAILABLE)
    2. Evidence Grade   -- how strong the SCIENTIFIC support is (A..D)   [separate field]
    3. Confidence       -- 0..1, how strongly evidence supports THIS patient's conclusion
    4. Data Completeness-- weighted (CORE=3 / SUPPORTING=2 / OPTIONAL=1), NOT a raw ratio
    + Biological Uncertainty -- 0..1, how many alternative biological models remain plausible

Hard rules encoded here:
  * HYPOTHESIS must NEVER raise an Axis score, Network score, NSS or Module Match score.
  * "No data" must NEVER be interpreted as normal -> NOT_ASSESSED with a reason.
  * Missing a CORE marker must not yield a high completeness.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class EvidenceStatus(str, Enum):
    """How a statement was produced."""
    MEASURED = "MEASURED"                      # lab/imaging/exam/validated device/structured report
    DERIVED = "DERIVED"                        # calculated from measured data via a defined formula
    CLINICAL_INFERENCE = "CLINICAL_INFERENCE"  # inferred from a clinically meaningful pattern
    HYPOTHESIS = "HYPOTHESIS"                  # plausible but NOT sufficient for scoring
    NOT_AVAILABLE = "NOT_AVAILABLE"            # required evidence absent


class EvidenceGrade(str, Enum):
    """Strength of scientific support for the claimed relationship (per module+claim+target+source).

    31 Jul §8 + Directive 13: 'not yet graded' is NOT the same as 'weakest evidence'. An
    ungraded module must be EVIDENCE_NOT_GRADED, never silently defaulted to D.
    """
    A = "A"   # strong, directly relevant human clinical evidence (meta-analysis / RCT)
    B = "B"   # human pilot / controlled / observational, with limitations
    C = "C"   # animal / cell / molecular / omics / mechanistic
    D = "D"   # traditional knowledge / expert opinion / indirect / unconfirmed
    EVIDENCE_NOT_GRADED = "EVIDENCE_NOT_GRADED"   # not yet reviewed -- distinct from D


class AxisStatus(str, Enum):
    """Official per-axis assessment states (31 Jul §10). Ordered weakest -> strongest.

    A symptom may create an AXIS_CANDIDATE; a hypothesis never produces a final score; an axis
    must satisfy its minimum-evidence gate before it can be ASSESSED. NOT_ASSESSED is never
    'normal'.
    """
    NOT_ASSESSED = "NOT_ASSESSED"                       # insufficient usable evidence
    AXIS_CANDIDATE = "AXIS_CANDIDATE"                   # raised by a weak/nonspecific signal
    PROVISIONALLY_ASSESSED = "PROVISIONALLY_ASSESSED"   # one usable source, incomplete
    ASSESSED = "ASSESSED"                               # >=2 reasonably independent concordant sources
    HIGH_CONFIDENCE_ASSESSED = "HIGH_CONFIDENCE_ASSESSED"  # multiple concordant layers / specific + correlation


class EvidenceWeight(str, Enum):
    CORE = "CORE"
    SUPPORTING = "SUPPORTING"
    OPTIONAL = "OPTIONAL"


_WEIGHT = {EvidenceWeight.CORE: 3.0, EvidenceWeight.SUPPORTING: 2.0, EvidenceWeight.OPTIONAL: 1.0}

# Only these statuses may contribute to a deterministic score.
_SCORING_STATUSES = {EvidenceStatus.MEASURED, EvidenceStatus.DERIVED, EvidenceStatus.CLINICAL_INFERENCE}

INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class EvidenceItem(BaseModel):
    """One piece of evidence supporting (or contradicting) a conclusion."""
    source: str
    status: EvidenceStatus = EvidenceStatus.CLINICAL_INFERENCE
    weight_class: EvidenceWeight = EvidenceWeight.SUPPORTING
    grade: EvidenceGrade | None = None
    contradicting: bool = False
    detail: str | None = None


def contributes_to_score(status: EvidenceStatus) -> bool:
    """HYPOTHESIS / NOT_AVAILABLE must never raise any score (expert hard rule)."""
    return status in _SCORING_STATUSES


def scoring_items(items: list[EvidenceItem]) -> list[EvidenceItem]:
    return [i for i in items if contributes_to_score(i.status) and not i.contradicting]


def data_completeness(available: list[EvidenceItem], expected: list[EvidenceWeight]) -> float:
    """Weighted completeness: Sigma weight(available) / Sigma weight(all expected).

    Deliberately NOT `present / expected` -- a missing CORE marker must drag this down.
    """
    total = sum(_WEIGHT[w] for w in expected)
    if total <= 0:
        return 0.0
    got = sum(_WEIGHT[i.weight_class] for i in available if contributes_to_score(i.status))
    return round(min(1.0, got / total), 2)


def confidence(items: list[EvidenceItem], completeness: float) -> float:
    """0..1 -- how strongly the available evidence supports the conclusion FOR THIS PATIENT.

    Reflects evidence quality/consistency and independent-source count -- not merely the number
    of data points -- and is reduced by contradicting evidence.
    """
    usable = scoring_items(items)
    if not usable:
        return 0.0
    quality = {EvidenceStatus.MEASURED: 1.0, EvidenceStatus.DERIVED: 0.9,
               EvidenceStatus.CLINICAL_INFERENCE: 0.6}
    best = max(quality[i.status] for i in usable)
    # independent concordant sources add confidence with diminishing returns
    independence = min(1.0, 0.6 + 0.2 * (len({i.source for i in usable}) - 1))
    contradictions = sum(1 for i in items if i.contradicting)
    penalty = 0.15 * contradictions
    val = best * independence * (0.5 + 0.5 * completeness) - penalty
    return round(max(0.0, min(1.0, val)), 2)


def biological_uncertainty(candidate_models: int, completeness: float,
                           discriminating_evidence_missing: bool = False,
                           conflicting: bool = False) -> float:
    """0..1 -- how many important alternative biological models remain plausible.

    Distinct from confidence: data may be complete and reliable, yet several network
    combinations explain the pattern equally well -> high uncertainty.
    """
    base = 0.0 if candidate_models <= 1 else min(1.0, 0.25 * (candidate_models - 1))
    base += 0.25 * (1.0 - completeness)
    if discriminating_evidence_missing:
        base += 0.15
    if conflicting:
        base += 0.15
    return round(max(0.0, min(1.0, base)), 2)


def axis_status(items: list[EvidenceItem], completeness: float) -> tuple[AxisStatus, str | None]:
    """Map evidence onto the official axis status ladder. Returns (status, reason)."""
    usable = scoring_items(items)
    if not usable:
        return AxisStatus.NOT_ASSESSED, INSUFFICIENT_DATA
    independent = len({i.source for i in usable})
    measured = [i for i in usable if i.status is EvidenceStatus.MEASURED]
    if (independent >= 2 and measured and completeness >= 0.6) or independent >= 3:
        return AxisStatus.HIGH_CONFIDENCE_ASSESSED, None
    if independent >= 2:
        return AxisStatus.ASSESSED, None
    # single usable source: measured / reasonably complete -> provisional; else a weak candidate
    if measured or completeness >= 0.5:
        return AxisStatus.PROVISIONALLY_ASSESSED, None
    return AxisStatus.AXIS_CANDIDATE, None


def label_confidence(value: float) -> str:
    for lo, label in ((0.90, "Very High"), (0.75, "High"), (0.50, "Moderate"), (0.25, "Low")):
        if value >= lo:
            return label
    return "Very Low"


def label_uncertainty(value: float) -> str:
    for lo, label in ((0.75, "Very High"), (0.50, "High"), (0.25, "Moderate")):
        if value >= lo:
            return label
    return "Low"
