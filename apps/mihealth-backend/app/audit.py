"""Append-only audit writer."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import AuditLog


def write(
    db: Session,
    action: str,
    *,
    actor_user_id: str | None = None,
    patient_id: str | None = None,
    report_id: str | None = None,
    allowed: bool = True,
    detail: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            action=action,
            actor_user_id=actor_user_id,
            patient_id=patient_id,
            report_id=report_id,
            allowed=allowed,
            detail=detail or {},
        )
    )
    db.commit()
