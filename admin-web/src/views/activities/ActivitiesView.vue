<template>
  <div class="activities-view">
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span class="header-title">🗺️ 非遗美育地图、活动与助农商城 (A-06 & M-20/M-21)</span>
        </div>
      </template>

      <el-tabs v-model="tab">
        <el-tab-pane label="天津非遗地标点" name="landmarks">
          <el-table :data="landmarks" style="width: 100%" stripe>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="name" label="地标名称" min-width="160" />
            <el-table-column prop="district" label="行政区" width="100" />
            <el-table-column prop="category" label="门类" width="120" />
            <el-table-column label="地理经纬度" width="180">
              <template #default="{ row }">
                <span style="font-family: monospace;">{{ row.latitude }}, {{ row.longitude }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="geofence_radius_meters" label="打卡围栏(米)" width="120" />
            <el-table-column prop="address" label="详细地址" min-width="200" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="助农文创与特色农产品" name="products">
          <el-table :data="products" style="width: 100%" stripe>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column label="封面" width="100">
              <template #default="{ row }">
                <el-image :src="row.cover_url" style="width: 60px; height: 60px; border-radius: 6px;" fit="cover" />
              </template>
            </el-table-column>
            <el-table-column prop="name" label="商品名称" min-width="180" />
            <el-table-column prop="category" label="类别" width="130" />
            <el-table-column prop="origin_place" label="乡村产地" width="140" />
            <el-table-column label="单价起" width="100">
              <template #default="{ row }">
                <span style="color: #B64A44; font-weight: bold;">¥ {{ row.starting_price_yuan }}</span>
              </template>
            </el-table-column>
            <el-table-column label="注入美育基金比例" width="150">
              <template #default="{ row }">
                <el-tag type="warning">{{ row.fund_rate_percent }}% 专项注入</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/api/request'

const tab = ref('landmarks')
const landmarks = ref<any[]>([])
const products = ref<any[]>([])

onMounted(async () => {
  try {
    const resL: any = await request.get('/activities/landmarks')
    landmarks.value = resL || []
    const resP: any = await request.get('/mall/products')
    products.value = resP || []
  } catch (e) {
    console.error(e)
  }
})
</script>

<style scoped>
.table-card { border-radius: 12px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.header-title { font-weight: 600; color: #2F2925; }
</style>
