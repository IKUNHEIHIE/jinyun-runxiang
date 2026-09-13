<template>
  <div class="community-page">
    <div class="page-header">
      <div>
        <h1 class="page-title font-serif">美育社区广场 · 乡土非遗创客集</h1>
        <p class="page-sub">
          汇聚天津各乡村中小学孩子们的非遗手工实物与 AI 灵感作品，交流研学心得，接受国家级非遗大师点赞指导
        </p>
      </div>
      <el-button type="primary" size="large" class="btn-primary" @click="publishModal = true">
        <el-icon class="mr-1"><EditPen /></el-icon> 我要发布非遗作品
      </el-button>
    </div>

    <!-- 筛选与排序 (Element Plus 工业级规范) -->
    <div class="filter-bar paper-card">
      <div class="tabs-group">
        <el-segmented 
          v-model="currentSort" 
          :options="sortOptions.map(s => ({ label: s.label, value: s.key }))"
          @change="fetchPosts"
        />
      </div>

      <div class="category-pills">
        <el-check-tag 
          v-for="c in categories" 
          :key="c.key"
          :checked="currentCategory === c.key"
          @change="() => { currentCategory = c.key; fetchPosts(); }"
          class="heritage-check-tag"
        >
          {{ c.label }}
        </el-check-tag>
      </div>
    </div>

    <!-- 骨架屏加载状态 -->
    <div v-if="loading" class="posts-grid">
      <div v-for="i in 6" :key="i" class="paper-card post-skeleton-card">
        <el-skeleton animated>
          <template #template>
            <el-skeleton-item variant="image" style="width: 100%; height: 200px; border-radius: 12px 12px 0 0;" />
            <div style="padding: 14px;">
              <el-skeleton-item variant="h3" style="width: 70%;" />
              <el-skeleton-item variant="text" style="width: 90%; margin-top: 10px;" />
              <el-skeleton-item variant="text" style="width: 50%; margin-top: 10px;" />
            </div>
          </template>
        </el-skeleton>
      </div>
    </div>

    <!-- 瀑布流作品列表 -->
    <div v-else class="posts-grid">
      <div 
        v-for="post in posts" 
        :key="post.id" 
        class="paper-card post-card"
        @click="openPostDetail(post.id)"
      >
        <div class="post-cover">
          <img :src="post.cover_url" :alt="post.title" @error="handleImageError" />
          <span v-if="post.is_co_creation" class="co-badge">
            🤝 城乡手拉手共创
          </span>
          <span v-if="post.heritage_master_like" class="master-badge">
            ❖ 非遗大师点赞
          </span>
          <span v-if="post.is_featured" class="featured-badge">
            ★ 精选
          </span>
        </div>

        <div class="post-body">
          <h3 class="post-title font-serif">{{ post.title }}</h3>
          
          <!-- 城乡手拉手双创作者标识 -->
          <div v-if="post.is_co_creation" class="dual-author-chip-box">
            <span class="chip-label rural">🌾 原作: {{ post.rural_author_name }} ({{ post.rural_school }})</span>
            <span class="chip-arrow">➔</span>
            <span class="chip-label urban">🎨 赋能: {{ post.co_creator_name }}</span>
          </div>

          <p class="post-content">{{ post.content }}</p>

          <div class="post-meta">
            <div class="author-info">
              <el-avatar :size="24" :src="post.author?.avatar_url || '/static/images/default_avatar.svg'" />
              <span class="author-name">{{ post.author?.nickname || '非遗学徒' }}</span>
            </div>

            <div class="interact-info" @click.stop>
              <button class="like-btn" @click="toggleLike(post)">
                <span :class="['heart', { liked: post.is_liked }]">♥</span>
                <span>{{ post.like_count || 0 }}</span>
              </button>
              <span class="comment-count">💬 {{ post.comment_count || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 帖子详情与评论抽屉 -->
    <el-drawer v-model="detailDrawer" size="580px" :show-close="true">
      <template #header>
        <h3 class="font-serif drawer-title">{{ activePost?.title }}</h3>
      </template>

      <div v-if="activePost" class="drawer-content">
        <!-- 城乡手拉手专属横幅与对比展示 -->
        <div v-if="activePost.is_co_creation" class="co-creation-drawer-banner">
          <div class="co-banner-header">
            <span class="co-banner-seal">🤝</span>
            <div>
              <strong>津门美育·城乡手拉手双生共创成果</strong>
              <p>乡村学童创意白模 × 城市高校/中小学数字化艺术套色赋能</p>
            </div>
          </div>
          <div class="co-dual-flow">
            <div class="co-flow-node rural">
              <span class="flow-role">🌾 乡村原创</span>
              <span class="flow-name">{{ activePost.rural_author_name || '乡村学子' }}</span>
              <span class="flow-school">{{ activePost.rural_school || '蓟州区乡村教学点' }}</span>
            </div>
            <div class="co-flow-arrow">➔ 数字化转译 ➔</div>
            <div class="co-flow-node urban">
              <span class="flow-role">🎨 城市赋能</span>
              <span class="flow-name">{{ activePost.co_creator_name || activePost.author?.nickname }}</span>
              <span class="flow-school">{{ activePost.co_creator_school || '天津市区实验学堂' }}</span>
            </div>
          </div>
          <div v-if="activePost.rural_original_url" class="dual-images-compare">
            <div class="compare-box">
              <span class="compare-title">🌾 乡村原作图谱/白模</span>
              <img :src="activePost.rural_original_url" class="compare-img" @error="handleImageError" />
            </div>
            <div class="compare-box">
              <span class="compare-title">🎨 城市赋能定稿</span>
              <img :src="activePost.cover_url" class="compare-img" @error="handleImageError" />
            </div>
          </div>
        </div>

        <img v-else :src="activePost.cover_url" class="drawer-cover" @error="handleImageError" />
        
        <div class="drawer-author-bar">
          <el-avatar :size="36" :src="activePost.author?.avatar_url || '/static/images/default_avatar.svg'" />
          <div>
            <div class="author-name-lg font-serif">{{ activePost.author?.nickname }}</div>
            <div class="author-time">{{ activePost.created_at }} · 乡村美育创作</div>
          </div>
        </div>

        <p class="drawer-text">{{ activePost.content }}</p>

        <!-- 针对未共创的乡村原生作品，提供接力共创入口 -->
        <div v-if="!activePost.is_co_creation" class="co-create-invite-box">
          <div class="invite-info">
            <div class="invite-title">🤝 开启城乡手拉手接力共创</div>
            <div class="invite-sub">城市师生、高校青年志愿者可认领此作，为乡村孩子的线稿进行数字化重构与五彩赋能！</div>
          </div>
          <el-button type="warning" round @click="openCoCreateModal(activePost)">
            🤝 我来接力共创
          </el-button>
        </div>

        <!-- 评论列表 -->
        <h4 class="font-serif comments-header">师生交流与点评 ({{ activePost.comments?.length || 0 }})</h4>
        <div class="comments-list">
          <div v-for="c in activePost.comments" :key="c.id" class="comment-item">
            <el-avatar :size="28" :src="c.user?.avatar_url" />
            <div class="comment-bubble">
              <div class="comment-user">{{ c.user?.nickname }}</div>
              <div class="comment-msg">{{ c.content }}</div>
            </div>
          </div>
        </div>

        <!-- 评论输入框 -->
        <div class="comment-input-bar">
          <el-input 
            v-model="commentInput" 
            placeholder="写下您的鼓励或工艺见解..." 
            size="large"
            @keyup.enter="submitComment"
          />
          <el-button type="primary" class="btn-primary" @click="submitComment">发表评论</el-button>
        </div>
      </div>
    </el-drawer>

    <!-- 发布作品弹窗 -->
    <el-dialog v-model="publishModal" title="发布我的乡村非遗手作/AI设计" width="560px">
      <el-form label-position="top">
        <el-form-item label="作品标题">
          <el-input v-model="newPost.title" placeholder="给作品起一个响亮的名字，如：下营小学皮影小哪吒" />
        </el-form-item>
        <el-form-item label="非遗门类">
          <el-select v-model="newPost.category" class="w-full">
            <el-option label="津派皮影戏" value="SHADOW_PUPPET" />
            <el-option label="汉沽版画 / 杨柳青年画" value="PAINTING" />
            <el-option label="泥人张彩塑 / 面塑" value="CLAY" />
            <el-option label="青铜神兽纹样" value="BRONZE" />
            <el-option label="古法大漆螺钿" value="LACQUER" />
          </el-select>
        </el-form-item>
        <el-form-item label="作品封面图片 URL">
          <el-input v-model="newPost.cover_url" placeholder="图片网络地址或使用默认美育图片" />
        </el-form-item>
        <el-form-item label="创作心得与设计理念">
          <el-input 
            v-model="newPost.content" 
            type="textarea" 
            :rows="4" 
            placeholder="讲述你在微课或AI工坊学到了什么，或者手作时克服了哪些工序难关..."
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="publishModal = false">取消</el-button>
        <el-button type="primary" class="btn-primary" :loading="publishing" @click="submitPost">
          提交审核发布 (+30 能量)
        </el-button>
      </template>
    </el-dialog>

    <!-- 🤝 城乡手拉手接力共创弹窗 (P3) -->
    <el-dialog v-model="coCreateModal" title="🤝 城乡手拉手 · 乡村非遗线稿接力赋能" width="600px">
      <div class="co-dialog-header">
        <div class="co-dialog-intro">
          您正在接力认领来自乡村学童 <strong>【{{ activePost?.rural_author_name || activePost?.author?.nickname }}】</strong> 的原创非遗作品。
          请填入您的城市共创团队信息及数字化重构/套色方案，共绘城乡美育结对画卷！
        </div>
      </div>
      <el-form label-position="top">
        <el-form-item label="城市接力创作者姓名">
          <el-input v-model="coCreateForm.co_creator_name" placeholder="例如：天津市实验中学 美育社团 / 王艺同学" />
        </el-form-item>
        <el-form-item label="所属结对学校 / 志愿组织">
          <el-input v-model="coCreateForm.co_creator_school" placeholder="例如：天津美术学院青年志愿服务队" />
        </el-form-item>
        <el-form-item label="数字化上色与重构成果图 URL">
          <el-input v-model="coCreateForm.colored_cover_url" placeholder="图片网络地址或使用平台推荐杨柳青矿物五彩图" />
        </el-form-item>
        <el-form-item label="城市赋能心得与设计寄语">
          <el-input 
            v-model="coCreateForm.co_note" 
            type="textarea" 
            :rows="3" 
            placeholder="写给乡村原作者小朋友的心里话，讲述你如何为这幅作品进行了色彩重塑与数字传承..."
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="coCreateModal = false">取消</el-button>
        <el-button type="primary" style="background: #8B4A2F; border-color: #8B4A2F;" :loading="coCreateSubmitting" @click="submitCoCreation">
          🤝 确认提交城乡共创成果 (+50 能量)
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../api/request'

const loading = ref(false)
const posts = ref<any[]>([])
const currentSort = ref('latest')
const currentCategory = ref('')

const detailDrawer = ref(false)
const activePost = ref<any>(null)
const commentInput = ref('')

const publishModal = ref(false)
const publishing = ref(false)
const newPost = ref({
  title: '',
  category: 'SHADOW_PUPPET',
  cover_url: '/static/images/shadow_puppet_1.svg',
  content: ''
})

// 🤝 城乡手拉手共创接力状态
const coCreateModal = ref(false)
const coCreateSubmitting = ref(false)
const coCreateForm = ref({
  co_creator_name: '',
  co_creator_school: '',
  colored_cover_url: '',
  co_note: ''
})

const openCoCreateModal = (post: any) => {
  coCreateForm.value = {
    co_creator_name: '天津美术学院 青年美育志愿队',
    co_creator_school: '天津美术学院中国画学院',
    colored_cover_url: post.cover_url || '/static/images/shadow_puppet_sheng.svg',
    co_note: '基于小朋友灵动质朴的线稿轮廓，采用了杨柳青传统品红与槐黄矿物颜料套色，增强了光影层次。'
  }
  coCreateModal.value = true
}

const submitCoCreation = async () => {
  if (!coCreateForm.value.co_creator_name || !coCreateForm.value.co_note) {
    ElMessage.warning('请填写城市共创者信息及赋能心得')
    return
  }
  coCreateSubmitting.value = true
  try {
    const res: any = await request.post(`/community/posts/${activePost.value.id}/co-create`, coCreateForm.value)
    ElMessage.success(res.message || '城乡双生共创作品发布成功！美育微光 +50 点！')
    coCreateSubmitting.value = false
    coCreateModal.value = false
    detailDrawer.value = false
    currentSort.value = 'co_creation'
    fetchPosts()
  } catch (err: any) {
    coCreateSubmitting.value = false
    ElMessage.error(err.response?.data?.message || '共创提交失败')
  }
}

const handleImageError = (e: Event) => {
  const target = e.target as HTMLImageElement
  if (target && target.src && !target.src.endsWith('/static/images/shadow_puppet_1.svg')) {
    target.src = '/static/images/shadow_puppet_1.svg'
  }
}

const sortOptions = [
  { key: 'latest', label: '最新发布' },
  { key: 'featured', label: '★ 名师精选' },
  { key: 'hot', label: '♥ 热门互动' },
  { key: 'co_creation', label: '🤝 城乡共创画廊' }
]

const categories = [
  { key: '', label: '全部门类' },
  { key: 'SHADOW_PUPPET', label: '津派皮影' },
  { key: 'PAINTING', label: '年画版画' },
  { key: 'CLAY', label: '泥人彩塑' },
  { key: 'BRONZE', label: '青铜金石' }
]

const fetchPosts = async () => {
  loading.value = true
  try {
    let url = `/community/posts?page=1&pageSize=20`
    if (currentSort.value === 'co_creation') {
      url += `&is_co_creation=true`
    } else {
      url += `&sort=${currentSort.value}`
    }
    if (currentCategory.value) url += `&category=${currentCategory.value}`
    const res: any = await request.get(url)
    if (res && res.list) {
      posts.value = res.list
    }
  } catch (e) {
  } finally {
    loading.value = false
  }
}

const openPostDetail = async (id: number) => {
  try {
    const res: any = await request.get(`/community/posts/${id}`)
    activePost.value = res
    detailDrawer.value = true
  } catch (e) {
    ElMessage.error('加载作品详情失败')
  }
}

const toggleLike = async (post: any) => {
  try {
    const res: any = await request.post(`/community/posts/${post.id}/like`, {})
    post.like_count = res.like_count
    post.is_liked = res.is_liked
    ElMessage.success(res.is_liked ? '点赞成功！' : '已取消点赞')
  } catch (e) {
    ElMessage.error('点赞失败')
  }
}

const submitComment = async () => {
  if (!commentInput.value.trim() || !activePost.value) return
  try {
    await request.post(`/community/posts/${activePost.value.id}/comments`, {
      content: commentInput.value
    })
    ElMessage.success('评论发表成功！')
    commentInput.value = ''
    openPostDetail(activePost.value.id)
  } catch (e) {
    ElMessage.error('评论失败')
  }
}

const submitPost = async () => {
  if (!newPost.value.title || !newPost.value.content) {
    ElMessage.warning('请填写作品标题与心得')
    return
  }

  // 敏感词预检
  const sensitives = ['暴力', '赌博', '违规']
  const hasSen = sensitives.some(s => newPost.value.title.includes(s) || newPost.value.content.includes(s))

  publishing.value = true
  try {
    const res: any = await request.post('/community/posts', newPost.value)
    publishing.value = false
    publishModal.value = false
    newPost.value = {
      title: '',
      category: 'SHADOW_PUPPET',
      cover_url: 'https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=600',
      content: ''
    }

    if (hasSen) {
      ElMessage.warning('您的作品包含敏感词，已自动送交平台管理员人工复审！')
    } else {
      ElMessage.success('作品发布成功！能量值 +30')
    }
    fetchPosts()
  } catch (e) {
    publishing.value = false
    ElMessage.error('发布失败')
  }
}

onMounted(() => {
  fetchPosts()
})
</script>

<style scoped>
.community-page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 32px 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
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

.filter-bar {
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.tabs-group {
  display: flex;
  gap: 8px;
}

.sort-tab {
  background: none;
  border: none;
  font-size: 14px;
  font-weight: 600;
  padding: 6px 14px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--color-text-regular);
  transition: all 0.2s ease;
}

.sort-tab.active {
  background: var(--color-primary);
  color: #fff;
}

.category-pills {
  display: flex;
  gap: 8px;
}

.pill {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  border: 1px solid var(--color-border);
  color: var(--color-text-regular);
  cursor: pointer;
  transition: all 0.2s ease;
}

.pill.active {
  border-color: var(--color-gold);
  background: #FFF8EA;
  color: var(--color-primary);
  font-weight: 700;
}

.posts-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.post-card {
  overflow: hidden;
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.post-cover {
  position: relative;
  height: 200px;
}

.post-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.post-card:hover .post-cover img {
  transform: scale(1.04);
}

.master-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(139, 74, 47, 0.9);
  backdrop-filter: blur(4px);
  color: #FFECC8;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 4px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
}

.featured-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(214, 168, 92, 0.9);
  color: #5C3D00;
  font-size: 11px;
  font-weight: 800;
  padding: 3px 8px;
  border-radius: 4px;
}

.post-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.post-title {
  font-size: 16px;
  color: var(--color-text-main);
  margin-bottom: 6px;
  line-height: 1.4;
}

.post-content {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin-bottom: 14px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.post-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px dashed var(--color-border);
  padding-top: 12px;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.author-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-regular);
}

