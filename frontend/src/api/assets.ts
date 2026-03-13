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

export interface Asset {
  id: number;
  name: string;
  asset_type: string;
  serial_number: string;
  location: string;
  description: string;
  created_by_id: number;
  created_at: string;
  updated_at: string;
}

export const getAssets = () => api.get<Asset[]>("/assets");
export const getAsset = (id: number) => api.get<Asset>(`/assets/${id}`);
export const createAsset = (data: Partial<Asset>) => api.post<Asset>("/assets", data);
export const updateAsset = (id: number, data: Partial<Asset>) => api.patch<Asset>(`/assets/${id}`, data);