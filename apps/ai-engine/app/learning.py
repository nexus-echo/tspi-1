"""Phase 12 — Adaptive Biological Intelligence Loop.

Replaces the Phase-4 loop, which auto-updated GLOBAL axis weights from individual outcomes.
That behaviour was declared NON-COMPLIANT by the domain experts (TSPI 3, Q11):

    "The AI must not automatically modify the Global Clinical Model. It may only generate
     PROPOSE_MODEL_UPDATE ... Only then may a new Model Version enter Production."

Three levels of learning:

  Level 1  adapt_patient()   -- patient-specific axis adaptation. Bounded: max +-5% per review
                               cycle, max +-20% cumulative. Improvement must be SUSTAINED
                               (>=2 consecutive) before priority is relaxed.
  Level 2  observe_networks() -- network BEHAVIOUR learning: which network moved first, what
                               followed, time-to-response, magnitude, repeatability.
                               "What the AI learns is not disease -- it is the behaviour of
                               biological networks."
  Level 3  rebuild_patient_model() -- versioned living patient model (v1 -> v2 -> v3).
                               New evidence may CONFIRM / REFINE / REDIRECT / OVERRIDE /
                               CONTRADICT. Old versions are never deleted.
  Level 4  propose_model_update() -- population learning: PROPOSALS ONLY, gated on sample size,
                               confounder review, statistics and clinical approval.
"""
from __future__ import annotations

import re
from collections import defaultdict

from app import store

# marker -> axis (placeholder until the official Marker Registry arrives)
_MARKER_AXIS = {
    "crp": "A1", "hscrp": "A1", "esr": "A1",
    "hba1c": "A5", "glucose": "A5", "fastingglucose": "A5",
    "hemoglobin": "A26", "hb": "A26", "mcv": "A26",
    "tsh": "A33", "ft3": "A33", "ft4": "A33",
    "ige": "A2", "vitamind": "A15",
}
# Ferritin deliberately omitted: it is CONTEXT_DEPENDENT (25 Jul Q1), not higher-better,
# and its inflammatory axis is A1, not A26/A34. The Marker Registry resolves it by context.
_LOWER_IS_BETTER = {"crp", "hscrp", "esr", "hba1c", "glucose", "fastingglucose", "ige"}
_HIGHER_IS_BETTER = {"hemoglobin", "hb", "vitamind"}

# --- expert-specified bounds (Q11) ---
MAX_STEP = 0.05                  # +-5% per review cycle
MAX_CUMULATIVE = 0.20            # +-20% cumulative, patient-specific
SUSTAINED_IMPROVEMENTS = 2       # >=2 consecutive improvements before relaxing priority
MIN_POPULATION_SAMPLE = 30       # population proposals need a real sample
_WMIN, _WMAX = 0.5, 2.0

CHANGE_KINDS = ("CONFIRM", "REFINE", "REDIRECT", "OVERRIDE", "CONTRADICT")


def _norm(m: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (m or "").lower())


def _improved(marker_norm: str, change: float) -> bool | None:
    # Marker Registry is authoritative (25 Jul). CONTEXT_DEPENDENT / TARGET_RANGE markers
    # return None here -> a raw delta is not interpretable, so learning must not infer a
    # direction (e.g. ferritin is context-dependent, NOT higher-better).
    from app.markers import direction_is_better
    verdict = direction_is_better(marker_norm, change)
    if verdict is not None:
        return verdict
    if marker_norm in _LOWER_IS_BETTER:
        return change < 0
    if marker_norm in _HIGHER_IS_BETTER:
        return change > 0
    return None                    # unknown direction -> never learn from it


