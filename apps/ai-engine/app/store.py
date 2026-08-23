"""Phase 3 persistence + audit (de-identified). Works on SQLite (dev) and Postgres (prod)."""
from __future__ import annotations

import uuid

from app.knowledge.db import get_session, init_db
from app.knowledge.models import AuditLog, OutcomeRow, Report, ReportValidation


def new_id() -> str:
    return uuid.uuid4().hex[:32]


def audit(action: str, *, case_id: str | None = None, report_id: str | None = None,
          actor: str | None = "mihealth", allowed: bool = True, detail: dict | None = None) -> None:
    init_db()
    s = get_session()
    try:
        s.add(AuditLog(action=action, case_id=case_id, report_id=report_id,
                       actor=actor, allowed=allowed, detail=detail or {}))
        s.commit()
    finally:
        s.close()


def save_report(case_id: str, status: str, nss: int, severity_level: int,
                payload: dict, safety_alerts: list | None) -> str:
    init_db()
    rid = new_id()
    s = get_session()
    try:
        s.add(Report(id=rid, case_id=case_id, status=status, nss=nss,
                     severity_level=severity_level, payload=payload,
                     safety_alerts={"alerts": safety_alerts or []}))
        s.commit()
    finally:
        s.close()
    return rid


def get_report(report_id: str) -> dict | None:
    s = get_session()
    try:
        r = s.get(Report, report_id)
        if not r:
            return None
        return {"id": r.id, "case_id": r.case_id, "status": r.status, "nss": r.nss,
                "severity_level": r.severity_level, "payload": r.payload,
                "safety_alerts": (r.safety_alerts or {}).get("alerts", []),
                "deliverable": r.status == "validated"}
    finally:
        s.close()


def record_validation(report_id: str, doctor_id: str, decision: str,
                      edits: dict | None) -> dict | None:
    s = get_session()
    try:
        r = s.get(Report, report_id)
        if not r:
            return None
        r.status = {"approve": "validated", "reject": "rejected", "edit": "validated"}.get(decision, r.status)
        s.add(ReportValidation(report_id=report_id, doctor_id=doctor_id,
                               decision=decision, edits=edits or {}))
        s.commit()
        return {"report_id": report_id, "status": r.status, "deliverable": r.status == "validated"}
    finally:
        s.close()


def save_outcome(report_id: str, marker: str, baseline: float, followup: float) -> dict:
    init_db()
    delta = followup - baseline
    s = get_session()
    try:
        s.add(OutcomeRow(report_id=report_id, marker=marker, baseline=baseline,
                         followup=followup, delta=delta))
        s.commit()
    finally:
        s.close()
    return {"report_id": report_id, "marker": marker, "delta": delta}


# --- Phase 4: axis weights (learning loop) ---
from app.knowledge.models import AxisWeight  # noqa: E402

_WEIGHTS_CACHE: dict[str, float] | None = None


def get_axis_weights() -> dict[str, float]:
    """Cached {axis_code: weight}. Missing axes default to 1.0 at the call site."""
    global _WEIGHTS_CACHE
    if _WEIGHTS_CACHE is None:
        init_db()
        s = get_session()
        try:
            _WEIGHTS_CACHE = {w.axis_code: w.weight for w in s.query(AxisWeight).all()}
        finally:
            s.close()
    return dict(_WEIGHTS_CACHE)


def set_axis_weight(axis_code: str, weight: float, samples: int = 0) -> None:
    init_db()
    s = get_session()
    try:
        w = s.get(AxisWeight, axis_code)
        if w:
            w.weight = weight
            w.samples = samples
        else:
            s.add(AxisWeight(axis_code=axis_code, weight=weight, samples=samples))
        s.commit()
    finally:
        s.close()
    invalidate_weights_cache()


def invalidate_weights_cache() -> None:
    global _WEIGHTS_CACHE
    _WEIGHTS_CACHE = None


def outcomes_for_case(case_id: str) -> list[dict]:
    """All outcomes for a case (joined via its reports), oldest first."""
    s = get_session()
    try:
        rows = (s.query(OutcomeRow, Report.case_id)
                .join(Report, OutcomeRow.report_id == Report.id)
                .filter(Report.case_id == case_id)
                .order_by(OutcomeRow.created_at.asc()).all())
        return [{"marker": o.marker, "baseline": o.baseline, "followup": o.followup,
                 "delta": o.delta, "report_id": o.report_id} for o, _cid in rows]
    finally:
        s.close()


