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
          <el-segmented 
            v-model="currentAge" 
            :options="ageGroups.map(g => ({ label: g.label, value: g.key }))"
            @change="fetchCourses"
          />
        </div>
      </div>

      <div class="filter-row" style="margin-top: 14px;">
        <span class="filter-label">非遗门类：</span>
        <div class="filter-tags">
          <el-check-tag 
            v-for="c in categories" 
            :key="c.key" 
            :checked="currentCategory === c.key"
            @change="() => { currentCategory = c.key; fetchCourses(); }"
            class="heritage-check-tag"
          >
            {{ c.label }}
          </el-check-tag>
        </div>
      </div>
    </div>

    <!-- 骨架屏加载状态 -->
    <div v-if="loading" class="courses-grid">
      <div v-for="i in 6" :key="i" class="paper-card course-skeleton-card">
        <el-skeleton animated>
          <template #template>
            <el-skeleton-item variant="image" style="width: 100%; height: 160px; border-radius: 12px 12px 0 0;" />
            <div style="padding: 14px;">
              <el-skeleton-item variant="h3" style="width: 60%;" />
              <el-skeleton-item variant="text" style="width: 90%; margin-top: 10px;" />
              <el-skeleton-item variant="text" style="width: 40%; margin-top: 10px;" />
            </div>
          </template>
        </el-skeleton>
      </div>
    </div>

    <!-- 课程列表网格 -->
    <div v-else class="courses-grid">
      <div 
        v-for="course in courses" 
        :key="course.id" 
        class="paper-card course-item"
        @click="openDetail(course.id)"
      >
        <div class="thumb-wrapper">
          <img :src="course.cover_url" :alt="course.title" @error="handleImgError" />
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
            <div class="video-bar-actions">
              <el-button 
                v-if="currentDetail.quiz_id" 
                type="warning" 
                size="small" 
                round 
                class="btn-quiz-start"
                @click="openQuizModal"
              >
                ❖ 课中非遗知识挑战 (+25 能量)
              </el-button>
              <el-button 
                type="primary" 
                size="small" 
                class="btn-primary"
                :disabled="activeChapter?.progress?.completed"
                @click="reportFinish(currentDetail.id, activeChapter?.id || 1)"
              >
                {{ activeChapter?.progress?.completed ? '已完成学习' : '完成本讲打卡 (+10 能量)' }}
              </el-button>
            </div>
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

    <!-- 课中非遗知识挑战弹窗 -->
    <el-dialog
      v-model="quizModalVisible"
      title="非遗小课堂 · 互动闯关挑战"
      width="640px"
      custom-class="quiz-dialog"
      destroy-on-close
    >
      <div v-if="quizData" class="quiz-modal-body">
        <div class="quiz-head">
          <span class="quiz-badge">❖ 考考你</span>
          <h3 class="font-serif quiz-title">{{ quizData.title }}</h3>
          <span class="quiz-energy-tip">及格线 {{ quizData.pass_score }} 分 · 通关奖励 +{{ quizData.energy_reward }} 能量</span>
        </div>

        <div v-if="!quizSubmitted" class="quiz-questions-list">
          <div 
            v-for="(q, qIdx) in quizData.questions" 
            :key="q.id" 
            class="quiz-q-card"
          >
            <div class="q-title">
              <span class="q-seq">{{ qIdx + 1 }}.</span>
              <span>{{ q.content }}</span>
              <span class="q-score">({{ q.score }}分)</span>
            </div>
            <div class="q-options">
              <el-radio-group v-model="userAnswers[q.id]">
                <el-radio 
                  v-for="opt in q.options" 
                  :key="opt.key" 
                  :value="opt.key"
                  class="quiz-option-radio"
                >
                  <span class="opt-key">{{ opt.key }}.</span> {{ opt.text }}
                </el-radio>
              </el-radio-group>
            </div>
          </div>
        </div>

        <!-- 提交后的评测与解析展示 -->
        <div v-else class="quiz-result-view">
          <div class="result-score-banner" :class="quizResult.passed ? 'pass' : 'fail'">
            <div class="score-number font-serif">{{ quizResult.score }} <span class="score-unit">分</span></div>
            <div class="score-status">
              {{ quizResult.passed ? '🎉 恭喜闯关成功！非遗工艺要点掌握优秀' : '💪 距离通关只差一点，仔细阅读名师解析再试一次吧！' }}
            </div>
            <div v-if="quizResult.passed" class="reward-tag">
              ⚡ 已斩获美育能量 +{{ quizResult.energy_reward }} 点
            </div>
          </div>

          <div class="quiz-explanations">
            <h4 class="font-serif exp-heading">❖ 名师工艺解析与要点回顾</h4>
            <div 
              v-for="(d, dIdx) in quizResult.details" 
              :key="dIdx" 
              class="exp-item"
              :class="d.is_correct ? 'exp-correct' : 'exp-wrong'"
            >
              <div class="exp-status-row">
                <span>第 {{ dIdx + 1 }} 题：{{ d.is_correct ? '✓ 作答正确' : '✕ 作答错误' }}</span>
                <span class="exp-answer-tag">正确答案：{{ d.correct_answers.join(', ') }}</span>
              </div>
              <p class="exp-text">{{ d.explanation }}</p>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div v-if="!quizSubmitted">
          <el-button @click="quizModalVisible = false">稍后再测</el-button>
          <el-button type="primary" class="btn-primary" :loading="submittingQuiz" @click="submitQuizAction">
            提交非遗答卷
          </el-button>
        </div>
        <div v-else>
          <el-button @click="resetQuiz">重新挑战</el-button>
          <el-button type="primary" class="btn-primary" @click="quizModalVisible = false">
            完成闯关并返回
          </el-button>
        </div>
      </template>
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

