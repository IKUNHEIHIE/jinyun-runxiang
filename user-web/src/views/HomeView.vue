<template>
  <div class="home-container">
    <!-- 1. 顶部非遗动态画卷 Hero Banner -->
    <section class="hero-section">
      <div class="hero-content">
        <div class="tag-gold mb-3">
          <span>❖ 国家级非物质文化遗产 · 数字化乡村美育赋能</span>
        </div>
        <h1 class="hero-title font-serif">津韵润乡 · 传承有道</h1>
        <p class="hero-subtitle">
          以天津皮影、杨柳青木版年画、泥人张、汉沽版画为源，巧借生成式 AI 与具身智能，点亮每一位乡村孩子的乡土美育梦想。
        </p>

        <div class="hero-actions">
          <router-link to="/courses">
            <el-button type="primary" size="large" class="btn-primary">
              <el-icon class="mr-1"><VideoPlay /></el-icon> 探索非遗微课
            </el-button>
          </router-link>
          <router-link to="/ai-workshop">
            <el-button size="large" class="btn-ai">
              <span>✦</span> 进入AI工坊创作
            </el-button>
          </router-link>
        </div>

        <!-- 核心统计数字条 -->
        <div class="stats-strip">
          <div class="stat-item">
            <span class="stat-num font-serif">16+</span>
            <span class="stat-label">天津非遗微课</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-num font-serif">5 大</span>
            <span class="stat-label">多模态AI非遗工坊</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-num font-serif">9 所</span>
            <span class="stat-label">天津各区结对乡村小学</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-num font-serif">¥{{ (fundTotal).toFixed(2) }}</span>
            <span class="stat-label">助农美育定向基金</span>
          </div>
        </div>
      </div>

      <div class="hero-visual">
        <div class="visual-card paper-card">
          <img src="https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=600" alt="津门非遗手作" class="visual-img" />
          <div class="visual-caption">
            <span class="tag-heritage">今日非遗聚焦</span>
            <h4 class="font-serif">津派皮影戏 · 巧手镂空</h4>
            <p>感受北方皮影造型的刚劲刀法与矿物敷色之美</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 2. 乡村美育学徒成长动态 -->
    <section class="section-apprentice">
      <div class="paper-card apprentice-card">
        <div class="apprentice-left">
          <div class="avatar-box">
            <el-avatar :size="60" src="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150" />
            <div class="badge-tag">LV.2</div>
          </div>
          <div class="apprentice-info">
            <div class="info-title">
              <span class="user-name font-serif">{{ userProfile.nickname || '小明同学' }}</span>
              <span class="school-name">蓟州区下营镇中心小学 · 四年级</span>
            </div>
            <div class="energy-track">
              <div class="track-header">
                <span>美育工匠修炼度</span>
                <span class="energy-score">⚡ <strong>{{ userProfile.energy_value || 1330 }}</strong> / 2000 能量</span>
              </div>
              <el-progress :percentage="68" :stroke-width="10" color="#8B4A2F" :show-text="false" />
            </div>
          </div>
        </div>
        <div class="apprentice-badges">
          <div class="badge-pill active" title="已点亮：初探津门非遗">🏮 初探津门</div>
          <div class="badge-pill active" title="已点亮：AI巧思匠人">🎨 AI巧思</div>
          <div class="badge-pill active" title="已点亮：版画小工匠">🪵 版画工匠</div>
          <div class="badge-pill locked" title="待解锁：乡村美育使者">🗺️ 美育使者</div>
        </div>
      </div>
    </section>

    <!-- 3. 精品非遗小课堂推荐 -->
    <section class="section-courses">
      <div class="section-header">
        <div>
          <h2 class="section-title font-serif">乡土美育 · 精品微课</h2>
          <p class="section-desc">由天津非遗大师亲授，配套视频详解与分龄趣味测验</p>
        </div>
        <router-link to="/courses" class="view-all-link">查看全部课程 ({{ courses.length }}) →</router-link>
      </div>

      <div class="course-grid">
        <div v-for="c in courses.slice(0, 4)" :key="c.id" class="paper-card course-card">
          <div class="course-thumb">
            <img :src="c.cover_url" :alt="c.title" />
            <span class="category-badge">{{ formatCategory(c.category) }}</span>
          </div>
          <div class="course-body">
            <h3 class="course-title font-serif">{{ c.title }}</h3>
            <p class="course-sub">{{ c.subtitle }}</p>
            <div class="course-footer">
              <span class="duration"><el-icon><Clock /></el-icon> {{ c.duration_minutes }} 分钟</span>
              <span class="reward">⚡ +{{ c.energy_reward }} 能量</span>
            </div>
            <router-link :to="`/courses?id=${c.id}`" class="course-play-btn">
              进入学习
            </router-link>
          </div>
        </div>
      </div>
    </section>

    <!-- 4. 五大 AI 多模态非遗工坊快速通道 -->
    <section class="section-ai-entry">
      <div class="section-header">
        <div>
          <h2 class="section-title font-serif">AI 工坊 · 智能创作</h2>
          <p class="section-desc">结合大模型多模态能力，为乡村孩子带来“指尖上的非遗数字工匠”体验</p>
        </div>
        <router-link to="/ai-workshop" class="view-all-link">进入工坊大厅 →</router-link>
      </div>

      <div class="ai-tools-grid">
        <router-link to="/ai-workshop?tool=SHADOW_PUPPET" class="paper-card ai-tool-card">
          <div class="tool-icon shadow-icon">🎭</div>
          <h3 class="font-serif">津派皮影生成</h3>
          <p>智能提取角色线稿，传统矿物套色，导出 3D 可动骨骼与激光雕镂图纸。</p>
          <span class="tool-action">开始雕镂 →</span>
        </router-link>

        <router-link to="/ai-workshop?tool=BRONZE" class="paper-card ai-tool-card">
          <div class="tool-icon bronze-icon">🏺</div>
          <h3 class="font-serif">青铜神兽饕餮纹</h3>
          <p>萃取天津博物馆馆藏青铜重器神韵，生成金石拓片与铜绿氧化纹饰。</p>
          <span class="tool-action">探寻青铜 →</span>
        </router-link>

        <router-link to="/ai-workshop?tool=BALLAD" class="paper-card ai-tool-card">
          <div class="tool-icon ballad-icon">🥁</div>
          <h3 class="font-serif">骆派大鼓曲牌</h3>
          <p>古诗词智能五声音阶作曲，融合津门三弦与书场快板鼓点伴奏。</p>
          <span class="tool-action">试听创作 →</span>
        </router-link>

        <router-link to="/ai-workshop?tool=LACQUER" class="paper-card ai-tool-card">
          <div class="tool-icon lacquer-icon">✨</div>
          <h3 class="font-serif">古法大漆螺钿</h3>
          <p>中国传统天然色号智能配色，流线型草图修整与螺钿光彩质感生成。</p>
          <span class="tool-action">髹饰器皿 →</span>
        </router-link>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '../api/request'

