import request from "@/utils/request";
import type { Ticket } from "@/types/ticket";

export const getTickets = () => request.get<Ticket[]>("/tickets");
export const getTicket = (id: number) => request.get<Ticket>(`/tickets/${id}`);
export const createTicket = (data: Partial<Ticket>) => request.post<Ticket>("/tickets", data);
export const updateTicket = (id: number, data: Partial<Ticket>) => request.patch<Ticket>(`/tickets/${id}`, data);
export const approveTicket = (id: number) => request.post(`/tickets/${id}/approve`);