const Layout = () => import("@/layout/index.vue");
export default {
  path: "/support",
  name: "SupportRoot",
  component: Layout,
  redirect: "/support/index",
  meta: {
    title: "用户服务",
    icon: "ri/customer-service-2-line",
    rank: 7,
    roles: ["ADMIN"]
  },
  children: [
    {
      path: "/support/index",
      name: "Support",
      component: () => import("@/views/support/SupportView.vue"),
      meta: { title: "兑换与反馈", roles: ["ADMIN"] }
    }
  ]
} satisfies RouteConfigsTable;
