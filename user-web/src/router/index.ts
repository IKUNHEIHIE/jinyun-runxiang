import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
    meta: { title: '首页 · 津门非遗画卷' }
  },
  {
    path: '/courses',
    name: 'Courses',
    component: () => import('../views/CoursesView.vue'),
    meta: { title: '非遗小课堂' }
  },
  {
    path: '/ai-workshop',
    name: 'AiWorkshop',
    component: () => import('../views/AiWorkshopView.vue'),
    meta: { title: 'AI多模态工坊' }
  },
  {
    path: '/community',
    name: 'Community',
    component: () => import('../views/CommunityView.vue'),
    meta: { title: '美育社区广场' }
  },
  {
    path: '/mall',
    name: 'Mall',
    component: () => import('../views/MallView.vue'),
    meta: { title: '文创助农市集' }
  },
  {
    path: '/landmarks',
    name: 'Landmarks',
    component: () => import('../views/LandmarksView.vue'),
    meta: { title: '津沽研学地图' }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/ProfileView.vue'),
    meta: { title: '个人中心 · 教师双师工作台' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.afterEach((to) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - 《津韵润乡》天津非遗赋能乡村美育智能平台`
  }
})

export default router
