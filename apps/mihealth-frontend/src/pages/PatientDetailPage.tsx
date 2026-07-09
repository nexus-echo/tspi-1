import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import {
  Patient,
  StaffUser,
  getPatient,
  listDoctors,
  updatePatient,
} from "../api/patients";
import ConsentCenter from "../components/ConsentCenter";
import IntakeForm from "../components/IntakeForm";
import DocumentUpload from "../components/DocumentUpload";
import LabReview from "../components/LabReview";
import ConfirmedLabs from "../components/ConfirmedLabs";
import ImagingPanel from "../components/ImagingPanel";
import ReportsPanel from "../components/ReportsPanel";
import Layout from "./Layout";

// Staff view of one patient: profile, consent/intake (read), documents + OCR lab review,
// confirmed labs. Admin may (re)assign a doctor.
export default function PatientDetailPage() {
  const { id = "" } = useParams();
  const { user } = useAuth();
  const [p, setP] = useState<Patient | null>(null);
  const [doctors, setDoctors] = useState<StaffUser[]>([]);
  const [err, setErr] = useState("");
  const [labsKey, setLabsKey] = useState(0);

  useEffect(() => {
    getPatient(id).then(setP).catch((e) => setErr(e?.response?.data?.detail || "Not found"));
    if (user?.role === "admin") listDoctors().then(setDoctors).catch(() => {});
  }, [id]);

  async function assign(doctorId: string) {
    setP(await updatePatient(id, { assigned_doctor_id: doctorId || null }));
  }

  if (err) return <Layout title="Patient"><div className="card error">{err}</div></Layout>;
  if (!p) return <Layout title="Patient"><div className="card">Loading…</div></Layout>;

  const isAdmin = user?.role === "admin";

  return (
    <Layout title={`${p.first_name || ""} ${p.last_name || ""}`.trim() || "Patient"}>
      <p><Link to={isAdmin ? "/admin/patients" : "/doctor"}>← Back</Link></p>

      <div className="card" style={{ marginBottom: 16 }}>
        <span className="badge">{p.case_id}</span>
        <table>
          <tbody>
            <tr><th>Age band</th><td>{p.age_band || "—"}</td></tr>
            <tr><th>Sex</th><td>{p.sex}</td></tr>
            <tr><th>DOB</th><td>{p.dob || "—"}</td></tr>
            <tr><th>Phone</th><td>{p.phone || "—"}</td></tr>
            <tr><th>Email</th><td>{p.email || "—"}</td></tr>
          </tbody>
        </table>
        {isAdmin && (
          <>
            <label>Assigned doctor</label>
            <select value={p.assigned_doctor_id || ""} onChange={(e) => assign(e.target.value)}>
              <option value="">— unassigned —</option>
              {doctors.map((d) => <option key={d.id} value={d.id}>{d.full_name || d.email}</option>)}
            </select>
          </>
        )}
      </div>

      <ConsentCenter patientId={p.id} onChange={() => setLabsKey((k) => k + 1)} />
      <IntakeForm patientId={p.id} onChange={() => setLabsKey((k) => k + 1)} />
      <DocumentUpload patientId={p.id} onChange={() => setLabsKey((k) => k + 1)} />
      <LabReview patientId={p.id} onConfirmed={() => setLabsKey((k) => k + 1)} />
      <ConfirmedLabs patientId={p.id} refreshKey={labsKey} />
      <ImagingPanel patientId={p.id} onChange={() => setLabsKey((k) => k + 1)} />
      <ReportsPanel patientId={p.id} canGenerate canValidate={user?.role === "doctor"} readinessKey={labsKey} />

    </Layout>
  );
}
