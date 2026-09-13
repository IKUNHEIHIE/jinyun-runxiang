<template>
  <div class="app-layout" :class="{ 'rural-classroom-mode': isClassroomMode }">
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

          <!-- 乡村大屏护眼高对比模式 (P1) -->
          <button
            class="eyecare-btn"
            :class="{ active: isClassroomMode }"
            @click="toggleClassroomMode"
            :title="isClassroomMode ? '恢复默认模式' : '开启乡村教室大屏护眼高对比模式'"
          >
            <span>🏮</span>
            <span>{{ isClassroomMode ? '大屏护眼开' : '大屏护眼' }}</span>
          </button>

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

    <!-- 津门非遗留声钵·环境音浮动控制器 (P3) -->
    <div class="soundscape-dock" :class="{ expanded: isSoundExpanded }">
      <div class="soundscape-pill" @click="toggleSoundExpand">
        <span class="sound-wave-icon" :class="{ playing: isPlayingSound }">🎵</span>
        <span class="sound-title">{{ activeSoundTrack ? activeSoundTrack.title.split('·')[0] : '津门留声钵' }}</span>
        <span class="sound-status-dot" :class="{ on: isPlayingSound }"></span>
      </div>

      <div v-if="isSoundExpanded" class="soundscape-panel">
        <div class="soundscape-header">
          <div class="panel-title font-serif">
            <span>🎐 津门非遗留声钵</span>
            <span class="panel-tag">环境音景</span>
          </div>
          <button class="close-btn" @click="isSoundExpanded = false">×</button>
        </div>

        <p class="soundscape-desc">{{ activeSoundTrack?.description }}</p>
        <div class="soundscape-note" v-if="activeSoundTrack?.culture_note">
          <span style="color: #C1272D; font-weight: bold;">❖ 文脉：</span>{{ activeSoundTrack.culture_note }}
        </div>

        <!-- 曲目切换列表 -->
        <div class="soundscape-tracks">
          <button
            v-for="t in soundTracks"
            :key="t.id"
            class="track-item"
            :class="{ active: activeSoundTrack?.id === t.id }"
            @click="selectTrack(t)"
          >
            <span class="track-icon">{{ t.icon }}</span>
            <span class="track-name">{{ t.title.split('·')[0] }}</span>
          </button>
        </div>

        <div class="soundscape-controls">
          <button class="play-toggle-btn" :class="{ playing: isPlayingSound }" @click="togglePlaySound">
            {{ isPlayingSound ? '⏸ 暂停沉浸' : '▶ 开启津门音景' }}
          </button>
          <div class="vol-slider">
            <span style="font-size: 11px; color: #8C827A;">音量</span>
            <input type="range" min="0" max="1" step="0.05" v-model.number="soundVolume" @input="updateVolume" style="width: 60px;" />
          </div>
        </div>
      </div>
    </div>
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

const isClassroomMode = ref(false)
const toggleClassroomMode = () => {
  isClassroomMode.value = !isClassroomMode.value
  if (isClassroomMode.value) {
    ElMessage.success('已开启【乡村教室大屏护眼高对比模式】，全站适老适幼高对比与暖宣纸质感生效')
  } else {
    ElMessage.info('已恢复标准显示模式')
  }
}

// -------------------------------------------------------------
// 津门非遗留声钵·环境音合成引擎 (P3)
// -------------------------------------------------------------
const isSoundExpanded = ref(false)
const isPlayingSound = ref(false)
const soundVolume = ref(0.4)
const soundTracks = ref<any[]>([])
const activeSoundTrack = ref<any>(null)

let audioCtx: any = null
let oscNode: any = null
let gainNode: any = null

const fetchSoundscapes = async () => {
  try {
    const res: any = await request.get('/heritage/soundscapes')
    if (res && res.length) {
      soundTracks.value = res
      activeSoundTrack.value = res[0]
    }
  } catch (e) {
    // default
  }
}

const toggleSoundExpand = () => {
  isSoundExpanded.value = !isSoundExpanded.value
}

const selectTrack = (t: any) => {
  activeSoundTrack.value = t
  if (isPlayingSound.value) {
    stopSound()
    startSound()
  }
}

const startSound = () => {
  try {
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
    if (!audioCtx && AudioContextClass) {
      audioCtx = new AudioContextClass()
    }
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume()
    }

    const freq = activeSoundTrack.value?.ambient_freq || 220
    const wave = activeSoundTrack.value?.wave_type || 'sine'

    oscNode = audioCtx.createOscillator()
    oscNode.type = wave
    oscNode.frequency.setValueAtTime(freq, audioCtx.currentTime)

    gainNode = audioCtx.createGain()
    gainNode.gain.setValueAtTime(soundVolume.value * 0.12, audioCtx.currentTime)

    const filter = audioCtx.createBiquadFilter()
    filter.type = 'lowpass'
    filter.frequency.setValueAtTime(700, audioCtx.currentTime)

    oscNode.connect(filter)
    filter.connect(gainNode)
    gainNode.connect(audioCtx.destination)

    oscNode.start()
    isPlayingSound.value = true
  } catch (e) {
    console.warn('Audio start note', e)
  }
}

