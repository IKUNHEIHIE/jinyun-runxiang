<template>
  <div class="app-layout">
    <!-- 顶部津派非遗文化导航栏 -->
    <header class="app-header">
      <div class="header-container">
        <router-link to="/" class="brand-logo">
          <div class="logo-seal">津</div>
          <div class="brand-text">
            <span class="brand-title font-serif">津韵润乡</span>
            <span class="brand-sub">天津非遗赋能乡村美育智能应用</span>
          </div>
        </router-link>

        <nav class="nav-links">
          <router-link to="/" class="nav-item" exact-active-class="active">首页画卷</router-link>
          <router-link to="/courses" class="nav-item" active-class="active">非遗微课堂</router-link>
          <router-link to="/ai-workshop" class="nav-item" active-class="active">
            <span class="ai-sparkle">✦</span> AI工坊
          </router-link>
          <router-link to="/community" class="nav-item" active-class="active">美育广场</router-link>
          <router-link to="/mall" class="nav-item" active-class="active">文创助农</router-link>
          <router-link to="/landmarks" class="nav-item" active-class="active">研学地图</router-link>
          <router-link to="/profile" class="nav-item" active-class="active">个人中心</router-link>
        </nav>

        <div class="header-actions">
          <!-- 当前用户能量气泡 -->
          <div class="energy-badge">
            <span class="energy-icon">⚡</span>
            <span class="energy-value">{{ currentEnergy }}</span>
            <span class="energy-label">美育能量</span>
          </div>

          <!-- 角色指示与切换 -->
          <el-button size="small" round @click="toggleRole" class="role-btn">
            {{ currentRole === 'STUDENT' ? '🎒 乡村学徒端' : '🎓 美育名师端' }}
          </el-button>

          <!-- 快速跳转后台管理系统 -->
          <a href="http://localhost:5173" target="_blank" class="admin-portal-link" title="前往运营管理中台">
            <span>后台管理 ↗</span>
          </a>
        </div>
      </div>
    </header>

    <!-- 路由页面渲染容器 -->
    <main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- 页脚非遗与美育致谢 -->
    <footer class="app-footer">
      <div class="footer-container">
        <div class="footer-col">
          <h3 class="font-serif footer-title">津韵润乡</h3>
          <p class="footer-desc">
            以天津皮影、杨柳青木版年画、泥人张、汉沽版画等国家级非遗为载体，通过生成式多模态 AI 与具身智能交互，赋能天津乡村中小学美育普及与文化振兴。
          </p>
        </div>
        <div class="footer-col links-col">
          <h4>非遗传承基地与乡村联结</h4>
          <p>蓟州穿芳峪镇中心小学 · 宝坻大口屯中学 · 独乐寺古建研学营地</p>
          <p>天津博物馆文创工坊 · 汉沽国际版画基地 · 西青杨柳青非遗馆</p>
        </div>
        <div class="footer-col system-col">
          <h4>系统与微服务架构</h4>
          <p>前端前台门户：Vite + Vue 3 (Port 5174)</p>
          <p>运营后台系统：Element Plus + ECharts (Port 5173)</p>
          <p>后端统一API：FastAPI + MySQL 8.0 + Redis (Port 8000)</p>
        </div>
      </div>
      <div class="footer-bottom">
        <p>© 2026 《津韵润乡》项目组 · 赋能乡村美育 · 天津乡土文化数字传承</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from './api/request'

const currentRole = ref<'STUDENT' | 'TEACHER'>('STUDENT')
const currentEnergy = ref(1330)

const fetchProfile = async () => {
  try {
    const res: any = await request.get('/auth/me')
    if (res && res.energy_value !== undefined) {
      currentEnergy.value = res.energy_value
      currentRole.value = res.role_code === 'TEACHER' ? 'TEACHER' : 'STUDENT'
    }
  } catch (e) {
    // default
  }
}

