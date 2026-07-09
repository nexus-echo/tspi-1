import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Patient, createPatient, listPatients } from "../api/patients";
import Layout from "./Layout";

export default function AdminPatients() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [first, setFirst] = useState("");
  const [last, setLast] = useState("");
  const [dob, setDob] = useState("");
  const [sex, setSex] = useState("female");
  const [msg, setMsg] = useState<{ ok?: string; err?: string }>({});

  async function load() {
    setPatients(await listPatients());
  }
  useEffect(() => {
    load();
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setMsg({});
    try {
      const p = await createPatient({ first_name: first, last_name: last, dob: dob || null, sex: sex as any });
      setMsg({ ok: `Created ${p.case_id}` });
      setFirst(""); setLast(""); setDob("");
      await load();
    } catch (e: any) {
      setMsg({ err: e?.response?.data?.detail || "Failed" });
    }
  }

  return (
    <Layout title="Patient registry">
      <div className="card" style={{ marginBottom: 20 }}>
        <h2>Register a patient</h2>
        <form onSubmit={onCreate}>
          <div className="row">
            <div><label>First name</label><input value={first} onChange={(e) => setFirst(e.target.value)} required /></div>
            <div><label>Last name</label><input value={last} onChange={(e) => setLast(e.target.value)} required /></div>
          </div>
          <div className="row">
            <div><label>Date of birth</label><input type="date" value={dob} onChange={(e) => setDob(e.target.value)} /></div>
            <div>
              <label>Sex</label>
              <select value={sex} onChange={(e) => setSex(e.target.value)}>
                <option value="female">Female</option><option value="male">Male</option>
                <option value="other">Other</option><option value="unknown">Unknown</option>
              </select>
            </div>
          </div>
          {msg.err && <div className="error">{msg.err}</div>}
          {msg.ok && <div className="ok">{msg.ok}</div>}
          <button>Create patient</button>
        </form>
      </div>

      <div className="card">
        <h2>Patients</h2>
        <table>
          <thead><tr><th>Case ID</th><th>Name</th><th>Age band</th><th>Doctor</th><th></th></tr></thead>
          <tbody>
            {patients.map((p) => (
              <tr key={p.id}>
                <td><span className="badge">{p.case_id}</span></td>
                <td>{[p.first_name, p.last_name].filter(Boolean).join(" ") || "—"}</td>
                <td>{p.age_band || "—"}</td>
                <td>{p.assigned_doctor_id ? "assigned" : "—"}</td>
                <td><Link to={`/patients/${p.id}`}>Open</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}
