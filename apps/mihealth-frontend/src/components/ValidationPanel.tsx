import { useState } from "react";
import { Report, ValidationBody, validateReport } from "../api/reports";

// Doctor-only. Approve, Suggest changes (free-text/markdown edit), or Reject.
export default function ValidationPanel({
  report,
  onValidated,
}: {
  report: Report;
  onValidated?: (r: Report) => void;
}) {
  const [mode, setMode] = useState<"" | "edit" | "reject">("");
  const [note, setNote] = useState("");
  const [edited, setEdited] = useState(report.report_markdown);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function submit(body: ValidationBody) {
    setErr("");
    setBusy(true);
    try {
      const r = await validateReport(report.id, body);
      onValidated?.(r);
      setMode("");
    } catch (e: any) {
      setErr(
        e?.response?.status === 502
          ? "TSPI engine unreachable — cannot record validation."
          : e?.response?.data?.detail || "Validation failed."
      );
    } finally {
      setBusy(false);
    }
  }

  if (report.status === "validated")
    return <div className="card ok">Approved — delivered to the patient{report.doctor_note ? ` · note: ${report.doctor_note}` : ""}.</div>;
  if (report.status === "rejected")
    return <div className="card error">Rejected{report.doctor_note ? ` · ${report.doctor_note}` : ""}. Not delivered.</div>;

  return (
    <div className="card" style={{ marginBottom: 16, background: "#f0f9ff" }}>
      <h2>Doctor validation</h2>
      <p className="muted">You hold final authority. Approve to deliver to the patient, suggest
        changes (your edited version is delivered), or reject.</p>
      {err && <div className="error">{err}</div>}

      {mode === "" && (
        <div className="row">
          <button onClick={() => submit({ decision: "approve" })} disabled={busy}>Approve &amp; deliver</button>
          <button className="secondary" onClick={() => setMode("edit")} disabled={busy}>Suggest changes</button>
          <button style={{ background: "#dc2626" }} onClick={() => setMode("reject")} disabled={busy}>Reject</button>
        </div>
      )}

      {mode === "edit" && (
        <>
          <label>Edited plan (markdown) — this version is delivered</label>
          <textarea value={edited} onChange={(e) => setEdited(e.target.value)} rows={10}
            style={{ width: "100%", fontFamily: "monospace", fontSize: 13 }} />
          <label>Note to record</label>
          <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="e.g. reduced KS dose" />
          <div className="row">
            <button onClick={() => submit({ decision: "edit", note, edited_markdown: edited })} disabled={busy}>
              Save changes &amp; deliver
            </button>
            <button className="secondary" onClick={() => setMode("")} disabled={busy}>Cancel</button>
          </div>
        </>
      )}

      {mode === "reject" && (
        <>
          <label>Reason for rejection</label>
          <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="e.g. insufficient data" />
          <div className="row">
            <button style={{ background: "#dc2626" }} onClick={() => submit({ decision: "reject", note })} disabled={busy}>
              Confirm reject
            </button>
            <button className="secondary" onClick={() => setMode("")} disabled={busy}>Cancel</button>
          </div>
        </>
      )}
    </div>
  );
}
