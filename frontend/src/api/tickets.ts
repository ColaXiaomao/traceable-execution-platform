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

export interface Ticket {
  id: number;
  title: string;
  description: string;
  asset_id: number;
  status: string;
  created_by_id: number;
  approved_by_id: number;
  created_at: string;
  updated_at: string;
}

export const getTickets = () => api.get<Ticket[]>("/tickets");
export const getTicket = (id: number) => api.get<Ticket>(`/tickets/${id}`);
export const createTicket = (data: Partial<Ticket>) => api.post<Ticket>("/tickets", data);
export const updateTicket = (id: number, data: Partial<Ticket>) => api.patch<Ticket>(`/tickets/${id}`, data);
export const approveTicket = (id: number) => api.post(`/tickets/${id}/approve`);