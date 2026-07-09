import { FormEvent, useState } from "react";
import { Patient, PatientInput, Sex } from "../api/patients";

// Create or edit profile (PII). age_band + case_id are derived server-side.
export default function PatientForm({
  initial,
  onSubmit,
  submitLabel = "Save profile",
}: {
  initial?: Partial<Patient>;
  onSubmit: (b: PatientInput) => Promise<void>;
  submitLabel?: string;
}) {
  const [first, setFirst] = useState(initial?.first_name || "");
  const [last, setLast] = useState(initial?.last_name || "");
  const [dob, setDob] = useState(initial?.dob || "");
  const [sex, setSex] = useState<Sex>((initial?.sex as Sex) || "unknown");
  const [phone, setPhone] = useState(initial?.phone || "");
  const [email, setEmail] = useState(initial?.email || "");
  const [address, setAddress] = useState(initial?.address || "");
  const [msg, setMsg] = useState<{ ok?: string; err?: string }>({});
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setMsg({});
    setBusy(true);
    try {
      await onSubmit({
        first_name: first,
        last_name: last,
        dob: dob || null,
        sex,
        phone: phone || null,
        email: email || null,
        address: address || null,
      });
      setMsg({ ok: "Saved" });
    } catch (e: any) {
      setMsg({ err: e?.response?.data?.detail || "Save failed" });
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card" style={{ marginBottom: 16 }} onSubmit={submit}>
      <h2>Profile</h2>
      <p className="muted">Identity is stored encrypted. Only an age band (not your date of birth) is sent to the analysis engine.</p>
      <div className="row">
        <div>
          <label>First name</label>
          <input value={first} onChange={(e) => setFirst(e.target.value)} required />
        </div>
        <div>
          <label>Last name</label>
          <input value={last} onChange={(e) => setLast(e.target.value)} required />
        </div>
      </div>
      <div className="row">
        <div>
          <label>Date of birth</label>
          <input type="date" value={dob || ""} onChange={(e) => setDob(e.target.value)} />
        </div>
        <div>
          <label>Sex</label>
          <select value={sex} onChange={(e) => setSex(e.target.value as Sex)}>
            <option value="female">Female</option>
            <option value="male">Male</option>
            <option value="other">Other</option>
            <option value="unknown">Prefer not to say</option>
          </select>
        </div>
      </div>
      <div className="row">
        <div>
          <label>Phone</label>
          <input value={phone} onChange={(e) => setPhone(e.target.value)} />
        </div>
        <div>
          <label>Email</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
      </div>
      <label>Address</label>
      <input value={address} onChange={(e) => setAddress(e.target.value)} />
      {msg.err && <div className="error">{msg.err}</div>}
      {msg.ok && <div className="ok">{msg.ok}</div>}
      <button disabled={busy}>{busy ? "Saving…" : submitLabel}</button>
    </form>
  );
}
