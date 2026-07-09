"""ORM models. Phase A: User (auth + roles). Phase B: Patient, Intake, Consent, AuditLog.
Later phases add documents, lab_results, reports, validations, outcomes."""
from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    JSON,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.encryption import EncryptedString


class Role(str, enum.Enum):
    admin = "admin"
    doctor = "doctor"
    patient = "patient"


class Sex(str, enum.Enum):
    female = "female"
    male = "male"
    other = "other"
    unknown = "unknown"


CONSENT_SCOPES = ("ai_analysis", "doctor_sharing", "tspi_connection", "research")


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[Role] = mapped_column(SAEnum(Role), nullable=False, default=Role.patient)
    full_name: Mapped[str] = mapped_column(String, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    owner_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    assigned_doctor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    first_name: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    last_name: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    phone: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    email: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    address: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)

    age_band: Mapped[str | None] = mapped_column(String, nullable=True)
    sex: Mapped[Sex] = mapped_column(SAEnum(Sex), default=Sex.unknown)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Intake(Base):
    __tablename__ = "intake"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True, nullable=False)
    symptoms_text: Mapped[str] = mapped_column(String, default="")
    conditions: Mapped[list] = mapped_column(JSON, default=list)
    medications: Mapped[list] = mapped_column(JSON, default=list)
    lifestyle: Mapped[dict] = mapped_column(JSON, default=dict)
    captured_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Consent(Base):
    __tablename__ = "consents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True, nullable=False)
    scope: Mapped[str] = mapped_column(String, nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, default=False)
    captured_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    action: Mapped[str] = mapped_column(String, nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    patient_id: Mapped[str | None] = mapped_column(String, nullable=True)
    report_id: Mapped[str | None] = mapped_column(String, nullable=True)
    allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


DOC_TYPES = ("lab", "imaging", "other")
OCR_STATUSES = ("pending", "review", "done", "failed")
LAB_SOURCES = ("ocr", "manual")


class Document(Base):
    """An uploaded health report file. Raw file stays in MiHealth only (may contain PII);
    only confirmed, structured labs (no PII) are later sent to TSPI."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, default="")
    mime_type: Mapped[str] = mapped_column(String, default="")
    size_bytes: Mapped[int] = mapped_column(default=0)
    doc_type: Mapped[str] = mapped_column(String, default="lab")
    ocr_status: Mapped[str] = mapped_column(String, default="pending")
    ocr_note: Mapped[str] = mapped_column(String, default="")
    uploaded_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LabResult(Base):
    """A single lab value. Created by OCR (confirmed=False) or manually; staff confirm before use."""

    __tablename__ = "lab_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True, nullable=False)
    document_id: Mapped[str | None] = mapped_column(ForeignKey("documents.id"), nullable=True, index=True)
    analyte: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(String, default="")     # kept as text (numbers or qualitative)
    unit: Mapped[str | None] = mapped_column(String, nullable=True)
    ref_low: Mapped[float | None] = mapped_column(nullable=True)
    ref_high: Mapped[float | None] = mapped_column(nullable=True)
    flag: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str] = mapped_column(String, default="ocr")
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmed_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ImagingFinding(Base):
    __tablename__ = "imaging_findings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True, nullable=False)
    document_id: Mapped[str | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    text: Mapped[str] = mapped_column(String, default="")
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


REPORT_STATUSES = ("draft", "validated", "rejected")


class Report(Base):
    """A TSPI Case Report mirrored in MiHealth. PII-free analysis; links to patient via case_id.
    deliverable flips true only after a doctor validates (Phase E)."""

    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True, nullable=False)
    case_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    tspi_report_id: Mapped[str | None] = mapped_column(String, nullable=True)

    status: Mapped[str] = mapped_column(String, default="draft")
    deliverable: Mapped[bool] = mapped_column(Boolean, default=False)

    nss: Mapped[int | None] = mapped_column(nullable=True)
    severity_level: Mapped[int | None] = mapped_column(nullable=True)
    severity_name: Mapped[str | None] = mapped_column(String, nullable=True)

    analysis: Mapped[dict] = mapped_column(JSON, default=dict)
    modules: Mapped[list] = mapped_column(JSON, default=list)
    monitoring: Mapped[list] = mapped_column(JSON, default=list)
    safety_alerts: Mapped[list] = mapped_column(JSON, default=list)
    report_markdown: Mapped[str] = mapped_column(String, default="")
    disclaimer: Mapped[str] = mapped_column(String, default="")

    doctor_note: Mapped[str] = mapped_column(String, default="")   # Phase E doctor edits/notes
    generated_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Validation(Base):
    """Doctor's decision on a report (mirrors what we POST to TSPI /validate)."""

    __tablename__ = "validations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), index=True, nullable=False)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    decision: Mapped[str] = mapped_column(String, nullable=False)   # approve | edit | reject
    note: Mapped[str] = mapped_column(String, default="")
    edited_markdown: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Outcome(Base):
    """A follow-up marker (baseline vs follow-up) feeding the learning loop."""

    __tablename__ = "outcomes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), index=True, nullable=False)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True, nullable=False)
    marker: Mapped[str] = mapped_column(String, nullable=False)
    baseline: Mapped[float] = mapped_column(nullable=False)
    followup: Mapped[float] = mapped_column(nullable=False)
    delta: Mapped[float] = mapped_column(nullable=False)
    synced_to_tspi: Mapped[bool] = mapped_column(Boolean, default=False)
    recorded_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
