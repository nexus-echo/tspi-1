import { useEffect, useState } from "react";
import {
  DocumentT,
  Lab,
  confirmLabs,
  getDocumentLabs,
  listDocuments,
} from "../api/documents";

// Editable row uses strings throughout (form inputs); converted to Lab on save.
interface Row {
  id?: string;
  analyte: string;
  value: string;
  unit: string;
  ref_low: string;
  ref_high: string;
}

const toRow = (l: Lab): Row => ({
  id: l.id,
  analyte: l.analyte,
  value: l.value ?? "",
  unit: l.unit ?? "",
  ref_low: l.ref_low == null ? "" : String(l.ref_low),
  ref_high: l.ref_high == null ? "" : String(l.ref_high),
});

const numOrNull = (s: string): number | null => (s.trim() === "" ? null : Number(s));

export default function LabReview({ patientId, onConfirmed }: { patientId: string; onConfirmed?: () => void }) {
  const [docs, setDocs] = useState<DocumentT[]>([]);
  const [docId, setDocId] = useState<string>("");
  const [rows, setRows] = useState<Row[]>([]);
  const [msg, setMsg] = useState<{ ok?: string; err?: string }>({});

  async function loadDocs() {
    const d = await listDocuments(patientId);
    setDocs(d);
    if (!docId && d[0]) setDocId(d[0].id);
  }
  useEffect(() => {
    loadDocs();
  }, [patientId]);

  useEffect(() => {
    if (docId) getDocumentLabs(docId).then((ls) => setRows(ls.map(toRow)));
  }, [docId]);

  function update(i: number, field: keyof Row, value: string) {
    setRows((rs) => rs.map((r, idx) => (idx === i ? { ...r, [field]: value } : r)));
  }
  function removeRow(i: number) {
    setRows((rs) => rs.filter((_, idx) => idx !== i));
  }
  function addRow() {
    setRows((rs) => [...rs, { analyte: "", value: "", unit: "", ref_low: "", ref_high: "" }]);
  }

  async function confirm() {
    setMsg({});
    try {
      const payload: Lab[] = rows
        .filter((r) => r.analyte.trim())
        .map((r) => ({
          id: r.id,
          analyte: r.analyte,
          value: r.value,
          unit: r.unit || null,
          ref_low: numOrNull(r.ref_low),
          ref_high: numOrNull(r.ref_high),
        }));
      const saved = await confirmLabs(docId, payload);
      setRows(saved.map(toRow));
      setMsg({ ok: `Confirmed ${saved.length} labs` });
      await loadDocs();
      onConfirmed?.();
    } catch (e: any) {
      setMsg({ err: e?.response?.data?.detail || "Confirm failed" });
    }
  }

  if (docs.length === 0) return <div className="card muted">No uploaded documents to review yet.</div>;

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <h2>Review &amp; confirm labs</h2>
      <label>Document</label>
      <select value={docId} onChange={(e) => setDocId(e.target.value)}>
        {docs.map((d) => (
          <option key={d.id} value={d.id}>{d.original_filename} — {d.ocr_status}</option>
        ))}
      </select>
      <table>
        <thead>
          <tr><th>Analyte</th><th>Value</th><th>Unit</th><th>Ref low</th><th>Ref high</th><th></th></tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.id || i}>
              <td><input value={r.analyte} onChange={(e) => update(i, "analyte", e.target.value)} /></td>
              <td><input value={r.value} onChange={(e) => update(i, "value", e.target.value)} /></td>
              <td><input value={r.unit} onChange={(e) => update(i, "unit", e.target.value)} /></td>
              <td><input value={r.ref_low} onChange={(e) => update(i, "ref_low", e.target.value)} /></td>
              <td><input value={r.ref_high} onChange={(e) => update(i, "ref_high", e.target.value)} /></td>
              <td><button className="link-btn" onClick={() => removeRow(i)}>Remove</button></td>
            </tr>
          ))}
          {rows.length === 0 && <tr><td colSpan={6} className="muted">No candidate labs — add rows manually.</td></tr>}
        </tbody>
      </table>
      <button className="secondary" onClick={addRow} style={{ width: "auto", padding: "8px 14px" }}>+ Add row</button>
      {msg.err && <div className="error">{msg.err}</div>}
      {msg.ok && <div className="ok">{msg.ok}</div>}
      <button onClick={confirm}>Confirm labs</button>
    </div>
  );
}
