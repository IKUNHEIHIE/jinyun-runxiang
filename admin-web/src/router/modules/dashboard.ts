const Layout = () => import("@/layout/index.vue");

export default {
  path: "/dashboard",
  name: "DashboardRoot",
  component: Layout,
  redirect: "/dashboard/index",
  meta: {
    icon: "ri/dashboard-line",
    title: "运营大盘",
    rank: 1
  },
  children: [
    {
      path: "/dashboard/index",
      name: "Dashboard",
      component: () => import("@/views/dashboard/DashboardView.vue"),
      meta: {
        title: "运营大盘",
        icon: "ri/dashboard-line"
      }
    }
  ]
} satisfies RouteConfigsTable;
