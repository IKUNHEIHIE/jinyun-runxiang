import { createRouter, createWebHashHistory } from "vue-router";
import { session } from "./api";
import { restoreProfileScroll } from "./profile-scroll";
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: "/",
      component: () => import("./views/HomePage.vue"),
      meta: { tab: "home", title: "首页" },
    },
    {
      path: "/courses",
      component: () => import("./views/CoursesPage.vue"),
      meta: { tab: "courses", title: "小课堂", surface: "#f5f0e6" },
    },
    {
      path: "/courses/:id",
      component: () => import("./views/CoursePlayerPage.vue"),
      meta: { hideTabs: true, title: "非遗研习" },
    },
    {
      path: "/heritage",
      component: () => import("./views/HeritagePage.vue"),
      meta: { title: "非遗百科库" },
    },
    {
      path: "/heritage/:id",
      component: () => import("./views/HeritageDetailPage.vue"),
      meta: { hideTabs: true, title: "非遗典藏" },
    },
    {
      path: "/profile",
      component: () => import("./views/ProfilePage.vue"),
      meta: {
        tab: "profile",
        title: "我的",
        surface:
          "linear-gradient(#c5aaa1 0px, #c5aaa1 calc(var(--safe-top) + 305px), #f5ede4 calc(var(--safe-top) + 305px))",
      },
    },
    {
      path: "/profile/walking",
      component: () => import("./views/WalkingProfilePage.vue"),
      meta: {
        tab: "profile",
        title: "文化行者",
        requiresAuth: true,
        surface: "#d4d6c1",
        navTheme: "walking",
      },
    },
    // Retained business screens are migrated one by one; see the implementation status document.
    {
      path: "/ai-workshop",
      component: () => import("./views/WorkshopPage.vue"),
      meta: { tab: "workshop", title: "AI工坊", surface: "#ebe3d5" },
    },
    {
      path: "/ai-workshop/:tool(bronze|shadow|lacquer)",
      component: () => import("./views/WorkshopEditorPage.vue"),
      meta: { hideTabs: true, title: "非遗创作" },
    },
    {
      path: "/community",
      component: () => import("./views/CommunityPage.vue"),
      meta: { tab: "community", title: "社区" },
    },
    {
      path: "/community/publish",
      component: () => import("./views/PublishPage.vue"),
      meta: { title: "发布作品", hideTabs: true, requiresAuth: true },
    },
    {
      path: "/community/:id",
      component: () => import("./views/CommunityDetailPage.vue"),
      meta: { title: "作品详情", hideTabs: true, surface: "#e4d4c3" },
    },
    {
      path: "/mall",
      component: () => import("./views/MallPage.vue"),
      meta: { title: "文创市集", surface: "#c9dbcb" },
    },
    {
      path: "/landmarks",
      component: () => import("./views/MapPage.vue"),
      meta: { title: "研学地图", surface: "#f5f0e8" },
    },
    {
      path: "/teacher",
      component: () => import("./views/TeacherPage.vue"),
      meta: {
        tab: "profile",
        title: "教学工坊",
        teacher: true,
        surface: "#e5d6d6",
      },
    },
    {
      path: "/teacher/lesson-plan",
      component: () => import("./views/LessonPlanPage.vue"),
      meta: {
        hideTabs: true,
        title: "智能备课",
        teacher: true,
        surface: "#fff9f9",
      },
    },
    {
      path: "/teacher/analytics",
      component: () => import("./views/TeacherAnalyticsPage.vue"),
      meta: {
        hideTabs: true,
        title: "班级实时数据",
        teacher: true,
        surface: "#dbdbdb",
      },
    },
    {
      path: "/teacher/assignments",
      component: () => import("./views/TeacherAssignmentsPage.vue"),
      meta: { hideTabs: true, title: "班级作业", teacher: true },
    },
    {
      path: "/teacher/assignments/:id",
      component: () => import("./views/TeacherAssignmentsPage.vue"),
      meta: { hideTabs: true, title: "作业批改", teacher: true },
    },
    {
      path: "/teacher/contests",
      component: () => import("./views/TeacherContestsPage.vue"),
      meta: { hideTabs: true, title: "班级对抗赛", teacher: true },
    },
    {
      path: "/contests",
      component: () => import("./views/ContestPage.vue"),
      meta: { hideTabs: true, title: "班级对抗赛", requiresAuth: true },
    },
    {
      path: "/contests/:id",
      component: () => import("./views/ContestPage.vue"),
      meta: { hideTabs: true, title: "对抗赛详情", requiresAuth: true },
    },
    {
      path: "/notices",
      component: () => import("./views/NoticesPage.vue"),
      meta: { hideTabs: true, title: "班级通知", requiresAuth: true },
    },
    {
      path: "/teacher/notices",
      component: () => import("./views/NoticesPage.vue"),
      meta: { hideTabs: true, title: "班级通知", teacher: true },
    },
    {
      path: "/teacher/classroom",
      component: () => import("./views/ClassroomHubPage.vue"),
      meta: { hideTabs: true, title: "双师课堂", teacher: true },
    },
    {
      path: "/classroom",
      component: () => import("./views/ClassroomHubPage.vue"),
      meta: { hideTabs: true, title: "双师课堂", requiresAuth: true },
    },
    {
      path: "/classroom/:id",
      component: () => import("./views/ClassroomPage.vue"),
      meta: { hideTabs: true, title: "双师课堂", requiresAuth: true },
    },
    {
      path: "/me/:section",
      component: () => import("./views/PersonalServicePage.vue"),
      meta: { title: "我的服务", requiresAuth: true },
    },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
  scrollBehavior: (to, from, position) => {
    if (position && to.path === "/profile") {
      const token = session.token;
      return restoreProfileScroll(
        position,
        () =>
          router.currentRoute.value.fullPath === to.fullPath &&
          token === session.token,
        (cancel) =>
          router.beforeEach(() => {
            cancel();
          }),
      );
    }
    if (position) return position;
    if (
      to.path === from.path &&
      (to.path === "/" ||
        to.path === "/profile" ||
        to.path.startsWith("/ai-workshop/"))
    )
      return false;
    return { top: 0 };
  },
});
router.beforeEach((to) => {
  if ((to.meta.requiresAuth || to.meta.teacher) && !session.token) {
    session.authVisible = true;
    return false;
  }
  if (
    to.meta.teacher &&
    session.profile &&
    !["TEACHER", "ADMIN"].includes(session.profile.role_code)
  ) {
    return "/profile";
  }
});
router.afterEach((to) => {
  document.title = String(to.meta.title || "津韵润乡") + " · 津韵润乡";
});
export default router;
