import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { RequireRole } from "./auth/RequireRole";
import Login from "./pages/Login";
import Register from "./pages/Register";
import AdminHome from "./pages/AdminHome";
import AdminPatients from "./pages/AdminPatients";
import DoctorHome from "./pages/DoctorHome";
import PatientHome from "./pages/PatientHome";
import PatientDetailPage from "./pages/PatientDetailPage";

function HomeRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <div className="center">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={`/${user.role}`} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route path="/admin" element={<RequireRole roles={["admin"]}><AdminHome /></RequireRole>} />
      <Route path="/admin/patients" element={<RequireRole roles={["admin"]}><AdminPatients /></RequireRole>} />
      <Route path="/doctor" element={<RequireRole roles={["doctor"]}><DoctorHome /></RequireRole>} />
      <Route path="/patient" element={<RequireRole roles={["patient"]}><PatientHome /></RequireRole>} />

      {/* staff-only patient detail */}
      <Route path="/patients/:id" element={<RequireRole roles={["admin", "doctor"]}><PatientDetailPage /></RequireRole>} />

      <Route path="/" element={<HomeRedirect />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
