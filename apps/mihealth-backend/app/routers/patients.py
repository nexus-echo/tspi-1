"""Patients, intake, and consent. Role-scoped:
- patients can create/read/update only their OWN record (one per patient user);
- staff (admin/doctor) can access any patient; only staff set assigned_doctor_id.
Treatment-plan generation is NOT here — it is staff-only and arrives in Phase D."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import audit
from app.database import get_db
from app.deps import get_current_user
from app.models import CONSENT_SCOPES, Consent, ImagingFinding, Intake, Patient, Role, User
from app.schemas import (
    ConsentOut,
    ConsentSet,
    ImagingIn,
    ImagingOut,
    IntakeCreate,
    IntakeOut,
    PatientCreate,
    PatientOut,
    PatientUpdate,
)
from app.util import band_from_dob, next_case_id

router = APIRouter(prefix="/patients", tags=["patients"])

STAFF = (Role.admin, Role.doctor)


def _is_staff(u: User) -> bool:
    return u.role in STAFF


def _load_patient(db: Session, patient_id: str) -> Patient:
    p = db.get(Patient, patient_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found")
    return p


def _authorize(patient: Patient, user: User) -> None:
    """Staff: any patient. Patient: only the record they own."""
    if _is_staff(user):
        return
    if patient.owner_user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your record")


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(
    body: PatientCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Patient:
    # Ownership: patients always own their own (single) record; staff may set owner/doctor.
    if _is_staff(user):
        owner_user_id = body.owner_user_id
        assigned_doctor_id = body.assigned_doctor_id
    else:
        if db.query(Patient).filter(Patient.owner_user_id == user.id).first():
            raise HTTPException(status.HTTP_409_CONFLICT, "You already have a patient profile")
        owner_user_id = user.id
        assigned_doctor_id = None  # admin assigns doctors manually

    age_band = band_from_dob(body.dob) if body.dob else None

    # Retry once on the rare case_id race.
    for _ in range(3):
        patient = Patient(
            case_id=next_case_id(db),
            owner_user_id=owner_user_id,
            assigned_doctor_id=assigned_doctor_id,
            first_name=body.first_name,
            last_name=body.last_name,
            dob=body.dob,
            sex=body.sex,
            phone=body.phone,
            email=body.email,
            address=body.address,
            age_band=age_band,
        )
        db.add(patient)
        try:
            db.commit()
            db.refresh(patient)
            break
        except IntegrityError:
            db.rollback()
    else:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Could not allocate case_id")

    audit.write(db, "patient_create", actor_user_id=user.id, patient_id=patient.id,
                detail={"case_id": patient.case_id})
    return patient


@router.get("", response_model=list[PatientOut])
def list_patients(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[Patient]:
    q = db.query(Patient)
    if user.role == Role.patient:
        q = q.filter(Patient.owner_user_id == user.id)
    elif user.role == Role.doctor:
        q = q.filter(Patient.assigned_doctor_id == user.id)
    # admin: all
    return q.order_by(Patient.created_at.desc()).all()


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Patient:
    p = _load_patient(db, patient_id)
    _authorize(p, user)
    return p


@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(
    patient_id: str, body: PatientUpdate, db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Patient:
    p = _load_patient(db, patient_id)
    _authorize(p, user)

    data = body.model_dump(exclude_unset=True)
    if "assigned_doctor_id" in data and not _is_staff(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only staff can assign a doctor")

    for field, value in data.items():
        setattr(p, field, value)
    if "dob" in data and p.dob:
        p.age_band = band_from_dob(p.dob)

    db.commit()
    db.refresh(p)
    audit.write(db, "patient_update", actor_user_id=user.id, patient_id=p.id,
                detail={"fields": list(data.keys())})
    return p


# ---- Intake ----

@router.post("/{patient_id}/intake", response_model=IntakeOut, status_code=status.HTTP_201_CREATED)
def create_intake(
    patient_id: str, body: IntakeCreate, db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Intake:
    p = _load_patient(db, patient_id)
    _authorize(p, user)
    intake = Intake(
        patient_id=p.id,
        symptoms_text=body.symptoms_text,
        conditions=body.conditions,
        medications=body.medications,
        lifestyle=body.lifestyle,
        captured_by=user.id,
    )
    db.add(intake)
    db.commit()
    db.refresh(intake)
    audit.write(db, "intake_create", actor_user_id=user.id, patient_id=p.id)
    return intake


@router.get("/{patient_id}/intake", response_model=IntakeOut | None)
def latest_intake(
    patient_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Intake | None:
    p = _load_patient(db, patient_id)
    _authorize(p, user)
    return (
        db.query(Intake).filter(Intake.patient_id == p.id)
        .order_by(Intake.created_at.desc()).first()
    )


# ---- Consent ----

@router.post("/{patient_id}/consent", response_model=ConsentOut, status_code=status.HTTP_201_CREATED)
def set_consent(
    patient_id: str, body: ConsentSet, db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Consent:
    if body.scope not in CONSENT_SCOPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Unknown scope. Allowed: {', '.join(CONSENT_SCOPES)}")
    p = _load_patient(db, patient_id)
    _authorize(p, user)
    row = Consent(patient_id=p.id, scope=body.scope, granted=body.granted, captured_by=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    audit.write(db, "consent_set", actor_user_id=user.id, patient_id=p.id,
                detail={"scope": body.scope, "granted": body.granted})
    return row


@router.get("/{patient_id}/consent", response_model=list[ConsentOut])
def get_consents(
    patient_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[ConsentOut]:
    p = _load_patient(db, patient_id)
    _authorize(p, user)
    # latest row per scope
    rows = (
        db.query(Consent).filter(Consent.patient_id == p.id)
        .order_by(Consent.created_at.desc()).all()
    )
    seen, latest = set(), []
    for r in rows:
        if r.scope not in seen:
            seen.add(r.scope)
            latest.append(r)
    return latest


# ---- Imaging findings ----

@router.post("/{patient_id}/imaging", response_model=ImagingOut, status_code=status.HTTP_201_CREATED)
def add_imaging(patient_id: str, body: ImagingIn, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)) -> ImagingFinding:
    p = _load_patient(db, patient_id)
    _authorize(p, user)
    row = ImagingFinding(patient_id=p.id, text=body.text, confirmed=True)
    db.add(row)
    db.commit()
    db.refresh(row)
    audit.write(db, "imaging_add", actor_user_id=user.id, patient_id=p.id)
    return row


@router.get("/{patient_id}/imaging", response_model=list[ImagingOut])
def list_imaging(patient_id: str, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)) -> list[ImagingFinding]:
    p = _load_patient(db, patient_id)
    _authorize(p, user)
    return (db.query(ImagingFinding).filter(ImagingFinding.patient_id == p.id)
            .order_by(ImagingFinding.created_at).all())
