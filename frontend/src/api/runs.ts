import request from "@/utils/request";
import type { Run } from "@/types/run";

export const getRuns = () => request.get<Run[]>("/runs");
export const getRun = (id: number) => request.get<Run>(`/runs/${id}`);
export const createRun = (data: {
  run_type: string;
  script_id: string;
  execution_context: Record<string, any>;
  ticket_id: number;
}) => request.post<Run>("/runs", data);