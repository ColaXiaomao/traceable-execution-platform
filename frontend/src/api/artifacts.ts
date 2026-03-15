import request from "@/utils/request";
import type { Artifact } from "@/types/artifact";

export const getTicketArtifacts = (ticketId: number) =>
  request.get<Artifact[]>(`/artifacts/ticket/${ticketId}`);

export const getArtifact = (id: number) =>
  request.get<Artifact>(`/artifacts/${id}`);

export const uploadArtifact = (ticketId: number, file: File, artifactType?: string, description?: string) => {
  const formData = new FormData();
  formData.append("file", file);
  return request.post<Artifact>(
    `/artifacts?ticket_id=${ticketId}${artifactType ? `&artifact_type=${artifactType}` : ""}${description ? `&description=${description}` : ""}`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
};

export const downloadArtifact = (id: number) =>
  request.get(`/artifacts/${id}/download`, { responseType: "blob" });