import { api } from "./client";

export interface Outcome {
  id: string;
  report_id: string;
  patient_id: string;
  marker: string;
  baseline: number;
  followup: number;
  delta: number;
  synced_to_tspi: boolean;
  created_at: string;
}

export interface TemporalPoint { baseline: number; followup: number; delta: number; at: string; }
export interface Temporal { case_id: string; markers: Record<string, TemporalPoint[]>; }

export const recordOutcome = (reportId: string, body: { marker: string; baseline: number; followup: number }) =>
  api.post<Outcome>(`/reports/${reportId}/outcomes`, body).then((r) => r.data);
export const listOutcomes = (reportId: string) =>
  api.get<Outcome[]>(`/reports/${reportId}/outcomes`).then((r) => r.data);
export const getTemporal = (patientId: string) =>
  api.get<Temporal>(`/patients/${patientId}/temporal`).then((r) => r.data);
export const recalibrate = () => api.post(`/learning/recalibrate`).then((r) => r.data);
export const getWeights = () => api.get(`/learning/weights`).then((r) => r.data);
