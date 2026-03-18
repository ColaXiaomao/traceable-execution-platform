import request from "@/utils/request";
import type { Asset } from "@/types/asset";

// 查询参数类型
interface GetAssetsParams {
  skip?: number;        // 跳过多少条（用于分页）
  limit?: number;       // 最多返回多少条（用于分页）
  asset_type?: string;  // 按资产类型筛选（可选）
}

// 获取资产列表，支持分页和类型筛选
export const getAssets = (params?: GetAssetsParams) =>
  request.get<Asset[]>("/assets", { params });

// 根据 ID 获取单个资产详情
export const getAsset = (id: number) =>
  request.get<Asset>(`/assets/${id}`);

// 创建新资产
// Partial<Asset> 表示 Asset 的所有字段都是可选的（不必填满）
export const createAsset = (data: Partial<Asset>) =>
  request.post<Asset>("/assets", data);

// 更新指定 ID 的资产（局部更新，只传要改的字段）
// PATCH 与 PUT 的区别：PATCH 只更新传入的字段，PUT 会替换整个对象
export const updateAsset = (id: number, data: Partial<Asset>) =>
  request.patch<Asset>(`/assets/${id}`, data);