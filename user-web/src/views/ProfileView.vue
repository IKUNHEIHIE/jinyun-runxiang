<template>
  <div class="profile-page">
    <!-- 用户顶部名片 -->
    <div class="paper-card profile-hero">
      <div class="hero-left">
        <el-avatar :size="80" :src="userInfo.avatar_url || '/static/images/default_avatar.svg'" />
        <div class="user-meta">
          <div class="name-row">
            <h2 class="font-serif user-title">{{ userInfo.nickname || '小明同学' }}</h2>
            <span class="role-tag">{{ isTeacher ? '乡村美育骨干教师' : '乡村非遗学徒' }}</span>
          </div>
          <p class="user-school">
            🏫 {{ userInfo.school_name || (isTeacher ? '蓟州区下营中心校美育教研组' : '蓟州区下营镇中心小学 · 四年级') }}
          </p>
        </div>
      </div>

      <div class="hero-right">
        <!-- 角色模式切换 -->
        <div class="switch-box">
          <span class="switch-label">身份视图：</span>
          <el-radio-group v-model="activeRoleTab" size="small" @change="onRoleTabChange">
            <el-radio-button label="STUDENT">🎒 乡村学徒视图</el-radio-button>
            <el-radio-button label="TEACHER">🎓 教师工作台视图</el-radio-button>
          </el-radio-group>
        </div>
      </div>
    </div>

    <!-- 视图 1：学生工匠档案 -->
    <div v-if="activeRoleTab === 'STUDENT'" class="student-view">
      <!-- 能量值与成长阶梯 -->
      <div class="paper-card section-card">
        <div class="section-title-row">
          <h3 class="font-serif">⚡ 非遗工匠能量等级</h3>
          <span class="level-name">当前称号：<strong>{{ levelName }}</strong></span>
        </div>
        <div class="level-progress-box">
          <div class="progress-labels">
            <span>LV.1 新晋学徒 (0)</span>
            <span>LV.2 熟练巧匠 (500)</span>
            <span>LV.3 乡村工匠 (1000)</span>
            <span>LV.4 非遗能手 (2000)</span>
          </div>
          <el-progress :percentage="energyPercent" :stroke-width="12" color="#8B4A2F" :show-text="false" />
          <div class="current-energy-tip">
            当前美育能量：<strong>{{ currentEnergy }}</strong> 点（离下一等级还需 {{ Math.max(0, 2000 - currentEnergy) }} 能量）
          </div>
        </div>
      </div>

      <!-- 徽章墙 -->
      <div class="paper-card section-card">
        <h3 class="font-serif section-heading">🏮 天津非遗学徒荣誉徽章</h3>
        <div class="badges-grid">
          <div class="badge-card unlocked">
            <span class="badge-icon">🏮</span>
            <h4>初探津门非遗</h4>
            <p>首次完成一节非遗微课点播打卡</p>
          </div>
          <div class="badge-card unlocked">
            <span class="badge-icon">🎨</span>
            <h4>AI巧思匠人</h4>
            <p>在AI工坊生成并导出首个皮影/纹样资产</p>
          </div>
          <div class="badge-card unlocked">
            <span class="badge-icon">🪵</span>
            <h4>汉沽版画小工匠</h4>
            <p>完成滨海盐滩黑白版画技艺微课</p>
          </div>
          <div class="badge-card unlocked">
            <span class="badge-icon">🗺️</span>
            <h4>乡村美育使者</h4>
            <p>完成至少1处天津历史文化地标研学打卡</p>
          </div>
          <div class="badge-card locked">
            <span class="badge-icon">🌟</span>
            <h4>非遗大师传人</h4>
            <p>在社区广场发布作品并获得大师点赞</p>
          </div>
        </div>
      </div>

      <!-- 我的助农文创订单 -->
      <div class="paper-card section-card">
        <h3 class="font-serif section-heading">📦 我的文创助农认购记录</h3>
        <div v-if="orders.length === 0" class="empty-tip">暂无订单，可前往文创市集挑选非遗手作助农！</div>
        <div v-else class="orders-list">
          <div v-for="o in orders" :key="o.order_no" class="order-row">
            <div class="order-info">
              <span class="order-no">单号：{{ o.order_no }}</span>
              <span class="order-time">{{ o.created_at }}</span>
            </div>
            <div class="order-right">
              <span class="order-amount">实付 ¥{{ o.total_amount_yuan }}</span>
              <span class="order-fund">♥ 美育基金贡献 ¥{{ o.fund_contributed_yuan }}</span>
              <el-tag size="small" type="success">已支付</el-tag>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 视图 2：教师智能工作台 -->
    <div v-else class="teacher-view">
      <!-- 快捷班级卡片 -->
      <div class="paper-card section-card">
        <h3 class="font-serif section-heading">🏫 我所负责的乡村美育班级</h3>
        <div class="classes-grid">
          <div v-for="c in teacherClasses" :key="c.id" class="class-card">
            <div class="class-card-top">
              <h4 class="font-serif">{{ c.name }}</h4>
              <el-tag size="small">{{ c.grade }}</el-tag>
            </div>
            <div class="class-meta">
              <span>班级邀请码：<strong>{{ c.invite_code }}</strong></span>
              <span>在籍乡村学生：<strong>{{ c.student_count }}</strong> 人</span>
            </div>
          </div>
        </div>
      </div>

      <!-- AI 智能备课核心功能 -->
      <div class="paper-card section-card">
        <div class="section-title-row">
          <div>
            <h3 class="font-serif">✦ AI 智能乡村美育备课</h3>
            <p class="section-sub">输入非遗主题与学段，大模型一键生成教学目标、难点解析、活动环节与讲稿</p>
          </div>
          <el-button type="primary" class="btn-primary" :loading="generatingPlan" @click="generatePlan">
            一键生成教案
          </el-button>
        </div>

        <div class="plan-inputs">
          <el-form :inline="true">
            <el-form-item label="授课主题">
              <el-select v-model="planForm.topic" style="width: 200px">
                <el-option label="天津皮影戏：骨骼与镂空" value="天津皮影戏" />
                <el-option label="杨柳青木版年画：抱鱼娃娃" value="杨柳青木版年画" />
                <el-option label="泥人张彩塑：指尖生灵" value="泥人张彩塑" />
                <el-option label="独乐寺古建：辽代榫卯" value="独乐寺榫卯古建" />
                <el-option label="古法大漆：黑漆螺钿" value="古法大漆螺钿" />
              </el-select>
            </el-form-item>
            <el-form-item label="教学学段">
              <el-select v-model="planForm.grade" style="width: 160px">
                <el-option label="小学三年级" value="小学三年级" />
                <el-option label="小学四年级" value="小学四年级" />
                <el-option label="初中一年级" value="初中一年级" />
              </el-select>
            </el-form-item>
            <el-form-item label="微课时长">
              <el-input-number v-model="planForm.duration_minutes" :min="20" :max="60" />
            </el-form-item>
          </el-form>
        </div>

        <!-- 生成出的教案卡片 -->
        <div v-if="generatedPlan" class="generated-plan-box">
          <div class="plan-header">
            <h4 class="font-serif plan-title">{{ generatedPlan.title }}</h4>
            <a :href="generatedPlan.ppt_download_url" target="_blank" class="download-link">
              下载配套课件 PPTX ↓
            </a>
          </div>

          <div class="plan-targets">
            <div class="target-item">
              <span class="target-badge">审美感知</span>
              <p>{{ generatedPlan.targets?.aesthetic }}</p>
            </div>
            <div class="target-item">
              <span class="target-badge">艺术实践</span>
              <p>{{ generatedPlan.targets?.skill }}</p>
            </div>
            <div class="target-item">
              <span class="target-badge">文化理解</span>
              <p>{{ generatedPlan.targets?.emotion }}</p>
            </div>
          </div>

          <h5 class="step-title">教学过程设计：</h5>
          <div class="steps-flow">
            <div v-for="(step, idx) in generatedPlan.teaching_process" :key="idx" class="step-box">
              <div class="step-header">{{ step.step }}</div>
              <div class="step-body">{{ step.content }}</div>
            </div>
          </div>

          <div class="script-box">
            <strong>教师课堂导语：</strong>
            <p>{{ generatedPlan.teacher_script }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../api/request'

const userInfo = ref<any>({})
const currentEnergy = ref(1330)
const isTeacher = ref(false)
const activeRoleTab = ref('STUDENT')

const orders = ref<any[]>([])
const teacherClasses = ref<any[]>([])

const planForm = ref({
  topic: '天津皮影戏',
  grade: '小学四年级',
  duration_minutes: 45
})
const generatingPlan = ref(false)
const generatedPlan = ref<any>(null)

const levelName = computed(() => {
  if (currentEnergy.value >= 2000) return 'LV.4 非遗能手'
  if (currentEnergy.value >= 1000) return 'LV.3 乡村工匠'
  if (currentEnergy.value >= 500) return 'LV.2 熟练巧匠'
  return 'LV.1 新晋学徒'
})

const energyPercent = computed(() => {
  return Math.min(100, Math.round((currentEnergy.value / 2000) * 100))
})

const loadProfile = async () => {
  try {
    const res: any = await request.get('/auth/me')
    userInfo.value = res
    currentEnergy.value = res.energy_value || 1330
    isTeacher.value = res.role_code === 'TEACHER'
    if (isTeacher.value) {
      activeRoleTab.value = 'TEACHER'
    }
  } catch (e) {}

  try {
    const resOrders: any = await request.get('/mall/orders')
    orders.value = resOrders || []
  } catch (e) {}

  try {
    const resClasses: any = await request.get('/teacher/classes')
    teacherClasses.value = resClasses || []
  } catch (e) {}
}

const onRoleTabChange = (val: any) => {
  if (val === 'TEACHER' && !isTeacher.value) {
    ElMessage.info('正在为您加载教师工作台数据演示...')
  }
}

const generatePlan = async () => {
  generatingPlan.value = true
  try {
    const res: any = await request.post('/teacher/lesson-plans/generate', planForm.value)
    generatedPlan.value = res
    generatingPlan.value = false
    ElMessage.success('AI 美育智能教案生成成功！')
  } catch (e) {
    generatingPlan.value = false
    ElMessage.error('生成教案失败')
  }
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile-page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 32px 24px;
}

.profile-hero {
  padding: 28px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.hero-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.user-title {
  font-size: 26px;
  color: var(--color-primary);
  margin-right: 12px;
}

.name-row {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
}

.role-tag {
  font-size: 12px;
  background: #FFF8EA;
  color: #B45309;
  border: 1px solid rgba(214, 168, 92, 0.4);
  padding: 2px 10px;
  border-radius: 20px;
  font-weight: 700;
}

.user-school {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.switch-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-regular);
  margin-right: 8px;
}

.section-card {
  padding: 24px 28px;
  margin-bottom: 28px;
}

.section-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-heading {
  font-size: 18px;
  color: var(--color-text-main);
  margin-bottom: 20px;
  border-left: 4px solid var(--color-primary);
  padding-left: 10px;
}

.section-sub {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 4px;
}

.level-name strong {
  color: var(--color-primary);
}

.level-progress-box {
  background: var(--color-paper);
  padding: 20px;
  border-radius: 12px;
}

.progress-labels {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.current-energy-tip {
  font-size: 13px;
  color: var(--color-text-regular);
  margin-top: 12px;
  text-align: right;
}

.current-energy-tip strong {
  color: #B45309;
  font-size: 16px;
}

.badges-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

.badge-card {
  padding: 20px 14px;
  text-align: center;
  border-radius: 12px;
  border: 1px solid var(--color-border);
  background: var(--color-paper);
}

.badge-card.unlocked {
  background: #FFFDF9;
  border-color: var(--color-gold);
  box-shadow: 0 4px 12px rgba(214, 168, 92, 0.1);
}

.badge-card.locked {
  opacity: 0.5;
  filter: grayscale(1);
}

.badge-icon {
  font-size: 36px;
  display: block;
  margin-bottom: 10px;
}

.badge-card h4 {
  font-size: 14px;
  color: var(--color-text-main);
  margin-bottom: 4px;
}

.badge-card p {
  font-size: 11px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.orders-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.order-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  background: var(--color-paper);
  border: 1px solid var(--color-border);
  border-radius: 8px;
}

.order-info {
  display: flex;
  gap: 16px;
  font-size: 13px;
}

.order-no {
  font-weight: 700;
  color: var(--color-text-main);
}

.order-time {
  color: var(--color-text-secondary);
}

.order-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.order-amount {
  font-weight: 700;
  color: var(--color-text-main);
}

.order-fund {
  font-size: 12px;
  color: #B45309;
  font-weight: 700;
}

/* 教师专属 */
.classes-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.class-card {
  padding: 18px;
  background: var(--color-paper);
  border: 1px solid var(--color-border);
  border-radius: 10px;
}

.class-card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.class-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.generated-plan-box {
  margin-top: 24px;
  background: var(--color-paper);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 24px;
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.plan-title {
  font-size: 20px;
  color: var(--color-primary);
}

.download-link {
  font-size: 13px;
  color: var(--color-primary);
  font-weight: 700;
  text-decoration: none;
}

.plan-targets {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.target-item {
  padding: 14px;
  background: #FFFDF9;
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.target-badge {
  font-size: 11px;
  font-weight: 800;
  color: var(--color-primary);
  background: rgba(139, 74, 47, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  display: inline-block;
  margin-bottom: 6px;
}

.target-item p {
  font-size: 12px;
  color: var(--color-text-regular);
  line-height: 1.6;
}

.step-title {
  font-size: 15px;
  color: var(--color-text-main);
  margin-bottom: 12px;
}

.steps-flow {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.step-box {
  background: #FFFDF9;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 12px;
}

.step-header {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-primary);
  margin-bottom: 4px;
}

.step-body {
  font-size: 11px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.script-box {
  background: #FFF8EA;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid rgba(214, 168, 92, 0.3);
  font-size: 13px;
  color: #78350F;
}

.script-box strong {
  display: block;
  margin-bottom: 4px;
}

.empty-tip {
  padding: 24px;
  text-align: center;
  color: var(--color-text-secondary);
  font-size: 13px;
}
</style>
