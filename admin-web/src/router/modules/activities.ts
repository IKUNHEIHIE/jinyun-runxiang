const Layout = () => import("@/layout/index.vue");

export default {
  path: "/activities",
  name: "ActivitiesRoot",
  component: Layout,
  redirect: "/activities/index",
  meta: {
    icon: "ri/map-pin-line",
    title: "研学活动",
    rank: 6
  },
  children: [
    {
      path: "/activities/index",
      name: "Activities",
      component: () => import("@/views/activities/ActivitiesView.vue"),
      meta: {
        title: "研学活动",
        icon: "ri/map-pin-line"
      }
    }
  ]
} satisfies RouteConfigsTable;
