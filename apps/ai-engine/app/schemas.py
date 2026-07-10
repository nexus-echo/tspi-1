"""Pydantic contracts for the whole pipeline.

input -> signals -> axis scores (+NSS/level/SPS) -> dosed modules -> de-identified report
(+ safety alerts, report_id, deliverable). Phase 3 adds validation/consent/audit fields.
"""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Severity(str, Enum):
    optimal = "optimal"
    subclinical = "subclinical"
    functional_impairment = "functional_impairment"
    pathological = "pathological"


class KeyCode(str, Enum):
    A = "A"
    B = "B"
    C = "C"


class LabResult(BaseModel):
    analyte: str
    value: float | str
    unit: str | None = None
    ref_low: float | None = None
    ref_high: float | None = None
    flag: str | None = None


class PatientInput(BaseModel):
    """De-identified by contract: case_id + minimal demographics only."""
    case_id: str = Field(..., examples=["TSPI-EX-001"])
    age_band: str | None = Field(None, examples=["mid-40s"])
    sex: Literal["female", "male", "other", "unknown"] = "unknown"
    symptoms: str = ""
    labs: list[LabResult] = []
    imaging: list[str] = []
    medications: list[str] = []
    conditions: list[str] = []          # for safety/contraindication checks
    lifestyle: dict[str, str] = {}
    omics: dict[str, str] = {}
    consent: dict[str, bool] = {}       # ai_analysis, doctor_sharing, tspi_connection, ...


class BiologicalSignal(BaseModel):
    concept: str
    direction: Literal["up", "down", "abnormal", "normal"] = "abnormal"
    magnitude: float | None = None
    source: str


class AxisScore(BaseModel):
    axis_code: str
    axis_name: str
    domain_code: str | None = None
    key: KeyCode | None = None
    severity: Severity
    is_driver: bool = False
    inferred: bool = False
    evidence: list[str] = []


class ModulePick(BaseModel):
    module_code: str
    module_name: str | None = None
    target_axes: list[str] = []
    mechanism: str | None = None
    dose: str | None = None
    clinical_role: str | None = None
    safety: str | None = None
    phase: Literal["step_1", "step_2", "step_3"] = "step_1"
    resolved: bool = True
    phytocore_code: str | None = None
    dose_type: str = "severity"                 # severity | bowel
    status: str = "active"
    axis_roles: dict[str, str] = {}             # axis_code -> "primary" | "secondary"
    contraindications: list[str] = []


class AnalysisResult(BaseModel):
    case_id: str
    signals: list[BiologicalSignal]
    axis_scores: list[AxisScore]
    root_cause_chain: list[str]
    nss: int = 0
    severity_level: int = 0
    severity_name: str = ""
    system_priority: list[dict] = []
    nine_step_position: int | None = None
    prakati_gap: str | None = None
    notes: list[str] = []


class CaseReport(BaseModel):
    case_id: str
    report_id: str | None = None              # persisted id (Phase 3)
    analysis: AnalysisResult
    modules: list[ModulePick]
    monitoring: list[dict] = []
    safety_alerts: list[dict] = []            # contraindication flags (Phase 3)
    report_markdown: str = ""
    disclaimer: str = "For clinician review and approval — not a substitute for medical judgment."
    status: Literal["draft", "validated", "rejected"] = "draft"
    deliverable: bool = False                 # only true once a doctor validates
    registry_version: str | None = None       # which module-registry version produced this
    framework_version: str | None = None      # which 39-axis framework version


class ValidationRequest(BaseModel):
    report_id: str
    doctor_id: str
    decision: Literal["approve", "edit", "reject"]
    edits: dict | None = None


class OutcomeRecord(BaseModel):
    report_id: str
    marker: str
    baseline: float
    followup: float


# --- Lab/imaging extraction (POST /extract) ---
class ExtractedLab(BaseModel):
    analyte: str
    value: float | str
    unit: str | None = None
    ref_low: float | None = None
    ref_high: float | None = None
    flag: str | None = None                 # H/L/normal/abnormal if the report states one


class ExtractionResult(BaseModel):
    """Candidate structured data read from ONE uploaded file. Always confirmed=False:
    a human must review before it feeds diagnosis (governance gate preserved)."""
    source: str                              # image | pdf-text | pdf-scan | text | unknown
    engine: str                              # e.g. ollama-vision:qwen2.5vl | ollama-text:qwen2.5:14b | heuristic
    labs: list[ExtractedLab] = []
    imaging_modality: str | None = None      # e.g. "Ultrasound (pelvic)"
    imaging_impression: str | None = None    # radiologist impression / conclusion
    imaging_findings: list[str] = []         # bulletable findings (sizes, locations, ...)
    narrative: str | None = None             # any free-text summary the model produced
    confirmed: bool = False
    notes: str = ""
