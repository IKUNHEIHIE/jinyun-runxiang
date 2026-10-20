<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api, mediaUrl, notify, post, requireSession } from "../api";
import { saveAsset } from "../files";
import Model3DViewer from "../components/Model3DViewer.vue";

type Quota = { used_today: number; remaining_today: number; daily_limit: number };
type ModelEntry = {
  id: string;
  file: string;
  name: string;
  subtitle: string;
  category: string;
  era: string;
  craft: string;
  material: string;
  description: string;
  tags: string[];
  palette: string[];
  url: string;
  size_mb: number;
  triangles: number;
  meshes: number;
  materials: number;
  license: string;
  source: string;
  source_url: string;
};
type Stage = { key: string; label: string; detail: string; demo: boolean };
type Result = {
  task_id: string;
  prompt?: string;
  description: string;
  model: ModelEntry;
  metrics: {
    mode: string;
    selection: string;
    matched_keyword: string | null;
    triangles: number;
    meshes: number;
    materials: number;
    size_mb: number;
    license: string;
    engine: string;
  };
  pipeline: Stage[];
};

const route = useRoute();
const router = useRouter();
const catalog = ref<ModelEntry[]>([]);
const preview = ref<ModelEntry | null>(null);
const result = ref<Result | null>(null);
const prompt = ref("为津门灯会复原一盏六方宫灯，绢面绘折枝海棠，六角垂红流苏");
const style = ref("民俗灯彩");
const busy = ref(false);
const stageIndex = ref(0);
const viewerProgress = ref(0);
const viewerError = ref("");
const autoRotate = ref(true);
const wireframe = ref(false);
const stats = ref({ triangles: 0, meshes: 0, materials: 0 });
const libraryHint = ref("");
const viewer = ref<InstanceType<typeof Model3DViewer>>();
const fps = ref(0);
const catalogReady = ref(false);
const collected = ref(false);
const quota = ref<Quota | null>(null);
const online = ref(typeof navigator === "undefined" ? true : navigator.onLine);
const elapsedMs = ref(0);
const restoring = ref(false);
let requestToken = 0;
const requestId = () => crypto.randomUUID().replace(/-/g, "");

const presets = [
  { label: "琉璃蟠龙", style: "琉璃雕塑", text: "以清代宫廷琉璃蟠龙为原型，琥珀色半透明龙身，鎏金鳞脊，盘旋成环" },
  { label: "六方宫灯", style: "民俗灯彩", text: "为津门灯会复原一盏六方宫灯，绢面绘折枝海棠，六角垂红流苏" },
  { label: "青花梅瓶", style: "陶瓷烧制", text: "明式青花梅瓶，小口丰肩，釉下钴蓝缠枝莲纹，器形饱满温润" },
  { label: "雀羽屏风", style: "髹漆木作", text: "双扇髹漆描金屏风，黑漆为底，金线孔雀与玉兰，明式边框起线" },
];
const pipelineDefaults: Stage[] = [
  { key: "parse", label: "器型解析", detail: "提取器型、纹样与材质线索", demo: true },
  { key: "topology", label: "拓扑营造", detail: "多视图取样 · 网格化", demo: true },
  { key: "uv", label: "展 UV", detail: "自动展开 · 法线校正", demo: true },
  { key: "pbr", label: "材质摹写", detail: "反照率 / 粗糙度 / 法线", demo: true },
  { key: "render", label: "光影预演", detail: "三点布光 · 环境遮蔽", demo: true },
];
const stageNames: Record<string, string> = {
  parse: "器型解析",
  topology: "拓扑营造",
  uv: "展 UV",
  pbr: "材质摹写",
  render: "光影预演",
};
function stageName(stage: Stage) {
  return stageNames[stage.key] || stage.label;
}

const currentModel = computed(() => result.value?.model || preview.value);
const viewerUrl = computed(() => (currentModel.value ? mediaUrl(currentModel.value.url) : ""));
const pipeline = computed(() => result.value?.pipeline || pipelineDefaults);
const progress = computed(() => {
  if (!busy.value) return 100;
  return Math.min(96, Math.round(((stageIndex.value + 1) / pipelineDefaults.length) * 100));
});
const elapsedText = computed(() =>
  result.value ? (elapsedMs.value / 1000).toFixed(1) + "s" : "—",
);
const triangleText = computed(() => {
  const value = result.value?.model.triangles || stats.value.triangles || currentModel.value?.triangles || 0;
  return value >= 10000 ? (value / 10000).toFixed(1) + "万" : value.toLocaleString("zh-CN");
});

let stageTimer: ReturnType<typeof setInterval> | undefined;
function startStages() {
  stageIndex.value = 0;
  clearInterval(stageTimer);
  stageTimer = setInterval(() => {
    if (stageIndex.value < pipelineDefaults.length - 1) stageIndex.value += 1;
  }, 760);
}

function usePreset(item: (typeof presets)[number]) {
  prompt.value = item.text;
  style.value = item.style;
  libraryHint.value = "";
}

function chooseModel(entry: ModelEntry) {
  result.value = null;
  preview.value = entry;
  libraryHint.value = "已切换馆藏预览 · " + entry.name;
}

