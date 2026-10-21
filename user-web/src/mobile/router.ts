import { createRouter, createWebHashHistory } from "vue-router";
import { session, loadProfile } from "./api";
import { restorePageScroll } from "./page-scroll";
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: "/",
      component: () => import("./views/HomePage.vue"),
      meta: { tab: "home", title: "首页", surface: "#f5ede4" },
    },
    {
      path: "/courses",
      component: () => import("./views/CoursesPage.vue"),
      meta: { tab: "courses", title: "小课堂", surface: "#f5ede4" },
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
        surface: "#f5ede4",
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
      meta: { tab: "workshop", title: "AI工坊", surface: "#f5ede4" },
    },
    {
      path: "/ai-workshop/shadow-3d",
      component: () => import("./views/Shadow3DPage.vue"),
      meta: { hideTabs: true, title: "皮影三维营造", surface: "#efe6d6" },
    },
    {
      path: "/ai-workshop/3d",
      component: () => import("./views/Model3DPage.vue"),
      meta: { hideTabs: true, title: "三维数字沙盘", surface: "#efe6d6" },
    },
    {
      path: "/ai-workshop/works",
      component: () => import("./views/WorkshopWorksPage.vue"),
      meta: { hideTabs: true, title: "我的工坊作品", surface: "#f5ede4" },
    },
    {
      path: "/ai-workshop/:tool(bronze|shadow|lacquer)",
      component: () => import("./views/WorkshopEditorPage.vue"),
      meta: { hideTabs: true, title: "非遗创作" },
    },
    {
      path: "/community",
      component: () => import("./views/CommunityPage.vue"),
      meta: { tab: "community", title: "社区", surface: "#f5ede4" },
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
      meta: { title: "文创共创市集", surface: "#c9dbcb" },
    },
    {
      path: "/landmarks",
      component: () => import("./views/MapPage.vue"),
      meta: { title: "行走的美育地图", surface: "#f5f0e8" },
    },
    {
      path: "/teacher",
      component: () => import("./views/TeacherPage.vue"),
      meta: {
        tab: "teacher",
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
        tab: "teacher_class",
        title: "班级实时数据",
        teacher: true,
        surface: "#dbdbdb",
      },
    },
    {
      path: "/teacher/assignments",
      component: () => import("./views/TeacherAssignmentsPage.vue"),
      meta: { tab: "teacher_work", title: "班级作业", teacher: true },
    },
    {
      path: "/teacher/assignments/:id",
      component: () => import("./views/TeacherAssignmentsPage.vue"),
      meta: { hideTabs: true, title: "作业批改", teacher: true },
    },
    {
      path: "/teacher/contests",
      component: () => import("./views/TeacherContestsPage.vue"),
      meta: { tab: "teacher_contest", title: "班级对抗赛", teacher: true },
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
      meta: { hideTabs: true, title: "在线课堂", teacher: true },
    },
    {
      path: "/classroom",
      component: () => import("./views/ClassroomHubPage.vue"),
      meta: { hideTabs: true, title: "在线课堂", requiresAuth: true },
    },
    {
      path: "/classroom/:id",
      component: () => import("./views/ClassroomPage.vue"),
      meta: { hideTabs: true, title: "在线课堂", requiresAuth: true },
    },
    {
      path: "/me/:section",
      component: () => import("./views/PersonalServicePage.vue"),
      meta: { title: "我的服务", requiresAuth: true },
    },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
  scrollBehavior: (to, from, position) => {
    if (!position && to.path === from.path)
      return false;
    const token = session.token;
    return restorePageScroll(
      position || { left: 0, top: 0 },
      to.fullPath,
      !!position,
      () => router.currentRoute.value.fullPath === to.fullPath && token === session.token,
      (cancel) => router.beforeEach(() => { cancel(); }),
    );
  },
});
const TEACHER_ROLES = ["TEACHER", "ADMIN"];
router.beforeEach(async (to, from) => {
  // 冷启动时 session.profile 还没回来，教师会先闪一下学生首页；这里等一次 /auth/me 再判定落在哪一端。
  if (
    session.token &&
    !session.profile &&
    (to.path === "/" || to.meta.teacher)
  )
    await loadProfile().catch(() => null);
  if (
    to.path === "/" &&
    session.token &&
    session.profile &&
    TEACHER_ROLES.includes(session.profile.role_code)
  )
    return "/teacher";
  if ((to.meta.requiresAuth || to.meta.teacher) && !session.token) {
    session.authRedirect = to.fullPath;
    session.authVisible = true;
    return from.matched.length ? false : "/profile";
  }
  if (
    to.meta.teacher &&
    session.profile &&
    !TEACHER_ROLES.includes(session.profile.role_code)
  ) {
    return "/profile";
  }
});
router.afterEach((to) => {
  document.title = String(to.meta.title || "津韵润乡") + " · 津韵润乡";
});
export default router;
