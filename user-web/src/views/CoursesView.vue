<template>
  <div class="courses-page">
    <div class="page-header">
      <h1 class="page-title font-serif">非遗小课堂 · 乡土美育微课</h1>
      <p class="page-sub">
        跟随天津非遗国家级/市级传承人与乡村骨干教师，动手探寻指尖上的津沽千百年工艺智慧
      </p>
    </div>

    <!-- 筛选面板 -->
    <div class="filter-box paper-card">
      <div class="filter-row">
        <span class="filter-label">学段分龄：</span>
        <div class="filter-tags">
          <button 
            v-for="g in ageGroups" 
            :key="g.key" 
            :class="['filter-btn', { active: currentAge === g.key }]"
            @click="currentAge = g.key; fetchCourses()"
          >
            {{ g.label }}
          </button>
        </div>
      </div>

      <div class="filter-row">
        <span class="filter-label">非遗门类：</span>
        <div class="filter-tags">
          <button 
            v-for="c in categories" 
            :key="c.key" 
            :class="['filter-btn', { active: currentCategory === c.key }]"
            @click="currentCategory = c.key; fetchCourses()"
          >
            {{ c.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- 课程列表网格 -->
    <div v-loading="loading" class="courses-grid">
      <div 
        v-for="course in courses" 
        :key="course.id" 
        class="paper-card course-item"
        @click="openDetail(course.id)"
      >
        <div class="thumb-wrapper">
          <img :src="course.cover_url" :alt="course.title" />
          <span class="tag-age">{{ formatAge(course.age_group) }}</span>
        </div>
        <div class="item-content">
          <div class="category-meta">{{ formatCategory(course.category) }}</div>
          <h3 class="course-name font-serif">{{ course.title }}</h3>
          <p class="course-intro">{{ course.subtitle }}</p>
          <div class="meta-row">
            <span><el-icon><VideoCamera /></el-icon> {{ course.duration_minutes }} 分钟</span>
            <span class="energy-text">⚡ 奖励 {{ course.energy_reward }} 能量</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 课程详情与微课学习弹窗 -->
    <el-dialog 
      v-model="detailVisible" 
      width="820px" 
      top="40px"
      :show-close="true"
      destroy-on-close
      custom-class="course-dialog"
    >
      <div v-if="currentDetail" class="dialog-body">
        <div class="video-player-box">
          <video 
            ref="videoPlayer" 
            class="real-video-player"
            :src="activeChapter?.video_url || '/static/videos/tianjin_shadow_puppet_lesson.mp4'" 
            controls 
            playsinline
          ></video>
          <div class="video-bar">
            <span>正在学习：{{ activeChapter?.title || currentDetail.title }}</span>
            <el-button 
              type="primary" 
              size="small" 
              class="btn-primary"
              :disabled="activeChapter?.progress?.completed"
              @click="reportFinish(currentDetail.id, activeChapter?.id || 1)"
            >
              {{ activeChapter?.progress?.completed ? '已完成学习' : '完成本讲学习打卡 (+10 能量)' }}
            </el-button>
          </div>
        </div>

        <div class="course-info-detail">
          <h2 class="font-serif detail-title">{{ currentDetail.title }}</h2>
          <p class="detail-desc">{{ currentDetail.description }}</p>

          <h4 class="font-serif section-heading">讲次与核心工序要点（点击切换播放）</h4>
          <div class="chapters-list">
            <div 
              v-for="ch in currentDetail.chapters" 
              :key="ch.id" 
              class="chapter-card"
              :class="{ 'active-chapter': activeChapter?.id === ch.id }"
              style="cursor: pointer;"
              @click="selectChapter(ch)"
            >
              <div class="ch-left">
                <span class="ch-num">第{{ ch.seq }}讲</span>
                <div>
                  <h5 class="ch-title">{{ ch.title }}</h5>
                  <div class="ch-tags">
                    <span v-for="(k, idx) in ch.key_points" :key="idx" class="point-tag">
                      ✓ {{ k }}
                    </span>
                  </div>
                </div>
              </div>
              <el-tag :type="ch.progress?.completed ? 'success' : 'info'" size="small">
                {{ ch.progress?.completed ? '已学完' : '待学习' }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../api/request'

const loading = ref(false)
const courses = ref<any[]>([])
const currentAge = ref('')
const currentCategory = ref('')

const detailVisible = ref(false)
const currentDetail = ref<any>(null)

const ageGroups = [
  { key: '', label: '全部学段' },
  { key: 'PRIMARY_LOW', label: '小学低段 (1-3年级)' },
  { key: 'PRIMARY_HIGH', label: '小学高段 (4-6年级)' },
  { key: 'JUNIOR', label: '初中学段 (7-9年级)' }
]

const categories = [
  { key: '', label: '全部非遗' },
  { key: 'SHADOW_PUPPET', label: '津派皮影' },
  { key: 'PAINTING', label: '版画/年画' },
  { key: 'BRONZE', label: '古建/青铜' },
  { key: 'CLAY', label: '面塑/泥塑' },
  { key: 'LACQUER', label: '大漆/闻药' },
  { key: 'BALLAD', label: '曲艺/评剧' }
]

const formatAge = (val: string) => {
  const map: Record<string, string> = {
    PRIMARY_LOW: '小学低段',
    PRIMARY_HIGH: '小学高段',
    JUNIOR: '初中'
  }
  return map[val] || '通用'
}

const formatCategory = (cat: string) => {
  const map: Record<string, string> = {
    SHADOW_PUPPET: '津派皮影戏',
    PAINTING: '汉沽版画/年画',
    CLAY: '泥人张/面塑',
    BRONZE: '独乐寺榫卯/青铜',
    LACQUER: '古法大漆/益德成',
    BALLAD: '宝坻评剧/大鼓',
    EMBROIDERY: '老美华手作'
  }
  return map[cat] || '非遗技艺'
}

const fetchCourses = async () => {
  loading.value = true
  try {
    let url = '/courses?page=1&pageSize=20'
    if (currentAge.value) url += `&age_group=${currentAge.value}`
    if (currentCategory.value) url += `&category=${currentCategory.value}`
    const res: any = await request.get(url)
    if (res && res.list) {
      courses.value = res.list
    }
  } catch (e) {
  } finally {
    loading.value = false
  }
}

const activeChapter = ref<any>(null)

const selectChapter = (ch: any) => {
  activeChapter.value = ch
}

const openDetail = async (id: number) => {
  try {
    const res: any = await request.get(`/courses/${id}`)
    currentDetail.value = res
    if (res.chapters && res.chapters.length > 0) {
      activeChapter.value = res.chapters[0]
    } else {
      activeChapter.value = null
    }
    detailVisible.value = true
  } catch (e) {
    ElMessage.error('加载课程详情失败')
  }
}

const reportFinish = async (courseId: number, chapterId: number) => {
  try {
    const res: any = await request.post('/courses/progress', {
      course_id: courseId,
      chapter_id: chapterId,
      position_seconds: 600,
      duration_seconds: 600,
      completed: true
    })
    ElMessage.success(`恭喜打卡成功！能量值 +${res.energy_added || 10}`)
    openDetail(courseId)
  } catch (e) {
    ElMessage.error('打卡同步失败')
  }
}

onMounted(() => {
  fetchCourses()
})
</script>

<style scoped>
.courses-page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 32px 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 32px;
  color: var(--color-primary);
  margin-bottom: 8px;
}

.page-sub {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.filter-box {
  padding: 20px 24px;
  margin-bottom: 32px;
}

.filter-row {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.filter-row:last-child {
  margin-bottom: 0;
}

.filter-label {
  width: 90px;
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-regular);
}

.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-btn {
  padding: 6px 14px;
  font-size: 13px;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 20px;
  color: var(--color-text-regular);
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-btn:hover {
  border-color: var(--color-gold);
  color: var(--color-primary);
}

.filter-btn.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
  font-weight: 600;
}

.courses-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 28px;
}

.course-item {
  overflow: hidden;
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.thumb-wrapper {
  position: relative;
  height: 200px;
}

.thumb-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.course-item:hover .thumb-wrapper img {
  transform: scale(1.04);
}

.tag-age {
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(31, 30, 27, 0.75);
  backdrop-filter: blur(4px);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 4px;
}

.item-content {
  padding: 20px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.category-meta {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-gold);
  margin-bottom: 6px;
}

.course-name {
  font-size: 18px;
  color: var(--color-text-main);
  margin-bottom: 8px;
  line-height: 1.4;
}

.course-intro {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--color-text-secondary);
  border-top: 1px dashed var(--color-border);
  padding-top: 12px;
}

.energy-text {
  color: #B45309;
  font-weight: 700;
}

/* Modal styles */
.video-player-box {
  background: #000;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.real-video-player {
  width: 100%;
  max-height: 380px;
  display: block;
  background-color: #000;
}

.video-bar {
  padding: 12px 20px;
  background: #1C1917;
  color: #A8A29E;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chapter-card.active-chapter {
  border-color: #8B4A2F;
  background-color: rgba(139, 74, 47, 0.06);
}

.detail-title {
  font-size: 24px;
  color: var(--color-primary);
  margin-bottom: 10px;
}

.detail-desc {
  font-size: 14px;
  color: var(--color-text-regular);
  line-height: 1.8;
  margin-bottom: 24px;
}

.section-heading {
  font-size: 18px;
  color: var(--color-text-main);
  margin-bottom: 14px;
  border-left: 4px solid var(--color-primary);
  padding-left: 10px;
}

.chapters-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chapter-card {
  padding: 14px 18px;
  background: var(--color-paper);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.ch-left {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.ch-num {
  font-size: 12px;
  font-weight: 800;
  color: var(--color-primary);
  background: rgba(139, 74, 47, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
}

.ch-title {
  font-size: 15px;
  color: var(--color-text-main);
  margin-bottom: 4px;
}

.ch-tags {
  display: flex;
  gap: 8px;
}

.point-tag {
  font-size: 11px;
  color: var(--color-text-secondary);
}
</style>