.interact-info {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.like-btn {
  background: none;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.heart {
  font-size: 14px;
}

.heart.liked {
  color: #E11D48;
}

/* Drawer styles */
.drawer-title {
  font-size: 20px;
  color: var(--color-primary);
}

.drawer-cover {
  width: 100%;
  height: 260px;
  object-fit: cover;
  border-radius: 12px;
  margin-bottom: 16px;
}

.drawer-author-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.author-name-lg {
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text-main);
}

.author-time {
  font-size: 11px;
  color: var(--color-text-secondary);
}

.drawer-text {
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text-regular);
  margin-bottom: 24px;
  background: var(--color-paper);
  padding: 16px;
  border-radius: 8px;
}

.comments-header {
  font-size: 16px;
  color: var(--color-text-main);
  margin-bottom: 14px;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
  max-height: 240px;
  overflow-y: auto;
}

.comment-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.comment-bubble {
  background: var(--color-paper);
  padding: 10px 14px;
  border-radius: 8px;
  flex: 1;
}

.comment-user {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-primary);
  margin-bottom: 2px;
}

.comment-msg {
  font-size: 13px;
  color: var(--color-text-regular);
}

.comment-input-bar {
  display: flex;
  gap: 10px;
}

.w-full {
  width: 100%;
}

.heritage-check-tag {
  margin-right: 8px;
  border-radius: 20px;
  cursor: pointer;
}

