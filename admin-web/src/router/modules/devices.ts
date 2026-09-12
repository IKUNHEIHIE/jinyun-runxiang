const Layout = () => import("@/layout/index.vue");

export default {
  path: "/devices",
  name: "DevicesRoot",
  component: Layout,
  redirect: "/devices/index",
  meta: {
    icon: "ri/robot-line",
    title: "具身设备",
    rank: 7
  },
  children: [
    {
      path: "/devices/index",
      name: "Devices",
      component: () => import("@/views/devices/DevicesView.vue"),
      meta: {
        title: "具身设备",
        icon: "ri/robot-line"
      }
    }
  ]
} satisfies RouteConfigsTable;
