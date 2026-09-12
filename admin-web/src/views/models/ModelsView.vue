<template>
  <div class="models-view">
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span class="header-title">🤖 AI模型与LoRA版本管理 (A-03)</span>
          <el-tag type="success">GPU推理集群在线就绪</el-tag>
        </div>
      </template>

      <el-row :gutter="16" v-loading="loading">
        <el-col :span="8" v-for="m in models" :key="m.id" style="margin-bottom: 16px;">
          <el-card shadow="hover" class="model-item-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
              <div>
                <h4 style="margin: 0; color: #2F2925;">{{ m.name }}</h4>
                <div style="font-size: 12px; color: #776D65; margin-top: 4px;">编码: {{ m.code }}</div>
              </div>
              <el-tag size="small" :type="m.status === 'ACTIVE' ? 'success' : 'info'">v{{ m.version }}</el-tag>
            </div>

            <div style="margin: 15px 0; font-size: 13px; color: #776D65; line-height: 22px;">
              <div>• 适用工坊: <strong>{{ formatTaskType(m.task_type) }}</strong></div>
              <div>• 运行提供方: {{ m.provider }}</div>
              <div>• 默认提示词模版: <span style="font-style: italic; color: #8B4A2F;">{{ m.prompt_template || '通用津沽非遗Prompt' }}</span></div>
              <div>• 运行状态: <el-tag size="small" :type="m.status === 'ACTIVE' ? 'success' : 'danger'">{{ m.status === 'ACTIVE' ? '在线就绪' : '已暂停服务' }}</el-tag></div>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #F0ECE4; padding-top: 10px;">
              <el-switch
                v-model="m.is_active"
                active-text="在线"
                inactive-text="下线"
                @change="handleStatusToggle(m)"
              />
              <el-button size="small" type="primary" link @click="openConfig(m)">参数与Prompt配置</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 模型参数微调弹窗 -->
    <el-dialog v-model="showEditDialog" :title="`模型配置 - ${editForm.name}`" width="560px">
      <el-form label-width="110px">
        <el-form-item label="模型显示名">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="模型版本号">
          <el-input v-model="editForm.version" />
        </el-form-item>
        <el-form-item label="服务状态">
          <el-radio-group v-model="editForm.status">
            <el-radio label="ACTIVE">在线运行</el-radio>
            <el-radio label="INACTIVE">离线维护</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="提示词模板">
          <el-input
            v-model="editForm.prompt_template"
            type="textarea"
            :rows="4"
            placeholder="津门非遗风格引导词，支持占位符如 {prompt}"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" style="background-color: #8B4A2F; border-color: #8B4A2F;" @click="saveModelConfig">
          保存配置
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/api/request'
import { ElMessage } from 'element-plus'

const models = ref<any[]>([])
const loading = ref(false)
const showEditDialog = ref(false)
const saving = ref(false)

const editForm = ref({
  id: 0,
  name: '',
  version: '',
  status: 'ACTIVE',
  prompt_template: ''
})

const formatTaskType = (type: string) => {
  const map: Record<string, string> = {
    'SHADOW_PUPPET': '皮影人物生成工坊',
    'YEAR_PAINTING': '杨柳青年画重构工坊',
    'CLAY_FIGURINE': '泥人张3D彩塑工坊',
    'RHYTHM_MUSIC': '津腔数来宝合辙'
  }
  return map[type] || type
}

const loadModels = async () => {
  try {
    loading.value = true
    const res: any = await request.get('/ai/models?all_status=true')
    models.value = (res || []).map((item: any) => ({
      ...item,
      is_active: item.status === 'ACTIVE'
    }))
  } catch (e: any) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const handleStatusToggle = async (m: any) => {
  const targetStatus = m.is_active ? 'ACTIVE' : 'INACTIVE'
  try {
    await request.put(`/ai/models/${m.id}`, { status: targetStatus })
    m.status = targetStatus
    ElMessage.success(`模型 ${m.name} 已${m.is_active ? '上线启用' : '暂停服务'}`)
  } catch (e: any) {
    m.is_active = !m.is_active // 回滚
    ElMessage.error(e.message || '更新模型状态失败')
  }
}

const openConfig = (m: any) => {
  editForm.value = {
    id: m.id,
    name: m.name,
    version: m.version,
    status: m.status,
    prompt_template: m.prompt_template || ''
  }
  showEditDialog.value = true
}

const saveModelConfig = async () => {
  try {
    saving.value = true
    await request.put(`/ai/models/${editForm.value.id}`, {
      name: editForm.value.name,
      version: editForm.value.version,
      status: editForm.value.status,
      prompt_template: editForm.value.prompt_template
    })
    ElMessage.success('模型配置保存成功')
    showEditDialog.value = false
    await loadModels()
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadModels()
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
.model-item-card {
  border-radius: 8px;
  background-color: #FAFAFA;
}
</style>