# ---------------------------------------------------------------------------
# LEVEL 1 — patient-specific adaptation (bounded; never global)
# ---------------------------------------------------------------------------
def adapt_patient(case_id: str) -> dict:
    """Adjust THIS patient's axis priorities from their own outcomes. Bounded and reversible."""
    outs = store.outcomes_for_case(case_id)
    agg: dict[str, list[int]] = defaultdict(lambda: [0, 0])       # axis -> [improved, worsened]
    for o in outs:
        m = _norm(o["marker"])
        axis = _MARKER_AXIS.get(m)
        if not axis:
            continue
        imp = _improved(m, o["delta"])
        if imp is None:
            continue
        agg[axis][0 if imp else 1] += 1

    changed: dict[str, dict] = {}
    for axis, (imp, wor) in agg.items():
        n = imp + wor
        if n == 0:
            continue
        row = store.get_patient_axis_row(case_id, axis) or {
            "weight": 1.0, "cumulative_adjustment": 0.0, "consecutive_improvements": 0, "samples": 0}
        consec = row["consecutive_improvements"]
        note = None

        if wor > imp:
            step = MAX_STEP                       # worsening -> more emphasis
            consec = 0
        elif imp > wor:
            consec += 1
            if consec < SUSTAINED_IMPROVEMENTS:
                # improvement must be SUSTAINED before we relax priority
                step = 0.0
                note = f"improvement not yet sustained ({consec}/{SUSTAINED_IMPROVEMENTS}) - weight held"
            else:
                step = -MAX_STEP
        else:
            step = 0.0
            note = "mixed outcomes - no change"

        # clamp cumulative drift to +-20%
        cum = row["cumulative_adjustment"] + step
        if abs(cum) > MAX_CUMULATIVE:
            step = (MAX_CUMULATIVE - abs(row["cumulative_adjustment"])) * (1 if step > 0 else -1)
            step = max(0.0, step) if step > 0 else min(0.0, step)
            cum = row["cumulative_adjustment"] + step
            note = "cumulative bound (+-20%) reached"

        new_w = min(_WMAX, max(_WMIN, row["weight"] + step))
        store.upsert_patient_axis_weight(case_id, axis, round(new_w, 4), round(cum, 4),
                                         consec, row["samples"] + n)
        changed[axis] = {"weight": round(new_w, 4), "step": round(step, 4),
                         "cumulative_adjustment": round(cum, 4), "improved": imp,
                         "worsened": wor, "consecutive_improvements": consec, "note": note}

    store.audit("learning_adapt_patient", case_id=case_id, detail={"axes_changed": len(changed)})
    return {"case_id": case_id, "level": "PATIENT_SPECIFIC", "axes_changed": len(changed),
            "bounds": {"max_step": MAX_STEP, "max_cumulative": MAX_CUMULATIVE,
                       "sustained_improvements_required": SUSTAINED_IMPROVEMENTS},
            "updated": changed}


# ---------------------------------------------------------------------------
# LEVEL 2 — network behaviour learning
# ---------------------------------------------------------------------------
def observe_networks(case_id: str) -> dict:
    """Record how this patient's axes/networks moved relative to one another over time."""
    outs = store.outcomes_for_case(case_id)
    events = []
    for o in outs:
        m = _norm(o["marker"])
        axis = _MARKER_AXIS.get(m)
        imp = _improved(m, o["delta"])
        if not axis or imp is None:
            continue
        events.append({"axis": axis, "direction": "improved" if imp else "worsened",
                       "magnitude": abs(o["delta"]), "at": o.get("created_at")})

    recorded = []
    if len(events) >= 1:
        first = events[0]
        downstream = next((e["axis"] for e in events[1:] if e["axis"] != first["axis"]), None)
        prior = store.network_observations(case_id)
        repeated = any(p["changed_first"] == first["axis"] and p["direction"] == first["direction"]
                       for p in prior)
        oid = store.add_network_observation(
            case_id=case_id, changed_first=first["axis"], direction=first["direction"],
            downstream=downstream, magnitude=first["magnitude"], repeated=repeated)
        recorded.append({"id": oid, "changed_first": first["axis"], "downstream": downstream,
                         "direction": first["direction"], "repeated": repeated})
    store.audit("learning_observe_networks", case_id=case_id, detail={"recorded": len(recorded)})
    return {"case_id": case_id, "level": "NETWORK_BEHAVIOUR", "observations": recorded,
            "history": store.network_observations(case_id)}


# ---------------------------------------------------------------------------
# LEVEL 3 — versioned patient biological model
# ---------------------------------------------------------------------------
def rebuild_patient_model(case_id: str, axis_state: dict | None = None,
                          network_state: dict | None = None, change_kind: str = "REFINE",
                          trigger: str | None = None) -> dict:
    """Reconstruct the patient's biological model as a NEW version. Never overwrites history."""
    if change_kind not in CHANGE_KINDS:
        change_kind = "REFINE"
    axis_state = axis_state if axis_state is not None else store.get_patient_axis_weights(case_id)
    network_state = network_state if network_state is not None else {
        "observations": store.network_observations(case_id)}
    version = store.save_patient_model(case_id, axis_state, network_state, change_kind, trigger)
    store.audit("patient_model_rebuild", case_id=case_id,
                detail={"version": version, "change_kind": change_kind})
    return {"case_id": case_id, "level": "PATIENT_BIOLOGICAL_MODEL", "version": version,
            "change_kind": change_kind, "trigger": trigger,
            "history": store.patient_model_history(case_id)}


