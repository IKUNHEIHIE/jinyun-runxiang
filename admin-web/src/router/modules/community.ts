const Layout = () => import("@/layout/index.vue");

export default {
  path: "/community",
  name: "CommunityRoot",
  component: Layout,
  redirect: "/community/index",
  meta: {
    icon: "ri/shield-check-line",
    title: "风控中心",
    rank: 5
  },
  children: [
    {
      path: "/community/index",
      name: "Community",
      component: () => import("@/views/community/CommunityView.vue"),
      meta: {
        title: "风控中心",
        icon: "ri/shield-check-line"
      }
    }
  ]
} satisfies RouteConfigsTable;
