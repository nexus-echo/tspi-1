"""Derivations that keep PII out of the TSPI payload: case_id + age_band."""
from __future__ import annotations

from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Patient


def compute_age(dob: date, today: date | None = None) -> int:
    today = today or date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def age_to_band(age: int) -> str:
    """Coarse band only — this (not DOB) is what TSPI ever receives.

    e.g. 8 -> 'child', 16 -> 'teens', 45 -> 'mid-40s', 71 -> 'early-70s'.
    """
    if age < 10:
        return "child"
    if age < 20:
        return "teens"
    decade = (age // 10) * 10
    pos = age % 10
    tier = "early" if pos <= 3 else "mid" if pos <= 6 else "late"
    return f"{tier}-{decade}s"


def band_from_dob(dob: date) -> str:
    return age_to_band(compute_age(dob))


def next_case_id(db: Session) -> str:
    """TSPI-{year}-{6-digit sequence}. Sequence is per-year, gap-tolerant.

    Caller should retry on the (rare) unique-collision race in a prototype.
    """
    year = date.today().year
    prefix = f"TSPI-{year}-"
    count = (
        db.query(func.count(Patient.id))
        .filter(Patient.case_id.like(f"{prefix}%"))
        .scalar()
        or 0
    )
    return f"{prefix}{count + 1:06d}"
