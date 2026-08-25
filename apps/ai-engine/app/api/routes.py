"""HTTP surface of the brain. Thin layer — real work lives in app/pipeline + app/store.

Phase 3: consent enforcement (+ audit), report persistence, doctor-validation workflow,
deliverable gating, outcome capture.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app import learning, red_flags, store
from app.auth import Principal, check_report_access, get_principal, require_role
from app.config import settings
from app.pipeline import extraction
from app.pipeline.orchestrator import analyze, build_report
from app.schemas import (
    AnalysisResult,
    CaseReport,
    OutcomeRecord,
    OverrideRequest,
    PatientInput,
    ValidationRequest,
    ExtractionResult,
)

router = APIRouter()


def _require_consent(p: PatientInput, scope: str) -> None:
    if not p.consent.get(scope, scope == "ai_analysis" and False):
        store.audit("consent_denied", case_id=p.case_id, allowed=False, detail={"scope": scope})
        raise HTTPException(status_code=403, detail=f"Consent '{scope}' not granted.")


def _audit_ctx(p: Principal) -> dict:
    return {"role": p.role, "source": p.source, "request_id": p.request_id}


@router.post("/screen", tags=["safety"])
async def screen_endpoint(patient: PatientInput,
                          p: Principal = Depends(require_role(
                              "clinic_staff", "clinician", "reviewer", "service"))) -> dict:
    """Phase 7 — deterministic red-flag screening. Runs before any TSPI reasoning.

    Conservative by design: it may only escalate care, never withhold it.
    """
    result = red_flags.screen(patient)
    store.audit("red_flag_screen", case_id=patient.case_id, actor=p.id,
                detail={"action_class": result.get("action_class"),
                        "count": len(result.get("red_flags", []))}, **_audit_ctx(p))
    return result


@router.post("/analyze", response_model=AnalysisResult, tags=["diagnosis"])
async def analyze_endpoint(patient: PatientInput,
                           p: Principal = Depends(require_role(
                               "clinic_staff", "clinician", "reviewer", "service"))) -> AnalysisResult:
    _require_consent(patient, "ai_analysis")
    result = await analyze(patient)
    store.audit("analyze", case_id=patient.case_id, actor=p.id,
                detail={"nss": result.nss}, **_audit_ctx(p))
    return result


@router.post("/report", response_model=CaseReport, tags=["diagnosis"])
async def report_endpoint(patient: PatientInput,
                          p: Principal = Depends(require_role(
                              "clinic_staff", "clinician", "reviewer", "service"))) -> CaseReport:
    _require_consent(patient, "ai_analysis")
    report = await build_report(patient)
    # Phase B — stamp ownership/tenant scope (de-identified keys, never PII).
    store.set_report_owner(
        report.report_id,
        clinician_id=(p.id if p.role in ("clinician", "reviewer") else None),
        case_subject=patient.case_id,
        clinic_id=p.clinic_id)
    store.audit("report", case_id=patient.case_id, report_id=report.report_id,
                actor=p.id, **_audit_ctx(p))
    return report


@router.get("/reports/{report_id}", tags=["workflow"])
async def get_report_endpoint(report_id: str,
                              p: Principal = Depends(require_role(
                                  "patient", "clinic_staff", "clinician", "reviewer",
                                  "auditor", "service"))) -> dict:
    rep = store.get_report(report_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Report not found.")
    check_report_access(p, rep, write=False)          # tenant / approved-only gate
    return rep


@router.post("/validate", tags=["workflow"])
async def validate_endpoint(req: ValidationRequest,
                            p: Principal = Depends(require_role(
                                "clinician", "reviewer", "service"))) -> dict:
    existing = store.get_report(req.report_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Report not found.")
    check_report_access(p, existing, write=True)      # only owner clinician / reviewer
    result = store.record_validation(req.report_id, req.doctor_id, req.decision, req.edits)
    store.audit("validate", report_id=req.report_id, actor=(p.id if settings.auth_enabled else req.doctor_id),
                detail={"decision": req.decision}, **_audit_ctx(p))
    return result


@router.post("/reports/{report_id}/override", tags=["workflow"])
async def override_endpoint(report_id: str, req: OverrideRequest,
                            p: Principal = Depends(require_role(
                                "clinician", "reviewer", "service"))) -> dict:
    """Apply structured physician edits to a draft plan (remove/reject module, change dose,
    override safety with justification, add/remove secondary axis, add note). NON-DESTRUCTIVE:
    the original plan and every edit are preserved with reason codes. Editing invalidates any
    prior approval — the plan returns to draft and must be re-approved."""
    existing = store.get_report(report_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    check_report_access(p, existing, write=True)
    result = store.record_override(
        report_id, req.clinician_id, [a.model_dump() for a in req.actions])
    store.audit("override", report_id=report_id, actor=req.clinician_id,
                detail={"actions": [a.action for a in req.actions],
                        "plan_version": result.get("plan_version")}, **_audit_ctx(p))
    return result


@router.get("/audit", tags=["workflow"])
async def audit_endpoint(case_id: str | None = None, report_id: str | None = None,
                         actor: str | None = None, action: str | None = None, limit: int = 200,
                         p: Principal = Depends(require_role("auditor", "reviewer"))) -> dict:
    """Read the append-only audit trail. Auditor/reviewer only."""
    return {"entries": store.list_audit(case_id=case_id, report_id=report_id,
                                        actor=actor, action=action, limit=limit)}


@router.post("/outcome", tags=["learning"])
async def outcome_endpoint(rec: OutcomeRecord,
                           p: Principal = Depends(require_role(
                               "clinician", "reviewer", "service"))) -> dict:
    result = store.save_outcome(rec.report_id, rec.marker, rec.baseline, rec.followup)
    store.audit("outcome", report_id=rec.report_id, detail=result)
    return result


@router.post("/learning/recalibrate", tags=["learning"])
async def recalibrate_endpoint(
        p: Principal = Depends(require_role("reviewer", "service"))) -> dict:
    """Phase 12: PROPOSE-ONLY. Population learning may never auto-change the global model.

    Creates PROPOSE_MODEL_UPDATE proposals for clinical review (expert rule Q11). The previous
    Phase-4 behaviour (auto-recalibrating global axis weights) was non-compliant and is removed.
    """
    result = learning.propose_model_update()
    store.audit("recalibrate", actor="system",
                detail={"proposals_created": result["proposals_created"],
                        "global_model_changed": False})
    return result


@router.get("/learning/proposals", tags=["learning"])
async def list_proposals_endpoint(status: str | None = None) -> dict:
    """Population model-update proposals awaiting clinical review."""
    return learning.list_proposals(status)


@router.post("/learning/proposals/{proposal_id}/decide", tags=["learning"])
async def decide_proposal_endpoint(proposal_id: int, reviewer: str, approve: bool = True,
                                   p: Principal = Depends(require_role("reviewer", "service"))) -> dict:
    """Clinician-gated. This is the ONLY path that may change the global clinical model."""
    result = learning.approve_proposal(proposal_id, reviewer, approve)
    if not result:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    return result


@router.post("/learning/adapt/{case_id}", tags=["learning"])
async def adapt_patient_endpoint(case_id: str) -> dict:
    """Level 1 — patient-specific axis adaptation (bounded +-5%/cycle, +-20% cumulative)."""
    return learning.adapt_patient(case_id)


@router.post("/learning/networks/{case_id}", tags=["learning"])
async def observe_networks_endpoint(case_id: str) -> dict:
    """Level 2 — learn the BEHAVIOUR of biological networks (what moved first, what followed)."""
    return learning.observe_networks(case_id)


@router.get("/patient-model/{case_id}", tags=["learning"])
async def patient_model_endpoint(case_id: str) -> dict:
    """Level 3 — the patient's versioned living biological model (history never deleted)."""
    return learning.patient_model(case_id)


@router.post("/patient-model/{case_id}/rebuild", tags=["learning"])
async def rebuild_patient_model_endpoint(case_id: str, change_kind: str = "REFINE",
                                         trigger: str | None = None,
                                         p: Principal = Depends(require_role("reviewer", "service"))) -> dict:
    """Level 3 — reconstruct the model as a NEW version (CONFIRM/REFINE/REDIRECT/OVERRIDE/CONTRADICT)."""
    return learning.rebuild_patient_model(case_id, change_kind=change_kind, trigger=trigger)


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
    p: Principal = Depends(require_role(
        "patient", "clinic_staff", "clinician", "reviewer", "service")),
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