async function generate() {
  if (busy.value) return;
  if (!online.value) {
    notify("当前离线，恢复网络后才能启动三维复原");
    return;
  }
  if (!requireSession(route.fullPath)) return;
  if (!prompt.value.trim()) {
    notify("请先写下想要复原的非遗器物");
    return;
  }
  const token = ++requestToken;
  busy.value = true;
  viewerError.value = "";
  result.value = null;
  collected.value = false;
  libraryHint.value = "";
  startStages();
  const startedAt = performance.now();
  try {
    const data = await post<Result & { quota?: Quota }>("/ai/3d/generate", {
      prompt: prompt.value.trim(),
      style: style.value,
      request_id: requestId(),
    });
    if (token !== requestToken) return;
    elapsedMs.value = performance.now() - startedAt;
    stageIndex.value = pipelineDefaults.length - 1;
    quota.value = data.quota || null;
    result.value = data;
  } catch (error) {
    if (token !== requestToken) return;
    notify(error instanceof Error ? error.message : "三维复原失败，请稍后重试");
  } finally {
    clearInterval(stageTimer);
    if (token === requestToken) busy.value = false;
  }
}

async function toggleFavorite() {
  if (!result.value) return;
  if (!requireSession(route.fullPath)) return;
  try {
    const data = await post<{ collected: boolean }>(
      "/ai/tasks/" + result.value.task_id + "/favorite",
      { collected: !collected.value },
    );
    collected.value = data.collected;
    notify(data.collected ? "已加入我的收藏" : "已取消收藏");
  } catch (error) {
    notify(error instanceof Error ? error.message : "收藏状态未能保存，请重试");
  }
}

async function exportModel() {
  const model = result.value?.model;
  if (!model) return;
  try {
    await saveAsset(model.url, model.file || model.id + ".glb", "馆藏三维模型 " + model.name);
  } catch (error) {
    notify(error instanceof Error ? error.message : "模型导出失败，请稍后重试");
  }
}

async function restore(taskId: string) {
  restoring.value = true;
  try {
    const data = await api<{ status: string; collected: boolean; result: Result | null }>(
      "/ai/tasks/" + taskId,
    );
    if (data.status !== "SUCCESS" || !data.result) return;
    result.value = data.result;
    preview.value = data.result.model;
    collected.value = !!data.collected;
    if (data.result.prompt) prompt.value = data.result.prompt;
    libraryHint.value = "已恢复历史作品 · " + data.result.model.name;
  } catch {
    libraryHint.value = "历史作品读取失败，请返回工坊重试";
  } finally {
    restoring.value = false;
  }
}

function backToWorkshop() {
  window.history.state.back ? router.back() : router.replace("/ai-workshop");
}

const setOnline = () => {
  online.value = navigator.onLine;
};

onMounted(async () => {
  window.addEventListener("online", setOnline);
  window.addEventListener("offline", setOnline);
  try {
    const data = await api<{ models: ModelEntry[] }>("/ai/3d/catalog");
    catalog.value = data.models;
    preview.value = data.models[0] || null;
    catalogReady.value = data.models.length > 0;
  } catch {
    libraryHint.value = "模型库暂时不可用，请检查网络";
  }
  const taskId = typeof route.query.task_id === "string" ? route.query.task_id : "";
  if (taskId) await restore(taskId);
});
onBeforeUnmount(() => {
  clearInterval(stageTimer);
  requestToken += 1;
  window.removeEventListener("online", setOnline);
  window.removeEventListener("offline", setOnline);
});
</script>

