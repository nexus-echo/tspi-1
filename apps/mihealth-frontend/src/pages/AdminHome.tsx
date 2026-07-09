import { FormEvent, useEffect, useState } from "react";
import { api } from "../api/client";
import { Role } from "../auth/AuthContext";
import Layout from "./Layout";
import LearningPanel from "../components/LearningPanel";

interface UserRow {
  id: string;
  email: string;
  role: Role;
  full_name: string;
  is_active: boolean;
}

export default function AdminHome() {
  const [users, setUsers] = useState<UserRow[]>([]);
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"doctor" | "admin">("doctor");
  const [msg, setMsg] = useState<{ ok?: string; err?: string }>({});
  const [busy, setBusy] = useState(false);

  async function load() {
    const { data } = await api.get<UserRow[]>("/admin/users");
    setUsers(data);
  }
  useEffect(() => {
    load();
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setMsg({});
    setBusy(true);
    try {
      await api.post("/admin/users", { email, password, full_name: fullName, role });
      setMsg({ ok: `Created ${role} ${email}` });
      setEmail("");
      setFullName("");
      setPassword("");
      await load();
    } catch (e: any) {
      setMsg({ err: e?.response?.data?.detail || "Failed to create user" });
    } finally {
      setBusy(false);
    }
  }

  return (
    <Layout title="Admin dashboard">
      <LearningPanel />
      <div className="card" style={{ marginBottom: 20 }}>
        <h2>Create staff account</h2>
        <p className="muted">Provision doctor or admin accounts. Patients self-register.</p>
        <form onSubmit={onSubmit}>
          <div className="row">
            <div>
              <label>Full name</label>
              <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
            </div>
            <div>
              <label>Email</label>
              <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
            </div>
          </div>
          <div className="row">
            <div>
              <label>Password</label>
              <input
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                type="password"
                minLength={8}
                required
              />
            </div>
            <div>
              <label>Role</label>
              <select value={role} onChange={(e) => setRole(e.target.value as any)}>
                <option value="doctor">Doctor</option>
                <option value="admin">Admin</option>
              </select>
            </div>
          </div>
          {msg.err && <div className="error">{msg.err}</div>}
          {msg.ok && <div className="ok">{msg.ok}</div>}
          <button disabled={busy}>{busy ? "Creating…" : "Create account"}</button>
        </form>
      </div>

      <div className="card">
        <h2>Users</h2>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Active</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.full_name || "—"}</td>
                <td>{u.email}</td>
                <td>
                  <span className="badge">{u.role}</span>
                </td>
                <td>{u.is_active ? "Yes" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}
