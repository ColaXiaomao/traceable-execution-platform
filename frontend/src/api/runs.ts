import request from "@/utils/request";
import type { Run } from "@/types/run";

export const getRuns = (params?: { skip?: number; limit?: number; ticket_id?: number }) =>
  request.get<Run[]>("/runs", { params });
export const getRun = (id: number) => request.get<Run>(`/runs/${id}`);
export const createRun = (data: {
  run_type: string;
  script_id: string;
  execution_context: Record<string, any>;
  ticket_id: number;
}) => request.post<Run>("/runs", data);