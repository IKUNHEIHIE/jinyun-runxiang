import { createRouter, createWebHistory } from 'vue-router'
import AdminLayout from '@/layouts/AdminLayout.vue'

const routes = [
  {
    path: '/',
    component: AdminLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/DashboardView.vue'),
        meta: { title: '运营看板' }
      },
      {
        path: 'content',
        name: 'Content',
        component: () => import('@/views/content/ContentView.vue'),
        meta: { title: '内容管理' }
      },
      {
        path: 'models',
        name: 'Models',
        component: () => import('@/views/models/ModelsView.vue'),
        meta: { title: 'AI模型管理' }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/users/UsersView.vue'),
        meta: { title: '用户与班级' }
      },
      {
        path: 'community',
        name: 'Community',
        component: () => import('@/views/community/CommunityView.vue'),
        meta: { title: '社区风控' }
      },
      {
        path: 'activities',
        name: 'Activities',
        component: () => import('@/views/activities/ActivitiesView.vue'),
        meta: { title: '非遗地图与活动' }
      },
      {
        path: 'devices',
        name: 'Devices',
        component: () => import('@/views/devices/DevicesView.vue'),
        meta: { title: '具身设备监控' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/SettingsView.vue'),
        meta: { title: '系统设置' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
