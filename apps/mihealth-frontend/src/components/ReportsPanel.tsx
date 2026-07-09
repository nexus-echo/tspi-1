import { useEffect, useState } from "react";
import { Readiness, Report, generateReport, getReadiness, listReports } from "../api/reports";
import PlanView from "./PlanView";
import ValidationPanel from "./ValidationPanel";
import OutcomesPanel from "./OutcomesPanel";

// Staff: generate + browse. Doctor (assigned): also validate. Patient: approved plans only.
export default function ReportsPanel({
  patientId,
  canGenerate = false,
  canValidate = false,
  readinessKey = 0,
}: {
  patientId: string;
  canGenerate?: boolean;
  canValidate?: boolean;
  readinessKey?: number;
}) {
  const [reports, setReports] = useState<Report[]>([]);
  const [selected, setSelected] = useState<Report | null>(null);
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function load(selectId?: string) {
    const rs = await listReports(patientId);
    setReports(rs);
    setSelected((cur) => rs.find((r) => r.id === (selectId || cur?.id)) || rs[0] || null);
  }
  useEffect(() => {
    load();
  }, [patientId]);

  useEffect(() => {
    if (canGenerate) getReadiness(patientId).then(setReadiness).catch(() => setReadiness(null));
  }, [patientId, canGenerate, readinessKey]);

  async function onGenerate() {
    setErr("");
    setBusy(true);
    try {
      const rep = await generateReport(patientId);
      await load(rep.id);
      getReadiness(patientId).then(setReadiness).catch(() => {});
    } catch (e: any) {
      const code = e?.response?.status;
      setErr(
        code === 409 ? (e?.response?.data?.detail || "Consent or precondition missing.")
        : code === 502 ? "The TSPI analysis engine is unreachable. Is it running on :8000?"
        : e?.response?.data?.detail || "Failed to generate plan."
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2 style={{ margin: 0 }}>{canGenerate ? "Treatment plans" : "My treatment plan"}</h2>
          {canGenerate && (
            <button onClick={onGenerate} disabled={busy || readiness?.blocker != null}
              title={readiness?.blocker || "Generate a treatment plan"}
              style={{ width: "auto", marginTop: 0, padding: "9px 16px" }}>
              {busy ? "Generating…" : "Generate plan"}
            </button>
          )}
        </div>
        {canGenerate && (
          <p className="muted">
            Builds a de-identified payload (case id + age band + sex + confirmed labs + symptoms +
            imaging + meds/conditions — no PII) and calls the TSPI engine.
          </p>
        )}
        {canGenerate && readiness && (
          <div style={{ margin: "8px 0" }}>
            <div className="muted" style={{ fontSize: 13 }}>
              Will send: <b>{readiness.confirmed_labs}</b> labs · <b>{readiness.symptom_count}</b> symptoms ·{" "}
              <b>{readiness.conditions}</b> conditions · <b>{readiness.medications}</b> meds ·{" "}
              <b>{readiness.imaging}</b> imaging · consent {readiness.ai_analysis_consent ? "✓" : "✗"}
            </div>
            {readiness.blocker && <div className="error">⚠ {readiness.blocker}</div>}
            {readiness.warnings.map((w, i) => (
              <div key={i} style={{ color: "#b45309", fontSize: 13 }}>• {w}</div>
            ))}
          </div>
        )}
        {err && <div className="error">{err}</div>}
        {reports.length > 1 && (
          <select value={selected?.id || ""} onChange={(e) => setSelected(reports.find((r) => r.id === e.target.value) || null)}>
            {reports.map((r) => (
              <option key={r.id} value={r.id}>
                {new Date(r.created_at).toLocaleString()} — {r.status} (NSS {r.nss ?? "—"})
              </option>
            ))}
          </select>
        )}
        {reports.length === 0 && (
          <p className="muted">{canGenerate ? "No plans generated yet." : "No approved plan available yet."}</p>
        )}
      </div>

      {selected && canValidate && (
        <ValidationPanel report={selected} onValidated={(r) => load(r.id)} />
      )}
      {selected && <PlanView report={selected} />}
      {selected && canGenerate && selected.status === "validated" && (
        <OutcomesPanel reportId={selected.id} />
      )}
    </div>
  );
}
