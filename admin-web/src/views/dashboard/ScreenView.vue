<template>
  <div class="screen-wrapper" ref="screenRef">
    <!-- 顶部科技感 Header -->
    <header class="screen-header">
      <div class="header-left">
        <div class="header-time">{{ currentTime }}</div>
        <div class="header-badge">
          <span class="pulse-dot"></span>
          <span>天津市美育浸润行动计划 · 48所乡村试点校实时联网</span>
        </div>
      </div>

      <div class="header-center">
        <div class="header-decor decor-left"></div>
        <div class="title-group">
          <h1 class="main-title">津脉智韵 · 乡村美育科技数据中台</h1>
          <span class="sub-title">TIANJIN RURAL AESTHETIC EDUCATION & DIGITAL TWIN PLATFORM</span>
        </div>
        <div class="header-decor decor-right"></div>
      </div>

      <div class="header-right">
        <div class="telemetry-pill">
          <span class="dot-online"></span>
          <span>具身机器人: 3 在线</span>
          <span class="separator">|</span>
          <span>网络时延: 16ms</span>
        </div>
        <button class="screen-btn" @click="toggleFullscreen">
          {{ isFullscreen ? '⛶ 退出全屏' : '⛶ 全屏展示' }}
        </button>
        <button class="screen-btn btn-back" @click="goBack">
          ← 返回后台
        </button>
      </div>
    </header>

    <!-- 顶部 5 大核心指标流 -->
    <section class="kpi-banner">
      <div class="kpi-box" v-for="(item, idx) in kpis" :key="idx">
        <div class="kpi-icon">{{ item.icon }}</div>
        <div class="kpi-content">
          <div class="kpi-label">{{ item.label }}</div>
          <div class="kpi-value-row">
            <span class="kpi-value" :style="{ color: item.color }">{{ item.value }}</span>
            <span class="kpi-unit">{{ item.unit }}</span>
          </div>
          <div class="kpi-subtext">{{ item.subtext }}</div>
        </div>
      </div>
    </section>

    <!-- 主体三栏网格 -->
    <main class="screen-main-grid">
      <!-- 左栏：课程研习与区域学时分布 -->
      <aside class="grid-col col-left">
        <!-- 左上卡片：非遗门类研习占比 -->
        <div class="tech-card">
          <div class="card-header">
            <span class="card-tag"></span>
            <span class="card-title">已通过审核作品门类分布</span>
            <span class="card-sub">已审核社区作品</span>
          </div>
          <div class="card-body">
            <div ref="pieChartRef" class="chart-container"></div>
          </div>
        </div>

        <!-- 左下卡片：涉农区县学时排行 -->
        <div class="tech-card">
          <div class="card-header">
            <span class="card-tag"></span>
            <span class="card-title">各涉农区县美育学时动态榜</span>
            <span class="card-sub">学时聚合 (小时)</span>
          </div>
          <div class="card-body">
            <div ref="barChartRef" class="chart-container"></div>
          </div>
        </div>
      </aside>

      <!-- 中栏：数字孪生基地拓扑 + 实时助农爱心流水 -->
      <section class="grid-col col-center">
        <!-- 中上：数字孪生试点学校拓扑网 -->
        <div class="tech-card center-top-card">
          <div class="card-header">
            <span class="card-tag gold"></span>
            <span class="card-title">数字孪生 · 天津市乡村美育试点基地网络</span>
            <div class="center-legend">
              <span class="legend-item"><span class="node-dot active"></span> 活跃基地</span>
              <span class="legend-item"><span class="node-dot robot"></span> 具身机器人</span>
            </div>
          </div>
          <div class="card-body map-container">
            <!-- 天津地图网格视觉底板与节点 -->
            <div class="map-bg-grid">
              <div class="map-contour"></div>
              
              <!-- 基地节点1: 蓟州区下营镇中心小学 -->
              <div class="school-node node-jizhou" style="top: 14%; left: 62%;">
                <div class="radar-pulse"></div>
                <div class="node-point"></div>
                <div class="node-card">
                  <div class="node-name">蓟州区 · 下营镇中心小学</div>
                  <div class="node-info">学子: 420人 · 在研: 津门皮影戏</div>
                  <div class="node-tag robot-tag">🤖 DEV-SHADOW-BOT-01 授课中</div>
                </div>
              </div>

              <!-- 基地节点2: 宝坻区林亭口小学 -->
              <div class="school-node node-baodi" style="top: 32%; left: 70%;">
                <div class="radar-pulse"></div>
                <div class="node-point"></div>
                <div class="node-card">
                  <div class="node-name">宝坻区 · 林亭口中心小学</div>
                  <div class="node-info">学子: 360人 · 在研: 年画套色木版拓印</div>
                  <div class="node-tag robot-tag">🤖 DEV-PAINT-BOT-02 运行中</div>
                </div>
              </div>

              <!-- 基地节点3: 武清区大王古庄美育工坊 -->
              <div class="school-node node-wuqing" style="top: 36%; left: 30%;">
                <div class="radar-pulse"></div>
                <div class="node-point"></div>
                <div class="node-card">
                  <div class="node-name">武清区 · 大王古庄乡村美育工坊</div>
                  <div class="node-info">学子: 290人 · 在研: 泥人张彩塑</div>
                  <div class="node-tag ai-tag">✦ AI名师审美诊断终端在机</div>
                </div>
              </div>

              <!-- 基地节点4: 静海区独流镇第一小学 -->
              <div class="school-node node-jinghai" style="top: 68%; left: 34%;">
                <div class="radar-pulse"></div>
                <div class="node-point"></div>
                <div class="node-card">
                  <div class="node-name">静海区 · 独流镇第一小学</div>
                  <div class="node-info">学子: 310人 · 在研: 汉沽版画与刻纸</div>
                  <div class="node-tag cert-tag">❖ 已发放爱心画材包 120 套</div>
                </div>
              </div>

              <!-- 基地节点5: 宁河区俵口镇美育基地 -->
              <div class="school-node node-ninghe" style="top: 50%; left: 78%;">
                <div class="radar-pulse"></div>
                <div class="node-point"></div>
                <div class="node-card">
                  <div class="node-name">宁河区 · 俵口镇七里海美育基地</div>
                  <div class="node-info">学子: 240人 · 在研: 芦苇编织工艺</div>
                  <div class="node-tag ai-tag">✦ 智韵双师联堂直播中</div>
                </div>
              </div>

              <!-- 装饰网格线与雷达扫描 -->
              <div class="radar-scanner"></div>
            </div>
          </div>
        </div>

        <!-- 中下：实时助农反哺美育爱心流水 -->
        <div class="tech-card center-bottom-card">
          <div class="card-header">
            <span class="card-tag red"></span>
            <span class="card-title">爱心助农 · 乡村美育公益反哺实时流水</span>
            <span class="card-sub">10%收益自动注入美育基金</span>
          </div>
          <div class="card-body ticker-container">
            <div class="ticker-list" :style="{ transform: `translateY(-${tickerOffset}px)` }">
              <div class="ticker-row" v-for="(order, i) in donationOrders" :key="i">
                <span class="t-time">{{ order.time }}</span>
                <span class="t-user">{{ order.user }}</span>
                <span class="t-action">认购</span>
                <span class="t-item">{{ order.item }}</span>
                <span class="t-fund">为{{ order.school }}注入美育基金 <strong class="fund-num">¥{{ order.fund }}</strong></span>
                <span class="t-hash">存证哈希: {{ order.hash }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 右栏：AI审美诊断指标 + 具身智能遥测 -->
      <aside class="grid-col col-right">
        <!-- 右上：AI 审美诊断雷达多维矩阵 -->
        <div class="tech-card">
          <div class="card-header">
            <span class="card-tag"></span>
            <span class="card-title">AI多模态非遗审美诊断矩阵</span>
            <span class="card-sub">千幅作品多维均分</span>
          </div>
          <div class="card-body">
            <div ref="radarChartRef" class="chart-container"></div>
            <div class="radar-meta-row">
              <div class="meta-item">
                <span class="label">优良率</span>
                <span class="val cyan">91.8%</span>
              </div>
              <div class="meta-item">
                <span class="label">最高维</span>
                <span class="val gold">传统意蕴 (94.1)</span>
              </div>
              <div class="meta-item">
                <span class="label">生成转化</span>
                <span class="val red">94.2%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 右下：具身智能助教机器人运行遥测 -->
        <div class="tech-card">
          <div class="card-header">
            <span class="card-tag gold"></span>
            <span class="card-title">具身助教机器人运行遥测</span>
            <span class="card-sub">边缘IoT协议接入</span>
          </div>
          <div class="card-body robot-list">
            <div class="robot-item" v-for="bot in robots" :key="bot.id">
              <div class="robot-top">
                <div class="robot-name">
                  <span class="bot-badge">IoT</span>
                  <strong>{{ bot.name }}</strong>
                </div>
                <span class="robot-status" :class="bot.statusClass">{{ bot.statusText }}</span>
              </div>
              <div class="robot-loc">📍 {{ bot.location }} · 任务: {{ bot.task }}</div>
              <div class="robot-stats">
                <div class="stat-col">
                  <span class="s-label">电池电量</span>
                  <div class="battery-bar">
                    <div class="battery-fill" :style="{ width: bot.battery + '%' }"></div>
                  </div>
                  <span class="s-val">{{ bot.battery == null ? '—' : bot.battery + '%' }}</span>
                </div>
                <div class="stat-col">
                  <span class="s-label">核心温度</span>
                  <span class="s-val">{{ bot.temp == null ? '—' : bot.temp + '°C' }}</span>
                </div>
                <div class="stat-col">
                  <span class="s-label">端侧延迟</span>
                  <span class="s-val">{{ bot.latency == null ? '—' : bot.latency + 'ms' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from "vue";
import { useRouter } from "vue-router";
import * as echarts from "echarts";
import request from "@/api/request";

const router = useRouter();
const screenRef = ref<HTMLElement | null>(null);
const isFullscreen = ref(false);
const currentTime = ref("");

// Chart refs
const pieChartRef = ref<HTMLElement | null>(null);
const barChartRef = ref<HTMLElement | null>(null);
const radarChartRef = ref<HTMLElement | null>(null);

let pieChart: echarts.ECharts | null = null;
let barChart: echarts.ECharts | null = null;
let radarChart: echarts.ECharts | null = null;
let clockTimer: any = null;
let tickerTimer: any = null;
let dataPollTimer: any = null;
const rawScreenData = ref<any>(null);

// KPI Counters
const kpis = ref<any[]>([]);

// 实时爱心流水
const tickerOffset = ref(0);
const donationOrders = ref<any[]>([]);

// 具身机器人状态
const robots = ref<any[]>([]);

// 更新当前时钟
const updateClock = () => {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const d = String(now.getDate()).padStart(2, "0");
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  const ss = String(now.getSeconds()).padStart(2, "0");
  const days = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"];
  currentTime.value = `${y}-${m}-${d} ${hh}:${mm}:${ss} ${days[now.getDay()]}`;
};

// 切换全屏
const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().then(() => {
      isFullscreen.value = true;
    }).catch(err => {
      console.warn("Fullscreen request denied:", err);
    });
  } else {
    document.exitFullscreen().then(() => {
      isFullscreen.value = false;
    });
  }
};

const goBack = () => {
  if (document.fullscreenElement) {
    document.exitFullscreen();
  }
  router.push("/dashboard/index");
};

// 从后端真实聚合接口获取大屏全景指标
const fetchScreenData = async () => {
  try {
    const res: any = await request.get("/screen/overview");
    const data = res.data || res;
    rawScreenData.value = data;
    kpis.value = data.kpis || [];
    donationOrders.value = data.donation_orders || [];
    robots.value = data.robots || [];
    if (pieChart && data.pie_chart) {
      pieChart.setOption({
        series: [{ data: data.pie_chart }]
      });
    }
    if (barChart && data.bar_chart) {
      barChart.setOption({
        yAxis: { data: data.bar_chart.categories },
        series: [{ data: data.bar_chart.values }]
      });
    }
  } catch (e) {
    console.error("Failed to load screen overview data:", e);
  }
};

// 初始化图表
const initCharts = () => {
  // 1. 饼图 / 玫瑰图
  if (pieChartRef.value) {
    pieChart = echarts.init(pieChartRef.value);
    pieChart.setOption({
      backgroundColor: "transparent",
      tooltip: {
        trigger: "item",
        formatter: "{b}: {c}次 ({d}%)",
        backgroundColor: "rgba(6, 12, 24, 0.9)",
        borderColor: "#00f2fe",
        textStyle: { color: "#fff" }
      },
      legend: {
        bottom: 0,
        left: "center",
        textStyle: { color: "#a0aec0", fontSize: 11 },
        itemWidth: 10,
        itemHeight: 10
      },
      series: [
        {
          name: "非遗门类研习",
          type: "pie",
          radius: ["35%", "68%"],
          center: ["50%", "45%"],
          roseType: "radius",
          itemStyle: {
            borderRadius: 6,
            borderColor: "#060b19",
            borderWidth: 2
          },
          label: {
            show: true,
            color: "#e2e8f0",
            fontSize: 11,
            formatter: "{b}\n{d}%"
          },
          labelLine: {
            length: 8,
            length2: 10,
            lineStyle: { color: "rgba(255,255,255,0.3)" }
          },
          data: rawScreenData.value?.pie_chart || []
        }
      ]
    });
  }

  // 2. 涉农区县学时排行横向条形图
  if (barChartRef.value) {
    barChart = echarts.init(barChartRef.value);
    barChart.setOption({
      backgroundColor: "transparent",
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        backgroundColor: "rgba(6, 12, 24, 0.9)",
        borderColor: "#00f2fe",
        textStyle: { color: "#fff" }
      },
      grid: {
        top: "8%",
        left: "3%",
        right: "12%",
        bottom: "5%",
        containLabel: true
      },
      xAxis: {
        type: "value",
        axisLine: { lineStyle: { color: "rgba(255,255,255,0.15)" } },
        splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)", type: "dashed" } },
        axisLabel: { color: "#a0aec0", fontSize: 11 }
      },
      yAxis: {
        type: "category",
        data: rawScreenData.value?.bar_chart?.categories || [],
        axisLine: { lineStyle: { color: "rgba(255,255,255,0.15)" } },
        axisLabel: { color: "#e2e8f0", fontSize: 12, fontWeight: 500 }
      },
      series: [
        {
          name: "注册学子人数",
          type: "bar",
          data: rawScreenData.value?.bar_chart?.values || [],
          barWidth: 14,
          itemStyle: {
            borderRadius: [0, 8, 8, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: "#1e3c72" },
              { offset: 1, color: "#00f2fe" }
            ])
          },
          label: {
            show: true,
            position: "right",
            color: "#00f2fe",
            fontSize: 11,
            formatter: "{c}人"
          }
        }
      ]
    });
  }

  // 3. AI 审美诊断多维测评雷达图
  if (radarChartRef.value) {
    radarChart = echarts.init(radarChartRef.value);
    radarChart.setOption({
      backgroundColor: "transparent",
      tooltip: {
        backgroundColor: "rgba(6, 12, 24, 0.9)",
        borderColor: "#ffaa00",
        textStyle: { color: "#fff" }
      },
      radar: {
        indicator: [
          { name: "构图章法", max: 100 },
          { name: "墨彩搭配", max: 100 },
          { name: "勾线笔法", max: 100 },
          { name: "传统意蕴", max: 100 },
          { name: "创新表现", max: 100 }
        ],
        center: ["50%", "50%"],
        radius: "62%",
        splitNumber: 4,
        axisName: {
          color: "#cbd5e1",
          fontSize: 11,
          borderRadius: 3,
          padding: [2, 4]
        },
        splitArea: {
          areaStyle: {
            color: [
              "rgba(0, 242, 254, 0.02)",
              "rgba(0, 242, 254, 0.05)",
              "rgba(0, 242, 254, 0.08)",
              "rgba(0, 242, 254, 0.12)"
            ]
          }
        },
        axisLine: { lineStyle: { color: "rgba(0, 242, 254, 0.25)" } },
        splitLine: { lineStyle: { color: "rgba(0, 242, 254, 0.2)" } }
      },
      series: [
        {
          name: "AI 审美诊断维度均分",
          type: "radar",
          data: []
        }
      ]
    });
  }
};

