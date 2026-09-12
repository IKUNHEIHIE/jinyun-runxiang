const Layout = () => import("@/layout/index.vue");

export default {
  path: "/models",
  name: "ModelsRoot",
  component: Layout,
  redirect: "/models/index",
  meta: {
    icon: "ri/cpu-line",
    title: "模型治理",
    rank: 3
  },
  children: [
    {
      path: "/models/index",
      name: "Models",
      component: () => import("@/views/models/ModelsView.vue"),
      meta: {
        title: "模型治理",
        icon: "ri/cpu-line"
      }
    }
  ]
} satisfies RouteConfigsTable;
