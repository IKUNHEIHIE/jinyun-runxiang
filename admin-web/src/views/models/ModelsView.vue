<template>
  <div class="models-view">
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span class="header-title">🤖 AI模型与LoRA版本管理 (A-03)</span>
          <el-tag type="success">GPU推理节点就绪</el-tag>
        </div>
      </template>

      <el-row :gutter="16">
        <el-col :span="8" v-for="m in models" :key="m.id" style="margin-bottom: 16px;">
          <el-card shadow="hover" class="model-item-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
              <div>
                <h4 style="margin: 0; color: #2F2925;">{{ m.name }}</h4>
                <div style="font-size: 12px; color: #776D65; margin-top: 4px;">编码: {{ m.code }}</div>
              </div>
              <el-tag size="small" :type="m.status === 'ACTIVE' ? 'success' : 'info'">v{{ m.version }}</el-tag>
            </div>

            <div style="margin: 15px 0; font-size: 13px; color: #776D65; line-height: 20px;">
              <div>• 适用工坊: <strong>{{ m.task_type }}</strong></div>
              <div>• 运行环境: {{ m.provider }}</div>
              <div>• 默认参数: 步数 25~30 / CFG 7.5</div>
              <div>• 平均推理时延: <span style="color: #4D8B63; font-weight: bold;">2.8s</span></div>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #F0ECE4; padding-top: 10px;">
              <el-switch v-model="m.is_active" active-text="在线" inactive-text="下线" />
              <el-button size="small" type="primary" link @click="openConfig(m)">参数微调</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/api/request'
import { ElMessage } from 'element-plus'

const models = ref<any[]>([])

onMounted(async () => {
  try {
    const res: any = await request.get('/ai/models')
    models.value = (res || []).map((item: any) => ({
      ...item,
      is_active: item.is_default || true
    }))
  } catch (e) {
    console.error(e)
  }
})

const openConfig = (m: any) => {
  ElMessage.info(`正在微调 ${m.name} 提示词引导参数`)
}
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
