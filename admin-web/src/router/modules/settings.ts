const Layout = () => import("@/layout/index.vue");

export default {
  path: "/settings",
  name: "SettingsRoot",
  component: Layout,
  redirect: "/settings/index",
  meta: {
    icon: "ri/settings-3-line",
    title: "系统设置",
    rank: 8
  },
  children: [
    {
      path: "/settings/index",
      name: "Settings",
      component: () => import("@/views/settings/SettingsView.vue"),
      meta: {
        title: "系统设置",
        icon: "ri/settings-3-line"
      }
    }
  ]
} satisfies RouteConfigsTable;