// 窗口 resize 监听
const handleResize = () => {
  pieChart?.resize();
  barChart?.resize();
  radarChart?.resize();
};

onMounted(async () => {
  updateClock();
  clockTimer = setInterval(updateClock, 1000);

  // 轮播滚动实时订单
  tickerTimer = setInterval(() => {
    tickerOffset.value += 38;
    if (tickerOffset.value >= donationOrders.value.length * 38) {
      tickerOffset.value = 0;
    }
  }, 3000);

  // 首次拉取大屏真实聚合流
  await fetchScreenData();

  nextTick(() => {
    initCharts();
    window.addEventListener("resize", handleResize);
  });

  // 10秒定时从后端增量刷新真实订单流水与最新KPI
  dataPollTimer = setInterval(fetchScreenData, 10000);
});

onUnmounted(() => {
  if (clockTimer) clearInterval(clockTimer);
  if (tickerTimer) clearInterval(tickerTimer);
  if (dataPollTimer) clearInterval(dataPollTimer);
  window.removeEventListener("resize", handleResize);
  pieChart?.dispose();
  barChart?.dispose();
  radarChart?.dispose();
});
</script>

<style scoped>
/* 整个大屏外壳 */
.screen-wrapper {
  width: 100vw;
  min-height: 100vh;
  background-color: #060b19;
  background-image: 
    radial-gradient(ellipse at 50% 0%, rgba(0, 242, 254, 0.12) 0%, transparent 60%),
    radial-gradient(circle at 15% 50%, rgba(30, 60, 114, 0.25) 0%, transparent 40%),
    radial-gradient(circle at 85% 50%, rgba(255, 170, 0, 0.1) 0%, transparent 40%);
  color: #e2e8f0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  padding: 12px 18px 18px 18px;
}

