import { useEffect, useRef, useState } from "react";
import { DocumentT, listDocuments, uploadDocument } from "../api/documents";

const STATUS_LABEL: Record<string, string> = {
  pending: "Processing…",
  review: "Ready for clinician review",
  done: "Confirmed",
  failed: "Could not auto-read — needs manual entry",
};

export default function DocumentUpload({
  patientId,
  onChange,
}: {
  patientId: string;
  onChange?: () => void;
}) {
  const [docs, setDocs] = useState<DocumentT[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  async function load() {
    setDocs(await listDocuments(patientId));
  }
  useEffect(() => {
    load();
  }, [patientId]);

  async function onUpload() {
    const f = fileRef.current?.files?.[0];
    if (!f) return;
    setErr("");
    setBusy(true);
    try {
      await uploadDocument(patientId, f);
      if (fileRef.current) fileRef.current.value = "";
      await load();
      // OCR runs in the background; refresh once shortly after.
      setTimeout(async () => {
        await load();
        onChange?.();
      }, 1500);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <h2>Health reports</h2>
      <p className="muted">Upload a lab report (PDF, image, or text). It is read automatically into
        lab values, then confirmed by clinical staff before use.</p>
      <div className="row" style={{ alignItems: "end" }}>
        <div style={{ flex: 3 }}>
          <input ref={fileRef} type="file" accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff,.txt,.csv" />
        </div>
        <div style={{ flex: 1 }}>
          <button onClick={onUpload} disabled={busy}>{busy ? "Uploading…" : "Upload"}</button>
        </div>
      </div>
      {err && <div className="error">{err}</div>}
      <table>
        <thead><tr><th>File</th><th>Type</th><th>Status</th><th></th></tr></thead>
        <tbody>
          {docs.map((d) => (
            <tr key={d.id}>
              <td>{d.original_filename || "—"}</td>
              <td>{d.doc_type}</td>
              <td><span className="badge">{STATUS_LABEL[d.ocr_status] || d.ocr_status}</span></td>
              <td><button className="link-btn" onClick={load}>Refresh</button></td>
            </tr>
          ))}
          {docs.length === 0 && <tr><td colSpan={4} className="muted">No reports uploaded yet.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
