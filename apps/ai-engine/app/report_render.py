"""P5 — bilingual report renderer (en/th), physician + patient audiences.

Deterministic render of the CaseReport (Analysis Object) into the common template
(docs/02-reference/TSPI_Report_Template.md). Section labels + fixed phrases localise (en/th);
canonical identifiers (axis/module codes, marker names, units) stay stable. PII stays as
`{{patient.*}}` placeholders — the identified version substitutes them at render (deid.reidentify),
never in the LLM prompt and never over chat.
"""
from __future__ import annotations

from app.steps import steps as _steps

L = {
    "en": {
        "title": "TSPI Integrative Case Report", "patient": "Patient", "case": "Case",
        "date": "Date", "language": "Language", "status": "Status",
        "summary": "Patient Clinical Summary", "assessment": "Assessment",
        "overview": "Clinical Overview — a Network Disorder",
        "axes": "Biological Systems / Axis Analysis", "notassessed": "Not assessed",
        "network": "Integrated Network Model", "objectives": "Therapeutic Objectives",
        "plan": "Treatment Protocol — Module Plan", "dose": "Dose", "targets": "Target axes",
        "monitoring": "Follow-up Monitoring", "principle": "Final Clinical Principle",
        "safety": "Safety & Red Flags", "disclaimer": "Disclaimer", "steps": "Restoration steps engaged",
        "severity": "Network Severity", "coverage": "Assessment coverage", "confidence": "Confidence",
        "confirmed": "Confirmed", "probable": "Probable", "notknown": "Not yet known",
        "yourplan": "Your plan", "nextsteps": "Suggested next tests",
        "prakati": "Ultimate goal: return to Prakati (biological balance).",
        "none": "none",
    },
    "th": {
        "title": "รายงานกรณีศึกษาเชิงบูรณาการ TSPI", "patient": "ผู้ป่วย", "case": "เคส",
        "date": "วันที่", "language": "ภาษา", "status": "สถานะ",
        "summary": "สรุปทางคลินิกของผู้ป่วย", "assessment": "การประเมิน",
        "overview": "ภาพรวมทางคลินิก — ความผิดปกติเชิงเครือข่าย",
        "axes": "การวิเคราะห์ระบบชีวภาพ / แกน", "notassessed": "ยังไม่ได้ประเมิน",
        "network": "แบบจำลองเครือข่ายเชิงบูรณาการ", "objectives": "เป้าหมายการรักษา",
        "plan": "โปรโตคอลการรักษา — แผนโมดูล", "dose": "ขนาด", "targets": "แกนเป้าหมาย",
        "monitoring": "การติดตามผล", "principle": "หลักการทางคลินิก",
        "safety": "ความปลอดภัยและสัญญาณอันตราย", "disclaimer": "ข้อจำกัดความรับผิดชอบ",
        "steps": "ขั้นตอนการฟื้นฟูที่เกี่ยวข้อง", "severity": "ความรุนแรงเครือข่าย",
        "coverage": "ความครอบคลุมการประเมิน", "confidence": "ความเชื่อมั่น",
        "confirmed": "ยืนยันแล้ว", "probable": "น่าจะเป็น", "notknown": "ยังไม่ทราบ",
        "yourplan": "แผนของคุณ", "nextsteps": "การตรวจที่แนะนำเพิ่มเติม",
        "prakati": "เป้าหมายสูงสุด: กลับสู่ปกติ (Prakati) สมดุลทางชีวภาพ",
        "none": "ไม่มี",
    },
}


def _lang(x: str | None) -> str:
    x = (x or "en").lower()
    return x if x in L else "en"