const handleImgError = (e: Event) => {
  const target = e.target as HTMLImageElement
  if (target && target.src && !target.src.endsWith('/static/images/shadow_puppet_1.svg')) {
    target.src = '/static/images/shadow_puppet_1.svg'
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

const quizModalVisible = ref(false)
const quizData = ref<any>(null)
const userAnswers = ref<Record<string, string>>({})
const submittingQuiz = ref(false)
const quizSubmitted = ref(false)
const quizResult = ref<any>(null)

const openQuizModal = async () => {
  if (!currentDetail.value || !currentDetail.value.quiz_id) return
  try {
    const res: any = await request.get(`/courses/quiz/${currentDetail.value.quiz_id}`)
    quizData.value = res
    userAnswers.value = {}
    quizSubmitted.value = false
    quizResult.value = null
    quizModalVisible.value = true
  } catch (err) {
    ElMessage.error('加载测验题目失败')
  }
}

const submitQuizAction = async () => {
  if (!quizData.value) return
  const payloadAnswers: Record<string, string[]> = {}
  for (const q of quizData.value.questions) {
    const selected = userAnswers.value[q.id]
    if (!selected) {
      ElMessage.warning(`第 ${q.seq} 题尚未作答，请完成后再提交`)
      return
    }
    payloadAnswers[q.id] = [selected]
  }

  submittingQuiz.value = true
  try {
    const res: any = await request.post(`/courses/quiz/${quizData.value.id}/submit`, {
      answers: payloadAnswers
    })
    quizResult.value = res
    quizSubmitted.value = true
    if (res.passed) {
      ElMessage.success(`🎉 闯关成功！获得美育能量 +${res.energy_reward} 点！`)
    } else {
      ElMessage.warning(`本次得分 ${res.score} 分，未达及格线，请仔细查看名师解析后再试！`)
    }
  } catch (err) {
    ElMessage.error('提交答卷失败')
  } finally {
    submittingQuiz.value = false
  }
}

const resetQuiz = () => {
  userAnswers.value = {}
  quizSubmitted.value = false
  quizResult.value = null
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

.heritage-check-tag {
  margin-right: 8px;
  margin-bottom: 6px;
  border-radius: 20px;
  cursor: pointer;
}

.course-skeleton-card {
  height: 280px;
  background-color: var(--color-paper-card);
  border-radius: var(--radius-card);
  overflow: hidden;
}

.video-bar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-quiz-start {
  font-weight: 700;
  box-shadow: 0 3px 8px rgba(217, 119, 6, 0.25);
}

/* 测验弹窗样式 */
.quiz-modal-body {
  padding: 10px 4px;
}

.quiz-head {
  text-align: center;
  padding-bottom: 16px;
  border-bottom: 1px dashed var(--color-border);
  margin-bottom: 20px;
}

.quiz-badge {
  font-size: 12px;
  background: rgba(196, 134, 58, 0.15);
  color: #92400E;
  padding: 3px 10px;
  border-radius: 12px;
  font-weight: 700;
}

.quiz-title {
  font-size: 18px;
  color: var(--color-primary);
  margin: 8px 0 4px;
}

.quiz-energy-tip {
  font-size: 12px;
  color: #B45309;
}

.quiz-questions-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.quiz-q-card {
  background: var(--color-paper);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 16px;
}

.q-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-main);
  margin-bottom: 12px;
  display: flex;
  align-items: flex-start;
  gap: 6px;
}

.q-seq {
  color: var(--color-primary);
}

.q-score {
  font-size: 12px;
  color: var(--color-text-secondary);
  font-weight: 400;
}

.q-options {
  padding-left: 14px;
}

.quiz-option-radio {
  display: flex !important;
  margin-bottom: 8px;
  font-size: 13px;
}

.opt-key {
  font-weight: 700;
  margin-right: 4px;
}

/* 测验结果 */
.result-score-banner {
  text-align: center;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 24px;
}

.result-score-banner.pass {
  background: #F0FDF4;
  border: 1px solid #BBF7D0;
}

.result-score-banner.fail {
  background: #FEF2F2;
  border: 1px solid #FECACA;
}

.score-number {
  font-size: 40px;
  font-weight: 900;
  line-height: 1;
}

.result-score-banner.pass .score-number { color: #15803D; }
.result-score-banner.fail .score-number { color: #B91C1C; }

.score-unit {
  font-size: 16px;
}

.score-status {
  font-size: 14px;
  font-weight: 700;
  margin-top: 8px;
}

.result-score-banner.pass .score-status { color: #166534; }
.result-score-banner.fail .score-status { color: #991B1B; }

.reward-tag {
  margin-top: 10px;
  display: inline-block;
  font-size: 13px;
  font-weight: 700;
  padding: 4px 14px;
  background: #FEF3C7;
  color: #92400E;
  border-radius: 20px;
}

.quiz-explanations {
  border-top: 1px dashed var(--color-border);
  padding-top: 16px;
}

.exp-heading {
  font-size: 15px;
  color: var(--color-primary);
  margin-bottom: 12px;
}

.exp-item {
  padding: 12px 14px;
  border-radius: 8px;
  margin-bottom: 12px;
}

.exp-correct {
  background: #F0FDF4;
  border: 1px solid #DCFCE7;
}

.exp-wrong {
  background: #FEF2F2;
  border: 1px solid #FEE2E2;
}

.exp-status-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 6px;
}

.exp-correct .exp-status-row { color: #15803D; }
.exp-wrong .exp-status-row { color: #B91C1C; }

.exp-answer-tag {
  color: var(--color-primary);
}

.exp-text {
  font-size: 12px;
  color: var(--color-text-regular);
  line-height: 1.6;
}
</style>
