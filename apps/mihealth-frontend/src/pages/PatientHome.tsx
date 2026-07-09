import { useEffect, useState } from "react";
import {
  Patient,
  PatientInput,
  createPatient,
  listPatients,
  updatePatient,
} from "../api/patients";
import ConsentCenter from "../components/ConsentCenter";
import IntakeForm from "../components/IntakeForm";
import PatientForm from "../components/PatientForm";
import DocumentUpload from "../components/DocumentUpload";
import ConfirmedLabs from "../components/ConfirmedLabs";
import ReportsPanel from "../components/ReportsPanel";
import Layout from "./Layout";

export default function PatientHome() {
  const [patient, setPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);
  const [labsKey, setLabsKey] = useState(0);

  async function load() {
    const list = await listPatients(); // patient sees only their own record
    setPatient(list[0] || null);
    setLoading(false);
  }
  useEffect(() => {
    load();
  }, []);

  async function onCreate(b: PatientInput) {
    setPatient(await createPatient(b));
  }
  async function onUpdate(b: PatientInput) {
    if (!patient) return;
    setPatient(await updatePatient(patient.id, b));
  }

  if (loading) return <Layout title="Patient dashboard"><div className="card">Loading…</div></Layout>;

  if (!patient) {
    return (
      <Layout title="Welcome — set up your profile">
        <PatientForm onSubmit={onCreate} submitLabel="Create profile" />
      </Layout>
    );
  }

  return (
    <Layout title="My health record">
      <div className="card" style={{ marginBottom: 16 }}>
        <span className="badge">{patient.case_id}</span>
        {patient.age_band && <span className="muted" style={{ marginLeft: 12 }}>age band: {patient.age_band}</span>}
        <p className="muted" style={{ marginTop: 8 }}>
          Complete your profile, consent, symptoms, and upload reports. Your treatment plan is
          generated and approved by clinical staff and will appear here once approved.
        </p>
      </div>
      <PatientForm initial={patient} onSubmit={onUpdate} />
      <ConsentCenter patientId={patient.id} />
      <IntakeForm patientId={patient.id} />
      <DocumentUpload patientId={patient.id} onChange={() => setLabsKey((k) => k + 1)} />
      <ReportsPanel patientId={patient.id} />
      <ConfirmedLabs patientId={patient.id} refreshKey={labsKey} />
    </Layout>
  );
}
