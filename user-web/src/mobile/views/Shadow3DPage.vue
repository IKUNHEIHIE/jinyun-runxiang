<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api, mediaUrl, notify, post, requireSession } from "../api";
import { saveAsset } from "../files";
import { useEvaluation } from "../useEvaluation";
import ShadowPuppet3D from "../components/ShadowPuppet3D.vue";
import GenerationTheater from "../components/GenerationTheater.vue";

type Quota = { used_today: number; remaining_today: number; daily_limit: number };
type SilhouetteResult = {
  task_id: string;
  silhouette_id: string;
  image_url: string;
  title: string;
  poem: string;
  prompt?: string;
  description: string;
  generation_method: string;
  params: { role: string; headwear: string; prop: string };
  width: number;
  height: number;
};

const route = useRoute();
const router = useRouter();
const steps = [
  { name: "选皮", title: "选皮 · 浸制", detail: "取上等驴皮，浸泡刮薄至半透明，绷平阴干，得到一张可透光的皮料。" },
  { name: "描样", title: "描样 · 起稿", detail: "以白描将人物侧影落在皮上，定出头茬、身段、水袖与执物的比例。" },
  { name: "镂刻", title: "镂刻 · 三千刀", detail: "一柄刻刀走完纹样与衣褶，阴阳相济，刀口利落，透光处见精神。" },
  { name: "敷彩", title: "敷彩 · 五色", detail: "以红、绿、黄、黑、白纯色平涂，色块分明，透光后浓而不滞。" },
  { name: "缀结", title: "缀结 · 关节", detail: "头、身、双臂以铜铆钉缀结，松紧得宜，方能抬手、转身、回眸。" },
  { name: "亮影", title: "装杆 · 亮影", detail: "三根竹签系于颈、腕，灯后起舞，一张驴皮便有了呼吸。" },
];
const step = ref(0);
const playing = ref(false);
let playTimer: ReturnType<typeof setInterval> | undefined;

function stopPlay() {
  playing.value = false;
  clearInterval(playTimer);
  playTimer = undefined;
}
function chooseStep(index: number) {
  stopPlay();
  step.value = index;
}
function togglePlay() {
  if (playing.value) {
    stopPlay();
    return;
  }
  if (step.value >= steps.length - 1) step.value = 0;
  playing.value = true;
  playTimer = setInterval(() => {
    if (step.value >= steps.length - 1) {
      stopPlay();
      return;
    }
    step.value += 1;
  }, 2600);
}
const activeStep = computed(() => steps[step.value]);

const prompt = ref("凤冠霞帔，侧身执团扇的旦角，海棠花冠，衣袂微扬");
const role = ref("旦");
const headwear = ref("crown");
const prop = ref("fan");
const generating = ref(false);
const silhouette = ref<SilhouetteResult | null>(null);
const error = ref("");
const roles = ["生", "旦", "净", "丑"];
const headwears = [
  { key: "crown", label: "凤冠" },
  { key: "bun", label: "云髻" },
  { key: "floral", label: "花冠" },
  { key: "feather", label: "翎羽" },
  { key: "scarf", label: "方巾" },
];
const props = [
  { key: "fan", label: "团扇" },
  { key: "folding_fan", label: "折扇" },
  { key: "sword", label: "长剑" },
  { key: "umbrella", label: "纸伞" },
  { key: "branch", label: "花枝" },
];
const taskId = ref("");
const collected = ref(false);
const quota = ref<Quota | null>(null);
const online = ref(typeof navigator === "undefined" ? true : navigator.onLine);
const restoring = ref(false);
const theater = ref(false);
const review = useEvaluation("SHADOW_PUPPET");
let requestToken = 0;
const requestId = () => crypto.randomUUID().replace(/-/g, "");

async function generateSilhouette() {
  if (generating.value) return;
  if (!online.value) {
    notify("当前离线，恢复网络后才能生成剪影");
    return;
  }
  if (!requireSession(route.fullPath)) return;
  if (!prompt.value.trim()) {
    notify("请先写下你想要的剪影人物");
    return;
  }
  const token = ++requestToken;
  generating.value = true;
  theater.value = true;
  error.value = "";
  try {
    const data = await post<SilhouetteResult & { quota?: Quota }>("/ai/silhouette/generate", {
      prompt: prompt.value.trim(),
      role: role.value,
      headwear: headwear.value,
      prop: prop.value,
      request_id: requestId(),
    });
    if (token !== requestToken) return;
    silhouette.value = data;
    taskId.value = data.task_id;
    collected.value = false;
    quota.value = data.quota || null;
  } catch (e) {
    if (token !== requestToken) return;
    error.value = e instanceof Error ? e.message : "剪影生成失败，请稍后重试";
    theater.value = false;
  } finally {
    if (token === requestToken) generating.value = false;
  }
}