<template>
  <div class="lab-page">
    <div class="lab-bg" aria-hidden="true">
      <i class="wash wash-a" /><i class="wash wash-b" /><i class="paper-grain" />
    </div>

    <header class="lab-top">
      <button class="lab-back" aria-label="返回 AI 工坊" @click="backToWorkshop">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 18l-6-6 6-6" /></svg>
      </button>
      <div class="lab-crumb"><span>AI 工坊</span><i />数字沙盘</div>
      <span class="lab-live" :class="{ off: !online || !catalogReady }">
        <i />{{ !online ? "离线" : catalogReady ? "模型库已连通" : "模型库未就绪" }}
      </span>
    </header>

    <section class="lab-hero">
      <div class="hero-seal" aria-hidden="true">
        <i class="ring ring-a" /><i class="ring ring-b" />
        <b>津韵</b>
      </div>
      <p class="hero-kicker">古法营造 · 数字孪生</p>
      <h1>三维非遗<br /><em>数字沙盘</em></h1>
      <p class="hero-sub">三维复原 · 材质摹写 · 墨色光影实时演算</p>
      <div class="hero-stats">
        <span><b>{{ catalog.length }}</b>件馆藏</span>
        <i />
        <span><b>{{ fps || "—" }}</b>帧实时</span>
        <i />
        <span><b>演示</b>馆藏库匹配</span>
      </div>
    </section>

    <section class="stage-card">
      <div class="stage-hud">
        <span class="hud-live"><i />实时渲染</span>
        <span class="hud-engine">黑漆描金 · 数字展台</span>
      </div>
      <div class="stage-canvas">
        <Model3DViewer
          v-if="viewerUrl"
          ref="viewer"
          :url="viewerUrl"
          :auto-rotate="autoRotate"
          :wireframe="wireframe"
          :label="(currentModel?.name || '馆藏模型') + ' 三维模型，聚焦后可用方向键旋转视角'"
          @loaded="stats = $event"
          @fps="fps = $event"
          @progress="viewerProgress = $event"
          @error="viewerError = $event"
        />
        <div v-else class="stage-empty">
          <i class="scan-cube" /><p>正在启封馆藏模型…</p>
        </div>
        <div class="stage-shine" aria-hidden="true" />
        <span class="corner tl" /><span class="corner tr" /><span class="corner bl" /><span class="corner br" />
        <div v-if="currentModel" class="stage-caption">
          <span>馆藏编号 / {{ currentModel.id.toUpperCase() }}</span>
          <b>{{ currentModel.name }}</b>
          <em>{{ currentModel.subtitle }}</em>
        </div>
        <div class="stage-tip">拖拽旋转 · 双指缩放</div>
        <div v-if="viewerProgress > 0 && viewerProgress < 100" class="stage-loading">
          <i :style="{ width: viewerProgress + '%' }" />
          <span>启封模型 {{ viewerProgress }}%</span>
        </div>
        <div v-if="viewerError" class="stage-error">{{ viewerError }}</div>
      </div>
      <div class="stage-tools">
        <button :class="{ on: autoRotate }" @click="autoRotate = !autoRotate">
          <i class="dot" />自动旋转
        </button>
        <button :class="{ on: wireframe }" @click="wireframe = !wireframe">
          <i class="wire" />线框
        </button>
        <button @click="viewer?.resetView()"><i class="reset" />重置视角</button>
        <span class="telemetry">
          <b>{{ triangleText }}</b>面<i />
          <b>{{ stats.meshes || currentModel?.meshes || 0 }}</b>网格<i />
          <b>{{ (currentModel?.size_mb || 0).toFixed(1) }}</b>MB
        </span>
      </div>
    </section>

    <section class="control-card">
      <div class="control-head">
        <span class="index">壹</span>
        <div><b>创作描述</b><em>描述器型、纹样与材质，沙盘会匹配最贴近的馆藏三维资产</em></div>
      </div>
      <label class="prompt-box">
        <textarea
          v-model="prompt"
          maxlength="500"
          rows="3"
          placeholder="例：为津门灯会复原一盏六方宫灯，绢面绘海棠，垂红流苏"
        />
        <span>{{ prompt.length }} / 500</span>
      </label>
      <div class="preset-row">
        <button v-for="item in presets" :key="item.label" @click="usePreset(item)">
          {{ item.label }}
        </button>
      </div>
      <button class="generate-btn" :disabled="busy" @click="generate">
        <i class="gen-seal" aria-hidden="true">造</i>
        <span>{{ busy ? "三维复原中…" : "启动三维复原" }}</span>
        <em>古法营造</em>
      </button>
      <p class="mode-note">
        演示模式 · 后端从馆藏级 CC0 模型库匹配返回，展台实时渲染{{
          quota ? " · 今日剩余 " + quota.remaining_today + " 次" : ""
        }}
      </p>
    </section>

    <section v-if="result" class="result-card">
      <div class="result-head">
        <div>
          <span class="result-kicker">数字沙盘 · 馆藏匹配</span>
          <h2>{{ result.model.name }}</h2>
          <p>{{ result.description }}</p>
        </div>
        <span class="result-seal">已完成</span>
      </div>
      <div class="result-metrics">
        <div><b>{{ triangleText }}</b><span>三角面</span></div>
        <div><b>{{ result.model.meshes }}</b><span>网格</span></div>
        <div><b>{{ result.model.materials }}</b><span>材质</span></div>
        <div><b>{{ elapsedText }}</b><span>本次匹配</span></div>
      </div>
      <p class="result-match">
        {{
          result.metrics.selection === "keyword"
            ? "描述命中关键词「" + result.metrics.matched_keyword + "」"
            : "描述未命中具体器型关键词，按馆藏库顺序选取"
        }}
      </p>
      <div class="result-meta">
        <span>{{ result.model.era }}</span><span>{{ result.model.craft }}</span><span>{{ result.model.material }}</span>
      </div>
      <ol class="pipeline-list">
        <li v-for="stage in result.pipeline" :key="stage.key">
          <i class="check">✓</i>
          <b>{{ stageName(stage) }}</b>
          <span>{{ stage.detail }}</span>
          <em>演示</em>
        </li>
      </ol>
      <div class="result-actions">
        <button class="collect" :class="{ on: collected }" :aria-pressed="collected" @click="toggleFavorite">
          {{ collected ? "已收藏" : "收藏作品" }}
        </button>
        <button class="export" @click="exportModel">导出 GLB</button>
        <RouterLink class="works" to="/ai-workshop/works">我的工坊作品</RouterLink>
      </div>
      <p class="license">
        {{ result.model.license }} · {{ result.model.source }} · 实时渲染 {{ fps || "—" }} 帧
      </p>
    </section>

    <section class="library-card">
      <div class="library-head">
        <div><span class="index">贰</span><b>馆藏模型库</b></div>
        <em>{{ catalog.length }} 件 · CC0 授权</em>
      </div>
      <div class="library-scroll">
        <button
          v-for="entry in catalog"
          :key="entry.id"
          class="library-item"
          :class="{ active: currentModel?.id === entry.id }"
          @click="chooseModel(entry)"
        >
          <i :style="{ background: 'linear-gradient(135deg, ' + entry.palette[0] + ', ' + entry.palette[1] + ')' }" />
          <b>{{ entry.name }}</b>
          <span>{{ entry.category }}</span>
          <em>{{ (entry.triangles / 10000).toFixed(1) }}万面</em>
        </button>
      </div>
      <p v-if="libraryHint" class="library-hint">{{ libraryHint }}</p>
    </section>

    <Teleport to="body">
      <Transition name="fade">
        <div v-if="busy" class="pipeline-mask">
          <div class="pipeline-panel">
            <div class="pipeline-title">
              <i class="pipeline-seal">造</i>
              <div><b>古法营造 · 三维复原</b><span>正在从馆藏三维库中取样匹配 · 以下工序为界面演算示意</span></div>
              <em>{{ progress }}%</em>
            </div>
            <div class="pipeline-bar"><i :style="{ width: progress + '%' }" /></div>
            <ol>
              <li
                v-for="(stage, index) in pipelineDefaults"
                :key="stage.key"
                :class="{ done: index < stageIndex, active: index === stageIndex }"
              >
                <i />
                <div><b>{{ stageName(stage) }}</b><span>{{ stage.detail }}</span></div>
                <em>{{ index < stageIndex ? "完成" : index === stageIndex ? "进行中" : "等待" }}</em>
              </li>
            </ol>
            <p>取样 · 拓扑 · 展 UV · 材质摹写 · 光影预演（演示工序，不生成新的几何体）</p>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.lab-page {
  position: relative;
  min-height: 100dvh;
  padding: calc(10px + var(--safe-top)) 16px 48px;
  color: #2c241b;
  background: #efe6d6;
  font-family: var(--sans);
  overflow: hidden;
}
.lab-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}
.paper-grain {
  position: absolute;
  inset: 0;
  opacity: 0.5;
  background-image:
    repeating-linear-gradient(0deg, rgba(126, 98, 58, 0.045) 0 1px, transparent 1px 3px),
    repeating-linear-gradient(90deg, rgba(126, 98, 58, 0.03) 0 1px, transparent 1px 4px);
  mask-image: radial-gradient(circle at 50% 20%, #000 0, transparent 85%);
}
.wash {
  position: absolute;
  border-radius: 50%;
  filter: blur(44px);
  opacity: 0.24;
}
.wash-a {
  top: -90px;
  right: -70px;
  width: 280px;
  height: 280px;
  background: #b9a077;
}
.wash-b {
  top: 380px;
  left: -120px;
  width: 260px;
  height: 260px;
  background: #c9b394;
}
.lab-top,
.lab-hero,
.stage-card,
.control-card,
.result-card,
.library-card {
  position: relative;
  z-index: 1;
}
.lab-top {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 40px;
}
.lab-back {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(139, 105, 48, 0.4);
  border-radius: 8px;
  background: rgba(250, 246, 236, 0.85);
  color: #5c4626;
}
.lab-back svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.lab-crumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  letter-spacing: 2px;
  color: #7c5c2c;
}
.lab-crumb span {
  color: rgba(44, 36, 27, 0.52);
}
.lab-crumb i {
  width: 18px;
  height: 1px;
  background: rgba(139, 105, 48, 0.45);
}
.lab-live {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 9px;
  letter-spacing: 1.6px;
  color: #8b1a1a;
}
.lab-live i {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #8b1a1a;
  box-shadow: 0 0 0 3px rgba(139, 26, 26, 0.1);
  animation: blink 2s infinite;
}
.lab-hero {
  padding: 26px 4px 20px;
}
.hero-seal {
  position: absolute;
  top: 8px;
  right: 2px;
  width: 96px;
  height: 96px;
  display: grid;
  place-items: center;
}
.ring {
  position: absolute;
  inset: 0;
  border: 1px solid rgba(139, 105, 48, 0.35);
  border-radius: 50%;
}
.ring-b {
  inset: 14px;
  border-style: dashed;
  border-color: rgba(139, 26, 26, 0.28);
  animation: spin 20s linear infinite;
}
.hero-seal b {
  position: relative;
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  border: 1.5px solid rgba(139, 26, 26, 0.72);
  border-radius: 4px;
  color: #8b1a1a;
  font-family: var(--serif);
  font-size: 15px;
  letter-spacing: 2px;
  line-height: 1;
  transform: rotate(-4deg);
  background: rgba(139, 26, 26, 0.04);
}
.hero-kicker {
  margin: 0 0 10px;
  font-size: 10px;
  letter-spacing: 3px;
  color: #8a6a37;
}
.lab-hero h1 {
  margin: 0;
  font-family: var(--serif);
  font-size: 31px;
  line-height: 1.25;
  font-weight: 700;
  letter-spacing: 2px;
  color: #1a365d;
}
.lab-hero h1 em {
  font-style: normal;
  color: #8b1a1a;
}
.hero-sub {
  margin: 10px 0 16px;
  max-width: 280px;
  font-size: 11px;
  line-height: 1.7;
  letter-spacing: 0.6px;
  color: rgba(44, 36, 27, 0.58);
}
.hero-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 10px;
  color: rgba(44, 36, 27, 0.55);
}
.hero-stats b {
  margin-right: 4px;
  font-family: var(--serif);
  font-size: 16px;
  color: #1a365d;
}
.hero-stats i {
  width: 1px;
  height: 14px;
  background: rgba(139, 105, 48, 0.28);
}
.stage-card {
  border: 1px solid rgba(139, 105, 48, 0.55);
  border-radius: 14px;
  background: #201a13;
  box-shadow: 0 18px 40px rgba(60, 44, 22, 0.22), inset 0 0 0 1px rgba(201, 168, 76, 0.18);
  overflow: hidden;
}
.stage-hud {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(201, 168, 76, 0.18);
  background: linear-gradient(180deg, #241d15, #1c1610);
  font-size: 9px;
  letter-spacing: 2px;
  color: rgba(216, 190, 138, 0.6);
}
.hud-live {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #d8be8a;
}
.hud-live i {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #b8862f;
  box-shadow: 0 0 6px rgba(201, 168, 76, 0.75);
  animation: blink 1.8s infinite;
}
.stage-canvas {
  position: relative;
  height: 336px;
  background:
    radial-gradient(circle at 50% 42%, rgba(120, 88, 40, 0.34), transparent 64%),
    linear-gradient(180deg, #1d1710, #120e0a);
}
.stage-empty {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  justify-items: center;
  gap: 16px;
  color: rgba(216, 190, 138, 0.6);
  font-size: 11px;
  letter-spacing: 1.4px;
}
.scan-cube {
  width: 34px;
  height: 34px;
  border: 1px solid #c9a84c;
  transform: rotate(45deg);
  animation: spin 5s linear infinite;
}
.stage-shine {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(180deg, transparent 0%, rgba(201, 168, 76, 0.1) 49%, transparent 52%);
  background-size: 100% 230%;
  animation: shine-scan 7s linear infinite;
  mix-blend-mode: screen;
}
.corner {
  position: absolute;
  width: 18px;
  height: 18px;
  border: solid rgba(201, 168, 76, 0.7);
  pointer-events: none;
}
.corner.tl { top: 10px; left: 10px; border-width: 1px 0 0 1px; }
.corner.tr { top: 10px; right: 10px; border-width: 1px 1px 0 0; }
.corner.bl { bottom: 10px; left: 10px; border-width: 0 0 1px 1px; }
.corner.br { bottom: 10px; right: 10px; border-width: 0 1px 1px 0; }
.stage-caption {
  position: absolute;
  left: 16px;
  bottom: 14px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  pointer-events: none;
}
.stage-caption span {
  font-size: 8px;
  letter-spacing: 1.8px;
  color: rgba(216, 190, 138, 0.55);
}
.stage-caption b {
  font-family: var(--serif);
  font-size: 20px;
  color: #f5ead2;
  letter-spacing: 3px;
}
.stage-caption em {
  font-style: normal;
  font-size: 9px;
  letter-spacing: 1.6px;
  color: rgba(201, 168, 76, 0.8);
}
.stage-tip {
  position: absolute;
  right: 15px;
  bottom: 15px;
  font-size: 8px;
  letter-spacing: 1.2px;
  color: rgba(216, 190, 138, 0.4);
}
.stage-loading {
  position: absolute;
  left: 16px;
  right: 16px;
  top: 14px;
  height: 2px;
  background: rgba(201, 168, 76, 0.14);
}
.stage-loading i {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #8b1a1a, #d8be8a);
  transition: width 0.25s;
}
.stage-loading span {
  position: absolute;
  right: 0;
  top: 5px;
  font-size: 8px;
  letter-spacing: 1px;
  color: rgba(216, 190, 138, 0.55);
}
.stage-error {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  padding: 24px;
  text-align: center;
  font-size: 12px;
  color: #f0c9a0;
  background: rgba(18, 13, 9, 0.9);
}
.stage-tools {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 10px 12px 12px;
  border-top: 1px solid rgba(201, 168, 76, 0.16);
  background: #1b1510;
}
.stage-tools button {
  display: flex;
  align-items: center;
  gap: 5px;
  height: 28px;
  padding: 0 10px;
  border: 1px solid rgba(201, 168, 76, 0.28);
  border-radius: 6px;
  background: rgba(201, 168, 76, 0.05);
  color: rgba(216, 190, 138, 0.72);
  font-size: 10px;
  letter-spacing: 0.6px;
}
.stage-tools button.on {
  border-color: rgba(201, 168, 76, 0.7);
  color: #e7cf9a;
  box-shadow: 0 0 10px rgba(201, 168, 76, 0.12) inset;
}
.stage-tools button i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}
.stage-tools button i.wire {
  border-radius: 1px;
  background: transparent;
  border: 1px solid currentColor;
}
.stage-tools button i.reset {
  border-radius: 50%;
  background: transparent;
  border: 1px solid currentColor;
  border-right-color: transparent;
}
.telemetry {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 8px;
  letter-spacing: 0.8px;
  color: rgba(216, 190, 138, 0.38);
}
.telemetry b {
  color: rgba(240, 226, 197, 0.82);
  font-weight: 600;
}
.telemetry i {
  width: 1px;
  height: 9px;
  margin: 0 3px;
  background: rgba(201, 168, 76, 0.2);
}
.control-card,
.result-card,
.library-card {
  margin-top: 16px;
  padding: 16px;
  border: 1px solid rgba(139, 105, 48, 0.3);
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(252, 248, 239, 0.96), rgba(246, 239, 226, 0.96));
  box-shadow: 0 8px 24px rgba(90, 70, 40, 0.08);
}
.control-head,
.library-head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}
.index {
  display: grid;
  place-items: center;
  width: 27px;
  height: 27px;
  flex: none;
  border: 1px solid rgba(139, 26, 26, 0.5);
  border-radius: 4px;
  font-family: var(--serif);
  font-size: 13px;
  color: #8b1a1a;
  background: rgba(139, 26, 26, 0.03);
}
.control-head div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.control-head b,
.library-head b {
  font-family: var(--serif);
  font-size: 14px;
  color: #1a365d;
  letter-spacing: 1px;
}
.control-head em {
  font-style: normal;
  font-size: 9px;
  line-height: 1.5;
  color: rgba(44, 36, 27, 0.5);
}
.prompt-box {
  position: relative;
  display: block;
  margin-top: 12px;
}
.prompt-box textarea {
  width: 100%;
  box-sizing: border-box;
  min-height: 84px;
  padding: 12px 12px 22px;
  border: 1px solid rgba(139, 105, 48, 0.28);
  border-radius: 8px;
  background: rgba(255, 252, 245, 0.9);
  color: #2c241b;
  font-family: var(--serif);
  font-size: 13px;
  line-height: 1.7;
  resize: none;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.prompt-box textarea:focus {
  border-color: rgba(139, 26, 26, 0.45);
  box-shadow: 0 0 0 3px rgba(139, 26, 26, 0.06);
}
.prompt-box textarea::placeholder {
  color: rgba(44, 36, 27, 0.32);
}
.prompt-box span {
  position: absolute;
  right: 10px;
  bottom: 7px;
  font-size: 8px;
  letter-spacing: 0.8px;
  color: rgba(44, 36, 27, 0.35);
}
.preset-row {
  display: flex;
  gap: 7px;
  margin: 10px 0 14px;
  overflow-x: auto;
  scrollbar-width: none;
}
.preset-row::-webkit-scrollbar {
  display: none;
}
.preset-row button {
  flex: none;
  height: 27px;
  padding: 0 12px;
  border: 1px solid rgba(139, 105, 48, 0.3);
  border-radius: 999px;
  background: rgba(201, 168, 76, 0.07);
  color: #7c5c2c;
  font-size: 10px;
  letter-spacing: 1px;
}
.generate-btn {
  position: relative;
  width: 100%;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: 1px solid rgba(139, 26, 26, 0.55);
  border-radius: 8px;
  background: linear-gradient(102deg, #7a1717 0%, #9d2b22 52%, #7a1717 100%);
  color: #fbf3e3;
  font-family: var(--serif);
  font-size: 15px;
  letter-spacing: 3px;
  box-shadow: 0 10px 22px rgba(110, 30, 20, 0.2), inset 0 1px rgba(255, 240, 210, 0.18);
  overflow: hidden;
}
.generate-btn::after {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  width: 38%;
  left: -60%;
  background: linear-gradient(100deg, transparent, rgba(255, 238, 200, 0.22), transparent);
  animation: shine 4.2s infinite;
}
.generate-btn:disabled {
  opacity: 0.72;
}
.gen-seal {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border: 1px solid rgba(255, 232, 190, 0.7);
  border-radius: 3px;
  font-style: normal;
  font-size: 13px;
  letter-spacing: 0;
}
.generate-btn em {
  font-style: normal;
  font-size: 8px;
  letter-spacing: 2px;
  color: rgba(251, 243, 227, 0.5);
}
.mode-note {
  margin: 9px 0 0;
  text-align: center;
  font-size: 8px;
  letter-spacing: 0.5px;
  color: rgba(44, 36, 27, 0.38);
}
.result-card {
  animation: rise 0.5s ease both;
  border-color: rgba(139, 105, 48, 0.45);
}
.result-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}
.result-kicker {
  font-size: 9px;
  letter-spacing: 2px;
  color: #8a6a37;
}
.result-head h2 {
  margin: 6px 0 5px;
  font-family: var(--serif);
  font-size: 23px;
  letter-spacing: 3px;
  color: #1a365d;
}
.result-head p {
  margin: 0;
  max-width: 240px;
  font-size: 10px;
  line-height: 1.7;
  color: rgba(44, 36, 27, 0.55);
}
.result-seal {
  height: 26px;
  padding: 0 8px;
  display: grid;
  place-items: center;
  flex: none;
  border: 1px solid rgba(139, 26, 26, 0.6);
  border-radius: 3px;
  font-family: var(--serif);
  font-size: 10px;
  letter-spacing: 1.4px;
  color: #8b1a1a;
  background: rgba(139, 26, 26, 0.04);
  transform: rotate(2deg);
}
.result-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  margin: 14px 0 10px;
}
.result-metrics div {
  padding: 9px 4px;
  border: 1px solid rgba(139, 105, 48, 0.2);
  border-radius: 6px;
  background: rgba(255, 252, 245, 0.8);
  text-align: center;
}
.result-metrics b {
  display: block;
  font-family: var(--serif);
  font-size: 15px;
  color: #8b1a1a;
  letter-spacing: 0.4px;
}
.result-metrics span {
  font-size: 8px;
  letter-spacing: 0.5px;
  color: rgba(44, 36, 27, 0.45);
}
.result-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.result-meta span {
  padding: 4px 8px;
  border-radius: 4px;
  background: rgba(139, 105, 48, 0.08);
  color: #7c5c2c;
  font-size: 9px;
  letter-spacing: 0.6px;
}
.pipeline-list {
  list-style: none;
  margin: 14px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.pipeline-list li {
  display: grid;
  grid-template-columns: 20px 70px 1fr auto;
  align-items: center;
  gap: 6px;
  padding: 7px 0;
  border-bottom: 1px dashed rgba(139, 105, 48, 0.18);
  font-size: 9px;
}
.pipeline-list .check {
  display: grid;
  place-items: center;
  width: 15px;
  height: 15px;
  border-radius: 50%;
  background: rgba(139, 26, 26, 0.08);
  color: #8b1a1a;
  font-size: 8px;
  font-style: normal;
}
.pipeline-list b {
  font-family: var(--serif);
  color: #3b2f22;
  font-weight: 600;
  letter-spacing: 0.8px;
}
.pipeline-list span {
  color: rgba(44, 36, 27, 0.42);
  letter-spacing: 0.3px;
}
.pipeline-list em {
  font-style: normal;
  color: rgba(124, 92, 44, 0.6);
  font-size: 8px;
}
.license {
  margin: 12px 0 0;
  font-size: 8px;
  line-height: 1.6;
  letter-spacing: 0.3px;
  color: rgba(44, 36, 27, 0.36);
}
.result-match {
  margin: 10px 0 0;
  padding: 7px 10px;
  border: 1px dashed rgba(139, 105, 48, 0.34);
  border-radius: 6px;
  background: rgba(201, 168, 76, 0.06);
  font-size: 9px;
  line-height: 1.6;
  letter-spacing: 0.4px;
  color: #7c5c2c;
}
.result-actions {
  display: flex;
  gap: 8px;
  margin-top: 14px;
}
.result-actions button,
.result-actions a {
  flex: 1;
  min-width: 0;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 7px;
  font-family: var(--serif);
  font-size: 12px;
  letter-spacing: 1.6px;
  text-decoration: none;
}
.result-actions .collect {
  border: 1px solid rgba(139, 26, 26, 0.5);
  background: rgba(139, 26, 26, 0.06);
  color: #8b1a1a;
}
.result-actions .collect.on {
  background: linear-gradient(102deg, #7a1717, #9d2b22);
  color: #fbf3e3;
}
.result-actions .export {
  border: 1px solid rgba(139, 105, 48, 0.45);
  background: rgba(250, 246, 236, 0.9);
  color: #5c4626;
}
.result-actions .works {
  border: 1px solid rgba(26, 54, 93, 0.4);
  background: rgba(26, 54, 93, 0.06);
  color: #1a365d;
}
.lab-live.off {
  color: #8a6a37;
}
.lab-live.off i {
  background: #8a6a37;
  box-shadow: 0 0 0 3px rgba(138, 106, 55, 0.12);
  animation: none;
}
.library-head {
  justify-content: space-between;
  align-items: center;
}
.library-head div {
  display: flex;
  align-items: center;
  gap: 10px;
}
.library-head em {
  font-style: normal;
  font-size: 8px;
  letter-spacing: 0.8px;
  color: rgba(44, 36, 27, 0.42);
}
.library-scroll {
  display: flex;
  gap: 9px;
  margin-top: 12px;
  overflow-x: auto;
  padding-bottom: 4px;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
}
.library-scroll::-webkit-scrollbar {
  display: none;
}
.library-item {
  scroll-snap-align: start;
  flex: none;
  width: 112px;
  padding: 10px;
  text-align: left;
  border: 1px solid rgba(139, 105, 48, 0.22);
  border-radius: 8px;
  background: rgba(255, 252, 245, 0.75);
  color: inherit;
  transition: border-color 0.2s, transform 0.2s;
}
.library-item.active {
  border-color: rgba(139, 26, 26, 0.55);
  box-shadow: 0 0 0 2px rgba(139, 26, 26, 0.05) inset;
}
.library-item:active {
  transform: scale(0.97);
}
.library-item i {
  display: block;
  width: 100%;
  height: 34px;
  border-radius: 5px;
  margin-bottom: 7px;
  opacity: 0.9;
}
.library-item b {
  display: block;
  font-family: var(--serif);
  font-size: 13px;
  letter-spacing: 1.4px;
  color: #1a365d;
}
.library-item span,
.library-item em {
  display: block;
  font-style: normal;
  font-size: 8px;
  letter-spacing: 0.6px;
  color: rgba(44, 36, 27, 0.45);
}
.library-item em {
  margin-top: 3px;
  color: rgba(124, 92, 44, 0.62);
}
.library-hint {
  margin: 8px 0 0;
  font-size: 9px;
  color: rgba(124, 92, 44, 0.62);
}
.pipeline-mask {
  position: fixed;
  inset: 0;
  z-index: 90;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(36, 28, 20, 0.55);
  backdrop-filter: blur(6px);
}
.pipeline-panel {
  width: min(360px, 100%);
  padding: 20px;
  border: 1px solid rgba(139, 105, 48, 0.6);
  border-radius: 12px;
  background:
    linear-gradient(180deg, #fbf6ea, #f2e9d6);
  box-shadow: 0 26px 60px rgba(40, 30, 18, 0.35), inset 0 0 0 4px rgba(255, 252, 244, 0.6);
}
.pipeline-title {
  display: flex;
  align-items: center;
  gap: 11px;
}
.pipeline-seal {
  width: 28px;
  height: 28px;
  flex: none;
  display: grid;
  place-items: center;
  border: 1.5px solid rgba(139, 26, 26, 0.7);
  border-radius: 3px;
  color: #8b1a1a;
  font-family: var(--serif);
  font-style: normal;
  font-size: 15px;
  transform: rotate(-3deg);
  animation: seal-pulse 2s infinite;
}
.pipeline-title div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.pipeline-title b {
  font-family: var(--serif);
  font-size: 13px;
  letter-spacing: 1px;
  color: #1a365d;
}
.pipeline-title span {
  font-size: 9px;
  color: rgba(44, 36, 27, 0.5);
  letter-spacing: 0.6px;
}
.pipeline-title em {
  margin-left: auto;
  font-style: normal;
  font-family: var(--serif);
  font-size: 20px;
  color: #8b1a1a;
}
.pipeline-bar {
  height: 3px;
  margin: 14px 0 16px;
  border-radius: 2px;
  background: rgba(139, 105, 48, 0.16);
  overflow: hidden;
}
.pipeline-bar i {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #8b1a1a, #c9a84c);
  transition: width 0.5s ease;
}
.pipeline-panel ol {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.pipeline-panel li {
  display: grid;
  grid-template-columns: 14px 1fr auto;
  gap: 9px;
  align-items: center;
  opacity: 0.45;
  transition: opacity 0.3s;
}
.pipeline-panel li.active,
.pipeline-panel li.done {
  opacity: 1;
}
.pipeline-panel li > i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  border: 1px solid rgba(139, 105, 48, 0.6);
}
.pipeline-panel li.active > i {
  background: #8b1a1a;
  border-color: #8b1a1a;
  box-shadow: 0 0 0 3px rgba(139, 26, 26, 0.1);
  animation: blink 1.2s infinite;
}
.pipeline-panel li.done > i {
  background: #c9a84c;
  border-color: #c9a84c;
}
.pipeline-panel li div {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.pipeline-panel li b {
  font-family: var(--serif);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1px;
  color: #3b2f22;
}
.pipeline-panel li span {
  font-size: 8px;
  color: rgba(44, 36, 27, 0.45);
}
.pipeline-panel li em {
  font-style: normal;
  font-size: 8px;
  letter-spacing: 1px;
  color: rgba(124, 92, 44, 0.5);
}
.pipeline-panel li.active em {
  color: #8b1a1a;
}
.pipeline-panel li.done em {
  color: #a07a33;
}
.pipeline-panel > p {
  margin: 16px 0 0;
  font-size: 8px;
  letter-spacing: 1px;
  text-align: center;
  color: rgba(44, 36, 27, 0.38);
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.28s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
@keyframes shine-scan {
  from { background-position: 0 -100%; }
  to { background-position: 0 200%; }
}
@keyframes shine {
  0% { left: -60%; }
  55%, 100% { left: 130%; }
}
@keyframes seal-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(139, 26, 26, 0.16); }
  50% { box-shadow: 0 0 0 5px rgba(139, 26, 26, 0.03); }
}
@keyframes rise {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: none; }
}
@media (prefers-reduced-motion: reduce) {
  .stage-shine,
  .generate-btn::after,
  .ring-b,
  .pipeline-seal,
  .scan-cube {
    animation: none;
  }
}
</style>
