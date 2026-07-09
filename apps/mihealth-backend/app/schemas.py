"""Pydantic request/response models. Phase A (auth+users) + Phase B (patients/intake/consent)."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import Role, Sex


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    role: Role
    full_name: str
    is_active: bool
    last_login_at: datetime | None = None

    class Config:
        from_attributes = True


class AdminCreateUser(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""
    role: Role  # admin or doctor (patients self-register)


# ---- Phase B: patients, intake, consent ----

class PatientCreate(BaseModel):
    first_name: str = ""
    last_name: str = ""
    dob: date | None = None
    sex: Sex = Sex.unknown
    phone: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    owner_user_id: str | None = None
    assigned_doctor_id: str | None = None


class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    dob: date | None = None
    sex: Sex | None = None
    phone: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    assigned_doctor_id: str | None = None


class PatientOut(BaseModel):
    id: str
    case_id: str
    owner_user_id: str | None = None
    assigned_doctor_id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    dob: date | None = None
    sex: Sex
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    age_band: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class IntakeCreate(BaseModel):
    symptoms_text: str = ""
    conditions: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    lifestyle: dict[str, str] = Field(default_factory=dict)


class IntakeOut(IntakeCreate):
    id: str
    patient_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConsentSet(BaseModel):
    scope: str
    granted: bool


class ConsentOut(BaseModel):
    scope: str
    granted: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Phase C: documents + labs ----

class DocumentOut(BaseModel):
    id: str
    patient_id: str
    original_filename: str
    mime_type: str
    size_bytes: int
    doc_type: str
    ocr_status: str
    ocr_note: str
    created_at: datetime

    class Config:
        from_attributes = True


class LabResultOut(BaseModel):
    id: str
    patient_id: str
    document_id: str | None = None
    analyte: str
    value: str
    unit: str | None = None
    ref_low: float | None = None
    ref_high: float | None = None
    flag: str | None = None
    source: str
    confirmed: bool

    class Config:
        from_attributes = True


class LabResultIn(BaseModel):
    id: str | None = None            # present -> update existing candidate; absent -> new row
    analyte: str
    value: str = ""
    unit: str | None = None
    ref_low: float | None = None
    ref_high: float | None = None
    flag: str | None = None


class ConfirmLabsRequest(BaseModel):
    labs: list[LabResultIn]          # staff-edited set; all marked confirmed on save


# ---- Phase D: reports ----

class ReportOut(BaseModel):
    id: str
    patient_id: str
    case_id: str
    tspi_report_id: str | None = None
    status: str
    deliverable: bool
    nss: int | None = None
    severity_level: int | None = None
    severity_name: str | None = None
    analysis: dict = {}
    modules: list = []
    monitoring: list = []
    safety_alerts: list = []
    report_markdown: str = ""
    disclaimer: str = ""
    doctor_note: str = ""
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Phase E: doctor validation ----

class ValidationRequest(BaseModel):
    decision: str                    # approve | edit | reject
    note: str = ""
    edited_markdown: str | None = None   # used with decision='edit' (free-text/markdown only)


# ---- Phase F: outcomes + learning ----

class OutcomeCreate(BaseModel):
    marker: str
    baseline: float
    followup: float


class OutcomeOut(BaseModel):
    id: str
    report_id: str
    patient_id: str
    marker: str
    baseline: float
    followup: float
    delta: float
    synced_to_tspi: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Imaging findings (spec: imaging[] when available) ----

class ImagingIn(BaseModel):
    text: str


class ImagingOut(BaseModel):
    id: str
    patient_id: str
    text: str
    confirmed: bool
    created_at: datetime

    class Config:
        from_attributes = True
