import { http } from "@/utils/http";

type Result = {
  success: boolean;
  data: Array<any>;
};

export const getAsyncRoutes = () => {
  // 不再请求后端，直接返回成功的 Promise
  return Promise.resolve({
    success: true,
    data: [] // 返回空数组，前端就会只显示本地写死的菜单
  });
};