.post-skeleton-card {
  height: 320px;
  background-color: var(--color-paper-card);
  border-radius: var(--radius-card);
  overflow: hidden;
}

/* 🤝 城乡手拉手共创专属卡片样式 */
.co-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  background: linear-gradient(135deg, #10B981 0%, #059669 100%);
  color: #FFF;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.4);
}

.dual-author-chip-box {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 6px 0 10px;
  font-size: 11px;
  flex-wrap: wrap;
}

.chip-label {
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.chip-label.rural {
  background: #FEF3C7;
  color: #92400E;
}

.chip-label.urban {
  background: #D1FAE5;
  color: #065F46;
}

.chip-arrow {
  color: #9CA3AF;
  font-weight: 700;
}

/* 抽屉共创专属横幅 */
.co-creation-drawer-banner {
  background: linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%);
  border: 1px solid #A7F3D0;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
}

.co-banner-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.co-banner-seal {
  font-size: 24px;
}

.co-banner-header strong {
  font-size: 14px;
  color: #065F46;
  display: block;
}

.co-banner-header p {
  font-size: 11px;
  color: #047857;
  margin: 2px 0 0;
}

.co-dual-flow {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #FFF;
  border: 1px dashed #6EE7B7;
  border-radius: 8px;
  padding: 10px 14px;
  margin-bottom: 14px;
}