async function toggleFavorite() {
  if (!taskId.value) return;
  if (!requireSession(route.fullPath)) return;
  try {
    const data = await post<{ collected: boolean }>(
      "/ai/tasks/" + taskId.value + "/favorite",
      { collected: !collected.value },
    );
    collected.value = data.collected;
    notify(data.collected ? "已加入我的收藏" : "已取消收藏");
  } catch (e) {
    notify(e instanceof Error ? e.message : "收藏状态未能保存，请重试");
  }
}

async function saveSilhouette() {
  if (!silhouette.value) return;
  try {
    await saveAsset(silhouette.value.image_url, silhouette.value.title + ".svg", "津韵润乡剪影");
  } catch (e) {
    notify(e instanceof Error ? e.message : "保存失败，请稍后重试");
  }
}

async function restore(task: string) {
  restoring.value = true;
  try {
    const data = await api<{
      status: string;
      tool_type?: string;
      collected: boolean;
      result: SilhouetteResult | null;
    }>("/ai/tasks/" + task);
    if (data.status !== "SUCCESS" || !data.result) return;
    if (data.tool_type && data.tool_type !== "SILHOUETTE") {
      error.value = "这条作品不是剪影画像，请在工坊里打开对应类型";
      return;
    }
    silhouette.value = data.result;
    taskId.value = data.result.task_id || task;
    collected.value = !!data.collected;
    if (data.result.prompt) prompt.value = data.result.prompt;
  } catch {
    error.value = "历史剪影读取失败，请返回工坊重试";
  } finally {
    restoring.value = false;
  }
}

const setOnline = () => {
  online.value = navigator.onLine;
};

onMounted(() => {
  window.addEventListener("online", setOnline);
  window.addEventListener("offline", setOnline);
  const task = typeof route.query.task_id === "string" ? route.query.task_id : "";
  if (task) void restore(task);
});

async function evaluateSilhouette() {
  if (!silhouette.value) return;
  if (!requireSession(route.fullPath)) return;
  await review.run(
    silhouette.value.image_url,
    silhouette.value.title,
    prompt.value.trim(),
  );
}

function back() {
  window.history.state.back ? router.back() : router.replace("/ai-workshop");
}
onBeforeUnmount(() => {
  stopPlay();
  requestToken += 1;
  window.removeEventListener("online", setOnline);
  window.removeEventListener("offline", setOnline);
});
</script>

