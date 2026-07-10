"""Wires the official TSPI-AI decision flow (Phase 0-3):
collect -> 12 Systems -> 39 Axes -> NSS -> SPS -> Level -> modules -> dosing -> KS ->
safety flags -> compose -> persist (de-identified) -> doctor validation gate.
"""
from __future__ import annotations

from app import safety, store
from app.config import settings
from app.knowledge import dosing
from app.knowledge.repository import KnowledgeRepo
from app.llm.provider import LLMProvider
from app.pipeline import (
    axis_mapper,
    graph_engine,
    module_matcher,
    normalizer,
    report_composer,
    sequencer,
    severity,
    step_locator,
)
from app.schemas import AnalysisResult, CaseReport, PatientInput

_repo = KnowledgeRepo()
_llm = LLMProvider()


async def analyze(patient: PatientInput) -> AnalysisResult:
    signals = normalizer.normalize(patient)
    axis_scores = await axis_mapper.map_axes(signals, _repo)
    chain, axis_scores = graph_engine.root_cause(axis_scores)
    weights = store.get_axis_weights()                 # Phase 4: learned weights (neutral if none)
    nss = severity.compute_nss(axis_scores, weights)
    level = dosing.level_for_nss(nss)
    sps = severity.compute_sps(axis_scores, weights)
    position, gap = step_locator.locate(axis_scores)
    return AnalysisResult(
        case_id=patient.case_id, signals=signals, axis_scores=axis_scores,
        root_cause_chain=chain, nss=nss, severity_level=level["level"],
        severity_name=level["name"], system_priority=sps,
        nine_step_position=position, prakati_gap=gap,
        notes=["NSS uses a documented heuristic pending the official formula.",
               dosing.safety_note()],
    )


async def build_report(patient: PatientInput) -> CaseReport:
    analysis = await analyze(patient)
    modules = module_matcher.match(analysis.axis_scores, _repo, patient.medications)
    modules = sequencer.sequence(modules)

    level = dosing.level_for_nss(analysis.nss)
    level_dose = dosing.dose_string(level)
    for m in modules:
        if m.dose_type == "bowel" or dosing.is_bowel(m.module_code) or dosing.is_bowel(m.module_name or ""):
            m.dose = dosing.bowel_dose(m.module_name or m.module_code)
        else:
            m.dose = level_dose

    # Phase 3 — safety flags (never drop a module; flag for clinician)
    alerts = safety.check_modules(modules, patient.medications, patient.conditions)

    report = await report_composer.compose(analysis, modules, _llm)
    report.monitoring = [{"reassess_every_days": dosing.reassessment_days()}]
    report.safety_alerts = alerts
    _meta = _repo.registry_meta()
    report.registry_version = _meta.get("registry_version")
    report.framework_version = _meta.get("framework_version")

    # Phase 3 — persist (de-identified) + doctor-validation gate
    status = "draft" if settings.require_doctor_validation else "validated"
    report.status = status
    report.deliverable = status == "validated"
    report.report_id = store.save_report(
        analysis.case_id, status, analysis.nss, analysis.severity_level,
        report.model_dump(mode="json"), alerts)
    store.audit("report", case_id=analysis.case_id, report_id=report.report_id,
                detail={"nss": analysis.nss, "level": analysis.severity_level,
                        "safety_alerts": len(alerts)})
    return report