.co-flow-node {
  display: flex;
  flex-direction: column;
}

.flow-role {
  font-size: 10px;
  font-weight: 700;
  margin-bottom: 2px;
}

.co-flow-node.rural .flow-role {
  color: #D97706;
}

.co-flow-node.urban .flow-role {
  color: #059669;
}

.flow-name {
  font-size: 13px;
  font-weight: 700;
  color: #1F2937;
}

.flow-school {
  font-size: 10px;
  color: #6B7280;
}

.co-flow-arrow {
  font-size: 11px;
  color: #059669;
  font-weight: 600;
}

.dual-images-compare {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.compare-box {
  background: #FFF;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  padding: 8px;
  text-align: center;
}

.compare-title {
  display: block;
  font-size: 11px;
  color: #4B5563;
  font-weight: 600;
  margin-bottom: 6px;
}

.compare-img {
  width: 100%;
  height: 160px;
  object-fit: cover;
  border-radius: 6px;
}

/* 接力共创倡议条 */
.co-create-invite-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
  border: 1px solid #FDE68A;
  border-radius: 10px;
  padding: 14px 18px;
  margin-bottom: 20px;
}

.invite-title {
  font-size: 13px;
  font-weight: 700;
  color: #92400E;
}

.invite-sub {
  font-size: 11px;
  color: #B45309;
  margin-top: 3px;
  max-width: 340px;
}

.co-dialog-header {
  margin-bottom: 16px;
}

.co-dialog-intro {
  background: #F3F4F6;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.6;
  color: #374151;
}
</style>
