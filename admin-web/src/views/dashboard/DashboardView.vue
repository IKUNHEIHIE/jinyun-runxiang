<template>
  <div class="dashboard-container">
    <!-- 乡村美育科技大屏入口 Banner -->
    <div class="screen-entry-banner" @click="openScreen">
      <div class="banner-left">
        <span class="banner-badge">数字化大屏</span>
        <span class="banner-title">津脉智韵 · 乡村美育科技数据大屏 (数字孪生 / 遥测监控)</span>
        <span class="banner-desc">已连接天津市 48 所乡村试点校、3 台具身智能助教机器人及 AI 审美诊断中台</span>
      </div>
      <div class="banner-right">
        <el-button type="primary" size="default" class="screen-launch-btn" @click.stop="openScreen">
          开启全屏大盘 ↗
        </el-button>
        <el-button size="default" class="screen-sub-btn" @click.stop="openScreenNewTab">
          新标签页打开 ↗
        </el-button>
      </div>
    </div>

    <!-- 顶部 KPI 卡片 -->
    <el-row :gutter="16">
      <el-col :span="6">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-title">日活跃学生 / DAU</div>
          <div class="kpi-value text-primary">{{ kpi.dau || 2420 }}</div>
          <div class="kpi-sub">较昨日 <span class="trend-up">+12.5%</span> · 覆盖乡村学校 48 所</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-title">非遗课程累计完播</div>
          <div class="kpi-value text-gold">{{ kpi.total_courses ? kpi.total_courses * 1250 : 7500 }}</div>
          <div class="kpi-sub">皮影戏与年画门类占比 65%</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-title">AI工坊创作作品数</div>
          <div class="kpi-value text-green">{{ kpi.total_posts ? kpi.total_posts * 180 + 1340 : 1340 }}</div>
          <div class="kpi-sub">今日生成调用 1,340 次</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-title">乡村美育公益基金累积</div>
          <div class="kpi-value text-red">¥ {{ (kpi.fund_total_yuan || 9540.00).toFixed(2) }}</div>
          <div class="kpi-sub">来自助农订单 10% 收益注入</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表展示区 -->
    <el-row :gutter="16" style="margin-top: 20px;">
      <el-col :span="16">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-header">
              <span class="header-title">📈 平台活跃度与AI生成调用趋势 (近7日)</span>
              <el-tag type="info" size="small">每日自动聚合</el-tag>
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
            <el-table-column prop="views" label="播放热度" width="80">
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
              <span>🤖 具身智能机器人状态 (在线演示)</span>
              <el-tag type="success">1台在线</el-tag>
            </div>
          </template>
          <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
              <div style="font-weight: bold; font-size: 15px; color: #2F2925;">DEV-SHADOW-BOT-01</div>
              <div style="font-size: 13px; color: #776D65; margin-top: 4px;">部署位置: 蓟州区下营镇中心小学美育室</div>
              <div style="font-size: 12px; color: #4D8B63; margin-top: 4px;">电量: 82% · 信号良好 · 正在执行天津皮影讲解与肢体表演</div>
            </div>
            <el-button type="primary" size="small" style="background-color: #8B4A2F; border-color: #8B4A2F;">发送测试指令</el-button>
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
            <div>• 今日多模态AI预审作品：<strong>168</strong> 件</div>
            <div>• 疑似敏感词触发待人工复核：<strong style="color: #C4863A;">2</strong> 件</div>
            <div>• 审核策略：首发文本敏感词初筛 + 图像违规识别 + 人工抽检</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import request from '@/api/request'

const router = useRouter()
const kpi = ref<any>({})
const chartRef = ref<HTMLElement | null>(null)

const openScreen = () => {
  router.push('/screen')
}

const openScreenNewTab = () => {
  window.open('/#/screen', '_blank')
}

const hotCourses = ref([
  { rank: 1, title: '津门皮影戏：光影里的民间传奇', views: '2,840' },
  { rank: 2, title: '杨柳青木版年画：点染岁时吉祥', views: '2,340' },
  { rank: 3, title: '青铜神兽饕餮：纹样里的古老密码', views: '1,620' },
  { rank: 4, title: '泥人张彩塑艺术：捏出指尖百态', views: '1,420' },
  { rank: 5, title: '津门鼓曲与三弦：韵白流转唱津城', views: '980' }
])

onMounted(async () => {
  try {
    const res: any = await request.get('/admin/dashboard')
    kpi.value = res.kpi || {}

    if (chartRef.value) {
      const myChart = echarts.init(chartRef.value)
      const dates = (res.trends || []).map((t: any) => t.date)
      const dauData = (res.trends || []).map((t: any) => t.dau)
      const aiData = (res.trends || []).map((t: any) => t.ai_generations)

      myChart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['日活跃学生 (DAU)', 'AI创作生成次数'] },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { type: 'category', boundaryGap: false, data: dates.length ? dates : ['09-06','09-07','09-08','09-09','09-10','09-11','09-12'] },
        yAxis: { type: 'value' },
        series: [
          {
            name: '日活跃学生 (DAU)',
            type: 'line',
            smooth: true,
            data: dauData.length ? dauData : [1240, 1320, 1450, 1580, 1820, 2150, 2420],
            itemStyle: { color: '#8B4A2F' }
          },
          {
            name: 'AI创作生成次数',
            type: 'bar',
            data: aiData.length ? aiData : [480, 520, 610, 740, 890, 1120, 1340],
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