const courses = ref<any[]>([])
const fundTotal = ref(137.75)
const userProfile = ref<any>({})

const formatCategory = (cat: string) => {
  const map: Record<string, string> = {
    SHADOW_PUPPET: '津派皮影',
    PAINTING: '杨柳青/版画',
    CLAY: '泥人张彩塑',
    BRONZE: '青铜金石',
    LACQUER: '大漆螺钿',
    BALLAD: '京韵大鼓'
  }
  return map[cat] || '非遗技艺'
}

const loadData = async () => {
  try {
    const resCourses: any = await request.get('/courses?page=1&pageSize=6')
    if (resCourses && resCourses.list) {
      courses.value = resCourses.list
    }
  } catch (e) {}

  try {
    const resMe: any = await request.get('/auth/me')
    if (resMe) {
      userProfile.value = resMe
    }
  } catch (e) {}
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.home-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 32px 24px;
}

/* Hero Section */
.hero-section {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 48px;
  align-items: center;
  padding: 32px 0 48px;
}

.hero-title {
  font-size: 46px;
  font-weight: 900;
  color: var(--color-primary);
  line-height: 1.2;
  margin-bottom: 16px;
  letter-spacing: -0.5px;
}

.hero-subtitle {
  font-size: 16px;
  color: var(--color-text-regular);
  line-height: 1.8;
  margin-bottom: 28px;
  max-width: 580px;
}

.hero-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 40px;
}

.btn-ai {
  border: 1px solid var(--color-gold);
  background: rgba(214, 168, 92, 0.1);
  color: #8C6212;
  font-weight: 600;
  border-radius: var(--radius-btn);
}

