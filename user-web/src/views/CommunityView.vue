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

    <!-- 筛选与排序 -->
    <div class="filter-bar paper-card">
      <div class="tabs-group">
        <button 
          v-for="s in sortOptions" 
          :key="s.key"
          :class="['sort-tab', { active: currentSort === s.key }]"
          @click="currentSort = s.key; fetchPosts()"
        >
          {{ s.label }}
        </button>
      </div>

      <div class="category-pills">
        <span 
          v-for="c in categories" 
          :key="c.key"
          :class="['pill', { active: currentCategory === c.key }]"
          @click="currentCategory = c.key; fetchPosts()"
        >
          {{ c.label }}
        </span>
      </div>
    </div>

    <!-- 瀑布流作品列表 -->
    <div v-loading="loading" class="posts-grid">
      <div 
        v-for="post in posts" 
        :key="post.id" 
        class="paper-card post-card"
        @click="openPostDetail(post.id)"
      >
        <div class="post-cover">
          <img :src="post.cover_url" :alt="post.title" />
          <span v-if="post.heritage_master_like" class="master-badge">
            ❖ 非遗大师点赞
          </span>
          <span v-if="post.is_featured" class="featured-badge">
            ★ 精选
          </span>
        </div>

        <div class="post-body">
          <h3 class="post-title font-serif">{{ post.title }}</h3>
          <p class="post-content">{{ post.content }}</p>

          <div class="post-meta">
            <div class="author-info">
              <el-avatar :size="24" :src="post.author?.avatar_url || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150'" />
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
    <el-drawer v-model="detailDrawer" size="560px" :show-close="true">
      <template #header>
        <h3 class="font-serif drawer-title">{{ activePost?.title }}</h3>
      </template>

      <div v-if="activePost" class="drawer-content">
        <img :src="activePost.cover_url" class="drawer-cover" />
        <div class="drawer-author-bar">
          <el-avatar :size="36" :src="activePost.author?.avatar_url" />
          <div>
            <div class="author-name-lg font-serif">{{ activePost.author?.nickname }}</div>
            <div class="author-time">{{ activePost.created_at }} · 乡村美育创作</div>
          </div>
        </div>

        <p class="drawer-text">{{ activePost.content }}</p>

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
  cover_url: 'https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=600',
  content: ''
})

const sortOptions = [
  { key: 'latest', label: '最新发布' },
  { key: 'featured', label: '★ 名师精选' },
  { key: 'hot', label: '♥ 热门互动' }
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
    let url = `/community/posts?sort=${currentSort.value}&page=1&pageSize=20`
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
</style>
