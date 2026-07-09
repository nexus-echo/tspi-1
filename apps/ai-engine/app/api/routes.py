"""HTTP surface of the brain. Thin layer — real work lives in app/pipeline + app/store.

Phase 3: consent enforcement (+ audit), report persistence, doctor-validation workflow,
deliverable gating, outcome capture.
"""
from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app import learning, store
from app.config import settings
from app.pipeline import extraction
from app.pipeline.orchestrator import analyze, build_report
from app.schemas import (
    AnalysisResult,
    CaseReport,
    OutcomeRecord,
    PatientInput,
    ValidationRequest,
    ExtractionResult,
)

router = APIRouter()


def _require_consent(p: PatientInput, scope: str) -> None:
    if not p.consent.get(scope, scope == "ai_analysis" and False):
        store.audit("consent_denied", case_id=p.case_id, allowed=False, detail={"scope": scope})
        raise HTTPException(status_code=403, detail=f"Consent '{scope}' not granted.")


@router.post("/analyze", response_model=AnalysisResult, tags=["diagnosis"])
async def analyze_endpoint(patient: PatientInput) -> AnalysisResult:
    _require_consent(patient, "ai_analysis")
    result = await analyze(patient)
    store.audit("analyze", case_id=patient.case_id, detail={"nss": result.nss})
    return result


@router.post("/report", response_model=CaseReport, tags=["diagnosis"])
async def report_endpoint(patient: PatientInput) -> CaseReport:
    _require_consent(patient, "ai_analysis")
    return await build_report(patient)


@router.get("/reports/{report_id}", tags=["workflow"])
async def get_report_endpoint(report_id: str) -> dict:
    rep = store.get_report(report_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Report not found.")
    return rep


@router.post("/validate", tags=["workflow"])
async def validate_endpoint(req: ValidationRequest) -> dict:
    result = store.record_validation(req.report_id, req.doctor_id, req.decision, req.edits)
    if not result:
        raise HTTPException(status_code=404, detail="Report not found.")
    store.audit("validate", report_id=req.report_id, actor=req.doctor_id,
                detail={"decision": req.decision})
    return result


@router.post("/outcome", tags=["learning"])
async def outcome_endpoint(rec: OutcomeRecord) -> dict:
    result = store.save_outcome(rec.report_id, rec.marker, rec.baseline, rec.followup)
    store.audit("outcome", report_id=rec.report_id, detail=result)
    return result


@router.post("/learning/recalibrate", tags=["learning"])
async def recalibrate_endpoint() -> dict:
    """Phase 4: update axis weights from accumulated outcomes (feeds weight-aware NSS/SPS)."""
    result = learning.recalibrate()
    store.audit("recalibrate", actor="system", detail={"axes_changed": result["axes_changed"]})
    return result


@router.get("/learning/weights", tags=["learning"])
async def weights_endpoint() -> dict:
    return {"axis_weights": store.get_axis_weights()}


@router.get("/temporal/{case_id}", tags=["learning"])
async def temporal_endpoint(case_id: str) -> dict:
    """Phase 4: per-marker trajectory for a case across its outcomes."""
    return learning.temporal(case_id)


@router.get("/knowledge/health", tags=["knowledge"])
async def knowledge_health() -> dict:
    return {
        "deidentification_enforced": settings.enforce_deidentification,
        "doctor_validation_required": settings.require_doctor_validation,
    }


@router.post("/extract", response_model=ExtractionResult, tags=["extraction"])
async def extract_endpoint(
    file: UploadFile = File(...),
    doc_type: str = Form("lab"),
) -> ExtractionResult:
    """Read ONE uploaded report file (image / scanned PDF / text PDF) with LOCAL models and
    return candidate labs + imaging narrative. Governance: local-only; confirmed=False (a human
    must review before it feeds diagnosis). Raw file bytes are processed in-memory, not stored."""
    data = await file.read()
    result = await extraction.extract_from_file(
        data, file.content_type or "", file.filename or "", doc_type
    )
    store.audit("extract", detail={"source": result.source, "engine": result.engine,
                                   "labs": len(result.labs)})
    return result
