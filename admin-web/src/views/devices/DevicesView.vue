<template>
  <div class="devices-view">
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span class="header-title">🤖 具身智能设备监控台 (A-07)</span>
          <el-tag type="success">MQTT 通信总线正常</el-tag>
        </div>
      </template>

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
                  <div style="font-size: 18px; font-weight: bold; color: #4D8B63;">{{ d.telemetry.battery_pct }}%</div>
                </el-col>
                <el-col :span="8">
                  <div style="font-size: 12px; color: #776D65;">无线信号强度</div>
                  <div style="font-size: 18px; font-weight: bold; color: #2F2925;">{{ d.telemetry.wifi_rssi }} dBm</div>
                </el-col>
                <el-col :span="8">
                  <div style="font-size: 12px; color: #776D65;">主板温度</div>
                  <div style="font-size: 18px; font-weight: bold; color: #C4863A;">{{ d.telemetry.cpu_temp_c }} °C</div>
                </el-col>
              </el-row>
            </div>

            <div style="font-size: 13px; color: #2F2925; margin-bottom: 15px;">
              <strong>当前正在执行动作:</strong> 天津皮影老生肢体走位与三签舞台表演演示
            </div>

            <div style="display: flex; gap: 10px; justify-content: flex-end;">
              <el-button size="small" @click="sendCommand(d.device_code, 'PERFORM_SHADOW_PLAY')">下发皮影表演</el-button>
              <el-button size="small" type="primary" style="background-color: #8B4A2F; border-color: #8B4A2F;" @click="sendCommand(d.device_code, 'SPEAK_EXPLANATION')">讲解天津皮影历史</el-button>
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

const devices = ref<any[]>([])

onMounted(async () => {
  try {
    const res: any = await request.get('/devices')
    devices.value = res || []
  } catch (e) {
    console.error(e)
  }
})

const sendCommand = async (deviceCode: string, commandType: string) => {
  try {
    const res: any = await request.post(`/devices/${deviceCode}/command`, {
      command_type: commandType,
      payload: { action: commandType, duration_sec: 10 }
    })
    ElMessage.success(res.message || '指令已成功响应并执行')
  } catch (e) {
    ElMessage.error('指令下发失败')
  }
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
</style>
