import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000/api/v1",
  headers: { "Content-Type": "application/json" }
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export interface Artifact {
  id: number;
  filename: string;
  artifact_type: string;
  description: string;
  content_type: string;
  size_bytes: number;
  sha256_hash: string;
  ticket_id: number;
  run_id: number;
  uploaded_by_id: number;
  is_deleted: boolean;
  created_at: string;
}

export const getTicketArtifacts = (ticketId: number) =>
  api.get<Artifact[]>(`/artifacts/ticket/${ticketId}`);

export const getArtifact = (id: number) =>
  api.get<Artifact>(`/artifacts/${id}`);

export const uploadArtifact = (
  ticketId: number,
  file: File,
  artifactType?: string,
  description?: string
) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post<Artifact>(
    `/artifacts?ticket_id=${ticketId}${artifactType ? `&artifact_type=${artifactType}` : ""}${description ? `&description=${description}` : ""}`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
};

export const downloadArtifact = (id: number) =>
  api.get(`/artifacts/${id}/download`, { responseType: "blob" });