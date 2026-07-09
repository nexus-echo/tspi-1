import { FormEvent, useEffect, useState } from "react";
import { Imaging, addImaging, listImaging } from "../api/patients";

// Staff enter imaging findings (e.g. "pelvic ultrasound: intramural fibroid") -> sent to TSPI.
export default function ImagingPanel({ patientId, onChange }: { patientId: string; onChange?: () => void }) {
  const [rows, setRows] = useState<Imaging[]>([]);
  const [text, setText] = useState("");

  async function load() {
    setRows(await listImaging(patientId));
  }
  useEffect(() => {
    load();
  }, [patientId]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    await addImaging(patientId, text.trim());
    setText("");
    await load();
    onChange?.();
  }

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <h2>Imaging findings</h2>
      <p className="muted">Free-text radiology/imaging impressions. Each line is sent to TSPI.</p>
      <form onSubmit={submit}>
        <input value={text} onChange={(e) => setText(e.target.value)}
          placeholder="e.g. pelvic ultrasound: intramural uterine fibroid" />
        <button style={{ width: "auto", padding: "8px 16px" }}>Add finding</button>
      </form>
      <ul className="muted">
        {rows.map((r) => <li key={r.id}>{r.text}</li>)}
        {rows.length === 0 && <li>No imaging findings recorded.</li>}
      </ul>
    </div>
  );
}
