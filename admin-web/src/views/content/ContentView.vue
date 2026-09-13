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
            <el-table-column label="操作" width="310" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="warning" link @click="exportLessonPlan(row)">导出教案 ↗</el-button>
                <el-button size="small" type="success" link @click="exportLessonPPT(row)">课件PPT ↗</el-button>
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
          <div class="festival-header-bar">
            <div class="festival-info">
              <span class="festival-subtitle">❖ 津沽传统岁时文化与非遗民俗档案（已由 SQLite 数据库动态持久化驱动）</span>
            </div>
            <div class="festival-controls">
              <el-radio-group v-model="festivalViewMode" size="small" style="margin-right: 12px;">
                <el-radio-button label="timeline">时间轴视图</el-radio-button>
                <el-radio-button label="table">数据表格视图</el-radio-button>
              </el-radio-group>
              <el-button type="primary" size="small" style="background-color: #8B4A2F; border-color: #8B4A2F;" @click="openAddFestival">
                + 新建民俗节日
              </el-button>
            </div>
          </div>

          <!-- 时间轴视图 -->
          <div v-if="festivalViewMode === 'timeline'" v-loading="loadingFestivals" style="margin-top: 20px;">
            <el-timeline>
              <el-timeline-item
                v-for="item in festivals"
                :key="item.id"
                :timestamp="`${item.lunar_date}${item.solar_date ? ' (' + item.solar_date + ')' : ''}`"
                placement="top"
                :color="item.status === 'PUBLISHED' ? '#8B4A2F' : '#909399'"
              >
                <el-card class="festival-timeline-card">
                  <div class="f-card-header">
                    <div class="f-title-wrap">
                      <span class="f-title">{{ item.title }}</span>
                      <el-tag size="small" type="warning" style="margin-left: 8px;">{{ item.tag || '津沽非遗' }}</el-tag>
                      <el-tag size="small" :type="item.status === 'PUBLISHED' ? 'success' : 'info'" style="margin-left: 6px;">
                        {{ item.status === 'PUBLISHED' ? '已上线' : '已下架' }}
                      </el-tag>
                    </div>
                    <div class="f-actions">
                      <el-button size="small" link type="primary" @click="openEditFestival(item)">编辑</el-button>
                      <el-button size="small" link :type="item.status === 'PUBLISHED' ? 'warning' : 'success'" @click="handleToggleFestival(item)">
                        {{ item.status === 'PUBLISHED' ? '下架' : '上架' }}
                      </el-button>
                      <el-button size="small" link type="danger" @click="handleDeleteFestival(item)">删除</el-button>
                    </div>
                  </div>
                  <div class="f-customs" v-if="item.customs">
                    <span class="f-label">特色风俗：</span>{{ item.customs }}
                  </div>
                  <p class="f-desc">{{ item.description }}</p>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </div>

          <!-- 数据表格视图 -->
          <div v-else v-loading="loadingFestivals" style="margin-top: 15px;">
            <el-table :data="festivals" border stripe style="width: 100%;">
              <el-table-column prop="title" label="节日名称" min-width="160">
                <template #default="{ row }">
                  <strong>{{ row.title }}</strong>
                </template>
              </el-table-column>
              <el-table-column prop="lunar_date" label="农历时令" width="120" />
              <el-table-column prop="solar_date" label="公历参考" width="120" />
              <el-table-column prop="tag" label="标签专题" width="130">
                <template #default="{ row }">
                  <el-tag size="small" type="warning">{{ row.tag }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="customs" label="传统民俗活动" min-width="200" show-overflow-tooltip />
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'PUBLISHED' ? 'success' : 'info'" size="small">
                    {{ row.status === 'PUBLISHED' ? '已上线' : '已下架' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="sort_order" label="排序" width="80" />
              <el-table-column label="操作" width="180" fixed="right">
                <template #default="{ row }">
                  <el-button size="small" type="primary" link @click="openEditFestival(row)">编辑</el-button>
                  <el-button 
                    size="small" 
                    :type="row.status === 'PUBLISHED' ? 'warning' : 'success'" 
                    link 
                    @click="handleToggleFestival(row)"
                  >
                    {{ row.status === 'PUBLISHED' ? '下架' : '上架' }}
                  </el-button>
                  <el-button size="small" type="danger" link @click="handleDeleteFestival(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
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

    <!-- 新建/编辑民俗节日弹窗 -->
    <el-dialog v-model="showFestivalDialog" :title="festivalForm.id ? '编辑民俗节日' : '新建津门民俗节日'" width="560px">
      <el-form label-width="100px">
        <el-form-item label="节日名称" required>
          <el-input v-model="festivalForm.title" placeholder="如：蓟州盘山重阳登高与茱萸民俗" />
        </el-form-item>
        <el-row :gutter="15">
          <el-col :span="12">
            <el-form-item label="农历时令" required>
              <el-input v-model="festivalForm.lunar_date" placeholder="如：九月初九" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="公历参考">
              <el-input v-model="festivalForm.solar_date" placeholder="如：2026-10-18" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="15">
          <el-col :span="12">
            <el-form-item label="非遗门类">
              <el-select v-model="festivalForm.category" style="width: 100%">
                <el-option label="民俗礼仪" value="FOLK_CUSTOM" />
                <el-option label="杨柳青年画" value="PAINTING" />
                <el-option label="泥人张彩塑" value="CLAY" />
                <el-option label="津门皮影" value="SHADOW_PUPPET" />
                <el-option label="风筝魏制作" value="KITE" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序权重">
              <el-input-number v-model="festivalForm.sort_order" :min="0" :max="99" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="专题标签">
          <el-input v-model="festivalForm.tag" placeholder="如：秋日茱萸雅集 / 津沽民俗专题" />
        </el-form-item>
        <el-form-item label="传统民俗风习">
          <el-input v-model="festivalForm.customs" placeholder="如：登盘山古道、插茱萸、品重阳花糕" />
        </el-form-item>
        <el-form-item label="文化内涵指引">
          <el-input v-model="festivalForm.description" type="textarea" :rows="3" placeholder="请输入节令文化渊源与乡村美育实践指引" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFestivalDialog = false">取消</el-button>
        <el-button type="primary" :loading="submittingFestival" style="background-color: #8B4A2F; border-color: #8B4A2F;" @click="handleSaveFestival">保存并同步</el-button>
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

const exportLessonPlan = (row: any) => {
  const url = `http://localhost:8000/api/v1/teacher/lesson-plans/export-html?topic=${encodeURIComponent(row.title)}&grade=${encodeURIComponent(row.age_group || '小学三年级')}`
  window.open(url, '_blank')
}

const exportLessonPPT = (row: any) => {
  const url = `http://localhost:8000/api/v1/teacher/lesson-plans/export-pptx?topic=${encodeURIComponent(row.title)}&grade=${encodeURIComponent(row.age_group || '小学三年级')}`
  window.open(url, '_blank')
}

const viewChapters = async (row: any) => {
  currentCourse.value = row
  chapterDrawer.value = true
  loadingChapters.value = true
  try {
    const res: any = await request.get(`/courses/${row.id}`)
    courseChapters.value = res.chapters || []
  } catch (e) {
    ElMessage.error('获取章节详情失败')
  } finally {
    loadingChapters.value = false
  }
}

// ----------------------------------------------------
// 民俗节日日历动态 CRUD 逻辑
// ----------------------------------------------------
const festivals = ref<any[]>([])
const loadingFestivals = ref(false)
const festivalViewMode = ref<'timeline' | 'table'>('timeline')
const showFestivalDialog = ref(false)
const submittingFestival = ref(false)

const festivalForm = ref<any>({
  id: null,
  title: '',
  lunar_date: '',
  solar_date: '',
  category: 'FOLK_CUSTOM',
  tag: '津沽民俗专题',
  customs: '',
  description: '',
  sort_order: 0
})

const fetchFestivals = async () => {
  try {
    loadingFestivals.value = true
    const res: any = await request.get('/festivals')
    festivals.value = Array.isArray(res) ? res : (res.data || [])
  } catch (e) {
    console.error('Failed to fetch festivals:', e)
  } finally {
    loadingFestivals.value = false
  }
}

const openAddFestival = () => {
  festivalForm.value = {
    id: null,
    title: '',
    lunar_date: '',
    solar_date: '',
    category: 'FOLK_CUSTOM',
    tag: '津沽民俗专题',
    customs: '',
    description: '',
    sort_order: festivals.value.length + 1
  }
  showFestivalDialog.value = true
}

const openEditFestival = (row: any) => {
  festivalForm.value = { ...row }
  showFestivalDialog.value = true
}

const handleSaveFestival = async () => {
  if (!festivalForm.value.title.trim() || !festivalForm.value.lunar_date.trim()) {
    ElMessage.warning('请填写民俗节日名称及农历时令')
    return
  }
  try {
    submittingFestival.value = true
    if (festivalForm.value.id) {
      await request.put(`/admin/festivals/${festivalForm.value.id}`, festivalForm.value)
      ElMessage.success('民俗节日信息已更新')
    } else {
      await request.post('/admin/festivals', festivalForm.value)
      ElMessage.success('民俗节日发布成功')
    }
    showFestivalDialog.value = false
    await fetchFestivals()
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    submittingFestival.value = false
  }
}

const handleToggleFestival = async (row: any) => {
  try {
    const res: any = await request.put(`/admin/festivals/${row.id}/status`)
    ElMessage.success(res.message || '状态已切换')
    await fetchFestivals()
  } catch (e: any) {
    ElMessage.error(e.message || '切换状态失败')
  }
}

const handleDeleteFestival = async (row: any) => {
  try {
    await request.delete(`/admin/festivals/${row.id}`)
    ElMessage.success('民俗节日已删除')
    await fetchFestivals()
  } catch (e: any) {
    ElMessage.error(e.message || '删除失败')
  }
}

onMounted(() => {
  fetchCourses()
  fetchFestivals()
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
.festival-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #FAF8F5;
  border: 1px solid #EFEAE3;
  border-radius: 8px;
  margin-top: 10px;
}
.festival-subtitle {
  font-size: 13px;
  color: #8B4A2F;
  font-weight: 600;
}
.festival-timeline-card {
  border-radius: 8px;
  border: 1px solid #ECE7E1;
}
.f-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.f-title-wrap {
  display: flex;
  align-items: center;
}
.f-title {
  font-size: 16px;
  font-weight: bold;
  color: #2F2925;
}
.f-customs {
  font-size: 13px;
  color: #C4863A;
  margin-bottom: 6px;
  font-weight: 500;
}
.f-label {
  color: #776D65;
}
.f-desc {
  font-size: 13px;
  color: #555;
  line-height: 1.6;
  margin: 0;
}
</style>
