const Layout = () => import("@/layout/index.vue");
export default {
  path: "/teacher",
  name: "TeacherRoot",
  component: Layout,
  redirect: "/teacher/workspace",
  meta: {
    title: "教师工作台",
    icon: "ri/graduation-cap-line",
    rank: 1,
    roles: ["TEACHER", "ADMIN"]
  },
  children: [
    {
      path: "/teacher/workspace",
      name: "TeacherWorkspace",
      component: () => import("@/views/teacher/TeacherWorkspace.vue"),
      meta: { title: "教师工作台", roles: ["TEACHER", "ADMIN"] }
    }
  ]
} satisfies RouteConfigsTable;
