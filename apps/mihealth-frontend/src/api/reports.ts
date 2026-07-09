import { api } from "./client";

export interface AxisScore {
  axis_code: string;
  axis_name: string;
  severity?: string;
  is_driver?: boolean;
  domain_code?: string | null;
}

export interface ModulePick {
  module_code: string;
  module_name?: string | null;
  dose?: string | null;
  phase?: string;
  clinical_role?: string | null;
  target_axes?: string[];
  resolved?: boolean;
}

export interface Analysis {
  nss?: number;
  severity_level?: number;
  severity_name?: string;
  axis_scores?: AxisScore[];
  system_priority?: Array<Record<string, unknown>>;
  root_cause_chain?: string[];
}

export interface Report {
  id: string;
  patient_id: string;
  case_id: string;
  tspi_report_id: string | null;
  status: string;
  deliverable: boolean;
  nss: number | null;
  severity_level: number | null;
  severity_name: string | null;
  analysis: Analysis;
  modules: ModulePick[];
  monitoring: Array<Record<string, unknown>>;
  safety_alerts: Array<Record<string, unknown>>;
  report_markdown: string;
  disclaimer: string;
  doctor_note: string;
  created_at: string;
}

export const generateReport = (pid: string) =>
  api.post<Report>(`/patients/${pid}/reports`).then((r) => r.data);
export const listReports = (pid: string) =>
  api.get<Report[]>(`/patients/${pid}/reports`).then((r) => r.data);
export const getReport = (id: string) => api.get<Report>(`/reports/${id}`).then((r) => r.data);

export interface ValidationBody {
  decision: "approve" | "edit" | "reject";
  note?: string;
  edited_markdown?: string | null;
}
export const validateReport = (reportId: string, body: ValidationBody) =>
  api.post<Report>(`/reports/${reportId}/validate`, body).then((r) => r.data);

export interface Readiness {
  confirmed_labs: number;
  lab_documents: number;
  symptom_count: number;
  conditions: number;
  medications: number;
  imaging: number;
  ai_analysis_consent: boolean;
  warnings: string[];
  blocker: string | null;
  ready: boolean;
}
export const getReadiness = (patientId: string) =>
  api.get<Readiness>(`/patients/${patientId}/report-readiness`).then((r) => r.data);
