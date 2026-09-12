<template>
  <div class="content-view">
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span class="header-title">📖 非遗美育内容管理 (A-02)</span>
          <el-button type="primary" size="small" style="background-color: #8B4A2F; border-color: #8B4A2F;" @click="showAddDialog = true">+ 新建非遗课程</el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="非遗微课库" name="courses">
          <el-table :data="courses" style="width: 100%" stripe v-loading="loadingCourses">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column label="封面" width="100">
              <template #default="{ row }">
                <el-image :src="row.cover_url" style="width: 70px; height: 45px; border-radius: 4px;" fit="cover" />
              </template>
            </el-table-column>
            <el-table-column prop="title" label="课程标题" min-width="180" />
            <el-table-column label="门类" width="130">
              <template #default="{ row }">
                <el-tag size="small">{{ formatCategory(row.category) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="age_group" label="适用学段" width="120">
              <template #default="{ row }">
                <el-tag size="small" type="info">{{ row.age_group }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="duration_minutes" label="时长(分)" width="90" />
            <el-table-column prop="energy_reward" label="通关能量" width="90">
              <template #default="{ row }">
                <span style="color: #D6A85C; font-weight: bold;">+{{ row.energy_reward }}</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'PUBLISHED' ? 'success' : 'danger'" size="small">
                  {{ row.status === 'PUBLISHED' ? '已上线' : '已下架' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="primary" link @click="viewChapters(row)">章节详情</el-button>
                <el-button 
                  size="small" 
                  :type="row.status === 'PUBLISHED' ? 'danger' : 'success'" 
                  link 
                  @click="handleToggleStatus(row)"
                >
                  {{ row.status === 'PUBLISHED' ? '下架' : '重新上架' }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="民俗节日日历" name="festivals">
          <el-timeline style="margin-top: 15px;">
            <el-timeline-item timestamp="农历正月十五" placement="top" color="#8B4A2F">
              <el-card>
                <h4>杨柳青元宵灯会与年画展</h4>
                <p>展出经典明清木版套印画样，乡村小学组织实地研学采风与拓印体验。</p>
              </el-card>
            </el-timeline-item>
            <el-timeline-item timestamp="农历八月十五" placement="top" color="#D6A85C">
              <el-card>
                <h4>津门中秋拜月与兔子王泥塑节</h4>
                <p>学习泥人张兔子王彩塑技法，体味津派民间雕塑的神韵。</p>
              </el-card>
            </el-timeline-item>
            <el-timeline-item timestamp="农历五月初五" placement="top" color="#409EFF">
              <el-card>
                <h4>海河端午龙舟竞渡非遗展演</h4>
                <p>津派传统龙舟模型制作与水上非遗展演，弘扬团结协作与坚韧不拔的津沽精神。</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 新建课程弹窗 -->
    <el-dialog v-model="showAddDialog" title="新建非遗美育课程" width="550px">
      <el-form label-width="90px">
        <el-form-item label="课程名称" required>
          <el-input v-model="newCourse.title" placeholder="如：津门皮影戏制作工坊" />
        </el-form-item>
        <el-form-item label="副标题">
          <el-input v-model="newCourse.subtitle" placeholder="如：从选皮雕刻到光影演绎" />
        </el-form-item>
        <el-form-item label="非遗门类">
          <el-select v-model="newCourse.category" placeholder="请选择门类" style="width: 100%">
            <el-option label="津门皮影" value="SHADOW_PUPPET" />
            <el-option label="杨柳青年画" value="PAINTING" />
            <el-option label="泥人张彩塑" value="CLAY" />
            <el-option label="青铜神兽" value="BRONZE" />
            <el-option label="风筝魏制作" value="KITE" />
            <el-option label="民俗礼仪" value="FOLK_CUSTOM" />
          </el-select>
        </el-form-item>
        <el-form-item label="适用学段">
          <el-radio-group v-model="newCourse.age_group">
            <el-radio label="小学低段">小学低段</el-radio>
            <el-radio label="小学高段">小学高段</el-radio>
            <el-radio label="初中阶段">初中阶段</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-row :gutter="15">
          <el-col :span="12">
            <el-form-item label="课程时长">
              <el-input-number v-model="newCourse.duration_minutes" :min="5" :max="180" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="通关能量">
              <el-input-number v-model="newCourse.energy_reward" :min="5" :max="500" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="课程简介">
          <el-input v-model="newCourse.description" type="textarea" :rows="3" placeholder="请输入课程主要知识点与教学目标" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" style="background-color: #8B4A2F; border-color: #8B4A2F;" @click="handleCreateCourse">确认发布</el-button>
      </template>
    </el-dialog>

    <!-- 章节详情抽屉 -->
    <el-drawer v-model="chapterDrawer" :title="`章节列表 - ${currentCourse?.title || ''}`" size="420px">
      <div v-loading="loadingChapters">
        <el-alert
          :title="`门类：${formatCategory(currentCourse?.category || '')} | 适用学段：${currentCourse?.age_group || ''}`"
          type="info"
          :closable="false"
          style="margin-bottom: 15px;"
        />
        <div v-if="courseChapters.length === 0" style="text-align: center; color: #999; margin-top: 40px;">
          暂无独立微课章节，默认包含主微课导学视频
        </div>
        <el-timeline v-else style="margin-top: 10px;">
          <el-timeline-item
            v-for="(item, idx) in courseChapters"
            :key="item.id || idx"
            :timestamp="`第 ${idx + 1} 讲 · ${item.duration_seconds ? Math.floor(item.duration_seconds / 60) + '分钟' : '10分钟'}`"
            placement="top"
          >
            <div style="font-weight: 500; font-size: 14px; margin-bottom: 4px;">{{ item.title }}</div>
            <div style="font-size: 12px; color: #888;">{{ item.video_url || '非遗数字导学资源' }}</div>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const activeTab = ref('courses')
const courses = ref<any[]>([])
const loadingCourses = ref(false)
const showAddDialog = ref(false)
const submitting = ref(false)

const newCourse = ref({
  title: '',
  subtitle: '非遗传统技艺微课',
  category: 'SHADOW_PUPPET',
  age_group: '小学低段',
  duration_minutes: 30,
  energy_reward: 30,
  cover_url: 'https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=600',
  description: '通过生动趣味的数字化动画与动手体验，引导青少年感受中华优秀传统文化的魅力。'
})

const chapterDrawer = ref(false)
const currentCourse = ref<any>(null)
const courseChapters = ref<any[]>([])
const loadingChapters = ref(false)

const formatCategory = (cat: string) => {
  const map: Record<string, string> = {
    'SHADOW_PUPPET': '津门皮影',
    'PAINTING': '杨柳青年画',
    'CLAY': '泥人张彩塑',
    'BRONZE': '青铜神兽',
    'KITE': '风筝魏制作',
    'FOLK_CUSTOM': '民俗礼仪'
  }
  return map[cat] || cat
}

const fetchCourses = async () => {
  try {
    loadingCourses.value = true
    const res: any = await request.get('/courses?page=1&pageSize=50&status=ALL')
    courses.value = res.list || []
  } catch (e) {
    console.error(e)
  } finally {
    loadingCourses.value = false
  }
}

const handleCreateCourse = async () => {
  if (!newCourse.value.title.trim()) {
    ElMessage.warning('请输入课程名称')
    return
  }
  try {
    submitting.value = true
    await request.post('/courses', newCourse.value)
    ElMessage.success('课程创建并发布成功！')
    showAddDialog.value = false
    newCourse.value.title = ''
    await fetchCourses()
  } catch (e: any) {
    ElMessage.error(e.message || '创建课程失败')
  } finally {
    submitting.value = false
  }
}

const handleToggleStatus = async (row: any) => {
  try {
    const res: any = await request.put(`/courses/${row.id}/status`)
    ElMessage.success(res.message || '状态已更新')
    await fetchCourses()
  } catch (e: any) {
    ElMessage.error(e.message || '状态更新失败')
  }
}

const viewChapters = async (row: any) => {
  currentCourse.value = row
  chapterDrawer.value = true
  loadingChapters.value = true
  try {
    const res: any = await request.get(`/courses/${row.id}`)
    courseChapters.value = res.chapters || []
  } catch (e: any) {
    ElMessage.error('获取章节详情失败')
  } finally {
    loadingChapters.value = false
  }
}

onMounted(() => {
  fetchCourses()
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
