import { ReactNode } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Layout({ title, children }: { title: string; children: ReactNode }) {
  const { user, logout } = useAuth();
  return (
    <>
      <div className="topbar">
        <span>
          <span className="brand">MiHealth Portal</span>
          {user?.role === "admin" && (
            <span style={{ marginLeft: 20 }}>
              <Link to="/admin" style={{ marginRight: 14 }}>Users</Link>
              <Link to="/admin/patients">Patients</Link>
            </span>
          )}
        </span>
        <span>
          {user && <span className="badge" style={{ marginRight: 12 }}>{user.role}</span>}
          {user?.full_name || user?.email}
          <button className="link-btn" style={{ marginLeft: 16 }} onClick={logout}>Log out</button>
        </span>
      </div>
      <div className="container">
        <h1>{title}</h1>
        {children}
      </div>
    </>
  );
}
