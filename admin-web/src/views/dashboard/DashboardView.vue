<template>
  <div class="dashboard-container">
    <div class="screen-entry-banner">
      <div class="banner-left">
        <span class="banner-badge">运营概览</span>
        <span class="banner-title">津韵润乡 · 业务数据</span>
        <span class="banner-desc">以下数量来自课程、创作、活动和审核记录；未建立采集的数据不会显示估算值。</span>
      </div>
    </div>

    <!-- 顶部 KPI 卡片 -->
    <el-row :gutter="16">
      <el-col :span="6">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-title">注册用户</div>
          <div class="kpi-value text-primary">{{ kpi.total_users ?? '—' }}</div>
          <div class="kpi-sub">日活跃用户暂未建立可靠采集</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-title">非遗课程累计完播</div>
          <div class="kpi-value text-gold">{{ kpi.completed_chapters ?? '—' }}</div>
          <div class="kpi-sub">实际完成的章节记录</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-title">AI工坊任务数</div>
          <div class="kpi-value text-green">{{ kpi.ai_tasks ?? '—' }}</div>
          <div class="kpi-sub">累计提交的真实任务</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-title">待处理审核</div>
          <div class="kpi-value text-red">{{ kpi.pending_reviews ?? '—' }}</div>
          <div class="kpi-sub">作品、评论与举报</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表展示区 -->
    <el-row :gutter="16" style="margin-top: 20px;">
      <el-col :span="16">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-header">
              <span class="header-title">📈 章节完成与AI任务趋势（近7日）</span>
              <el-tag type="info" size="small">来自业务记录</el-tag>
            </div>
          </template>
          <div ref="chartRef" style="height: 320px; width: 100%;"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-header">
              <span class="header-title">🔥 热门非遗课程榜单</span>
            </div>
          </template>
          <el-table :data="hotCourses" size="small" style="width: 100%">
            <el-table-column prop="rank" label="排名" width="50" />
            <el-table-column prop="title" label="课程名称" />
            <el-table-column prop="views" label="浏览数" width="80">
              <template #default="{ row }">
                <span style="color: #8B4A2F; font-weight: bold;">{{ row.views }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 底部状态概览 -->
    <el-row :gutter="16" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>📅 活动参与</span>
              <el-tag type="info">实际记录</el-tag>
            </div>
          </template>
          <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
              <div style="font-weight: bold; font-size: 15px; color: #2F2925;">活动 {{ kpi.activities ?? '—' }} 场</div>
              <div style="font-size: 13px; color: #776D65; margin-top: 4px;">现场签到 {{ kpi.attendances ?? '—' }} 人次</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>🛡️ 社区风控待审队列</span>
              <el-button type="text" size="small" @click="$router.push('/community')">进入风控中心 →</el-button>
            </div>
          </template>
          <div style="font-size: 13px; color: #776D65; line-height: 24px;">
            <div>• 待审作品：<strong>{{ pendingReviews.posts ?? '—' }}</strong> 件</div>
            <div>• 待审评论：<strong>{{ pendingReviews.comments ?? '—' }}</strong> 件</div>
            <div>• 待处理举报：<strong>{{ pendingReviews.reports ?? '—' }}</strong> 件</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'
import request from '@/api/request'

const kpi = ref<any>({})
const pendingReviews = ref<any>({})
const chartRef = ref<HTMLElement | null>(null)
const hotCourses = ref<any[]>([])

onMounted(async () => {
  try {
    const res: any = await request.get('/admin/dashboard')
    kpi.value = res.kpi || {}
    pendingReviews.value = res.pending_reviews || {}
    hotCourses.value = (res.hot_courses || []).map((course: any, index: number) => ({
      rank: index + 1,
      title: course.title,
      views: course.views
    }))

    if (chartRef.value) {
      const myChart = echarts.init(chartRef.value)
      const dates = (res.trends || []).map((t: any) => t.date)
      const completionData = (res.trends || []).map((t: any) => t.course_completed)
      const aiData = (res.trends || []).map((t: any) => t.ai_tasks)

      myChart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['章节完成数', 'AI任务提交数'] },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { type: 'category', boundaryGap: false, data: dates },
        yAxis: { type: 'value' },
        series: [
          {
            name: '章节完成数',
            type: 'line',
            smooth: true,
            data: completionData,
            itemStyle: { color: '#8B4A2F' }
          },
          {
            name: 'AI任务提交数',
            type: 'bar',
            data: aiData,
            itemStyle: { color: '#D6A85C' }
          }
        ]
      })
    }
  } catch (e) {
    console.error('Failed to load dashboard data', e)
  }
})
</script>

<style scoped>
.kpi-card {
  border-radius: 12px;
  background-color: #FFFFFF;
}
.kpi-title {
  font-size: 13px;
  color: #776D65;
  font-weight: 500;
}
.kpi-value {
  font-size: 28px;
  font-weight: bold;
  margin: 10px 0;
}
.text-primary { color: #8B4A2F; }
.text-gold { color: #C4863A; }
.text-green { color: #4D8B63; }
.text-red { color: #B64A44; }
.kpi-sub {
  font-size: 12px;
  color: #776D65;
}
.trend-up {
  color: #4D8B63;
  font-weight: bold;
}
.chart-card {
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

.screen-entry-banner {
  margin-bottom: 20px;
  background: linear-gradient(135deg, #0f1c3f 0%, #1e3c72 50%, #2a5298 100%);
  border: 1px solid rgba(0, 242, 254, 0.4);
  border-radius: 12px;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #FFFFFF;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(15, 28, 63, 0.15);
  transition: all 0.3s ease;
}
.screen-entry-banner:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 242, 254, 0.25);
  border-color: #00f2fe;
}
.banner-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.banner-badge {
  background: #00f2fe;
  color: #060b19;
  font-size: 11px;
  font-weight: bold;
  padding: 2px 8px;
  border-radius: 4px;
  letter-spacing: 0.5px;
}
.banner-title {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.banner-desc {
  font-size: 13px;
  color: #cbd5e1;
  margin-left: 8px;
}
.banner-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.screen-launch-btn {
  background: #00f2fe !important;
  border-color: #00f2fe !important;
  color: #060b19 !important;
  font-weight: bold !important;
  box-shadow: 0 0 10px rgba(0, 242, 254, 0.5);
}
.screen-launch-btn:hover {
  background: #fff !important;
  border-color: #fff !important;
}
.screen-sub-btn {
  background: rgba(255, 255, 255, 0.12) !important;
  border-color: rgba(255, 255, 255, 0.3) !important;
  color: #ffffff !important;
}
.screen-sub-btn:hover {
  background: rgba(255, 255, 255, 0.25) !important;
  border-color: #ffffff !important;
}
</style>
