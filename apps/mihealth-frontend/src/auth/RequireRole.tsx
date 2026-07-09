import { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { Role, useAuth } from "./AuthContext";

// Guards a route. If not logged in -> /login. If wrong role -> their own home.
export function RequireRole({ roles, children }: { roles: Role[]; children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="center">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (!roles.includes(user.role)) return <Navigate to={`/${user.role}`} replace />;
  return <>{children}</>;
}