<template>
  <div class="shadow-lab">
    <div class="lab-bg" aria-hidden="true"><i class="wash a" /><i class="wash b" /><i class="grain" /></div>

    <GenerationTheater
      v-if="theater"
      title="正在落刀"
      :steps="['解析人物描述', '匹配行当与头冠', '雕刻镂空纹样', '输出高清剪影']"
      :preview="silhouette ? mediaUrl(silhouette.image_url) : ''"
      :stats="[
        {
          label: '画幅',
          value: silhouette ? silhouette.width + '×' + silhouette.height : '600×800',
        },
        { label: '分层', value: '3 层' },
        { label: '引擎', value: '本地模板' },
      ]"
      caption="本地规则模板 · 按行当、头冠、执物与描述拼装，不调用外部生成模型"
      :waiting="generating"
      @done="theater = false"
    />

    <header class="lab-top">
      <button class="back" aria-label="返回 AI 工坊" @click="back">
        <svg viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6" /></svg>
      </button>
      <div class="crumb"><span>AI 工坊</span><i />剪影工坊</div>
      <span class="live" :class="{ off: !online }"><i />{{ online ? "剪影工坊就绪" : "当前离线" }}</span>
    </header>

    <section class="hero">
      <div class="hero-seal" aria-hidden="true"><b>影</b><i /></div>
      <p class="kicker">蓟州皮影 · 三维营造</p>
      <h1>一张驴皮<br /><em>三千刀</em></h1>
      <p class="sub">选皮、描样、镂刻、敷彩、缀结、亮影——六道工序在数字展台中重演</p>
      <div class="stats">
        <span><b>六</b>道工序</span><i />
        <span><b>三</b>根竹签</span><i />
        <span><b>千年</b>光影</span>
      </div>
    </section>

    <section class="stage-card">
      <div class="stage-hud">
        <span class="hud-step">工序 {{ String(step + 1).padStart(2, "0") }} / 06</span>
        <span class="hud-name">{{ activeStep.title }}</span>
      </div>
      <div class="stage-canvas">
        <ShadowPuppet3D :step="step" />
        <div class="screen-glow" aria-hidden="true" />
        <span class="corner tl" /><span class="corner tr" /><span class="corner bl" /><span class="corner br" />
        <div class="stage-caption">
          <span>SHADOW PUPPET / 三维工序</span>
          <b>{{ activeStep.title }}</b>
        </div>
        <div class="stage-tip">光影自动演示</div>
      </div>
      <div class="stage-controls">
        <button class="play" @click="togglePlay">
          <i :class="playing ? 'pause' : 'play-icon'" />
          {{ playing ? "暂停工序" : step >= steps.length - 1 ? "重新演示" : "播放工序" }}
        </button>
        <div class="step-list">
          <button
            v-for="(item, index) in steps"
            :key="item.name"
            :class="{ active: index === step, done: index < step }"
            @click="chooseStep(index)"
          >
            <em>{{ String(index + 1).padStart(2, "0") }}</em>
            {{ item.name }}
          </button>
        </div>
      </div>
    </section>

    <section class="step-note">
      <span class="note-index">{{ String(step + 1).padStart(2, "0") }}</span>
      <div>
        <b>{{ activeStep.title }}</b>
        <p>{{ activeStep.detail }}</p>
      </div>
    </section>

    <section class="generate-card">
      <div class="gen-head">
        <div><span class="kicker">按意生成 · 剪影画像</span><h2>把你想要的角色，刻成一张剪影</h2></div>
        <span class="gen-seal">剪</span>
      </div>
      <div class="choice-row">
        <span>角色</span>
        <button v-for="item in roles" :key="item" :class="{ on: role === item }" @click="role = item">{{ item }}</button>
      </div>
      <div class="choice-row">
        <span>头冠</span>
        <button v-for="item in headwears" :key="item.key" :class="{ on: headwear === item.key }" @click="headwear = item.key">{{ item.label }}</button>
      </div>
      <div class="choice-row">
        <span>执物</span>
        <button v-for="item in props" :key="item.key" :class="{ on: prop === item.key }" @click="prop = item.key">{{ item.label }}</button>
      </div>
      <label class="prompt-box">
        <textarea v-model="prompt" maxlength="300" rows="3" placeholder="例：凤冠霞帔的旦角，侧身执团扇，衣袂微扬" />
        <span>{{ prompt.length }} / 300</span>
      </label>
      <button class="generate-btn" :disabled="generating" @click="generateSilhouette">
        <i>剪</i>
        <span>{{ generating ? "正在落刀…" : "生成剪影画像" }}</span>
        <em>PAPER CUT</em>
      </button>
      <p v-if="error" class="error">{{ error }}</p>
      <p class="mode-note">
        本地规则模板 · 按行当、头冠、执物与描述拼装，不调用外部生成模型{{
          quota ? " · 今日剩余 " + quota.remaining_today + " 次" : ""
        }}
      </p>

      <div v-if="silhouette" class="silhouette-result">
        <div class="result-frame">
          <img :src="mediaUrl(silhouette.image_url)" :alt="silhouette.title" />
        </div>
        <div class="result-copy">
          <span class="result-kicker">剪影已成 · {{ silhouette.params.role }}角</span>
          <h3>{{ silhouette.title }}</h3>
          <p>{{ silhouette.poem }}</p>
          <div class="result-meta">
            <span>{{ headwears.find((i) => i.key === silhouette!.params.headwear)?.label }}</span>
            <span>{{ props.find((i) => i.key === silhouette!.params.prop)?.label }}</span>
          </div>
          <div class="result-actions">
            <button class="save-btn" @click="saveSilhouette">保存剪影</button>
            <button class="collect-btn" :class="{ on: collected }" :aria-pressed="collected" @click="toggleFavorite">
              {{ collected ? "已收藏" : "收藏作品" }}
            </button>
            <button class="review-btn" :disabled="review.busy.value" @click="evaluateSilhouette">
              {{ review.busy.value ? "导师看画中…" : "请导师点评" }}
            </button>
          </div>
          <p v-if="review.error.value" class="error">{{ review.error.value }}</p>
          <div v-if="review.result.value" class="review-card">
            <div class="review-score">
              <b>{{ review.result.value.total_score }}</b>
              <span>{{ "★".repeat(review.result.value.stars) }}{{ "☆".repeat(5 - review.result.value.stars) }}</span>
              <em v-if="review.result.value.energy_reward">+{{ review.result.value.energy_reward }} 能量</em>
            </div>
            <p class="review-comment">{{ review.result.value.mentor_comment }}</p>
            <ul class="review-dims">
              <li v-for="item in Object.values(review.result.value.dimensions)" :key="item.name">
                <span>{{ item.name }}</span><b>{{ item.score }}</b>
                <em>{{ item.feedback }}</em>
              </li>
            </ul>
          </div>
          <RouterLink class="works-link" to="/ai-workshop/works">我的工坊作品</RouterLink>
        </div>
      </div>
      <div v-else class="result-empty">
        <i class="empty-seal">影</i>
        <p>写下人物、头冠与执物，落刀后在此处揭晓</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.shadow-lab {
  position: relative;
  min-height: 100dvh;
  padding: calc(10px + var(--safe-top)) 16px 48px;
  color: #2c241b;
  background: #efe6d6;
  font-family: var(--sans);
  overflow: hidden;
}
.lab-bg { position: absolute; inset: 0; pointer-events: none; }
.grain {
  position: absolute; inset: 0; opacity: 0.5;
  background-image:
    repeating-linear-gradient(0deg, rgba(126, 98, 58, 0.045) 0 1px, transparent 1px 3px),
    repeating-linear-gradient(90deg, rgba(126, 98, 58, 0.03) 0 1px, transparent 1px 4px);
  mask-image: radial-gradient(circle at 50% 20%, #000 0, transparent 85%);
}
.wash { position: absolute; border-radius: 50%; filter: blur(44px); opacity: 0.22; }
.wash.a { top: -70px; right: -60px; width: 260px; height: 260px; background: #b9a077; }
.wash.b { top: 520px; left: -110px; width: 240px; height: 240px; background: #caa77c; }
.lab-top, .hero, .stage-card, .step-note, .generate-card { position: relative; z-index: 1; }
.lab-top { display: flex; align-items: center; gap: 12px; height: 40px; }
.back {
  width: 34px; height: 34px; display: grid; place-items: center;
  border: 1px solid rgba(139, 105, 48, 0.4); border-radius: 8px;
  background: rgba(250, 246, 236, 0.88); color: #5c4626;
}
.back svg { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; }
.crumb { display: flex; align-items: center; gap: 8px; font-size: 11px; letter-spacing: 2px; color: #7c5c2c; }
.crumb span { color: rgba(44, 36, 27, 0.52); }
.crumb i { width: 18px; height: 1px; background: rgba(139, 105, 48, 0.45); }
.live { margin-left: auto; display: flex; align-items: center; gap: 6px; font-size: 9px; letter-spacing: 1.6px; color: #8b1a1a; }
.live i { width: 5px; height: 5px; border-radius: 50%; background: #8b1a1a; box-shadow: 0 0 0 3px rgba(139, 26, 26, 0.1); animation: blink 2s infinite; }
.hero { padding: 24px 4px 18px; }
.hero-seal { position: absolute; top: 10px; right: 2px; width: 86px; height: 86px; display: grid; place-items: center; }
.hero-seal i { position: absolute; inset: 12px; border: 1px dashed rgba(139, 26, 26, 0.3); border-radius: 50%; animation: spin 24s linear infinite; }
.hero-seal b {
  width: 44px; height: 44px; display: grid; place-items: center;
  border: 1.5px solid rgba(139, 26, 26, 0.75); border-radius: 3px;
  color: #8b1a1a; font-family: var(--serif); font-size: 24px; line-height: 1;
  transform: rotate(-4deg); background: rgba(139, 26, 26, 0.035);
}
.kicker { margin: 0 0 8px; font-size: 10px; letter-spacing: 3px; color: #8a6a37; }
.hero h1 { margin: 0; font-family: var(--serif); font-size: 32px; line-height: 1.22; letter-spacing: 2px; color: #1a365d; }
.hero h1 em { font-style: normal; color: #8b1a1a; }
.sub { margin: 10px 0 14px; max-width: 285px; font-size: 11px; line-height: 1.7; letter-spacing: 0.5px; color: rgba(44, 36, 27, 0.58); }
.stats { display: flex; align-items: center; gap: 12px; font-size: 10px; color: rgba(44, 36, 27, 0.55); }
.stats b { margin-right: 4px; font-family: var(--serif); font-size: 16px; color: #1a365d; }
.stats i { width: 1px; height: 14px; background: rgba(139, 105, 48, 0.28); }
.stage-card {
  border: 1px solid rgba(139, 105, 48, 0.6); border-radius: 14px;
  background: #201a13; overflow: hidden;
  box-shadow: 0 18px 40px rgba(60, 44, 22, 0.22), inset 0 0 0 1px rgba(201, 168, 76, 0.18);
}
.stage-hud { display: flex; justify-content: space-between; padding: 10px 14px; font-size: 9px; letter-spacing: 1.8px; color: rgba(216, 190, 138, 0.66); border-bottom: 1px solid rgba(201, 168, 76, 0.18); }
.hud-name { color: #d8be8a; }
.stage-canvas {
  position: relative; height: 390px;
  background: radial-gradient(circle at 50% 44%, rgba(120, 82, 36, 0.45), transparent 68%), linear-gradient(180deg, #1b1510, #100c08);
}
.screen-glow { position: absolute; inset: 12% 8%; pointer-events: none; border-radius: 50%; background: radial-gradient(circle, rgba(247, 226, 184, 0.18), transparent 68%); filter: blur(18px); }
.corner { position: absolute; width: 18px; height: 18px; border: solid rgba(201, 168, 76, 0.7); pointer-events: none; z-index: 2; }
.corner.tl { top: 10px; left: 10px; border-width: 1px 0 0 1px; }
.corner.tr { top: 10px; right: 10px; border-width: 1px 1px 0 0; }
.corner.bl { bottom: 10px; left: 10px; border-width: 0 0 1px 1px; }
.corner.br { bottom: 10px; right: 10px; border-width: 0 1px 1px 0; }
.stage-caption { position: absolute; left: 16px; bottom: 14px; display: flex; flex-direction: column; gap: 2px; pointer-events: none; z-index: 2; }
.stage-caption span { font-size: 8px; letter-spacing: 1.8px; color: rgba(216, 190, 138, 0.55); }
.stage-caption b { font-family: var(--serif); font-size: 19px; color: #f5ead2; letter-spacing: 2px; }
.stage-tip { position: absolute; right: 15px; bottom: 15px; font-size: 8px; letter-spacing: 1.2px; color: rgba(216, 190, 138, 0.42); z-index: 2; }
.stage-controls { padding: 12px; background: #1b1510; border-top: 1px solid rgba(201, 168, 76, 0.16); }
.play {
  width: 100%; height: 38px; display: flex; align-items: center; justify-content: center; gap: 8px;
  border: 1px solid rgba(201, 168, 76, 0.55); border-radius: 6px;
  background: rgba(201, 168, 76, 0.07); color: #e7cf9a;
  font-family: var(--serif); font-size: 13px; letter-spacing: 2px;
}
.play i { width: 0; height: 0; border-top: 5px solid transparent; border-bottom: 5px solid transparent; border-left: 8px solid #d8be8a; }
.play i.pause { width: 7px; height: 10px; border: 0; border-left: 2px solid #d8be8a; border-right: 2px solid #d8be8a; }
.step-list { display: flex; gap: 5px; margin-top: 10px; }
.step-list button {
  flex: 1; min-width: 0; padding: 7px 0 6px; border: 1px solid rgba(201, 168, 76, 0.16);
  border-radius: 6px; background: rgba(201, 168, 76, 0.03); color: rgba(216, 190, 138, 0.48);
  font-family: var(--serif); font-size: 10px; letter-spacing: 1px;
}
.step-list em { display: block; font-style: normal; font-family: var(--sans); font-size: 7px; letter-spacing: 1px; color: rgba(216, 190, 138, 0.28); margin-bottom: 2px; }
.step-list button.done { color: rgba(231, 207, 154, 0.72); border-color: rgba(201, 168, 76, 0.3); }
.step-list button.active { color: #f6ead0; border-color: rgba(201, 168, 76, 0.68); background: rgba(139, 26, 26, 0.35); }
.step-list button.active em { color: #e7cf9a; }
.step-note {
  display: flex; gap: 12px; margin-top: 14px; padding: 14px 16px;
  border: 1px solid rgba(139, 105, 48, 0.28); border-radius: 12px;
  background: linear-gradient(180deg, rgba(252, 248, 239, 0.96), rgba(246, 239, 226, 0.96));
}
.note-index { font-family: var(--serif); font-size: 26px; line-height: 1; color: rgba(139, 26, 26, 0.6); }
.step-note b { display: block; font-family: var(--serif); font-size: 15px; letter-spacing: 1.4px; color: #1a365d; }
.step-note p { margin: 5px 0 0; font-size: 10px; line-height: 1.75; color: rgba(44, 36, 27, 0.6); }
.generate-card {
  margin-top: 16px; padding: 16px;
  border: 1px solid rgba(139, 105, 48, 0.34); border-radius: 14px;
  background: linear-gradient(180deg, rgba(252, 248, 239, 0.97), rgba(246, 239, 226, 0.97));
  box-shadow: 0 10px 28px rgba(90, 70, 40, 0.08);
}
.gen-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.gen-head h2 { margin: 6px 0 0; font-family: var(--serif); font-size: 20px; line-height: 1.4; letter-spacing: 1.4px; color: #1a365d; max-width: 250px; }
.gen-seal { width: 32px; height: 32px; flex: none; display: grid; place-items: center; border: 1.5px solid rgba(139, 26, 26, 0.7); border-radius: 3px; color: #8b1a1a; font-family: var(--serif); font-size: 16px; transform: rotate(-4deg); }
.choice-row { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-top: 12px; }
.choice-row > span { width: 32px; font-size: 10px; letter-spacing: 1px; color: #8a6a37; }
.choice-row button {
  height: 27px; padding: 0 11px; border: 1px solid rgba(139, 105, 48, 0.28); border-radius: 999px;
  background: rgba(201, 168, 76, 0.06); color: #6b5634; font-size: 10px; letter-spacing: 1px;
}
.choice-row button.on { border-color: rgba(139, 26, 26, 0.62); background: rgba(139, 26, 26, 0.08); color: #8b1a1a; }
.prompt-box { position: relative; display: block; margin-top: 14px; }
.prompt-box textarea {
  width: 100%; box-sizing: border-box; min-height: 82px; padding: 12px 12px 22px;
  border: 1px solid rgba(139, 105, 48, 0.28); border-radius: 8px;
  background: rgba(255, 252, 245, 0.92); color: #2c241b;
  font-family: var(--serif); font-size: 13px; line-height: 1.7; resize: none; outline: none;
}
.prompt-box textarea:focus { border-color: rgba(139, 26, 26, 0.45); box-shadow: 0 0 0 3px rgba(139, 26, 26, 0.06); }
.prompt-box span { position: absolute; right: 10px; bottom: 7px; font-size: 8px; color: rgba(44, 36, 27, 0.35); }
.generate-btn {
  width: 100%; height: 48px; margin-top: 12px; display: flex; align-items: center; justify-content: center; gap: 10px;
  border: 1px solid rgba(139, 26, 26, 0.55); border-radius: 8px;
  background: linear-gradient(102deg, #7a1717 0%, #9d2b22 52%, #7a1717 100%);
  color: #fbf3e3; font-family: var(--serif); font-size: 15px; letter-spacing: 3px;
  box-shadow: 0 10px 22px rgba(110, 30, 20, 0.18), inset 0 1px rgba(255, 240, 210, 0.18);
}
.generate-btn:disabled { opacity: 0.72; }
.generate-btn i { width: 22px; height: 22px; display: grid; place-items: center; border: 1px solid rgba(255, 232, 190, 0.7); border-radius: 3px; font-style: normal; font-size: 12px; }
.generate-btn em { font-style: normal; font-size: 8px; letter-spacing: 2px; color: rgba(251, 243, 227, 0.5); }
.error { margin: 10px 0 0; font-size: 10px; color: #a12626; }
.result-empty { margin-top: 14px; padding: 24px; border: 1px dashed rgba(139, 105, 48, 0.3); border-radius: 10px; text-align: center; }
.empty-seal { width: 36px; height: 36px; display: inline-grid; place-items: center; border: 1px solid rgba(139, 26, 26, 0.4); border-radius: 3px; color: rgba(139, 26, 26, 0.55); font-family: var(--serif); font-size: 18px; font-style: normal; transform: rotate(-4deg); }
.result-empty p { margin: 10px 0 0; font-size: 10px; color: rgba(44, 36, 27, 0.45); }
.silhouette-result { margin-top: 16px; }
.result-frame { max-width: 304px; margin: 0 auto; border: 1px solid rgba(139, 105, 48, 0.42); border-radius: 8px; overflow: hidden; background: #f7efe0; box-shadow: 0 10px 24px rgba(80, 58, 28, 0.14); }
.result-frame img { display: block; width: 100%; }
.result-copy { padding-top: 12px; text-align: center; }
.result-kicker { font-size: 8px; letter-spacing: 1.6px; color: #8a6a37; }
.result-copy h3 { margin: 6px 0 0; font-family: var(--serif); font-size: 18px; line-height: 1.4; letter-spacing: 1.6px; color: #1a365d; }
.result-copy p { margin: 6px 0 0; font-family: var(--serif); font-size: 12px; color: #6b5634; }
.result-meta { display: flex; flex-wrap: wrap; justify-content: center; gap: 5px; margin-top: 9px; }
.result-meta span { padding: 3px 7px; border: 1px solid rgba(201, 168, 76, 0.32); border-radius: 4px; font-size: 8px; color: #7c5c2c; }
.save-btn { display: block; margin: 12px auto 0; height: 30px; padding: 0 12px; border: 1px solid rgba(139, 26, 26, 0.5); border-radius: 5px; background: rgba(139, 26, 26, 0.06); color: #8b1a1a; font-family: var(--serif); font-size: 11px; letter-spacing: 1.4px; }
.mode-note { margin: 10px 0 0; font-size: 9px; line-height: 1.6; letter-spacing: 0.3px; color: rgba(44, 36, 27, 0.42); }
.live.off { color: #8a6a37; }
.live.off i { background: #8a6a37; box-shadow: 0 0 0 3px rgba(138, 106, 55, 0.12); animation: none; }
.result-actions { display: flex; gap: 6px; margin-top: 12px; }
.result-actions button {
  flex: 1; min-width: 0; height: 34px; border-radius: 6px;
  font-family: var(--serif); font-size: 11px; letter-spacing: 1.2px;
}
.result-actions .save-btn { margin: 0; }
.result-actions .collect-btn {
  border: 1px solid rgba(139, 105, 48, 0.45); background: rgba(250, 246, 236, 0.9); color: #5c4626;
}
.result-actions .collect-btn.on {
  border-color: rgba(139, 26, 26, 0.6); background: linear-gradient(102deg, #7a1717, #9d2b22); color: #fbf3e3;
}
.result-actions .review-btn {
  border: 1px solid rgba(26, 54, 93, 0.42); background: rgba(26, 54, 93, 0.06); color: #1a365d;
}
.result-actions button:disabled { opacity: 0.6; }
.review-card {
  margin-top: 12px; padding: 12px; text-align: left;
  border: 1px solid rgba(201, 168, 76, 0.42); border-radius: 10px;
  background: linear-gradient(180deg, rgba(252, 248, 239, 0.98), rgba(246, 239, 226, 0.98));
}
.review-score { display: flex; align-items: baseline; gap: 8px; }
.review-score b { font-family: var(--serif); font-size: 26px; line-height: 1; color: #8b1a1a; }
.review-score span { font-size: 12px; letter-spacing: 2px; color: #b8860b; }
.review-score em { margin-left: auto; font-style: normal; font-size: 9px; color: #4a7c6f; }
.review-comment { margin: 8px 0 0; font-family: var(--serif); font-size: 11px; line-height: 1.8; color: #4a3a26; }
.review-dims { margin: 10px 0 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 6px; }
.review-dims li { display: grid; grid-template-columns: 68px 28px 1fr; gap: 6px; align-items: baseline; }
.review-dims span { font-size: 9px; letter-spacing: 0.6px; color: #8a6a37; }
.review-dims b { font-family: var(--serif); font-size: 12px; color: #1a365d; }
.review-dims em { font-style: normal; font-size: 9px; line-height: 1.6; color: rgba(44, 36, 27, 0.6); }
.works-link { display: block; margin-top: 10px; font-size: 10px; letter-spacing: 1.2px; color: #8a6125; text-decoration: none; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
@keyframes spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .hero-seal i, .live i { animation: none; } }
</style>
