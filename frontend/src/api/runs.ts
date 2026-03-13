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

export interface Run {
  id: number;
  run_type: string;
  script_id: string;
  execution_context: Record<string, any>;
  status: string;
  ticket_id: number;
  executed_by_id: number;
  validator_version: string;
  rules_version: string;
  inputs_manifest: Record<string, any>;
  outputs_manifest: Record<string, any>;
  result_summary: string;
  exit_code: number;
  created_at: string;
  updated_at: string;
  stdout_log?: string;
  stderr_log?: string;
}

export const getRuns = () => api.get<Run[]>("/runs");
export const getRun = (id: number) => api.get<Run>(`/runs/${id}`);
export const createRun = (data: {
  run_type: string;
  script_id: string;
  execution_context: Record<string, any>;
  ticket_id: number;
}) => api.post<Run>("/runs", data);