const Layout = () => import("@/layout/index.vue");

export default {
  path: "/catalog",
  name: "CatalogRoot",
  component: Layout,
  redirect: "/catalog/index",
  meta: {
    icon: "ri/store-3-line",
    title: "目录管理",
    rank: 9
  },
  children: [
    {
      path: "/catalog/index",
      name: "Catalog",
      component: () => import("@/views/catalog/CatalogView.vue"),
      meta: {
        title: "目录管理",
        icon: "ri/store-3-line"
      }
    }
  ]
} satisfies RouteConfigsTable;
