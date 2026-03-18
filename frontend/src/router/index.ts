import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/dashboard"
    },
    {
      path: "/login",
      name: "Login",
      component: () => import("@/views/Login.vue")
    },
    {
      path: "/",
      component: () => import("@/layout/index.vue"),
      meta: { requiresAuth: true },
      children: [
        {
          path: "dashboard",
          name: "Dashboard",
          component: () => import("@/views/Dashboard.vue")
        },
        {
          path: "tickets",
          name: "Tickets",
          component: () => import("@/views/tickets/Index.vue")
        },
        {
          path: "tickets/create",
          name: "TicketsCreate",
          component: () => import("@/views/tickets/Create.vue")
        },
        {
          path: "tickets/:id",
          name: "TicketDetail",
          component: () => import("@/views/tickets/Detail.vue")
        },
        {
          path: "assets",
          name: "Assets",
          component: () => import("@/views/assets/Index.vue")
        },
        {
          path: "assets/create",
          name: "AssetsCreate",
          component: () => import("@/views/assets/Create.vue")
        },
        {
          path: "assets/:id",
          name: "AssetDetail",
          component: () => import("@/views/assets/Detail.vue")
        },
        {
          path: "runs",
          name: "Runs",
          component: () => import("@/views/runs/Index.vue")
        },
        {
          path: "runs/create",
          name: "RunCreate",
          component: () => import("@/views/runs/Create.vue"),
          meta: { requiresAdmin: true }
        },
        {
          path: "runs/:id",
          name: "RunDetail",
          component: () => import("@/views/runs/Detail.vue")
        }
      ]
    },
    {
      path: "/403",
      name: "Forbidden",
      component: () => import("@/views/error/403.vue")
    },
    {
      path: "/500",
      name: "ServerError",
      component: () => import("@/views/error/500.vue")
    },
    {
      path: "/:pathMatch(.*)*",
      name: "NotFound",
      component: () => import("@/views/error/404.vue")
    }
  ]
});

router.beforeEach((to, _, next) => {
  const token = localStorage.getItem("token");

  // 未登录跳登录页
  if (to.meta.requiresAuth && !token) {
    next("/login");
    return;
  }

  // 需要管理员权限
  if (to.meta.requiresAdmin) {
    const userInfo = JSON.parse(localStorage.getItem("userInfo") || "{}");
    if (!userInfo?.is_admin) {
      next("/403");
      return;
    }
  }

  next();
});

export default router;