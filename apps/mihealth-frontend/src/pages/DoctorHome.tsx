import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Patient, listPatients } from "../api/patients";
import Layout from "./Layout";

export default function DoctorHome() {
  const [patients, setPatients] = useState<Patient[]>([]);
  useEffect(() => {
    listPatients().then(setPatients); // doctor sees only assigned patients
  }, []);

  return (
    <Layout title="My patients">
      <div className="card">
        <p className="muted">Patients assigned to you. Open a patient to review and validate their treatment plan.</p>
        <table>
          <thead><tr><th>Case ID</th><th>Name</th><th>Age band</th><th></th></tr></thead>
          <tbody>
            {patients.map((p) => (
              <tr key={p.id}>
                <td><span className="badge">{p.case_id}</span></td>
                <td>{[p.first_name, p.last_name].filter(Boolean).join(" ") || "—"}</td>
                <td>{p.age_band || "—"}</td>
                <td><Link to={`/patients/${p.id}`}>Open</Link></td>
              </tr>
            ))}
            {patients.length === 0 && <tr><td colSpan={4} className="muted">No patients assigned yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}