def all_outcomes() -> list[dict]:
    s = get_session()
    try:
        return [{"marker": o.marker, "baseline": o.baseline, "followup": o.followup,
                 "delta": o.delta} for o in s.query(OutcomeRow).all()]
    finally:
        s.close()


def unlearned_outcomes() -> list[dict]:
    s = get_session()
    try:
        rows = s.query(OutcomeRow).filter(OutcomeRow.learned == False).all()  # noqa: E712
        return [{"id": o.id, "marker": o.marker, "delta": o.delta} for o in rows]
    finally:
        s.close()


def mark_learned(ids: list[int]) -> None:
    s = get_session()
    try:
        for oid in ids:
            o = s.get(OutcomeRow, oid)
            if o:
                o.learned = True
        s.commit()
    finally:
        s.close()


# ---------------------------------------------------------------------------
# Phase 12 — 3-level learning store (patient-specific / network behaviour / patient model)
# + population proposals (never auto-applied).
# ---------------------------------------------------------------------------
from datetime import datetime, timezone  # noqa: E402

from app.knowledge.models import (  # noqa: E402
    LearningRecord,
    ModelUpdateProposal,
    NetworkObservation,
    PatientAxisWeight,
    PatientModel,
)


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# --- Level 1: patient-specific axis weights -------------------------------
def get_patient_axis_weights(case_id: str) -> dict[str, float]:
    init_db()
    s = get_session()
    try:
        return {w.axis_code: w.weight
                for w in s.query(PatientAxisWeight).filter_by(case_id=case_id).all()}
    finally:
        s.close()


def get_patient_axis_row(case_id: str, axis_code: str) -> dict | None:
    init_db()
    s = get_session()
    try:
        w = s.get(PatientAxisWeight, {"case_id": case_id, "axis_code": axis_code})
        if not w:
            return None
        return {"case_id": w.case_id, "axis_code": w.axis_code, "weight": w.weight,
                "cumulative_adjustment": w.cumulative_adjustment,
                "consecutive_improvements": w.consecutive_improvements, "samples": w.samples}
    finally:
        s.close()


def upsert_patient_axis_weight(case_id: str, axis_code: str, weight: float,
                               cumulative_adjustment: float, consecutive_improvements: int,
                               samples: int) -> None:
    init_db()
    s = get_session()
    try:
        w = s.get(PatientAxisWeight, {"case_id": case_id, "axis_code": axis_code})
        if w:
            w.weight = weight
            w.cumulative_adjustment = cumulative_adjustment
            w.consecutive_improvements = consecutive_improvements
            w.samples = samples
            w.updated_at = _now()
        else:
            s.add(PatientAxisWeight(case_id=case_id, axis_code=axis_code, weight=weight,
                                    cumulative_adjustment=cumulative_adjustment,
                                    consecutive_improvements=consecutive_improvements,
                                    samples=samples, updated_at=_now()))
        s.commit()
    finally:
        s.close()


# --- Level 2: network behaviour -------------------------------------------
def add_network_observation(case_id: str, changed_first: str, direction: str,
                            downstream: str | None = None, magnitude: float | None = None,
                            time_to_response_days: int | None = None, repeated: bool = False,
                            confounders: str | None = None) -> int:
    init_db()
    s = get_session()
    try:
        row = NetworkObservation(case_id=case_id, changed_first=changed_first, downstream=downstream,
                                 direction=direction, magnitude=magnitude,
                                 time_to_response_days=time_to_response_days, repeated=repeated,
                                 confounders=confounders, created_at=_now())
        s.add(row)
        s.commit()
        return row.id
    finally:
        s.close()


def network_observations(case_id: str | None = None) -> list[dict]:
    init_db()
    s = get_session()
    try:
        q = s.query(NetworkObservation)
        if case_id:
            q = q.filter_by(case_id=case_id)
        return [{"id": r.id, "case_id": r.case_id, "changed_first": r.changed_first,
                 "downstream": r.downstream, "direction": r.direction, "magnitude": r.magnitude,
                 "time_to_response_days": r.time_to_response_days, "repeated": r.repeated}
                for r in q.order_by(NetworkObservation.created_at).all()]
    finally:
        s.close()


