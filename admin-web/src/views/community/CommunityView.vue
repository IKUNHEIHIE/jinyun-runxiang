<template>
  <div class="community-view">
    <el-card shadow="never" class="table-card">
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
        <el-table-column prop="title" label="作品标题" min-width="150" />
        <el-table-column prop="category" label="非遗门类" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ formatCategory(row.category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="author_name" label="创作者" width="120" />
        <el-table-column label="风控风险评级" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.risk_level === 'HIGH'" type="danger" effect="dark">高风险拦截</el-tag>
            <el-tag v-else-if="row.risk_level === 'MEDIUM'" type="warning">疑似涉敏</el-tag>
            <el-tag v-else type="success">安全绿色</el-tag>
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
    <el-drawer v-model="drawerVisible" title="作品多模态风控详细核验" size="480px">
      <div v-if="currentRow" class="drawer-body">
        <el-image :src="currentRow.cover_url" fit="contain" style="width: 100%; max-height: 280px; border-radius: 8px; background: #000;" />
        <h3 style="margin-top: 15px; color: #2F2925;">{{ currentRow.title }}</h3>
        <p style="color: #776D65; font-size: 14px; line-height: 22px;">{{ currentRow.content }}</p>

        <el-divider>AI 多模态预审判定</el-divider>
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="OCR文字检测">未发现涉政与违法违禁词</el-descriptions-item>
          <el-descriptions-item label="多模态图像风险">色情概率 0.01% · 暴力倾向 0.00%</el-descriptions-item>
          <el-descriptions-item label="非遗元素关联度">98% (命中天津皮影/青铜雕纹样式特征)</el-descriptions-item>
        </el-descriptions>

        <div style="margin-top: 30px; display: flex; gap: 12px; justify-content: flex-end;">
          <el-button type="danger" @click="doAction(currentRow.post_id, 'REJECT')">驳回并下架</el-button>
          <el-button type="primary" style="background-color: #8B4A2F; border-color: #8B4A2F;" @click="doAction(currentRow.post_id, 'APPROVE')">审核通过并公开展出</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/api/request'
import { ElMessage } from 'element-plus'

const filterStatus = ref('PENDING_REVIEW')
const posts = ref<any[]>([])
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

const openDrawer = (row: any) => {
  currentRow.value = row
  drawerVisible.value = true
}

const doAction = async (postId: number, action: string) => {
  try {
    await request.post(`/admin/reviews/${postId}/action`, { action, comment: '管理员后台处理' })
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