def patient_model(case_id: str) -> dict:
    return {"case_id": case_id, "current": store.latest_patient_model(case_id),
            "history": store.patient_model_history(case_id)}


# ---------------------------------------------------------------------------
# LEVEL 4 — population learning: PROPOSE ONLY (never auto-applied)
# ---------------------------------------------------------------------------
def propose_model_update() -> dict:
    """Analyse accumulated outcomes and PROPOSE global weight changes for clinical review.

    This function deliberately does NOT change the global model. Approval is required
    (see approve_proposal) -- expert rule Q11.
    """
    outs = store.unlearned_outcomes()
    agg: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for o in outs:
        m = _norm(o["marker"])
        axis = _MARKER_AXIS.get(m)
        if not axis:
            continue
        imp = _improved(m, o["delta"])
        if imp is None:
            continue
        agg[axis][0 if imp else 1] += 1

    store.mark_learned([o["id"] for o in outs])
    weights = store.get_axis_weights()
    proposals = []
    for axis, (imp, wor) in agg.items():
        n = imp + wor
        if n == 0:
            continue
        signal = (wor - imp) / n
        current = weights.get(axis, 1.0)
        proposed = min(_WMAX, max(_WMIN, current + MAX_STEP * signal))
        blocking = []
        if n < MIN_POPULATION_SAMPLE:
            blocking.append(f"sample_size {n} < required {MIN_POPULATION_SAMPLE}")
        blocking += ["confounder review pending", "statistical validation pending",
                     "clinical review required"]
        pid = store.add_proposal(
            axis_code=axis, current_weight=current, proposed_weight=round(proposed, 4),
            sample_size=n, improved=imp, worsened=wor,
            rationale=(f"{wor} worsened vs {imp} improved across {n} outcomes "
                       f"-> propose weight {current:.3f} -> {proposed:.3f}"),
            blocking_reasons="; ".join(blocking))
        proposals.append({"id": pid, "axis_code": axis, "current_weight": current,
                          "proposed_weight": round(proposed, 4), "sample_size": n,
                          "status": "PROPOSE_MODEL_UPDATE", "blocking_reasons": blocking})

    store.audit("learning_propose_model_update", actor="system",
                detail={"proposals": len(proposals)})
    return {"level": "POPULATION", "status": "PROPOSE_MODEL_UPDATE",
            "global_model_changed": False,          # <-- the compliance guarantee
            "proposals_created": len(proposals), "proposals": proposals,
            "note": ("AI may only propose. A proposed update must pass sample size, data-quality, "
                     "confounder review, statistics, clinical review and version approval before "
                     "it can enter production.")}


def list_proposals(status: str | None = None) -> dict:
    return {"proposals": store.list_proposals(status)}


def approve_proposal(proposal_id: int, reviewer: str, approve: bool = True) -> dict | None:
    """Clinician-gated. ONLY this path may change the global model."""
    result = store.decide_proposal(proposal_id, reviewer, approve)
    if result:
        store.audit("learning_proposal_decision", actor=reviewer,
                    detail={"proposal_id": proposal_id, "status": result["status"]})
    return result


# ---------------------------------------------------------------------------
# temporal trajectory (unchanged behaviour)
# ---------------------------------------------------------------------------
def temporal(case_id: str) -> dict:
    outs = store.outcomes_for_case(case_id)
    by_marker: dict[str, list[dict]] = defaultdict(list)
    for o in outs:
        by_marker[o["marker"]].append(o)

    series = []
    for marker, rows in by_marker.items():
        first, last = rows[0]["baseline"], rows[-1]["followup"]
        change = last - first
        imp = _improved(_norm(marker), change)
        trend = "flat" if abs(change) < 1e-9 else (
            "improving" if imp else "worsening" if imp is False else "changed")
        series.append({"marker": marker, "first": first, "last": last,
                       "change": round(change, 3), "trend": trend, "points": len(rows)})
    return {"case_id": case_id, "markers": series}


# --- deprecated Phase-4 entry point ---------------------------------------
def recalibrate(learning_rate: float | None = None) -> dict:
    """DEPRECATED: Phase-4 global auto-recalibration was non-compliant.

    Kept as a stable entry point; it now PROPOSES instead of applying.
    """
    out = propose_model_update()
    out["deprecated"] = ("recalibrate() no longer modifies the global model; it creates "
                         "PROPOSE_MODEL_UPDATE proposals requiring clinical approval.")
    out["axes_changed"] = 0                 # nothing is auto-changed any more
    return out
