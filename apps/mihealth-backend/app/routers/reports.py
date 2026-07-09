"""Phase D: staff-only treatment-plan generation via the TSPI brain, plus report read access.

Flow: gather confirmed labs + intake + consent -> de-identify -> POST TSPI /report ->
store as draft (deliverable=false). Doctor validation (Phase E) flips deliverable. Patients
can read a report only once it is deliverable."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import audit, deid, tspi
from app.database import get_db
from app.deps import get_current_user
from app.models import Patient, Report, Role, User, Validation
from app.routers.patients import _authorize, _is_staff, _load_patient
from app.schemas import ReportOut, ValidationRequest

router = APIRouter(tags=["reports"])


def _consent_granted(db: Session, patient_id: str, scope: str) -> bool:
    from app.models import Consent
    row = (
        db.query(Consent).filter(Consent.patient_id == patient_id, Consent.scope == scope)
        .order_by(Consent.created_at.desc()).first()
    )
    return bool(row and row.granted)


@router.post("/patients/{patient_id}/reports", response_model=ReportOut,
             status_code=status.HTTP_201_CREATED)
def generate_report(patient_id: str, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)) -> Report:
    if not _is_staff(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only staff can generate a treatment plan")
    p = _load_patient(db, patient_id)

    # Local consent gate (clear UX) — TSPI re-enforces via the payload flags.
    if not _consent_granted(db, p.id, "ai_analysis"):
        audit.write(db, "report_generate_blocked", actor_user_id=user.id, patient_id=p.id,
                    allowed=False, detail={"reason": "ai_analysis consent missing"})
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Patient has not granted 'ai_analysis' consent.")

    # Pre-flight completeness check (spec §5): block a near-empty, symptom-only call.
    summary = deid.summarize(db, p)
    if summary["blocker"]:
        audit.write(db, "report_generate_blocked", actor_user_id=user.id, patient_id=p.id,
                    allowed=False, detail={"reason": summary["blocker"]})
        raise HTTPException(status.HTTP_409_CONFLICT, summary["blocker"])

    payload = deid.build_payload(db, p)            # de-identified + guarded

    try:
        result = tspi.generate_report(payload)
    except tspi.ConsentRejected as e:
        raise HTTPException(status.HTTP_409_CONFLICT, f"TSPI consent check failed: {e}")
    except tspi.BrainUnavailable as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e))

    analysis = result.get("analysis", {}) or {}
    report = Report(
        patient_id=p.id,
        case_id=p.case_id,
        tspi_report_id=result.get("report_id"),
        status=result.get("status", "draft"),
        deliverable=bool(result.get("deliverable", False)),
        nss=analysis.get("nss"),
        severity_level=analysis.get("severity_level"),
        severity_name=analysis.get("severity_name"),
        analysis=analysis,
        modules=result.get("modules", []),
        monitoring=result.get("monitoring", []),
        safety_alerts=result.get("safety_alerts", []),
        report_markdown=result.get("report_markdown", ""),
        disclaimer=result.get("disclaimer", ""),
        generated_by=user.id,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    audit.write(db, "report_generate", actor_user_id=user.id, patient_id=p.id,
                report_id=report.id, detail={"nss": report.nss, "tspi_report_id": report.tspi_report_id,
                                              "labs_sent": summary["confirmed_labs"], "imaging_sent": summary["imaging"],
                                              "conditions": summary["conditions"], "medications": summary["medications"]})
    return report


@router.get("/patients/{patient_id}/report-readiness")
def report_readiness(patient_id: str, db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)) -> dict:
    """What MiHealth would send to TSPI + completeness warnings (spec §5 checklist)."""
    p = _load_patient(db, patient_id)
    _authorize(p, user)
    return deid.summarize(db, p)


@router.get("/patients/{patient_id}/reports", response_model=list[ReportOut])
def list_reports(patient_id: str, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)) -> list[Report]:
    p = _load_patient(db, patient_id)
    _authorize(p, user)
    q = db.query(Report).filter(Report.patient_id == p.id)
    if user.role == Role.patient:
        q = q.filter(Report.deliverable == True)  # noqa: E712  patient sees approved only
    return q.order_by(Report.created_at.desc()).all()


@router.get("/reports/{report_id}", response_model=ReportOut)
def get_report(report_id: str, db: Session = Depends(get_db),
               user: User = Depends(get_current_user)) -> Report:
    rep = db.get(Report, report_id)
    if not rep:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
    p = db.get(Patient, rep.patient_id)
    _authorize(p, user)
    if user.role == Role.patient and not rep.deliverable:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Report not yet available")
    return rep


@router.post("/reports/{report_id}/validate", response_model=ReportOut)
def validate_report(report_id: str, body: ValidationRequest, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)) -> Report:
    """Doctor-only gate to delivery. Locked semantics: approve|edit -> validated & deliverable
    (edit delivers the doctor's edited version); reject -> rejected & not deliverable."""
    if user.role != Role.doctor:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only a doctor can validate a plan")
    rep = db.get(Report, report_id)
    if not rep:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
    patient = db.get(Patient, rep.patient_id)
    if patient.assigned_doctor_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You are not the assigned doctor for this patient")
    if body.decision not in ("approve", "edit", "reject"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "decision must be approve|edit|reject")

    # Mirror to TSPI when we have its report id (skip cleanly for stub-generated reports).
    if rep.tspi_report_id:
        edits = None
        if body.decision == "edit":
            edits = {"note": body.note, "markdown": body.edited_markdown}
        elif body.note:
            edits = {"note": body.note}
        try:
            tspi.validate(rep.tspi_report_id, user.email, body.decision, edits)
        except tspi.BrainUnavailable as e:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e))

    if body.decision == "reject":
        rep.status, rep.deliverable = "rejected", False
    else:  # approve | edit
        rep.status, rep.deliverable = "validated", True
        if body.decision == "edit" and body.edited_markdown:
            rep.report_markdown = body.edited_markdown
    rep.doctor_note = body.note or rep.doctor_note

    db.add(Validation(report_id=rep.id, doctor_id=user.id, decision=body.decision,
                      note=body.note, edited_markdown=body.edited_markdown or ""))
    db.commit()
    db.refresh(rep)
    audit.write(db, "report_validate", actor_user_id=user.id, patient_id=rep.patient_id,
                report_id=rep.id, detail={"decision": body.decision, "deliverable": rep.deliverable})
    return rep
