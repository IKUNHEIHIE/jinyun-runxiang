<template>
  <div class="landmarks-page">
    <div class="page-header">
      <div class="tag-gold mb-2">❖ 津沽地理研学 · 现场/云端非遗探访</div>
      <h1 class="page-title font-serif">津门非遗研学地图 · 文旅打卡营地</h1>
      <p class="page-sub">
        依托天津各区县非遗物质与非物质文化遗存，支持乡村孩子与公众通过电子围栏打卡，沉浸式体验家乡历史文脉
      </p>
    </div>

    <!-- 地图与地标列表网格 -->
    <div v-loading="loading" class="landmarks-grid">
      <div 
        v-for="item in landmarks" 
        :key="item.id" 
        class="paper-card landmark-card"
      >
        <div class="lm-cover">
          <img :src="item.cover_url" :alt="item.name" />
          <span class="district-badge">{{ item.district }}</span>
        </div>

        <div class="lm-body">
          <div class="category-tag">🏛️ {{ item.category }}</div>
          <h3 class="lm-title font-serif">{{ item.name }}</h3>
          <p class="lm-address">📍 {{ item.address }}</p>
          <p class="lm-desc">{{ item.description }}</p>

          <div class="lm-footer">
            <div class="geofence-info">
              <span class="distance-text">模拟距您：<strong>{{ item.distance_mock || 280 }}</strong> 米</span>
              <span class="status-dot online">围栏内可打卡</span>
            </div>

            <el-button 
              type="primary" 
              size="small" 
              class="btn-primary"
              @click="checkin(item)"
            >
              研学打卡 (+30 能量)
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../api/request'

const loading = ref(false)
const landmarks = ref<any[]>([])

const fetchLandmarks = async () => {
  loading.value = true
  try {
    const res: any = await request.get('/activities/landmarks')
    landmarks.value = res || []
  } catch (e) {
  } finally {
    loading.value = false
  }
}

const checkin = async (lm: any) => {
  try {
    const res: any = await request.post('/activities/checkin', {
      landmark_id: lm.id,
      latitude: lm.latitude || 39.123,
      longitude: lm.longitude || 117.234
    })

    let tip = `恭喜您成功打卡【${res.landmark_name}】！获得美育能量 +${res.energy_added}`
    if (res.badge_unlocked) {
      tip += `，并点亮新徽章：【${res.badge_unlocked}】！`
    }

    ElMessageBox.alert(tip, '研学打卡成功', {
      confirmButtonText: '确定',
      type: 'success'
    })
  } catch (e) {
    ElMessage.error('打卡失败')
  }
}

onMounted(() => {
  fetchLandmarks()
})
</script>

<style scoped>
.landmarks-page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 32px 24px;
}

.page-header {
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

.landmarks-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 28px;
}

.landmark-card {
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.lm-cover {
  position: relative;
  height: 200px;
}

.lm-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.landmark-card:hover .lm-cover img {
  transform: scale(1.04);
}

.district-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(31, 30, 27, 0.8);
  backdrop-filter: blur(4px);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 4px;
}

.lm-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.category-tag {
  font-size: 12px;
  color: var(--color-teal);
  font-weight: 700;
  margin-bottom: 6px;
}

.lm-title {
  font-size: 18px;
  color: var(--color-text-main);
  margin-bottom: 6px;
}

.lm-address {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 12px;
}

.lm-desc {
  font-size: 13px;
  color: var(--color-text-regular);
  line-height: 1.6;
  margin-bottom: 20px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.lm-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px dashed var(--color-border);
  padding-top: 14px;
}

.geofence-info {
  display: flex;
  flex-direction: column;
  font-size: 11px;
}

.distance-text {
  color: var(--color-text-secondary);
}

.distance-text strong {
  color: var(--color-primary);
}

.status-dot.online {
  color: #059669;
  font-weight: 600;
}
</style>