.btn-ai:hover {
  background: rgba(214, 168, 92, 0.2);
  border-color: var(--color-gold);
}

.stats-strip {
  display: flex;
  align-items: center;
  background: var(--color-paper-card);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 16px 24px;
  box-shadow: var(--shadow-soft);
}

.stat-item {
  flex: 1;
  text-align: center;
}

.stat-num {
  display: block;
  font-size: 22px;
  font-weight: 800;
  color: var(--color-primary);
}

.stat-label {
  font-size: 11px;
  color: var(--color-text-secondary);
}

.stat-divider {
  width: 1px;
  height: 32px;
  background: var(--color-border);
}

.visual-card {
  padding: 14px;
  overflow: hidden;
}

.visual-img {
  width: 100%;
  height: 320px;
  object-fit: cover;
  border-radius: 12px;
  margin-bottom: 14px;
}

.visual-caption h4 {
  font-size: 18px;
  color: var(--color-text-main);
  margin: 6px 0 4px;
}

.visual-caption p {
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* Apprentice Bar */
.section-apprentice {
  margin: 20px 0 48px;
}

.apprentice-card {
  padding: 20px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 32px;
}

.apprentice-left {
  display: flex;
  align-items: center;
  gap: 20px;
  flex: 1;
}

.avatar-box {
  position: relative;
}

.badge-tag {
  position: absolute;
  bottom: -4px;
  right: -4px;
  background: var(--color-gold);
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 10px;
  border: 2px solid #fff;
}

.apprentice-info {
  flex: 1;
}

.info-title {
  margin-bottom: 8px;
}

.user-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-main);
  margin-right: 12px;
}

.school-name {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.energy-track {
  max-width: 460px;
}

.track-header {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.energy-score strong {
  color: var(--color-primary);
}

.apprentice-badges {
  display: flex;
  gap: 10px;
}

.badge-pill {
  padding: 6px 14px;
  font-size: 12px;
  border-radius: 20px;
  font-weight: 600;
}

.badge-pill.active {
  background: #FFF8EA;
  color: #8C6212;
  border: 1px solid rgba(214, 168, 92, 0.4);
}

.badge-pill.locked {
  background: #F0EAE1;
  color: #A0988E;
  border: 1px dashed var(--color-border);
}

/* Sections */
.section-courses, .section-ai-entry {
  margin-bottom: 56px;
}

.section-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 24px;
}

.section-title {
  font-size: 26px;
  font-weight: 800;
  color: var(--color-primary);
  margin-bottom: 4px;
}

.section-desc {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.view-all-link {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-primary);
  text-decoration: none;
}

.view-all-link:hover {
  text-decoration: underline;
}

/* Courses Grid */
.course-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.course-card {
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.course-thumb {
  position: relative;
  height: 160px;
  overflow: hidden;
}

.course-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.course-card:hover .course-thumb img {
  transform: scale(1.05);
}

.category-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(31, 30, 27, 0.75);
  backdrop-filter: blur(4px);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 4px;
}

.course-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.course-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text-main);
  margin-bottom: 6px;
  line-height: 1.4;
}

.course-sub {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 14px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.course-footer {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 12px;
}

.reward {
  color: #B45309;
  font-weight: 700;
}

.course-play-btn {
  display: block;
  text-align: center;
  padding: 8px;
  background: var(--color-primary);
  color: #fff;
  text-decoration: none;
  border-radius: var(--radius-btn);
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.course-play-btn:hover {
  background: var(--color-primary-light);
}

/* AI Tools Grid */
.ai-tools-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.ai-tool-card {
  padding: 24px;
  text-decoration: none;
  color: inherit;
  display: flex;
  flex-direction: column;
}

.tool-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  margin-bottom: 16px;
}

.shadow-icon { background: rgba(139, 74, 47, 0.12); }
.bronze-icon { background: rgba(44, 79, 84, 0.12); }
.ballad-icon { background: rgba(214, 168, 92, 0.15); }
.lacquer-icon { background: rgba(31, 30, 27, 0.1); }

.ai-tool-card h3 {
  font-size: 18px;
  color: var(--color-text-main);
  margin-bottom: 8px;
}

.ai-tool-card p {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin-bottom: 20px;
  flex: 1;
}

.tool-action {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-primary);
}
</style>