# --- Level 3: versioned patient biological model ---------------------------
def latest_patient_model(case_id: str) -> dict | None:
    init_db()
    s = get_session()
    try:
        m = (s.query(PatientModel).filter_by(case_id=case_id)
             .order_by(PatientModel.version.desc()).first())
        if not m:
            return None
        return {"case_id": m.case_id, "version": m.version, "change_kind": m.change_kind,
                "axis_state": m.axis_state, "network_state": m.network_state,
                "trigger": m.trigger, "superseded": m.superseded}
    finally:
        s.close()


def save_patient_model(case_id: str, axis_state: dict, network_state: dict,
                       change_kind: str = "CONFIRM", trigger: str | None = None) -> int:
    """Append a NEW version. Old versions are never deleted (audit history)."""
    init_db()
    s = get_session()
    try:
        prev = (s.query(PatientModel).filter_by(case_id=case_id)
                .order_by(PatientModel.version.desc()).first())
        version = (prev.version + 1) if prev else 1
        if prev:
            prev.superseded = True                 # marked, NOT deleted
        s.add(PatientModel(case_id=case_id, version=version, change_kind=change_kind,
                           axis_state=axis_state, network_state=network_state,
                           trigger=trigger, created_at=_now()))
        s.commit()
        return version
    finally:
        s.close()


def patient_model_history(case_id: str) -> list[dict]:
    init_db()
    s = get_session()
    try:
        return [{"version": m.version, "change_kind": m.change_kind, "trigger": m.trigger,
                 "superseded": m.superseded, "created_at": str(m.created_at)}
                for m in (s.query(PatientModel).filter_by(case_id=case_id)
                          .order_by(PatientModel.version).all())]
    finally:
        s.close()


# --- Level 4: population proposals (propose-only) ---------------------------
def add_proposal(axis_code: str, current_weight: float, proposed_weight: float, sample_size: int,
                 improved: int, worsened: int, rationale: str, blocking_reasons: str) -> int:
    init_db()
    s = get_session()
    try:
        p = ModelUpdateProposal(axis_code=axis_code, current_weight=current_weight,
                                proposed_weight=proposed_weight, sample_size=sample_size,
                                improved=improved, worsened=worsened, rationale=rationale,
                                blocking_reasons=blocking_reasons,
                                status="PROPOSE_MODEL_UPDATE", created_at=_now())
        s.add(p)
        s.commit()
        return p.id
    finally:
        s.close()


def list_proposals(status: str | None = None) -> list[dict]:
    init_db()
    s = get_session()
    try:
        q = s.query(ModelUpdateProposal)
        if status:
            q = q.filter_by(status=status)
        return [{"id": p.id, "axis_code": p.axis_code, "current_weight": p.current_weight,
                 "proposed_weight": p.proposed_weight, "sample_size": p.sample_size,
                 "improved": p.improved, "worsened": p.worsened, "rationale": p.rationale,
                 "blocking_reasons": p.blocking_reasons, "status": p.status,
                 "reviewed_by": p.reviewed_by}
                for p in q.order_by(ModelUpdateProposal.created_at.desc()).all()]
    finally:
        s.close()


def decide_proposal(proposal_id: int, reviewer: str, approve: bool) -> dict | None:
    """Apply a proposal to the GLOBAL model only after explicit clinical approval."""
    init_db()
    s = get_session()
    try:
        p = s.get(ModelUpdateProposal, proposal_id)
        if not p:
            return None
        p.status = "APPROVED" if approve else "REJECTED"
        p.reviewed_by = reviewer
        p.review_date = _now()
        s.commit()
        out = {"id": p.id, "axis_code": p.axis_code, "status": p.status,
               "proposed_weight": p.proposed_weight, "reviewed_by": reviewer}
    finally:
        s.close()
    if approve:
        set_axis_weight(out["axis_code"], out["proposed_weight"], samples=0)   # now (and only now)
    return out


# --- learning records ------------------------------------------------------
def add_learning_record(case_id: str, **kw) -> int:
    init_db()
    s = get_session()
    try:
        r = LearningRecord(case_id=case_id, created_at=_now(), **kw)
        s.add(r)
        s.commit()
        return r.id
    finally:
        s.close()
