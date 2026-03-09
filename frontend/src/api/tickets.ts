// src/api/tickets.ts
import { http } from "@/utils/http";

/** 工单类型 */
export type Ticket = {
  id: number;
  title: string;
  status: "submitted" | "approved" | "rejected";
  description: string | null;
  asset_id: number | null;
  created_by_id: number;
  approved_by_id: number | null;
  created_at: string;
  updated_at: string;
  [key: string]: any; // 保留额外字段，防止后端加字段报错
};

/** 获取工单列表 */
// api/tickets.ts
export const getTicketList = (params?: { page?: number; pageSize?: number }) => {
  return http.request<{ list: Ticket[]; total: number }>("get", "/api/v1/tickets", {
    params
  });
};

/** 创建新工单 */
export const createTicket = (data: { title: string; description?: string }) => {
  return http.request("post", "/api/v1/tickets", { data });
};

/** 获取单个工单详情 */
export const getTicket = (ticket_id: number | string) => {
  return http.request<{ data: Ticket }>("get", `/api/v1/tickets/${ticket_id}`);
};

/** 更新工单 */
export const updateTicket = (ticket_id: number | string, data: Partial<Ticket>) => {
  return http.request("patch", `/api/v1/tickets/${ticket_id}`, { data });
};

/** 审批工单 */
export const approveTicket = (ticket_id: number | string) => {
  return http.request("post", `/api/v1/tickets/${ticket_id}/approve`);
};

