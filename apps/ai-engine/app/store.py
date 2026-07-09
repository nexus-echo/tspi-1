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
