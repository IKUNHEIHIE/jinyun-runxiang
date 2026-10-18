<template>
  <div class="devices-view">
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span class="header-title">🤖 具身智能设备监控台 (A-07)</span>
          <el-tag type="warning">设备网关未接入</el-tag>
        </div>
      </template>

      <el-alert
        type="warning"
        :closable="false"
        show-icon
        title="设备网关尚未接入，遥测与远程指令不可用"
        description="设备状态来自数据库登记；电池、信号、温度与当前任务暂无真实回传。"
        style="margin-bottom: 16px;"
      />

      <el-row :gutter="16">
        <el-col :span="12" v-for="d in devices" :key="d.id">
          <el-card shadow="hover" style="border-radius: 10px;">
            <div style="display: flex; justify-content: space-between;">
              <div>
                <h3 style="margin: 0; color: #2F2925;">{{ d.device_name }}</h3>
                <div style="font-size: 13px; color: #776D65; margin-top: 5px;">编号: {{ d.device_code }} · 型号: {{ d.model }}</div>
              </div>
              <el-tag :type="d.status === 'ONLINE' ? 'success' : 'danger'" effect="dark">
                {{ d.status === 'ONLINE' ? '● 设备在线' : '○ 离线' }}
              </el-tag>
            </div>

            <div style="margin: 20px 0; background-color: #F8F4EC; padding: 12px; border-radius: 8px;">
              <el-row :gutter="12">
                <el-col :span="8">
                  <div style="font-size: 12px; color: #776D65;">电池电量</div>
                  <div style="font-size: 18px; font-weight: bold; color: #4D8B63;">{{ d.telemetry.battery_pct == null ? '—' : d.telemetry.battery_pct + '%' }}</div>
                </el-col>
                <el-col :span="8">
                  <div style="font-size: 12px; color: #776D65;">无线信号强度</div>
                  <div style="font-size: 18px; font-weight: bold; color: #2F2925;">{{ d.telemetry.wifi_rssi == null ? '—' : d.telemetry.wifi_rssi + ' dBm' }}</div>
                </el-col>
                <el-col :span="8">
                  <div style="font-size: 12px; color: #776D65;">主板温度</div>
                  <div style="font-size: 18px; font-weight: bold; color: #C4863A;">{{ d.telemetry.cpu_temp_c == null ? '—' : d.telemetry.cpu_temp_c + ' °C' }}</div>
                </el-col>
              </el-row>
            </div>

            <div style="font-size: 13px; color: #2F2925; margin-bottom: 15px;">
              <strong>最近心跳:</strong> {{ d.last_seen_at || '无记录' }}
              <span style="color: #8C827A;"> · 当前任务无回执</span>
            </div>

            <div style="display: flex; gap: 10px; justify-content: flex-end;">
              <el-button size="small" disabled title="设备网关未接入">下发皮影表演</el-button>
              <el-button size="small" type="primary" disabled title="设备网关未接入">讲解天津皮影历史</el-button>
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

const devices = ref<any[]>([])

onMounted(async () => {
  try {
    const res: any = await request.get('/devices')
    devices.value = res || []
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
