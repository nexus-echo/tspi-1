"""SQLAlchemy models for the knowledge base (relational source of truth).

This is the 'exact catalog' half of storage. The 'semantic librarian' half lives in the
vector store (pgvector/Chroma), embedded FROM these rows so there is one source of truth.

Run migrations in Phase 0 to load: 39 axes (from the Thai summary PDFs / axes/*.md) and the
module/product catalog, then populate `axis_module_map`.
"""
from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Key(Base):                      # 3 Keys
    __tablename__ = "keys"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(1), unique=True)   # A / B / C
    name: Mapped[str] = mapped_column(String(120))


class Step(Base):                     # 9 Steps of Wellness
    __tablename__ = "steps"
    id: Mapped[int] = mapped_column(primary_key=True)
    order: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(120))


class Domain(Base):                   # 12 Domains
    __tablename__ = "domains"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    key_id: Mapped[int | None] = mapped_column(ForeignKey("keys.id"))
    axes: Mapped[list["Axis"]] = relationship(back_populates="domain")


class Axis(Base):                     # 39 Axes
    __tablename__ = "axes"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(8), unique=True)   # A1..A39
    name: Mapped[str] = mapped_column(String(200))
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id"))
    domain: Mapped[Domain] = relationship(back_populates="axes")
    sub_axes: Mapped[list["SubAxis"]] = relationship(back_populates="axis")


class SubAxis(Base):
    __tablename__ = "sub_axes"
    id: Mapped[int] = mapped_column(primary_key=True)
    axis_id: Mapped[int] = mapped_column(ForeignKey("axes.id"))
    letter: Mapped[str] = mapped_column(String(2))             # A / B / C / D
    description: Mapped[str] = mapped_column(Text)
    axis: Mapped[Axis] = relationship(back_populates="sub_axes")


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    tspi_id: Mapped[str | None] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(200))
    ingredients: Mapped[str | None] = mapped_column(Text)
    mechanisms: Mapped[str | None] = mapped_column(Text)
    active_compounds: Mapped[str | None] = mapped_column(Text)
    dosage: Mapped[str | None] = mapped_column(Text)
    safety: Mapped[str | None] = mapped_column(Text)
    therapeutic_focus: Mapped[str | None] = mapped_column(Text)


class Module(Base):                   # therapeutic unit = ONE product (1 module = 1 product)
    __tablename__ = "modules"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)          # H-Code (primary business key)
    name: Mapped[str | None] = mapped_column(String(200))               # English canonical name
    name_th: Mapped[str | None] = mapped_column(String(200))            # localized display name
    phytocore_code: Mapped[str | None] = mapped_column(String(120))     # long-term scientific ID
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))   # 1:1 product link
    dose_type: Mapped[str] = mapped_column(String(16), default="severity")      # severity | bowel
    status: Mapped[str] = mapped_column(String(16), default="active")           # active|deprecated|archived|draft
    replaced_by: Mapped[str | None] = mapped_column(String(32))         # successor H-Code (supersede)
    registry_version: Mapped[str | None] = mapped_column(String(32))
    contraindications: Mapped[str | None] = mapped_column(Text)         # JSON-encoded list of notes


class ModuleProduct(Base):            # kept for history; module<->product is now 1:1
    __tablename__ = "module_products"
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id"), primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), primary_key=True)


class AxisModuleMap(Base):            # THE key mapping table (axis -> module, with role)
    __tablename__ = "axis_module_map"
    axis_id: Mapped[int] = mapped_column(ForeignKey("axes.id"), primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id"), primary_key=True)
    relevance: Mapped[float] = mapped_column(Float, default=1.0)
    role: Mapped[str] = mapped_column(String(16), default="primary")    # primary | secondary


class RegistryMeta(Base):             # which registry/framework versions are loaded
    __tablename__ = "registry_meta"
    id: Mapped[int] = mapped_column(primary_key=True)
    registry_version: Mapped[str | None] = mapped_column(String(32))
    framework_version: Mapped[str | None] = mapped_column(String(32))
    effective_date: Mapped[str | None] = mapped_column(String(32))


# ---------------------------------------------------------------------------
# Phase 3 — workflow, audit & outcomes (de-identified; no PII stored)
# ---------------------------------------------------------------------------
from datetime import datetime, timezone  # noqa: E402

from sqlalchemy import JSON, Boolean, DateTime  # noqa: E402


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Report(Base):
    """A generated TSPI Case Report (de-identified). Persisted for validation + audit."""
    __tablename__ = "reports"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)        # uuid
    case_id: Mapped[str] = mapped_column(String(64))                     # de-identified handle
    status: Mapped[str] = mapped_column(String(16), default="draft")    # draft|validated|rejected
    nss: Mapped[int] = mapped_column(Integer, default=0)
    severity_level: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[dict] = mapped_column(JSON)                          # full CaseReport JSON
    safety_alerts: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ReportValidation(Base):
    __tablename__ = "report_validations"
    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"))
    doctor_id: Mapped[str] = mapped_column(String(64))
    decision: Mapped[str] = mapped_column(String(16))                    # approve|edit|reject
    edits: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class OutcomeRow(Base):
    __tablename__ = "outcomes"
    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"))
    marker: Mapped[str] = mapped_column(String(64))
    baseline: Mapped[float] = mapped_column(Float)
    followup: Mapped[float] = mapped_column(Float)
    delta: Mapped[float] = mapped_column(Float)
    learned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class AuditLog(Base):
    """Append-only audit trail. Records actions + consent decisions; no PII."""
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(40))     # analyze|report|validate|outcome|consent_denied
    case_id: Mapped[str | None] = mapped_column(String(64))
    report_id: Mapped[str | None] = mapped_column(String(40))
    actor: Mapped[str | None] = mapped_column(String(64))   # 'mihealth' | doctor_id | 'system'
    allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    detail: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class AxisWeight(Base):
    """Phase 4 — learned per-axis weight (1.0 = neutral). Adjusted by the learning loop from
    outcomes; consumed by the severity engine (NSS/SPS)."""
    __tablename__ = "axis_weights"
    axis_code: Mapped[str] = mapped_column(String(8), primary_key=True)   # A1..A39
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    samples: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
