import request from "@/utils/request";
import type { Asset } from "@/types/asset";

export const getAssets = (params?: { skip?: number; limit?: number; asset_type?: string }) =>
  request.get<Asset[]>("/assets", { params });
export const getAsset = (id: number) => request.get<Asset>(`/assets/${id}`);
export const createAsset = (data: Partial<Asset>) => request.post<Asset>("/assets", data);
export const updateAsset = (id: number, data: Partial<Asset>) => request.patch<Asset>(`/assets/${id}`, data);