const stopSound = () => {
  if (oscNode) {
    try { oscNode.stop() } catch (e) {}
    try { oscNode.disconnect() } catch (e) {}
    oscNode = null
  }
  isPlayingSound.value = false
}

const togglePlaySound = () => {
  if (isPlayingSound.value) {
    stopSound()
    ElMessage.info('已暂停津门非遗环境音')
  } else {
    startSound()
    ElMessage.success(`已伴随【${activeSoundTrack.value?.title}】开启沉浸式美育`)
  }
}

const updateVolume = () => {
  if (gainNode && audioCtx) {
    gainNode.gain.setValueAtTime(soundVolume.value * 0.12, audioCtx.currentTime)
  }
}

onMounted(() => {
  fetchProfile()
  fetchSoundscapes()
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

/* 乡村教室大屏护眼高对比模式 (P1) */
.eyecare-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  border-radius: 20px;
  background: #FFFDF9;
  border: 1px solid #D6A85C;
  color: #8B4A2F;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.eyecare-btn:hover {
  background: #F8F1E5;
}
.eyecare-btn.active {
  background: #8B4A2F;
  border-color: #8B4A2F;
  color: #FFFFFF;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(139, 74, 47, 0.3);
}

.app-layout.rural-classroom-mode {
  background-color: #F8F4EB !important;
  filter: contrast(108%);
}
.app-layout.rural-classroom-mode :deep(h1),
.app-layout.rural-classroom-mode :deep(h2),
.app-layout.rural-classroom-mode :deep(h3) {
  letter-spacing: 0.5px;
}

/* 津门非遗留声钵·环境音浮动控制器 (P3) */
.soundscape-dock {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 999;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.soundscape-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(47, 41, 37, 0.92);
  color: #F8F4EC;
  backdrop-filter: blur(8px);
  padding: 9px 16px;
  border-radius: 30px;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.25);
  cursor: pointer;
  border: 1px solid #D6A85C;
  transition: all 0.25s ease;
}
.soundscape-pill:hover {
  transform: translateY(-2px);
  background: #231E1B;
  box-shadow: 0 6px 22px rgba(0, 0, 0, 0.35);
}

.sound-wave-icon {
  font-size: 15px;
}
.sound-wave-icon.playing {
  animation: pulseBeat 1.4s infinite ease-in-out;
}
@keyframes pulseBeat {
  0% { transform: scale(1); }
  50% { transform: scale(1.25); }
  100% { transform: scale(1); }
}

.sound-title {
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.sound-status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #7D756C;
}
.sound-status-dot.on {
  background: #52C41A;
  box-shadow: 0 0 8px #52C41A;
}

.soundscape-panel {
  position: absolute;
  bottom: 52px;
  right: 0;
  width: 310px;
  background: #FFFDF9;
  border: 1px solid #D6A85C;
  border-radius: 14px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.18);
  padding: 16px 18px;
  color: #2F2925;
}

.soundscape-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #F0E6D8;
  padding-bottom: 10px;
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: #8B4A2F;
  display: flex;
  align-items: center;
  gap: 6px;
}

.panel-tag {
  font-size: 10px;
  background: #F4E8D7;
  color: #8B4A2F;
  padding: 1px 6px;
  border-radius: 4px;
}

.close-btn {
  background: transparent;
  border: none;
  font-size: 18px;
  color: #A8A095;
  cursor: pointer;
}
.close-btn:hover {
  color: #2F2925;
}

.soundscape-desc {
  font-size: 12px;
  color: #6E655E;
  margin: 10px 0 6px;
  line-height: 1.6;
}

.soundscape-note {
  font-size: 11px;
  color: #8C827A;
  background: #F8F4EB;
  padding: 6px 8px;
  border-radius: 6px;
  margin-bottom: 12px;
  line-height: 1.5;
}

.soundscape-tracks {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 14px;
}

.track-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 10px;
  border-radius: 8px;
  background: #F9F6F0;
  border: 1px solid #EBE2D5;
  color: #554D46;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}
.track-item:hover {
  background: #F2ECE0;
}
.track-item.active {
  background: #8B4A2F;
  color: #FFF;
  border-color: #8B4A2F;
  font-weight: 600;
}

.soundscape-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid #F0E6D8;
}

.play-toggle-btn {
  padding: 6px 14px;
  border-radius: 20px;
  background: #8B4A2F;
  color: #FFF;
  border: none;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.play-toggle-btn:hover {
  background: #A35939;
}
.play-toggle-btn.playing {
  background: #4A7A60;
}

.vol-slider {
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
