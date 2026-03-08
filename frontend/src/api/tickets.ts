// 此为tickets的api接口,写所有请求
import { http } from "@/utils/http";

/** * 
 * 这里的 'any' 后续建议替换为你定义的具体 Interface 
 * 以符合你追求的工程化标准
 */

// 1. 获取工单列表 (GET /api/v1/tickets)
export const getTicketList = (params?: object) => {
  return http.request<any>("get", "/api/v1/tickets", { params });
};

// 2. 创建新工单 (POST /api/v1/tickets)
export const createTicket = (data: object) => {
  return http.request<any>("post", "/api/v1/tickets", { data });
};

// 3. 获取指定工单详情 (GET /api/v1/tickets/{ticket_id})
export const getTicketDetail = (id: string | number) => {
  return http.request<any>("get", `/api/v1/tickets/${id}`);
};

// 4. 更新工单 (PATCH /api/v1/tickets/{ticket_id})
export const updateTicket = (id: string | number, data: object) => {
  return http.request<any>("patch", `/api/v1/tickets/${id}`, { data });
};

// 5. 审批工单 (POST /api/v1/tickets/{ticket_id}/approve)
export const approveTicket = (id: string | number) => {
  return http.request<any>("post", `/api/v1/tickets/${id}/approve`);
};

//写类型
export interface Ticket {
  id: number;
  title: string;
  description: string;
  status: string;
  created_at: string;
}