const toggleRole = async () => {
  if (currentRole.value === 'STUDENT') {
    // 切换到教师端
    try {
      const res: any = await request.post('/auth/login', {
        username: 'teacher_wang',
        password: 'teacher123'
      })
      localStorage.setItem('jinyun_user_token', res.token)
      localStorage.setItem('jinyun_user_info', JSON.stringify(res.user))
      currentRole.value = 'TEACHER'
      ElMessage.success('已切换为【美育名师模式】，解锁AI智能备课与班级学情看板！')
      window.location.reload()
    } catch (e) {
      ElMessage.error('切换教师失败')
    }
  } else {
    // 切换回学生端
    try {
      const res: any = await request.post('/auth/login', {
        username: 'student_ming',
        password: 'student123'
      })
      localStorage.setItem('jinyun_user_token', res.token)
      localStorage.setItem('jinyun_user_info', JSON.stringify(res.user))
      currentRole.value = 'STUDENT'
      ElMessage.success('已切换为【乡村学徒模式】，享受微课打卡与AI创作！')
      window.location.reload()
    } catch (e) {
      ElMessage.error('切换学生失败')
    }
  }
}

onMounted(() => {
  fetchProfile()
})
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255, 253, 249, 0.95);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--color-border);
  box-shadow: 0 2px 10px rgba(139, 74, 47, 0.04);
}

.header-container {
  max-width: 1440px;
  margin: 0 auto;
  height: 72px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  flex-shrink: 0;
}

.logo-seal {
  width: 38px;
  height: 38px;
  background: var(--color-primary);
  color: #fff;
  font-family: var(--font-serif);
  font-size: 22px;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  box-shadow: 0 3px 8px rgba(139, 74, 47, 0.3);
  position: relative;
  border: 1px solid rgba(255, 255, 255, 0.3);
  flex-shrink: 0;
}

.brand-title {
  font-size: 20px;
  font-weight: 900;
  color: var(--color-primary);
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.brand-sub {
  display: block;
  font-size: 11px;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.nav-item {
  padding: 6px 11px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-regular);
  text-decoration: none;
  border-radius: 8px;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
  flex-shrink: 0;
}

.nav-item:hover {
  color: var(--color-primary);
  background: rgba(139, 74, 47, 0.06);
}

.nav-item.active {
  color: var(--color-primary);
  font-weight: 700;
  background: rgba(139, 74, 47, 0.1);
}

.ai-sparkle {
  color: var(--color-gold);
  font-size: 13px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.energy-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  background: #FFF8EA;
  border: 1px solid rgba(214, 168, 92, 0.4);
  border-radius: 20px;
  white-space: nowrap;
  flex-shrink: 0;
}

.energy-icon {
  color: #D97706;
  font-size: 14px;
}

.energy-value {
  font-weight: 800;
  color: #B45309;
  font-size: 14px;
}

.energy-label {
  font-size: 11px;
  color: #92400E;
  white-space: nowrap;
}

.role-btn {
  border-color: var(--color-border);
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}

.admin-portal-link {
  font-size: 13px;
  color: var(--color-teal);
  text-decoration: none;
  padding: 6px 12px;
  border-radius: 6px;
  background: rgba(44, 79, 84, 0.08);
  font-weight: 600;
  transition: all 0.2s ease;
  white-space: nowrap;
  flex-shrink: 0;
}

.admin-portal-link:hover {
  background: rgba(44, 79, 84, 0.15);
}

@media (max-width: 1260px) {
  .brand-sub {
    display: none;
  }
  .nav-item {
    padding: 6px 8px;
    font-size: 13.5px;
  }
  .header-actions {
    gap: 8px;
  }
}

@media (max-width: 1080px) {
  .energy-label {
    display: none;
  }
  .nav-links {
    gap: 2px;
  }
  .nav-item {
    padding: 5px 6px;
    font-size: 13px;
  }
  .header-actions .role-btn {
    padding: 6px 8px;
    font-size: 12px;
  }
}

.app-main {
  flex: 1;
}

.app-footer {
  background: #25221F;
  color: #D9D2C7;
  padding: 48px 0 24px;
  margin-top: 60px;
}

.footer-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
  display: grid;
  grid-template-columns: 2fr 1.5fr 1.5fr;
  gap: 40px;
}

.footer-title {
  color: #F8F4EC;
  font-size: 24px;
  margin-bottom: 12px;
}

.footer-desc {
  font-size: 13px;
  line-height: 1.8;
  color: #A8A095;
}

.footer-col h4 {
  color: var(--color-gold);
  font-size: 15px;
  margin-bottom: 14px;
}

.footer-col p {
  font-size: 13px;
  line-height: 1.9;
  color: #A8A095;
}

.footer-bottom {
  max-width: 1280px;
  margin: 36px auto 0;
  padding: 20px 24px 0;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  text-align: center;
  font-size: 12px;
  color: #7D756C;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
