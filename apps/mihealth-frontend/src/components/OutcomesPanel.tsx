import { FormEvent, useEffect, useState } from "react";
import { Outcome, listOutcomes, recordOutcome } from "../api/outcomes";

// Staff records follow-up markers on a validated report -> feeds the learning loop.
export default function OutcomesPanel({ reportId }: { reportId: string }) {
  const [rows, setRows] = useState<Outcome[]>([]);
  const [marker, setMarker] = useState("");
  const [baseline, setBaseline] = useState("");
  const [followup, setFollowup] = useState("");
  const [msg, setMsg] = useState<{ ok?: string; err?: string }>({});

  async function load() {
    setRows(await listOutcomes(reportId));
  }
  useEffect(() => {
    load();
  }, [reportId]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setMsg({});
    try {
      await recordOutcome(reportId, { marker, baseline: Number(baseline), followup: Number(followup) });
      setMarker(""); setBaseline(""); setFollowup("");
      await load();
      setMsg({ ok: "Outcome recorded" });
    } catch (e: any) {
      setMsg({ err: e?.response?.data?.detail || "Failed to record outcome" });
    }
  }

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <h2>Follow-up outcomes</h2>
      <p className="muted">Record baseline vs follow-up markers. These feed the brain's learning loop
        (recalibration is an admin action).</p>
      <form onSubmit={submit}>
        <div className="row">
          <div><label>Marker</label><input value={marker} onChange={(e) => setMarker(e.target.value)} placeholder="e.g. CRP" required /></div>
          <div><label>Baseline</label><input type="number" step="any" value={baseline} onChange={(e) => setBaseline(e.target.value)} required /></div>
          <div><label>Follow-up</label><input type="number" step="any" value={followup} onChange={(e) => setFollowup(e.target.value)} required /></div>
        </div>
        {msg.err && <div className="error">{msg.err}</div>}
        {msg.ok && <div className="ok">{msg.ok}</div>}
        <button style={{ width: "auto", padding: "8px 16px" }}>Record outcome</button>
      </form>
      <table>
        <thead><tr><th>Marker</th><th>Baseline</th><th>Follow-up</th><th>Δ</th><th>Synced</th></tr></thead>
        <tbody>
          {rows.map((o) => (
            <tr key={o.id}>
              <td>{o.marker}</td>
              <td>{o.baseline}</td>
              <td>{o.followup}</td>
              <td style={{ color: o.delta < 0 ? "#059669" : o.delta > 0 ? "#dc2626" : undefined }}>
                {o.delta > 0 ? "▲" : o.delta < 0 ? "▼" : ""} {o.delta.toFixed(2)}
              </td>
              <td>{o.synced_to_tspi ? "✓" : "local"}</td>
            </tr>
          ))}
          {rows.length === 0 && <tr><td colSpan={5} className="muted">No outcomes recorded yet.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
