<template>
  <el-container class="admin-layout">
    <!-- 侧边栏导航 -->
    <el-aside width="240px" class="admin-sidebar">
      <div class="sidebar-logo">
        <span class="logo-badge">津</span>
        <div class="logo-text">
          <div class="title">津韵润乡</div>
          <div class="sub">非遗美育管理后台</div>
        </div>
      </div>

      <el-menu
        :default-active="route.path"
        router
        class="menu-vertical"
        background-color="#2F2925"
        text-color="#F8F4EC"
        active-text-color="#D6A85C"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>运营看板 (A-01)</span>
        </el-menu-item>
        <el-menu-item index="/content">
          <el-icon><Reading /></el-icon>
          <span>内容管理 (A-02)</span>
        </el-menu-item>
        <el-menu-item index="/models">
          <el-icon><Cpu /></el-icon>
          <span>AI模型管理 (A-03)</span>
        </el-menu-item>
        <el-menu-item index="/users">
          <el-icon><UserFilled /></el-icon>
          <span>用户与班级 (A-04)</span>
        </el-menu-item>
        <el-menu-item index="/community">
          <el-icon><CircleCheck /></el-icon>
          <span>社区风控 (A-05)</span>
        </el-menu-item>
        <el-menu-item index="/activities">
          <el-icon><MapLocation /></el-icon>
          <span>非遗地图与活动 (A-06)</span>
        </el-menu-item>
        <el-menu-item index="/devices">
          <el-icon><Connection /></el-icon>
          <span>具身设备监控</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主体区域 -->
    <el-container>
      <el-header class="admin-header">
        <div class="header-left">
          <span class="breadcrumb-text">天津非遗赋能乡村美育智能应用 · 综合管控平台</span>
        </div>
        <div class="header-right">
          <el-badge :value="2" class="item" type="warning" style="margin-right: 20px;">
            <el-button circle size="small"><el-icon><Bell /></el-icon></el-button>
          </el-badge>
          <el-avatar size="small" src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150" />
          <span class="admin-name">津韵总管 (管理员)</span>
          <el-button type="text" size="small" style="color: #B64A44; margin-left: 15px;" @click="handleLogout">退出</el-button>
        </div>
      </el-header>

      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import {
  DataAnalysis, Reading, Cpu, UserFilled,
  CircleCheck, MapLocation, Connection, Bell
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

const handleLogout = () => {
  localStorage.removeItem('jinyun_admin_token')
  ElMessage.success('已安全退出管理系统')
  router.push('/dashboard')
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;
}
.admin-sidebar {
  background-color: #2F2925;
  color: #F8F4EC;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
}
.sidebar-logo {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
.logo-badge {
  background-color: #8B4A2F;
  color: #F8F4EC;
  font-size: 20px;
  font-weight: bold;
  width: 36px;
  height: 36px;
  line-height: 36px;
  text-align: center;
  border-radius: 8px;
  margin-right: 12px;
  border: 1px solid #D6A85C;
}
.logo-text .title {
  font-size: 16px;
  font-weight: bold;
  color: #F8F4EC;
}
.logo-text .sub {
  font-size: 11px;
  color: #D6A85C;
}
.menu-vertical {
  border-right: none;
}
.admin-header {
  background-color: #FFFFFF;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid #E5E0D8;
}
.breadcrumb-text {
  font-size: 15px;
  font-weight: 500;
  color: #63351F;
}
.header-right {
  display: flex;
  align-items: center;
}
.admin-name {
  margin-left: 10px;
  font-size: 14px;
  color: #2F2925;
  font-weight: 500;
}
.admin-main {
  background-color: #F8F4EC;
  padding: 20px;
  overflow-y: auto;
}
</style>