def render(cr: dict, language: str | None = None, audience: str = "physician") -> str:
    lang = _lang(language or cr.get("report_language"))
    t = L[lang]
    a = cr.get("analysis", {}) or {}
    nss = cr.get("nss_detail", {}) or {}
    out: list[str] = []

    # Header
    out += [f"# {t['title']}", ""]
    out.append(f"**{t['patient']}:** {{{{patient.full_name}}}}   ·   {t['case']}: {cr.get('case_id','')}")
    out.append(f"{t['language']}: {lang}   ·   {t['status']}: {cr.get('status','draft')}")
    if cr.get("pilot_notice"):
        out.append(f"\n> ⚠ {cr['pilot_notice']}")
    out.append("")

    if audience == "patient":
        return _render_patient(out, t, a, cr)

    # Physician report ---------------------------------------------------------
    out += [f"## {t['summary']}", ""]
    out.append(f"**{t['assessment']}:** {t['severity']} {a.get('nss',0)}/100 "
               f"({a.get('severity_name','')}) · {t['coverage']} {nss.get('assessment_coverage','?')}% "
               f"· {t['confidence']} {nss.get('overall_confidence_label','?')}")
    out.append("")

    # Axis analysis
    out += [f"## {t['axes']}", ""]
    for ax in a.get("axis_scores", []):
        drv = " (driver)" if ax.get("is_driver") else ""
        out.append(f"- **{ax['axis_code']} {ax['axis_name']}** — {ax.get('severity','')}"
                   f"{drv} · status {ax.get('status','')} · grade {ax.get('evidence_grade') or '—'}")
    na = a.get("not_assessed", [])
    if na:
        out.append(f"\n_{t['notassessed']}:_ " + ", ".join(x['axis_code'] for x in na[:20]))
    out.append("")

    # Network model
    nets = cr.get("networks", [])
    if nets:
        out += [f"## {t['network']}", ""]
        out.append(" · ".join(a.get("root_cause_chain", [])) or "—")
        out.append("")
        for n in nets[:8]:
            out.append(f"- {n.get('name','')} ({n.get('legacy_id','')} → {n.get('primary_axis','')}) "
                       f"[{n.get('mapping_status','CANDIDATE')}]")
        out.append("")

    # Module plan
    out += [f"## {t['plan']}", ""]
    for m in cr.get("modules", []):
        note = " · ".join(m.get("match_notes", []))
        out.append(f"- **{m.get('module_code','')} {m.get('module_name') or ''}** — "
                   f"{t['dose']}: {m.get('dose') or '—'} · {t['targets']}: {', '.join(m.get('target_axes', []))} "
                   f"· safety {m.get('safety_outcome','PASS')}{(' · ' + note) if note else ''}")
    steps_engaged = sorted({s['code'] for s in _steps()})  # pilot: list canonical steps
    out.append(f"\n_{t['steps']}:_ S1–S9 ({len(steps_engaged)})")
    out.append("")

    # Monitoring
    mon = cr.get("monitoring", [])
    if mon:
        out += [f"## {t['monitoring']}", ""]
        for x in mon[:20]:
            out.append(f"- {x}")
        out.append("")

    # Safety
    out += [f"## {t['safety']}", ""]
    rf = (cr.get("red_flag_screen") or {}).get("red_flags", [])
    if rf:
        for f in rf:
            out.append(f"- 🚩 {f.get('name','')} [{f.get('action_class','')}]")
    else:
        out.append(f"- {t['none']}")
    for s in cr.get("safety_alerts", []):
        out.append(f"- {s.get('module') or '*'}: {s.get('reason','')}")
    out.append("")

    out += [f"## {t['principle']}", "", t["prakati"], ""]
    out.append(f"> {cr.get('disclaimer','')}")
    return "\n".join(out)


def _render_patient(out: list[str], t: dict, a: dict, cr: dict) -> str:
    """Simplified patient view — Confirmed / Probable / Not-yet-known / plan / safety."""
    high = [ax for ax in a.get("axis_scores", []) if ax.get("status") == "HIGH_CONFIDENCE_ASSESSED"]
    prob = [ax for ax in a.get("axis_scores", []) if ax.get("status") in ("ASSESSED", "PROVISIONALLY_ASSESSED")]
    out += [f"## {t['confirmed']}", ""]
    out += [f"- {ax['axis_name']}" for ax in high] or [f"- {t['none']}"]
    out += ["", f"## {t['probable']}", ""]
    out += [f"- {ax['axis_name']}" for ax in prob] or [f"- {t['none']}"]
    out += ["", f"## {t['notknown']}", ""]
    out += [f"- {x['axis_code']} {x.get('axis_name','')}" for x in a.get("not_assessed", [])[:8]] or [f"- {t['none']}"]
    out += ["", f"## {t['yourplan']}", ""]
    out += [f"- {m.get('module_name') or m.get('module_code')} — {m.get('dose') or ''}"
            for m in cr.get("modules", [])] or [f"- {t['none']}"]
    out += ["", f"## {t['safety']}", ""]
    rf = (cr.get("red_flag_screen") or {}).get("red_flags", [])
    out += [f"- 🚩 {f.get('name','')}" for f in rf] or [f"- {t['none']}"]
    out += ["", f"> {cr.get('disclaimer','')}"]
    return "\n".join(out)
