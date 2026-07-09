import { useEffect, useState } from "react";
import { Lab, listPatientLabs } from "../api/documents";

// Read-only list of confirmed labs (the set that will feed plan generation).
export default function ConfirmedLabs({ patientId, refreshKey = 0 }: { patientId: string; refreshKey?: number }) {
  const [labs, setLabs] = useState<Lab[]>([]);
  useEffect(() => {
    listPatientLabs(patientId, true).then(setLabs);
  }, [patientId, refreshKey]);

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <h2>Confirmed labs</h2>
      <p className="muted">Clinician-confirmed values. Only these (no PII) are sent to the analysis engine.</p>
      <table>
        <thead><tr><th>Analyte</th><th>Value</th><th>Unit</th><th>Reference</th><th>Source</th></tr></thead>
        <tbody>
          {labs.map((l) => (
            <tr key={l.id}>
              <td>{l.analyte}</td>
              <td>{l.value}</td>
              <td>{l.unit || "—"}</td>
              <td>{l.ref_low ?? "—"}{(l.ref_low != null || l.ref_high != null) ? " – " : ""}{l.ref_high ?? ""}</td>
              <td><span className="badge">{l.source}</span></td>
            </tr>
          ))}
          {labs.length === 0 && <tr><td colSpan={5} className="muted">No confirmed labs yet.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
