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
      component: () => import("@/views/Layout.vue"),
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
          path: "runs",
          name: "Runs",
          component: () => import("@/views/runs/Index.vue")
        },
        {
          path: "tickets/:id",
          name: "TicketDetail",
          component: () => import("@/views/tickets/Detail.vue")
       }
      ]
    }
  ]
});

router.beforeEach((to, _, next) => {
  const token = localStorage.getItem("token");
  if (to.meta.requiresAuth && !token) {
    next("/login");
  } else {
    next();
  }
});

export default router;