<template>
  <div class="community-view">
    <el-tabs v-model="activeTab" @tab-change="loadCurrentTab">
      <el-tab-pane label="作品审核" name="posts" />
      <el-tab-pane label="评论审核" name="comments" />
      <el-tab-pane label="举报处理" name="reports" />
    </el-tabs>
    <el-card v-if="activeTab === 'posts'" shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span class="header-title">🛡️ 社区风控中心 (A-05)</span>
          <div>
            <el-radio-group v-model="filterStatus" size="small" @change="fetchPosts">
              <el-radio-button label="PENDING_REVIEW">待复核队列</el-radio-button>
              <el-radio-button label="APPROVED">已过审作品</el-radio-button>
              <el-radio-button label="REJECTED">已拦截违规</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </template>

      <el-table :data="posts" v-loading="loading" style="width: 100%" stripe>
        <el-table-column prop="post_id" label="ID" width="70" />
        <el-table-column label="作品封面" width="100">
          <template #default="{ row }">
            <el-image
              :src="row.cover_url"
              style="width: 60px; height: 60px; border-radius: 6px;"
              fit="cover"
              :preview-src-list="[row.cover_url]"
            />
          </template>
        </el-table-column>
        <el-table-column prop="title" label="作品标题" min-width="170">
          <template #default="{ row }">
            <div style="font-weight: 500;">{{ row.title }}</div>
            <div v-if="row.is_co_creation" style="margin-top: 4px;">
              <el-tag size="small" type="warning" effect="plain" style="border-color: #C1272D; color: #C1272D;">
                🤝 城乡手拉手共创
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="非遗门类" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ formatCategory(row.category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创作者信息" width="160">
          <template #default="{ row }">
            <div v-if="row.is_co_creation">
              <div style="font-size: 13px; color: #8B4A2F;">乡村: {{ row.rural_author_name || row.author_name }}</div>
              <div style="font-size: 12px; color: #4A7A60;">城市: {{ row.co_creator_name || '赋能者' }}</div>
            </div>
            <div v-else>{{ row.author_name }}</div>
          </template>
        </el-table-column>
        <el-table-column label="风控风险评级" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.risk_level === 'HIGH'" type="danger" effect="dark">高风险拦截</el-tag>
            <el-tag v-else-if="row.risk_level === 'MEDIUM'" type="warning">疑似涉敏</el-tag>
          <el-tag v-else-if="row.risk_level === 'LOW'" type="success">低风险提示</el-tag>
          <el-tag v-else type="info">未评估</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交时间" width="160" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openDrawer(row)">审阅详情</el-button>
            <el-button v-if="filterStatus === 'PENDING_REVIEW'" size="small" type="success" link @click="doAction(row.post_id, 'APPROVE')">通过</el-button>
            <el-button v-if="filterStatus === 'PENDING_REVIEW'" size="small" type="danger" link @click="doAction(row.post_id, 'REJECT')">驳回</el-button>
            <el-button v-if="filterStatus === 'APPROVED'" size="small" type="warning" link @click="doAction(row.post_id, 'FEATURE')">精选</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 右侧审阅抽屉 -->
    <el-drawer v-model="drawerVisible" title="作品人工审核" size="480px">
      <div v-if="currentRow" class="drawer-body">
        <el-image :src="currentRow.cover_url" fit="contain" style="width: 100%; max-height: 280px; border-radius: 8px; background: #000;" />
        <h3 style="margin-top: 15px; color: #2F2925;">{{ currentRow.title }}</h3>
        <p style="color: #776D65; font-size: 14px; line-height: 22px;">{{ currentRow.content }}</p>

        <el-divider>审核记录</el-divider>
        <p>风险级别：{{ currentRow.risk_level || '未评估' }}</p>
        <p v-if="currentRow.ai_analysis && Object.keys(currentRow.ai_analysis).length">{{ currentRow.ai_analysis }}</p>
        <p v-else>暂无模型分析记录，请人工核验作品内容。</p>

        <div v-if="filterStatus === 'PENDING_REVIEW'" style="margin-top: 30px; display: flex; gap: 12px; justify-content: flex-end;">
          <el-button type="danger" @click="doAction(currentRow.post_id, 'REJECT')">驳回</el-button>
          <el-button type="primary" style="background-color: #8B4A2F; border-color: #8B4A2F;" @click="doAction(currentRow.post_id, 'APPROVE')">审核通过并公开展出</el-button>
        </div>
      </div>
    </el-drawer>

    <el-card v-if="activeTab === 'comments'" shadow="never" class="table-card">
      <template #header>评论审核</template>
      <el-radio-group v-model="commentStatus" size="small" @change="fetchComments">
        <el-radio-button label="PENDING_REVIEW">待审核</el-radio-button>
        <el-radio-button label="APPROVED">已公开</el-radio-button>
        <el-radio-button label="REJECTED">已驳回</el-radio-button>
      </el-radio-group>
      <el-table :data="comments" v-loading="loading" stripe>
        <el-table-column prop="id" label="评论 ID" width="100" />
        <el-table-column prop="post_id" label="作品 ID" width="100" />
        <el-table-column prop="content" label="评论内容" min-width="300" />
        <el-table-column prop="created_at" label="提交时间" width="190" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button v-if="commentStatus === 'PENDING_REVIEW'" link type="success" @click="reviewComment(row.id, 'APPROVE')">通过</el-button>
            <el-button v-if="commentStatus === 'PENDING_REVIEW'" link type="danger" @click="reviewComment(row.id, 'REJECT')">驳回</el-button>
            <el-button v-if="commentStatus === 'APPROVED'" link type="warning" @click="reviewComment(row.id, 'OFFLINE')">下线</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-if="activeTab === 'reports'" shadow="never" class="table-card">
      <template #header>举报处理</template>
      <el-radio-group v-model="reportStatus" size="small" @change="fetchReports">
        <el-radio-button label="PENDING">待处理</el-radio-button>
        <el-radio-button label="HANDLED">已处理</el-radio-button>
        <el-radio-button label="REJECTED">已驳回</el-radio-button>
      </el-radio-group>
      <el-table :data="reports" v-loading="loading" stripe>
        <el-table-column prop="id" label="举报 ID" width="100" />
        <el-table-column prop="post_id" label="作品 ID" width="100" />
        <el-table-column prop="reason" label="原因" width="140" />
        <el-table-column prop="description" label="说明" min-width="260" />
        <el-table-column prop="created_at" label="提交时间" width="190" />
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button v-if="reportStatus === 'PENDING'" link type="warning" @click="handleReport(row.id, 'DISMISS')">驳回举报</el-button>
            <el-button v-if="reportStatus === 'PENDING'" link type="primary" @click="handleReport(row.id, 'RESOLVE')">已处理</el-button>
            <el-button v-if="reportStatus === 'PENDING'" link type="danger" @click="handleReport(row.id, 'OFFLINE_POST')">下线作品</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/api/request'
import { ElMessage, ElMessageBox } from 'element-plus'

const activeTab = ref('posts')
const filterStatus = ref('PENDING_REVIEW')
const posts = ref<any[]>([])
const commentStatus = ref('PENDING_REVIEW')
const comments = ref<any[]>([])
const reportStatus = ref('PENDING')
const reports = ref<any[]>([])
const loading = ref(false)
const drawerVisible = ref(false)
const currentRow = ref<any>(null)

const formatCategory = (cat: string) => {
  const map: Record<string, string> = {
    'SHADOW_PUPPET': '津门皮影',
    'PAINTING': '杨柳青年画',
    'CLAY': '泥人张彩塑',
    'BRONZE': '青铜神兽纹样',
    'BALLAD': '骆派京韵大鼓',
    'LACQUER': '古法大漆螺钿'
  }
  return map[cat] || cat
}

const fetchPosts = async () => {
  loading.value = true
  try {
    const res: any = await request.get(`/admin/reviews?status=${filterStatus.value}`)
    posts.value = res || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const fetchComments = async () => {
  loading.value = true
  try {
    comments.value = await request.get('/admin/comment-reviews', { status: commentStatus.value })
  } catch { ElMessage.error('评论列表加载失败') }
  finally { loading.value = false }
}

const fetchReports = async () => {
  loading.value = true
  try {
    reports.value = await request.get('/admin/reports', { status: reportStatus.value })
  } catch { ElMessage.error('举报列表加载失败') }
  finally { loading.value = false }
}

const loadCurrentTab = () => {
  if (activeTab.value === 'comments') fetchComments()
  else if (activeTab.value === 'reports') fetchReports()
  else fetchPosts()
}

const reviewComment = async (id: number, action: string) => {
  try {
    const { value: comment } = await ElMessageBox.prompt('填写审核说明', '评论审核', {
      inputValue: action === 'APPROVE' ? '审核通过' : '内容不适合公开',
      inputValidator: value => !!value.trim() || '请填写审核说明'
    })
    const result: any = await request.post(`/admin/comment-reviews/${id}/action`, { action, comment })
    if (result?.code && result.code !== 0) throw new Error(result.message)
    ElMessage.success('评论审核已保存')
    fetchComments()
  } catch (error: any) {
    if (error !== 'cancel' && error !== 'close') ElMessage.error(error?.message || '评论审核失败')
  }
}

const handleReport = async (id: number, action: string) => {
  try {
    const { value: note } = await ElMessageBox.prompt('填写处理说明', '处理举报', {
      inputValue: action === 'DISMISS' ? '举报依据不足' : '已核查处理',
      inputValidator: value => !!value.trim() || '请填写处理说明'
    })
    const result: any = await request.post(`/admin/reports/${id}/action`, { action, note })
    if (result?.code && result.code !== 0) throw new Error(result.message)
    ElMessage.success('举报处理已保存')
    fetchReports()
  } catch (error: any) {
    if (error !== 'cancel' && error !== 'close') ElMessage.error(error?.message || '举报处理失败')
  }
}

const openDrawer = (row: any) => {
  currentRow.value = row
  drawerVisible.value = true
}

const doAction = async (postId: number, action: string) => {
  try {
    const result: any = await request.post(`/admin/reviews/${postId}/action`, { action, comment: '管理员后台处理' })
    if (result?.code && result.code !== 0) throw new Error(result.message)
    ElMessage.success('操作已生效')
    drawerVisible.value = false
    fetchPosts()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

onMounted(() => {
  fetchPosts()
})
</script>

<style scoped>
.table-card {
  border-radius: 12px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-title {
  font-weight: 600;
  color: #2F2925;
}
</style>
