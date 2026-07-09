"""Phase F: outcome capture + learning loop.

Doctor-approved results + follow-up markers feed the brain's recalibration so future NSS/SPS
improve (digital-twin loop). Outcomes are stored locally and mirrored to TSPI best-effort; the
temporal trajectory is built locally so it works even when the brain is offline."""
from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import audit, tspi
from app.database import get_db
from app.deps import get_current_user, require_roles
from app.models import Outcome, Patient, Report, Role, User
from app.routers.patients import _authorize, _is_staff, _load_patient
from app.schemas import OutcomeCreate, OutcomeOut

router = APIRouter(tags=["learning"])


@router.post("/reports/{report_id}/outcomes", response_model=OutcomeOut,
             status_code=status.HTTP_201_CREATED)
def record_outcome(report_id: str, body: OutcomeCreate, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)) -> Outcome:
    if not _is_staff(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only staff can record outcomes")
    rep = db.get(Report, report_id)
    if not rep:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")

    row = Outcome(
        report_id=rep.id, patient_id=rep.patient_id, marker=body.marker,
        baseline=body.baseline, followup=body.followup,
        delta=body.followup - body.baseline, recorded_by=user.id,
    )
    # Mirror to TSPI (best-effort) so the brain's learning loop sees it.
    if rep.tspi_report_id:
        try:
            tspi.outcome(rep.tspi_report_id, body.marker, body.baseline, body.followup)
            row.synced_to_tspi = True
        except tspi.BrainUnavailable:
            row.synced_to_tspi = False
    db.add(row)
    db.commit()
    db.refresh(row)
    audit.write(db, "outcome_record", actor_user_id=user.id, patient_id=rep.patient_id,
                report_id=rep.id, detail={"marker": body.marker, "delta": row.delta,
                                          "synced": row.synced_to_tspi})
    return row


@router.get("/reports/{report_id}/outcomes", response_model=list[OutcomeOut])
def list_outcomes(report_id: str, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)) -> list[Outcome]:
    rep = db.get(Report, report_id)
    if not rep:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
    _authorize(db.get(Patient, rep.patient_id), user)
    return db.query(Outcome).filter(Outcome.report_id == rep.id).order_by(Outcome.created_at).all()


@router.get("/patients/{patient_id}/temporal")
def temporal(patient_id: str, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)) -> dict:
    """Per-marker trajectory built from stored outcomes (works offline)."""
    p = _load_patient(db, patient_id)
    _authorize(p, user)
    rows = (
        db.query(Outcome).filter(Outcome.patient_id == p.id)
        .order_by(Outcome.created_at).all()
    )
    series: dict[str, list] = defaultdict(list)
    for r in rows:
        series[r.marker].append({"baseline": r.baseline, "followup": r.followup,
                                 "delta": r.delta, "at": r.created_at.isoformat()})
    return {"case_id": p.case_id, "markers": series}


@router.post("/learning/recalibrate")
def recalibrate(db: Session = Depends(get_db),
                user: User = Depends(require_roles(Role.admin))) -> dict:
    try:
        result = tspi.recalibrate()
    except tspi.BrainUnavailable as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e))
    audit.write(db, "learning_recalibrate", actor_user_id=user.id,
                detail={"axes_changed": result.get("axes_changed")})
    return result


@router.get("/learning/weights")
def weights(user: User = Depends(require_roles(Role.admin))) -> dict:
    try:
        return tspi.weights()
    except tspi.BrainUnavailable as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e))
