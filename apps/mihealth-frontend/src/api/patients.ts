import { api } from "./client";

export type Sex = "female" | "male" | "other" | "unknown";

export interface Patient {
  id: string;
  case_id: string;
  owner_user_id: string | null;
  assigned_doctor_id: string | null;
  first_name: string | null;
  last_name: string | null;
  dob: string | null;
  sex: Sex;
  phone: string | null;
  email: string | null;
  address: string | null;
  age_band: string | null;
  created_at: string;
}

export interface PatientInput {
  first_name?: string;
  last_name?: string;
  dob?: string | null;
  sex?: Sex;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  assigned_doctor_id?: string | null;
}

export interface Intake {
  id?: string;
  patient_id?: string;
  symptoms_text: string;
  conditions: string[];
  medications: string[];
  lifestyle: Record<string, string>;
  created_at?: string;
}

export interface Consent {
  scope: string;
  granted: boolean;
  created_at?: string;
}

export const CONSENT_SCOPES = [
  { scope: "ai_analysis", label: "AI analysis", help: "Required — lets the engine analyse your data to generate a treatment plan." },
  { scope: "doctor_sharing", label: "Doctor sharing", help: "Share the validated plan with your clinician." },
  { scope: "tspi_connection", label: "TSPI programs", help: "Connect to TSPI intervention programs / clinic." },
  { scope: "research", label: "Research", help: "Allow de-identified outcomes to improve the model." },
];

export const listPatients = () => api.get<Patient[]>("/patients").then((r) => r.data);
export const getPatient = (id: string) => api.get<Patient>(`/patients/${id}`).then((r) => r.data);
export const createPatient = (b: PatientInput) => api.post<Patient>("/patients", b).then((r) => r.data);
export const updatePatient = (id: string, b: PatientInput) =>
  api.put<Patient>(`/patients/${id}`, b).then((r) => r.data);

export const getIntake = (id: string) =>
  api.get<Intake | null>(`/patients/${id}/intake`).then((r) => r.data);
export const saveIntake = (id: string, b: Intake) =>
  api.post<Intake>(`/patients/${id}/intake`, b).then((r) => r.data);

export const getConsents = (id: string) =>
  api.get<Consent[]>(`/patients/${id}/consent`).then((r) => r.data);
export const setConsent = (id: string, scope: string, granted: boolean) =>
  api.post<Consent>(`/patients/${id}/consent`, { scope, granted }).then((r) => r.data);

export interface StaffUser { id: string; email: string; full_name: string; role: string; }
export const listDoctors = () =>
  api.get<StaffUser[]>("/admin/users").then((r) => r.data.filter((u) => u.role === "doctor"));

export interface Imaging { id: string; patient_id: string; text: string; confirmed: boolean; created_at: string; }
export const listImaging = (id: string) => api.get<Imaging[]>(`/patients/${id}/imaging`).then((r) => r.data);
export const addImaging = (id: string, text: string) =>
  api.post<Imaging>(`/patients/${id}/imaging`, { text }).then((r) => r.data);
