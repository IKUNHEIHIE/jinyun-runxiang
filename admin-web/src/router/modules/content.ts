const Layout = () => import("@/layout/index.vue");

export default {
  path: "/content",
  name: "ContentRoot",
  component: Layout,
  redirect: "/content/index",
  meta: {
    icon: "ri/book-open-line",
    title: "内容管理",
    rank: 2
  },
  children: [
    {
      path: "/content/index",
      name: "Content",
      component: () => import("@/views/content/ContentView.vue"),
      meta: {
        title: "内容管理",
        icon: "ri/book-open-line"
      }
    }
  ]
} satisfies RouteConfigsTable;
