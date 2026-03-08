// 1. 使用路径别名 @，确保指向的是路由系统真正的类型定义文件
import type { RouteConfigsTable } from "@/router/utils";

const ticketRouter = {
  path: "/ticket",
  name: "Ticket",
  meta: {
    title: "工单管理",
    icon: "ep:ticket",
    rank: 10 // 满足 handRank 的排序需求
  },
  children: [
    {
      path: "/ticket/index",
      name: "TicketList",
      component: () => import("@/views/ticket/index.vue"),
      meta: {
        title: "工单列表"
      }
    }
  ]
} satisfies RouteConfigsTable; // 2. 使用 satisfies 进行类型检查

export default ticketRouter;