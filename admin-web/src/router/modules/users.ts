const Layout = () => import("@/layout/index.vue");

export default {
  path: "/users",
  name: "UsersRoot",
  component: Layout,
  redirect: "/users/index",
  meta: {
    icon: "ri/user-settings-line",
    title: "用户中台",
    rank: 4
  },
  children: [
    {
      path: "/users/index",
      name: "Users",
      component: () => import("@/views/users/UsersView.vue"),
      meta: {
        title: "用户中台",
        icon: "ri/user-settings-line"
      }
    }
  ]
} satisfies RouteConfigsTable;
