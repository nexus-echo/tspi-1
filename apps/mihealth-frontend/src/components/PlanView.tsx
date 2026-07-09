import { Report } from "../api/reports";
import { printReportPdf } from "../lib/printReport";

const LEVEL_COLOR = ["#059669", "#65a30d", "#d97706", "#dc2626"]; // 0..3

function NssGauge({ nss, level }: { nss: number | null; level: number | null }) {
  const v = Math.max(0, Math.min(100, nss ?? 0));
  const color = LEVEL_COLOR[level ?? 0] || "#2563eb";
  return (
    <div style={{ margin: "8px 0 16px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
        <strong>NSS {nss ?? "—"}</strong>
        <span className="muted">Network Severity Score (0–100)</span>
      </div>
      <div style={{ height: 12, background: "#eee", borderRadius: 8, overflow: "hidden", marginTop: 4 }}>
        <div style={{ width: `${v}%`, height: "100%", background: color }} />
      </div>
    </div>
  );
}

export default function PlanView({ report }: { report: Report }) {
  const a = report.analysis || {};
  const drivers = (a.axis_scores || []).filter((x) => x.is_driver);
  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ margin: 0 }}>Treatment plan</h2>
        <span>
          <span className="badge" style={{ marginRight: 8 }}>{report.status}</span>
          <span className="badge" style={{ marginRight: 8 }}>{report.deliverable ? "deliverable" : "draft — not delivered"}</span>
          <button className="link-btn" onClick={() => printReportPdf(report)} title="Open print dialog — choose 'Save as PDF'">
            Download PDF
          </button>
        </span>
      </div>
      <p className="muted">case {report.case_id}{report.tspi_report_id ? ` · TSPI ${report.tspi_report_id}` : ""}</p>

      <NssGauge nss={report.nss} level={report.severity_level} />
      <p>
        <strong>Severity:</strong>{" "}
        Level {report.severity_level ?? "—"} — {report.severity_name || "—"}
      </p>

      {report.safety_alerts.length > 0 && (
        <div className="card" style={{ background: "#fef2f2", borderColor: "#fecaca" }}>
          <h2 style={{ color: "#b91c1c" }}>⚠ Safety alerts</h2>
          <ul>
            {report.safety_alerts.map((s, i) => (
              <li key={i}>
                <strong>{String((s as any).module || "")}</strong> — {String((s as any).reason || "")}{" "}
                <span className="badge">{String((s as any).severity || "review")}</span>
              </li>
            ))}
          </ul>
          <p className="muted">Flagged for clinician review — never auto-removed.</p>
        </div>
      )}

      {drivers.length > 0 && (
        <>
          <h2>Root-cause drivers</h2>
          <table>
            <thead><tr><th>Axis</th><th>Name</th><th>Severity</th></tr></thead>
            <tbody>
              {drivers.map((ax) => (
                <tr key={ax.axis_code}>
                  <td><span className="badge">{ax.axis_code}</span></td>
                  <td>{ax.axis_name}</td>
                  <td>{ax.severity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {(a.root_cause_chain?.length ?? 0) > 0 && (
        <p><strong>Chain:</strong> {a.root_cause_chain!.join("  →  ")}</p>
      )}

      <h2>Module plan (dosed &amp; sequenced)</h2>
      <table>
        <thead><tr><th>Module</th><th>Phase</th><th>Dose</th><th>Role</th><th></th></tr></thead>
        <tbody>
          {report.modules.map((m, i) => (
            <tr key={i}>
              <td><span className="badge">{m.module_code}</span> {m.module_name || ""}</td>
              <td>{m.phase || "—"}</td>
              <td>{m.dose || "—"}</td>
              <td>{m.clinical_role || "—"}</td>
              <td>{m.resolved === false ? <span className="badge" style={{ background: "#fef3c7" }}>not in catalog</span> : ""}</td>
            </tr>
          ))}
          {report.modules.length === 0 && <tr><td colSpan={5} className="muted">No modules.</td></tr>}
        </tbody>
      </table>

      {report.monitoring.length > 0 && (
        <p className="muted">Reassess: {report.monitoring.map((mo) => JSON.stringify((mo as any).reassess_every_days ?? mo)).join(", ")}</p>
      )}

      {report.doctor_note && (
        <div className="card" style={{ background: "#eff6ff" }}>
          <strong>Doctor note:</strong> {report.doctor_note}
        </div>
      )}

      <h2>Full report</h2>
      <pre style={{ whiteSpace: "pre-wrap", background: "#f8fafc", padding: 12, borderRadius: 8, fontSize: 13 }}>
        {report.report_markdown || "(no narrative)"}
      </pre>
      {report.disclaimer && <p className="muted">{report.disclaimer}</p>}
    </div>
  );
}
