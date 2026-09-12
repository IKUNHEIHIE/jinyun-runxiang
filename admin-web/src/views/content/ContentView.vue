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
          <el-table :data="courses" style="width: 100%" stripe>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column label="封面" width="100">
              <template #default="{ row }">
                <el-image :src="row.cover_url" style="width: 70px; height: 45px; border-radius: 4px;" fit="cover" />
              </template>
            </el-table-column>
            <el-table-column prop="title" label="课程标题" min-width="180" />
            <el-table-column prop="category" label="门类" width="120" />
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
            <el-table-column label="操作" width="150" fixed="right">
              <template #default>
                <el-button size="small" type="primary" link>编辑章节</el-button>
                <el-button size="small" type="danger" link>下架</el-button>
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
          </el-timeline>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 新建课程弹窗 -->
    <el-dialog v-model="showAddDialog" title="新建非遗美育课程" width="500px">
      <el-form label-width="80px">
        <el-form-item label="课程名称">
          <el-input placeholder="请输入课程标题" />
        </el-form-item>
        <el-form-item label="非遗门类">
          <el-select placeholder="请选择门类" style="width: 100%">
            <el-option label="津门皮影" value="SHADOW_PUPPET" />
            <el-option label="杨柳青年画" value="PAINTING" />
            <el-option label="泥人张彩塑" value="CLAY" />
            <el-option label="青铜神兽" value="BRONZE" />
          </el-select>
        </el-form-item>
        <el-form-item label="适用学段">
          <el-radio-group>
            <el-radio label="小学低段(动画为主)" />
            <el-radio label="小学高段(实操为主)" />
            <el-radio label="初中(项目式)" />
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" style="background-color: #8B4A2F; border-color: #8B4A2F;" @click="showAddDialog = false">确认发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/api/request'

const activeTab = ref('courses')
const courses = ref<any[]>([])
const showAddDialog = ref(false)

onMounted(async () => {
  try {
    const res: any = await request.get('/courses?page=1&pageSize=20')
    courses.value = res.list || []
  } catch (e) {
    console.error(e)
  }
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
