import { useState } from "react";
import { getWeights, recalibrate } from "../api/outcomes";

// Admin: trigger the brain's learning recalibration and inspect axis weights.
export default function LearningPanel() {
  const [result, setResult] = useState<any>(null);
  const [weights, setWeights] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function run(fn: () => Promise<any>, set: (v: any) => void) {
    setErr("");
    setBusy(true);
    try {
      set(await fn());
    } catch (e: any) {
      setErr(
        e?.response?.status === 502
          ? "TSPI engine unreachable — start the brain on :8000 to run learning."
          : e?.response?.data?.detail || "Request failed."
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <h2>Learning loop</h2>
      <p className="muted">Recalibrate axis weights from accumulated, doctor-approved outcomes
        (digital-twin loop). Affects future NSS/SPS scoring.</p>
      <div className="row">
        <button onClick={() => run(recalibrate, setResult)} disabled={busy} style={{ width: "auto", padding: "9px 16px" }}>
          {busy ? "Working…" : "Recalibrate now"}
        </button>
        <button className="secondary" onClick={() => run(getWeights, setWeights)} disabled={busy} style={{ width: "auto", padding: "9px 16px" }}>
          View axis weights
        </button>
      </div>
      {err && <div className="error">{err}</div>}
      {result && <div className="ok">Recalibrated — axes changed: {result.axes_changed ?? "—"}</div>}
      {weights && (() => {
        const w = weights.axis_weights ?? weights;
        const empty = !w || Object.keys(w).length === 0;
        return empty ? (
          <div className="muted" style={{ marginTop: 8 }}>
            No learned axis weights yet — the brain starts from neutral (1.0) and only stores weights
            after outcomes are recorded and <em>Recalibrate</em> runs successfully.
          </div>
        ) : (
          <pre style={{ whiteSpace: "pre-wrap", background: "#f8fafc", padding: 12, borderRadius: 8, fontSize: 13 }}>
            {JSON.stringify(w, null, 2)}
          </pre>
        );
      })()}
    </div>
  );
}