/* 顶部科技感 Header */
.screen-header {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(0, 242, 254, 0.25);
  background: linear-gradient(180deg, rgba(10, 22, 45, 0.8) 0%, rgba(6, 11, 25, 0.4) 100%);
  padding: 0 16px;
  position: relative;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.header-time {
  font-family: "Courier New", Courier, monospace;
  font-size: 15px;
  font-weight: bold;
  color: #00f2fe;
  letter-spacing: 1px;
}
.header-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #94a3b8;
}
.pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background-color: #00e676;
  box-shadow: 0 0 8px #00e676;
  animation: pulse-ring 2s infinite;
}

.header-center {
  display: flex;
  align-items: center;
  gap: 16px;
  text-align: center;
}
.header-decor {
  width: 60px;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00f2fe);
}
.decor-right {
  transform: rotate(180deg);
}
.title-group {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.main-title {
  margin: 0;
  font-size: 24px;
  font-weight: 800;
  letter-spacing: 4px;
  background: linear-gradient(90deg, #00f2fe 0%, #fff 50%, #f9d423 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 20px rgba(0, 242, 254, 0.4);
}
.sub-title {
  font-size: 9px;
  letter-spacing: 2px;
  color: #64748b;
  margin-top: 2px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.telemetry-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 242, 254, 0.08);
  border: 1px solid rgba(0, 242, 254, 0.3);
  padding: 4px 10px;
  border-radius: 14px;
  font-size: 12px;
  color: #cbd5e1;
}
.dot-online {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #00e676;
  box-shadow: 0 0 6px #00e676;
}
.separator {
  color: rgba(255,255,255,0.2);
}
.screen-btn {
  background: rgba(0, 242, 254, 0.15);
  border: 1px solid #00f2fe;
  color: #00f2fe;
  padding: 5px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.screen-btn:hover {
  background: #00f2fe;
  color: #060b19;
  box-shadow: 0 0 10px #00f2fe;
}
.btn-back {
  border-color: #f9d423;
  color: #f9d423;
  background: rgba(249, 212, 35, 0.1);
}
.btn-back:hover {
  background: #f9d423;
  color: #060b19;
  box-shadow: 0 0 10px #f9d423;
}

/* 顶部 KPI 卡片 */
.kpi-banner {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
  margin: 14px 0;
}
.kpi-box {
  background: linear-gradient(135deg, rgba(15, 30, 60, 0.7) 0%, rgba(8, 16, 35, 0.8) 100%);
  border: 1px solid rgba(0, 242, 254, 0.25);
  box-shadow: inset 0 0 15px rgba(0, 242, 254, 0.05);
  border-radius: 6px;
  padding: 12px 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: transform 0.2s, border-color 0.2s;
}
.kpi-box:hover {
  transform: translateY(-2px);
  border-color: rgba(0, 242, 254, 0.6);
}
.kpi-icon {
  font-size: 26px;
}
.kpi-content {
  flex: 1;
}
.kpi-label {
  font-size: 12px;
  color: #94a3b8;
}
.kpi-value-row {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin: 2px 0;
}
.kpi-value {
  font-size: 22px;
  font-weight: 800;
  font-family: "Impact", "Arial Black", sans-serif;
  letter-spacing: 0.5px;
}
.kpi-unit {
  font-size: 12px;
  color: #cbd5e1;
}
.kpi-subtext {
  font-size: 10px;
  color: #64748b;
}

/* 主体网格 */
.screen-main-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 28% 44% 28%;
  gap: 14px;
}
.grid-col {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* 通用科技卡片 */
.tech-card {
  background: rgba(10, 20, 42, 0.7);
  border: 1px solid rgba(0, 242, 254, 0.22);
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}
.tech-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 10px;
  height: 10px;
  border-top: 2px solid #00f2fe;
  border-left: 2px solid #00f2fe;
}
.tech-card::after {
  content: "";
  position: absolute;
  bottom: 0;
  right: 0;
  width: 10px;
  height: 10px;
  border-bottom: 2px solid #00f2fe;
  border-right: 2px solid #00f2fe;
}

.card-header {
  height: 38px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  background: linear-gradient(90deg, rgba(0, 242, 254, 0.1) 0%, transparent 100%);
  border-bottom: 1px solid rgba(0, 242, 254, 0.15);
  gap: 8px;
}
.card-tag {
  width: 3px;
  height: 14px;
  background: #00f2fe;
  border-radius: 2px;
}
.card-tag.gold {
  background: #ffaa00;
}
.card-tag.red {
  background: #ff4b2b;
}
.card-title {
  font-size: 13px;
  font-weight: 700;
  color: #e2e8f0;
  letter-spacing: 0.5px;
}
.card-sub {
  font-size: 10px;
  color: #64748b;
  margin-left: auto;
}
.card-body {
  flex: 1;
  padding: 8px;
  position: relative;
}
.chart-container {
  width: 100%;
  height: 220px;
}

/* 中栏拓扑网 */
.center-top-card {
  height: 420px;
}
.center-legend {
  margin-left: auto;
  display: flex;
  gap: 12px;
  font-size: 11px;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #94a3b8;
}
.node-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.node-dot.active {
  background: #00f2fe;
  box-shadow: 0 0 6px #00f2fe;
}
.node-dot.robot {
  background: #f9d423;
  box-shadow: 0 0 6px #f9d423;
}

.map-container {
  position: relative;
  overflow: hidden;
}
.map-bg-grid {
  width: 100%;
  height: 100%;
  position: relative;
  background: 
    linear-gradient(rgba(0, 242, 254, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 242, 254, 0.04) 1px, transparent 1px);
  background-size: 28px 28px;
  border-radius: 4px;
}

/* 基地节点 */
.school-node {
  position: absolute;
  transform: translate(-50%, -50%);
  cursor: pointer;
  z-index: 10;
}
.node-point {
  width: 12px;
  height: 12px;
  background: #00f2fe;
  border: 2px solid #fff;
  border-radius: 50%;
  box-shadow: 0 0 12px #00f2fe;
  position: relative;
  z-index: 2;
}
.radar-pulse {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 28px;
  height: 28px;
  transform: translate(-50%, -50%);
  border: 2px solid #00f2fe;
  border-radius: 50%;
  animation: radar-expand 2s infinite ease-out;
  z-index: 1;
}

.node-card {
  position: absolute;
  left: 20px;
  top: -15px;
  width: 200px;
  background: rgba(10, 22, 45, 0.92);
  border: 1px solid rgba(0, 242, 254, 0.5);
  border-radius: 4px;
  padding: 6px 10px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
  pointer-events: none;
}
.node-name {
  font-size: 11px;
  font-weight: 700;
  color: #00f2fe;
}
.node-info {
  font-size: 10px;
  color: #cbd5e1;
  margin: 2px 0;
}
.node-tag {
  font-size: 9px;
  padding: 2px 4px;
  border-radius: 2px;
  display: inline-block;
}
.robot-tag {
  background: rgba(249, 212, 35, 0.2);
  color: #f9d423;
  border: 1px solid rgba(249, 212, 35, 0.4);
}
.ai-tag {
  background: rgba(0, 242, 254, 0.2);
  color: #00f2fe;
  border: 1px solid rgba(0, 242, 254, 0.4);
}
.cert-tag {
  background: rgba(255, 75, 43, 0.2);
  color: #ff7675;
  border: 1px solid rgba(255, 75, 43, 0.4);
}

/* 中下实时流水 */
.center-bottom-card {
  height: 180px;
}
.ticker-container {
  height: 130px;
  overflow: hidden;
  position: relative;
}
.ticker-list {
  display: flex;
  flex-direction: column;
  transition: transform 0.6s ease-in-out;
}
.ticker-row {
  height: 38px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 11px;
  border-bottom: 1px dashed rgba(255, 255, 255, 0.08);
  padding: 0 6px;
}
.t-time {
  color: #64748b;
  font-family: monospace;
}
.t-user {
  color: #cbd5e1;
  font-weight: 600;
}
.t-action {
  color: #94a3b8;
}
.t-item {
  color: #f9d423;
}
.t-fund {
  color: #e2e8f0;
}
.fund-num {
  color: #ff4b2b;
}
.t-hash {
  margin-left: auto;
  color: #475569;
  font-family: monospace;
  font-size: 10px;
}

/* 右栏 */
.radar-meta-row {
  display: flex;
  justify-content: space-around;
  margin-top: 6px;
  padding: 4px 0;
  border-top: 1px dashed rgba(255, 255, 255, 0.1);
}
.meta-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.meta-item .label {
  font-size: 10px;
  color: #94a3b8;
}
.meta-item .val {
  font-size: 13px;
  font-weight: 700;
}
.val.cyan { color: #00f2fe; }
.val.gold { color: #ffaa00; }
.val.red { color: #ff4b2b; }

.robot-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px;
}
.robot-item {
  background: rgba(15, 28, 55, 0.5);
  border: 1px solid rgba(0, 242, 254, 0.15);
  border-radius: 4px;
  padding: 8px 10px;
}
.robot-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.bot-badge {
  background: #1e3c72;
  color: #00f2fe;
  font-size: 9px;
  padding: 1px 4px;
  border-radius: 2px;
  margin-right: 4px;
}
.robot-name strong {
  font-size: 11px;
  color: #f1f5f9;
}
.robot-status {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 2px;
}
.robot-status.running {
  background: rgba(0, 230, 118, 0.15);
  color: #00e676;
  border: 1px solid rgba(0, 230, 118, 0.4);
}
.robot-status.idle {
  background: rgba(148, 163, 184, 0.15);
  color: #94a3b8;
  border: 1px solid rgba(148, 163, 184, 0.3);
}
.robot-loc {
  font-size: 10px;
  color: #94a3b8;
  margin: 3px 0;
}
.robot-stats {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 4px;
}
.stat-col {
  display: flex;
  align-items: center;
  gap: 4px;
}
.s-label {
  font-size: 9px;
  color: #64748b;
}
.s-val {
  font-size: 10px;
  font-weight: 600;
  color: #00f2fe;
}
.battery-bar {
  width: 32px;
  height: 8px;
  background: rgba(255,255,255,0.1);
  border-radius: 2px;
  overflow: hidden;
}
.battery-fill {
  height: 100%;
  background: #00e676;
}

@keyframes pulse-ring {
  0% { transform: scale(0.9); opacity: 0.8; }
  50% { transform: scale(1.4); opacity: 0.3; }
  100% { transform: scale(0.9); opacity: 0.8; }
}

@keyframes radar-expand {
  0% { transform: translate(-50%, -50%) scale(0.4); opacity: 1; }
  100% { transform: translate(-50%, -50%) scale(2.2); opacity: 0; }
}
</style>
