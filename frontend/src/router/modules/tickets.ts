import { type RouteRecordRaw } from "vue-router";
//import Layout from "@/layout/index.vue";

const ticketsRoutes: RouteRecordRaw = {
  path: "/ticket",
  name: "Ticket",
  //component: Layout,
  redirect: "/ticket/index", // 父路由重定向到列表页
  meta: {
    title: "工单管理",
    icon: "ep:ticket",
    rank: 10
  },
  children: [
    {
      path: "/ticket/index",
      name: "TicketList",
      component: () => import("@/views/tickets/index.vue"),
      meta: {
        title: "工单列表",
        showLink: true
      }
    },
    {
      path: "/ticket/create",
      name: "TicketCreate",
      component: () => import("@/views/tickets/create.vue"),
      meta: {
        title: "创建工单",
        showLink: true
      }
    },
    {
      path: "/ticket/detail/:id",
      name: "TicketDetail",
      component: () => import("@/views/tickets/detail.vue"),
      meta: {
        title: "工单详情",
        showLink: false // 详情页不显示在菜单
      }
    }
  ]
};

export default ticketsRoutes;