import { api } from "./client";

export interface DocumentT {
  id: string;
  patient_id: string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  doc_type: string;
  ocr_status: "pending" | "review" | "done" | "failed";
  ocr_note: string;
  created_at: string;
}

export interface Lab {
  id?: string;
  patient_id?: string;
  document_id?: string | null;
  analyte: string;
  value: string;
  unit: string | null;
  ref_low: number | null;
  ref_high: number | null;
  flag?: string | null;
  source?: string;
  confirmed?: boolean;
}

export const listDocuments = (pid: string) =>
  api.get<DocumentT[]>(`/patients/${pid}/documents`).then((r) => r.data);

export const uploadDocument = (pid: string, file: File, docType = "lab") => {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("doc_type", docType);
  return api
    .post<DocumentT>(`/patients/${pid}/documents`, fd, { headers: { "Content-Type": "multipart/form-data" } })
    .then((r) => r.data);
};

export const getDocument = (id: string) => api.get<DocumentT>(`/documents/${id}`).then((r) => r.data);
export const getDocumentLabs = (id: string) =>
  api.get<Lab[]>(`/documents/${id}/labs`).then((r) => r.data);
export const confirmLabs = (id: string, labs: Lab[]) =>
  api.post<Lab[]>(`/documents/${id}/labs/confirm`, { labs }).then((r) => r.data);

export const listPatientLabs = (pid: string, confirmed?: boolean) =>
  api
    .get<Lab[]>(`/patients/${pid}/labs`, { params: confirmed === undefined ? {} : { confirmed } })
    .then((r) => r.data);
export const addManualLab = (pid: string, lab: Lab) =>
  api.post<Lab>(`/patients/${pid}/labs`, lab).then((r) => r.data);
