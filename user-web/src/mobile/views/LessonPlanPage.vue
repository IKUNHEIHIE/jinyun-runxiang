<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from "vue";
import { useRouter } from "vue-router";
import { api, post, session, notify } from "../api";
import { saveApiFile } from "../files";
import { designImage, designIcon } from "../design";
import { formatDate } from "../dates";
interface Plan {
  id: number;
  source: string;
  content: Record<string, any>;
}
interface HistoryItem {
  id: number;
  topic: string;
  title: string;
  grade: string;
  source: string;
  created_at: string;
}
const router = useRouter();
const image = (id: string) => designImage("layer-5-02348", id);
const icon = (id: string) => designIcon("layer-5-02348", id);
const grade = ref(""),
  topic = ref(""),
  duration = ref(45),
  mode = ref<"LOCAL" | "AUTO">("LOCAL");
const result = ref<Plan>(),
  history = ref<HistoryItem[]>([]),
  historyTotal = ref(0),
  cursor = ref<number | null>(null);
const busy = ref(false),
  historyBusy = ref(false),
  openingId = ref<number>(),
  exporting = ref(false);
const error = ref(""),
  historyError = ref(""),
  detailError = ref(""),
  exportError = ref(""),
  capabilityError = ref("");
const expanded = ref(false),
  settingsVisible = ref(false),
  historyVisible = ref(false),
  modelEnabled = ref(false);
const configRegion = ref<HTMLElement>(),
  resultRegion = ref<HTMLElement>();
const grades = ["小学三年级", "小学六年级", "初中", "高中", "大学"];
const themes = [
  "天津皮影戏",
  "杨柳青年画",
  "泥人张彩塑",
  "景泰蓝工艺",
  "苏绣针法",
  "古琴鉴赏",
  "陶瓷文化",
  "京剧脸谱",
];
const templates = [
  {
    topic: "古琴鉴赏",
    grade: "大学",
    detail: "大学 · 音乐系",
    icon: "5:02803",
  },
  { topic: "陶瓷文化", grade: "高中", detail: "高中 · 美术", icon: "5:02820" },
  {
    topic: "京剧脸谱",
    grade: "小学三年级",
    detail: "小学 · 综合实践",
    icon: "",
  },
];
let alive = true,
  epoch = 0,
  detailVersion = 0,
  historyVersion = 0,
  capabilityVersion = 0;
let pendingHistoryKey = "",
  retryIdentity: { body: string; id: string } | undefined;
const current = (token: string, version: number) =>
  alive && !!token && token === session.token && version === epoch;
const textValues = (value: unknown): string[] => {
  if (value == null) return [];
  const values = Array.isArray(value)
    ? value
    : typeof value === "object"
      ? Object.values(value)
      : [value];
  return values
    .filter((v) => v != null)
    .map((v) => (typeof v === "object" ? JSON.stringify(v) : String(v)));
};
const targets = computed(() => textValues(result.value?.content.targets));
const difficult = computed(() => {
  const value = result.value?.content.key_difficult_points;
  return value && typeof value === "object" && !Array.isArray(value)
    ? Object.entries(value).map(([key, text]) => ({
        label: key === "key" ? "重点" : key === "difficult" ? "难点" : key,
        text: textValues(text).join("\n"),
      }))
    : textValues(value).map((text) => ({ label: "重难点", text }));
});
const script = computed(() =>
  textValues(result.value?.content.teacher_script).join("\n"),
);
const steps = computed(() => {
  const value = result.value?.content.teaching_process;
  return Array.isArray(value)
    ? value.map((s, i) =>
        typeof s === "object" && s
          ? {
              title: String(s.step || "教学环节 " + (i + 1)),
              text: textValues(s.content).join("\n"),
            }
          : { title: "教学环节 " + (i + 1), text: String(s) },
      )
    : textValues(value).map((text) => ({ title: "教学过程", text }));
});
const questions = computed(() =>
  textValues(result.value?.content.interactive_questions),
);
const homework = computed(() =>
  textValues(result.value?.content.homework_proposal).join("\n"),
);
async function loadCapabilities() {
  const token = session.token,
    version = epoch,
    serial = ++capabilityVersion;
  try {
    const caps = await api("/mobile/teacher/lesson-plans/capabilities");
    if (!current(token, version) || serial !== capabilityVersion) return;
    modelEnabled.value = !!caps.model_enabled;
    capabilityError.value = "";
    if (!modelEnabled.value) mode.value = "LOCAL";
  } catch {
    if (current(token, version) && serial === capabilityVersion)
      capabilityError.value = "暂时无法确认模型服务，可先使用本地课程模板";
  }
}
async function loadHistory(reset = true, force = false) {
  const token = session.token,
    version = epoch;
  if (!token || (!reset && !cursor.value)) return;
  const before = reset ? null : cursor.value,
    key = token + ":" + (before || "first");
  if (!force && historyBusy.value && pendingHistoryKey === key) return;
  pendingHistoryKey = key;
  const serial = ++historyVersion;
  historyBusy.value = true;
  historyError.value = "";
  try {
    const page = await api(
      "/mobile/teacher/lesson-plans/history?limit=12" +
        (before ? "&before_id=" + before : ""),
    );
    if (!current(token, version) || serial !== historyVersion) return;
    const previous = reset ? [] : history.value,
      seen = new Set(previous.map((r) => r.id));
    history.value = [
      ...previous,
      ...page.items.filter((r: HistoryItem) => !seen.has(r.id)),
    ];
    historyTotal.value = page.total;
    cursor.value = page.next_cursor;
  } catch (e) {
    if (current(token, version) && serial === historyVersion)
      historyError.value = (e as Error).message;
  } finally {
    if (current(token, version) && serial === historyVersion) {
      historyBusy.value = false;
      pendingHistoryKey = "";
    }
  }
}
async function revealResult(token: string, version: number, serial: number) {
  await nextTick();
  if (current(token, version) && serial === detailVersion)
    resultRegion.value?.scrollIntoView({ behavior: "smooth", block: "start" });
}
async function generate() {
  if (busy.value) return;
  error.value = "";
  if (
    !grade.value ||
    !topic.value ||
    !Number.isInteger(Number(duration.value)) ||
    duration.value < 10 ||
    duration.value > 240
  ) {
    error.value = "请选择学段和主题，课堂时长应为10至240分钟";
    return;
  }
  if (mode.value === "AUTO" && !modelEnabled.value) {
    error.value = "模型服务尚未启用，请选择本地课程模板";
    return;
  }
  const token = session.token,
    version = epoch,
    serial = ++detailVersion;
  if (!token) return;
  const body = {
    grade: grade.value,
    topic: topic.value,
    duration_minutes: Number(duration.value),
    mode: mode.value,
  };
  const fingerprint = JSON.stringify(body);
  if (retryIdentity?.body !== fingerprint)
    retryIdentity = { body: fingerprint, id: crypto.randomUUID() };
  busy.value = true;
  openingId.value = undefined;
  detailError.value = "";
  exportError.value = "";
  try {
    const plan = await post<Plan>("/mobile/teacher/lesson-plans", {
      ...body,
      request_id: retryIdentity!.id,
    });
    if (!current(token, version) || serial !== detailVersion) return;
    result.value = plan;
    expanded.value = false;
    retryIdentity = undefined;
    notify("教案已生成并保存");
    void loadHistory(true, true);
    void revealResult(token, version, serial);
  } catch (e) {
    if (current(token, version) && serial === detailVersion)
      error.value = (e as Error).message;
  } finally {
    if (current(token, version) && serial === detailVersion) busy.value = false;
  }
}
async function open(id: number) {
  if (busy.value || openingId.value === id) return;
  const token = session.token,
    version = epoch,
    serial = ++detailVersion;
  openingId.value = id;
  detailError.value = "";
  exportError.value = "";
  try {
    const plan = await api<Plan>("/mobile/teacher/lesson-plans/" + id);
    if (!current(token, version) || serial !== detailVersion) return;
    result.value = plan;
    expanded.value = false;
    historyVisible.value = false;
    void revealResult(token, version, serial);
  } catch (e) {
    if (current(token, version) && serial === detailVersion)
      detailError.value = (e as Error).message;
  } finally {
    if (current(token, version) && serial === detailVersion)
      openingId.value = undefined;
  }
}
async function exportPpt() {
  if (!result.value || exporting.value || busy.value || openingId.value) return;
  const token = session.token,
    version = epoch,
    serial = detailVersion,
    plan = result.value;
  const valid = () =>
    current(token, version) &&
    serial === detailVersion &&
    result.value?.id === plan.id;
  exporting.value = true;
  exportError.value = "";
  try {
    await saveApiFile(
      "/mobile/teacher/lesson-plans/" + plan.id + "/pptx",
      String(plan.content.topic || "非遗课程") + ".pptx",
      valid,
    );
  } catch (e) {
    if (valid()) exportError.value = (e as Error).message;
  } finally {
    if (current(token, version)) exporting.value = false;
  }
}
function selectTemplate(template: (typeof templates)[number]) {
  if (busy.value) return;
  grade.value = template.grade;
  topic.value = template.topic;
  configRegion.value?.scrollIntoView({ behavior: "smooth", block: "start" });
}
function back() {
  if (window.history.state?.back) router.back();
  else void router.replace("/teacher");
}
function initialize() {
  if (session.token) {
    void loadCapabilities();
    void loadHistory();
  }
}
watch(
  () => session.token,
  () => {
    epoch++;
    detailVersion++;
    historyVersion++;
    capabilityVersion++;
    result.value = undefined;
    history.value = [];
    historyTotal.value = 0;
    cursor.value = null;
    busy.value =
      historyBusy.value =
      exporting.value =
      modelEnabled.value =
        false;
    openingId.value = undefined;
    settingsVisible.value = historyVisible.value = expanded.value = false;
    error.value =
      historyError.value =
      detailError.value =
      exportError.value =
      capabilityError.value =
        "";
    grade.value = topic.value = "";
    duration.value = 45;
    mode.value = "LOCAL";
    retryIdentity = undefined;
    pendingHistoryKey = "";
    initialize();
  },
  { flush: "sync" },
);
onMounted(initialize);
onUnmounted(() => {
  alive = false;
  epoch++;
  detailVersion++;
  historyVersion++;
  capabilityVersion++;
});
</script>
<template>
  <main class="lesson-planning" data-design-node="5:02348">
    <header class="planning-hero" data-design-node="5:02838">
      <img class="hero-ornament" :src="icon('5:02891')" alt="" />
      <button class="planning-back" aria-label="返回教学工坊" @click="back">
        <img :src="icon('5:02842')" alt="" />
      </button>
      <div class="hero-title" data-design-node="5:02843">
        <h1>智能备课·工坊</h1>
        <p>非遗文化 · 一键生成教案与课件</p>
        <div class="planning-seal" aria-hidden="true">
          <span>匠心</span><img :src="icon('5:02848')" alt="" /><span
            >备课</span
          >
        </div>
      </div>
    </header>
    <div class="planning-body">
      <section
        ref="configRegion"
        class="planning-config"
        data-design-node="5:02715"
      >
        <img class="config-ornament" :src="icon('5:02732')" alt="" />
        <h2 class="marked-heading">课程配置</h2>
        <form @submit.prevent="generate">
          <label for="plan-grade">选择学段</label
          ><select id="plan-grade" v-model="grade" :disabled="busy" required>
            <option disabled value="">请选择学段</option>
            <option v-for="g in grades" :key="g">{{ g }}</option>
          </select>
          <label for="plan-topic">非遗主题</label
          ><select id="plan-topic" v-model="topic" :disabled="busy" required>
            <option disabled value="">请选择非遗主题</option>
            <option v-for="t in themes" :key="t">{{ t }}</option>
          </select>
          <button class="generate-button" :disabled="busy">
            <img :src="icon('5:02784')" alt="" />生成教案与课件
          </button>
        </form>
        <div v-if="busy" class="generation-progress" role="status">
          <img :src="icon('5:02762')" alt="" />正在生成中…
        </div>
        <button v-else class="planning-options" @click="settingsVisible = true">
          <span
            >{{ duration }}分钟 ·
            {{ mode === "LOCAL" ? "本地课程模板" : "模型辅助" }}</span
          ><b>设置</b>
        </button>
        <p v-if="error" class="plan-error" role="alert">{{ error }}</p>
      </section>
      <p v-if="openingId" class="plan-status" role="status">
        正在读取备课方案…
      </p>
      <p
        v-if="detailError && !historyVisible"
        class="plan-error standalone"
        role="alert"
      >
        {{ detailError }}
      </p>
      <article
        v-if="result"
        ref="resultRegion"
        class="lesson-plan-result"
        aria-label="已保存的备课方案"
      >
        <header class="result-heading" data-design-node="5:02521">
          <img class="result-rule top" :src="image('5:02526')" alt="" /><img
            class="result-rule bottom"
            :src="image('5:02529')"
            alt=""
          />
          <span class="document-icon"
            ><img :src="icon('5:02547')" alt=""
          /></span>
          <div>
            <h2>{{ result.content.title }}</h2>
            <p>{{ result.content.grade }} · {{ result.content.duration }}</p>
          </div>
          <small>已生成</small>
        </header>
        <section class="plan-panel target-panel" data-design-node="5:02360">
          <h2><img :src="icon('5:02392')" alt="" />教学目标</h2>
          <ol>
            <li v-for="(target, i) in targets" :key="i">
              <span>{{ i + 1 }}</span>
              <p>{{ target }}</p>
            </li>
          </ol>
          <p v-if="!targets.length" class="plan-empty">此方案未提供教学目标</p>
        </section>
        <section class="plan-panel difficulty-panel" data-design-node="5:02579">
          <h2><img :src="icon('5:02619')" alt="" />教学重难点</h2>
          <div class="difficulty-grid">
            <article v-for="(point, i) in difficult" :key="i">
              <strong>{{ point.label }}</strong>
              <p>{{ point.text }}</p>
            </article>
          </div>
          <p v-if="!difficult.length" class="plan-empty">此方案未提供重难点</p>
        </section>
        <section class="plan-panel script-panel" data-design-node="5:02409">
          <h2><img :src="icon('5:02429')" alt="" />课堂讲稿</h2>
          <p class="teacher-script" :class="{ collapsed: !expanded }">
            {{ script || "此方案未提供课堂讲稿" }}
          </p>
          <button
            class="expand-script"
            :aria-expanded="expanded"
            @click="expanded = !expanded"
          >
            {{ expanded ? "收起完整讲稿" : "展开完整讲稿"
            }}<img
              :class="{ rotated: expanded }"
              :src="icon('5:02423')"
              alt=""
            />
          </button>
          <div v-if="expanded" class="plan-extra">
            <h3>教学过程</h3>
            <section v-for="(step, i) in steps" :key="i">
              <h4>{{ step.title }}</h4>
              <p>{{ step.text }}</p>
            </section>
            <p v-if="!steps.length">此方案未提供教学过程</p>
            <h3>互动问题</h3>
            <ol>
              <li v-for="(question, i) in questions" :key="i">
                {{ question }}
              </li>
            </ol>
            <p v-if="!questions.length">此方案未提供互动问题</p>
            <h3>课后作业</h3>
            <p>{{ homework || "此方案未提供课后作业" }}</p>
            <p class="plan-source">生成来源：{{ result.source }}</p>
          </div>
        </section>
        <p class="source-caption">来源：{{ result.source }}</p>
        <button
          class="export-plan"
          :disabled="exporting || busy || !!openingId"
          @click="exportPpt"
        >
          <img :src="icon('5:02575')" alt="" />{{
            exporting ? "正在准备课件…" : "导出PPT课件"
          }}
        </button>
        <p v-if="exportError" class="plan-error standalone" role="alert">
          {{ exportError }}
        </p>
      </article>
      <section v-else class="plan-first-use">
        <h2>让一堂非遗课，从这里开始</h2>
        <p>
          选择学段与主题，生成的教案会保存到历史记录，也可以导出为可编辑课件。
        </p>
      </section>
      <section class="planning-history" data-design-node="5:02620">
        <header class="planning-section-heading">
          <h2 class="marked-heading">历史备课记录</h2>
          <button @click="historyVisible = true">
            查看全部<span v-if="historyTotal">（{{ historyTotal }}）</span>
          </button>
        </header>
        <p v-if="historyError" class="plan-error" role="alert">
          {{ historyError }} <button @click="loadHistory()">重试</button>
        </p>
        <p
          v-if="historyBusy && !history.length"
          class="plan-empty"
          role="status"
        >
          正在读取历史记录…
        </p>
        <button
          v-for="record in history.slice(0, 3)"
          :key="record.id"
          class="history-record"
          :disabled="busy || openingId === record.id"
          @click="open(record.id)"
        >
          <span>{{ record.topic?.slice(0, 1) || "课" }}</span>
          <div>
            <h3>{{ record.topic || record.title }}</h3>
            <p>
              {{ record.grade }} · {{ formatDate(record.created_at, false) }}
            </p>
          </div>
          <small>{{ openingId === record.id ? "读取中" : "已保存" }}</small>
        </button>
        <p
          v-if="!historyBusy && !historyError && !history.length"
          class="plan-empty"
        >
          还没有备课记录，生成第一份教案后会保存在这里
        </p>
      </section>
      <section class="planning-templates" data-design-node="5:02785">
        <h2 class="marked-heading">推荐模板</h2>
        <div class="template-list">
          <button
            v-for="template in templates"
            :key="template.topic"
            :disabled="busy"
            @click="selectTemplate(template)"
          >
            <span class="template-art"
              ><img v-if="template.icon" :src="icon(template.icon)" alt=""
            /></span>
            <h3>{{ template.topic }}</h3>
            <p>{{ template.detail }}</p>
          </button>
        </div>
      </section>
    </div>
    <div
      v-if="settingsVisible"
      class="sheet-overlay"
      @click.self="settingsVisible = false"
    >
      <section
        class="auth-sheet corner-card planning-sheet"
        role="dialog"
        aria-modal="true"
        aria-labelledby="plan-options-title"
      >
        <button
          class="sheet-close"
          aria-label="关闭备课设置"
          @click="settingsVisible = false"
        >
          ×
        </button>
        <h2 id="plan-options-title">备课设置</h2>
        <label
          >课堂时长（分钟）<input
            v-model.number="duration"
            type="number"
            min="10"
            max="240"
            step="1" /></label
        ><label
          >生成方式<select v-model="mode">
            <option value="LOCAL">本地课程模板</option>
            <option value="AUTO" :disabled="!modelEnabled">
              模型辅助{{ modelEnabled ? "" : "（尚未启用）" }}
            </option>
          </select></label
        >
        <p>
          本地模板提供课堂结构与活动建议，请结合教学材料核对和调整。模型辅助失败时会使用本地模板，并在方案中标明来源。
        </p>
        <p v-if="capabilityError" class="plan-error">
          {{ capabilityError }} <button @click="loadCapabilities">重试</button>
        </p>
        <button class="generate-button" @click="settingsVisible = false">
          完成
        </button>
      </section>
    </div>
    <div
      v-if="historyVisible"
      class="sheet-overlay"
      @click.self="historyVisible = false"
    >
      <section
        class="auth-sheet corner-card planning-sheet history-sheet"
        role="dialog"
        aria-modal="true"
        aria-labelledby="plan-history-title"
      >
        <button
          class="sheet-close"
          aria-label="关闭备课历史"
          @click="historyVisible = false"
        >
          ×
        </button>
        <h2 id="plan-history-title">全部备课记录</h2>
        <button
          class="refresh-history"
          :disabled="historyBusy"
          @click="loadHistory()"
        >
          {{ historyBusy ? "正在读取…" : "刷新记录" }}
        </button>
        <p v-if="historyError || detailError" class="plan-error" role="alert">
          {{ historyError || detailError }}
        </p>
        <button
          v-for="record in history"
          :key="record.id"
          class="history-record"
          :disabled="busy || openingId === record.id"
          @click="open(record.id)"
        >
          <span>{{ record.topic?.slice(0, 1) || "课" }}</span>
          <div>
            <h3>{{ record.topic || record.title }}</h3>
            <p>
              {{ record.grade }} · {{ formatDate(record.created_at, false) }}
            </p>
          </div>
          <small>{{ openingId === record.id ? "读取中" : "查看" }}</small>
        </button>
        <p v-if="!historyBusy && !history.length" class="plan-empty">
          暂无备课记录
        </p>
        <button
          v-if="cursor"
          class="load-plans"
          :disabled="historyBusy"
          @click="loadHistory(false)"
        >
          {{ historyBusy ? "正在读取…" : "加载更多" }}
        </button>
      </section>
    </div>
  </main>
</template>
<style scoped>
.lesson-planning {
  --plan-ink: #4a3a3a;
  --plan-muted: #8b7b7b;
  --plan-rose: #c45c5c;
  color: var(--plan-ink);
  background: #fff9f9 url("/design/images/5576fb521ca134e55c7ca0d481dcc303.webp")
    center/cover;
  padding-top: 9px;
  min-height: 100dvh;
}
.planning-hero {
  height: 183px;
  position: relative;
  background: url("/design/images/a2aef60c7c74fe0b299c150a0b28d1a9.webp")
    center/cover;
}
.hero-ornament {
  position: absolute;
  width: 120px;
  height: 60px;
  right: 24px;
  top: 16px;
  opacity: 0.2;
}
.planning-back {
  position: absolute;
  top: 8px;
  left: 16px;
  width: 40px;
  height: 40px;
  border: 1px solid #f5e8b880;
  border-radius: 50%;
  background: #f0e6d0cc;
  display: grid;
  place-items: center;
  z-index: 2;
}
.planning-back img {
  width: 6px;
  height: 12px;
}
.hero-title {
  position: absolute;
  top: 40px;
  left: 16px;
  right: 24px;
  min-height: 103px;
  padding: 16px 60px 16px 13px;
  background: #cdb0ae;
}
.hero-title h1 {
  font: 700 28px/35px var(--serif);
  letter-spacing: 0.7px;
  margin: 0;
  white-space: nowrap;
}
.hero-title p {
  font-size: 14px;
  font-weight: 300;
  line-height: 20px;
  letter-spacing: 0.7px;
  color: var(--plan-muted);
  margin: 8px 0 0 6px;
  white-space: nowrap;
}
.planning-seal {
  position: absolute;
  top: 16px;
  right: 0;
  width: 50px;
  height: 50px;
  border: 2px solid #c45c5c66;
  border-radius: 3px;
  display: flex;
  gap: 2px;
  align-items: center;
  justify-content: center;
  color: var(--plan-rose);
}
.planning-seal span {
  width: 12px;
  font: 700 12px/16px var(--serif);
  writing-mode: vertical-rl;
}
.planning-seal img {
  width: 20px;
  height: 24px;
}
.planning-body {
  padding: 0 20px 31px;
  background: url("/design/images/a2aef60c7c74fe0b299c150a0b28d1a9.webp")
    center/cover;
}
.planning-config {
  position: relative;
  padding: 24px;
  min-height: 404px;
  border-radius: 16px;
  background: #fff9f9;
  box-shadow: 0 4px 20px #c45c5c14;
  scroll-margin-top: 12px;
}
.config-ornament {
  position: absolute;
  right: 52px;
  top: 14px;
  width: 67.2px;
  height: 67.2px;
  opacity: 1;
  pointer-events: none;
}
.marked-heading {
  font-size: 18px;
  font-weight: 600;
  line-height: 28px;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
.marked-heading:before {
  content: "";
  width: 4px;
  height: 20px;
  border-radius: 20px;
  background: var(--plan-rose);
  flex-shrink: 0;
}
.planning-config form {
  display: block;
  gap: 0;
  margin: 20px 0 0;
}
.planning-config label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
  margin-bottom: 8px;
}
.planning-config select {
  display: block;
  width: 100%;
  height: 48px;
  border: 1px solid #e8d0d0;
  border-radius: 12px;
  background: #fffafa;
  background-image: url('/design/images/1300b6d5aa58073b885a353487d01eb4.webp');
  background-repeat: no-repeat;
  background-size: 16px 14px;
  background-position: right 12px center;
  appearance: none;
  padding: 0 34px 0 16px;
  color: var(--plan-ink);
  font-size: 14px;
  margin: 0 0 16px;
}
.planning-config #plan-topic {
  margin-bottom: 0;
}
.generate-button {
  width: 100%;
  height: 52px;
  border: 0;
  border-radius: 14px;
  background: #9f7272;
  color: white;
  font-size: 16px;
  font-weight: 500;
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px #c45c5c4d;
}
.planning-config .generate-button {
  margin-top: 24px;
}
.generate-button img {
  width: 15px;
  height: 15px;
}
.planning-options,
.generation-progress {
  width: 100%;
  min-height: 52px;
  margin-top: 12px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 12px;
}
.planning-options {
  background: #fff0f080;
  border: 1px solid #e8d0d04d;
  color: var(--plan-muted);
  padding: 8px;
}
.planning-options b {
  font-weight: 500;
  color: #9f7272;
  padding: 8px;
}
.generation-progress {
  color: white;
  background: #95606099;
}
.generation-progress img {
  width: 24px;
  height: 24px;
  animation: planning-spin 1.2s linear infinite;
}
@keyframes planning-spin {
  to {
    transform: rotate(360deg);
  }
}
.plan-error {
  color: #a74444;
  font-size: 12px;
  line-height: 1.8;
  margin: 12px 0 0;
  overflow-wrap: anywhere;
}
.plan-error button {
  text-decoration: underline;
  padding: 4px;
}
.plan-error.standalone,
.plan-status {
  padding: 12px;
  border-radius: 12px;
  background: #fff9f9;
  font-size: 13px;
}
.lesson-plan-result {
  margin-top: 24px;
  scroll-margin-top: 12px;
}
.result-heading {
  min-height: 74px;
  position: relative;
  background: white;
  border-radius: 16px 16px 0 0;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.result-heading > div {
  min-width: 0;
  flex: 1;
}
.result-heading h2 {
  font-size: 16px;
  font-weight: 600;
  line-height: 24px;
  margin: 0;
  overflow-wrap: anywhere;
}
.result-heading p {
  color: var(--plan-muted);
  font-size: 12px;
  line-height: 16px;
  margin: 2px 0 0;
}
.document-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #fff0f0;
  flex-shrink: 0;
  display: grid;
  place-items: center;
}
.document-icon img {
  width: 20px;
  height: 20px;
}
.result-heading small {
  flex-shrink: 0;
  border: 1px solid #e8d0d0;
  border-radius: 20px;
  background: #c45c5c0f;
  color: var(--plan-rose);
  font-size: 12px;
  line-height: 18px;
  padding: 4px 12px;
}
.result-rule {
  position: absolute;
  left: 0;
  width: 100%;
  height: 3px;
  opacity: 0.4;
  pointer-events: none;
}
.result-rule.top {
  top: 0;
}
.result-rule.bottom {
  bottom: 0;
}
.plan-panel {
  padding: 16px 20px;
  background: #fff;
  border-top: 1px solid #e8d0d080;
}
.plan-panel h2 {
  font-size: 14px;
  line-height: 20px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 12px;
}
.plan-panel h2 img {
  width: 14px;
  height: 14px;
  object-fit: contain;
}
.target-panel {
  min-height: 213px;
}
.target-panel ol {
  padding: 0;
  margin: 0;
  list-style: none;
  display: grid;
  gap: 8px;
}
.target-panel li {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  min-height: 44px;
}
.target-panel li > span {
  width: 20px;
  height: 20px;
  line-height: 20px;
  font-size: 12px;
  text-align: center;
  background: #fff0f0;
  color: var(--plan-rose);
  border-radius: 50%;
  flex-shrink: 0;
}
.target-panel p {
  font-size: 14px;
  line-height: 22px;
  margin: 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.difficulty-panel {
  min-height: 161px;
}
.difficulty-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.difficulty-grid article {
  min-height: 105px;
  border-radius: 10px;
  padding: 12px;
  background: #fff0f080;
}
.difficulty-grid article:nth-child(even) {
  background: #f0d4b04d;
}
.difficulty-grid strong {
  color: var(--plan-rose);
  font-size: 12px;
  line-height: 17px;
  font-weight: 500;
}
.difficulty-grid article:nth-child(even) strong {
  color: #b78552;
}
.difficulty-grid p {
  font-size: 12px;
  line-height: 16px;
  margin: 7px 0 0;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}
.script-panel {
  margin-top: 9px;
  border: 0;
  border-radius: 0 0 16px 16px;
  min-height: 386px;
}
.teacher-script {
  font-size: 14px;
  line-height: 20px;
  white-space: pre-wrap;
  margin: 0;
  overflow-wrap: anywhere;
}
.teacher-script.collapsed {
  height: 280px;
  overflow: hidden;
}
.expand-script {
  width: 100%;
  min-height: 29px;
  border-top: 1px solid #e8d0d04d;
  margin-top: 12px;
  color: var(--plan-muted);
  font-size: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
}
.expand-script img {
  width: 7px;
  height: 4px;
}
.expand-script img.rotated {
  transform: rotate(180deg);
}
.plan-extra h3 {
  font-size: 14px;
  line-height: 22px;
  margin: 24px 0 12px;
}
.plan-extra h4 {
  font-size: 13px;
  line-height: 20px;
  margin: 16px 0 6px;
}
.plan-extra p,
.plan-extra li {
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.plan-extra ol {
  padding-left: 20px;
}
.plan-extra .plan-source {
  color: var(--plan-muted);
  font-size: 11px;
}
.source-caption {
  width: fit-content;
  max-width: 100%;
  margin: 8px 0;
  padding: 3px 8px;
  border-radius: 6px;
  background: #fff9f9;
  color: var(--plan-muted);
  font-size: 11px;
  line-height: 16px;
}
.export-plan {
  margin: 8px 4px 0;
  width: calc(100% - 8px);
  min-height: 48px;
  border: 2px solid #e8d0d0;
  border-radius: 14px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #9f7272;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 2px 12px #c45c5c1f;
}
.export-plan img {
  width: 18px;
  height: 18px;
}
.plan-first-use {
  background: #fff9f9;
  border: 1px solid #e8d0d0;
  border-radius: 16px;
  padding: 24px 20px;
  margin-top: 24px;
}
.plan-first-use h2 {
  font-size: 16px;
  line-height: 26px;
  margin: 0 0 12px;
}
.plan-first-use p {
  font-size: 13px;
  line-height: 1.9;
  color: var(--plan-muted);
  margin: 0;
}
.planning-history {
  margin-top: 24px;
  min-height: 124px;
}
.planning-section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: 24px;
  margin-bottom: 16px;
  background: #fff9f9;
  border-radius: 8px;
  padding: 4px;
}
.planning-section-heading h2,
.planning-templates > h2 {
  font-size: 16px;
  line-height: 24px;
}
.planning-section-heading button {
  font-size: 12px;
  color: var(--plan-muted);
  min-height: 32px;
  padding: 0 4px;
  flex-shrink: 0;
}
.history-record {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  margin-bottom: 12px;
  background: #fff;
  border: 1px solid #e8d0d080;
  border-radius: 14px;
  width: 100%;
  min-height: 88px;
  text-align: left;
  box-shadow: 0 2px 12px #0000000a;
}
.history-record > span {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  background: #c45c5c1a;
  border-radius: 12px;
  color: var(--plan-rose);
  font: 700 18px/28px var(--serif);
}
.history-record:nth-of-type(even) > span {
  background: #f0d4b066;
  color: #d4a574;
}
.history-record > div {
  min-width: 0;
  flex: 1;
}
.history-record h3 {
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
  margin: 0;
  overflow-wrap: anywhere;
}
.history-record p {
  font-size: 12px;
  line-height: 16px;
  color: var(--plan-muted);
  margin: 7px 0 0;
}
.history-record small {
  font-size: 12px;
  font-weight: 500;
  color: var(--plan-rose);
  white-space: nowrap;
}
.plan-empty {
  color: var(--plan-muted);
  background: #fff9f9;
  padding: 16px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.8;
}
.planning-templates {
  margin-top: 24px;
}
.planning-templates > h2 {
  width: fit-content;
  background: #fff9f9;
  border-radius: 8px;
  padding: 4px;
}
.planning-templates > h2:before {
  background: #d4a574;
}
.template-list {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  scroll-snap-type: x proximity;
  margin: 16px -20px 0;
  padding: 0 20px 8px;
}
.template-list button {
  width: 140px;
  min-height: 147px;
  flex-shrink: 0;
  border-radius: 14px;
  padding: 12px;
  background: white;
  box-shadow: 0 2px 12px #0000000a;
  text-align: left;
  scroll-snap-align: center;
}
.template-art {
  display: grid;
  place-items: center;
  height: 80px;
  background: #fff0f0;
  border-radius: 10px;
}
.template-art img {
  width: 32px;
  height: 32px;
  object-fit: contain;
}
.template-list button:nth-child(2) .template-art {
  background: #f0d4b04d;
}
.template-list h3 {
  font-size: 12px;
  font-weight: 500;
  line-height: 16px;
  margin: 0;
}
.template-list p {
  font-size: 10px;
  line-height: 15px;
  color: var(--plan-muted);
  margin: 4px 0 0;
}
.planning-sheet {
  --ink: #4a3a3a;
  --muted: #8b7b7b;
  position: relative;
  background: #fff9f9;
  color: var(--plan-ink);
}
.planning-sheet h2 {
  font-size: 22px;
}
.planning-sheet label {
  display: block;
  font-size: 13px;
  margin: 20px 0;
}
.planning-sheet input,
.planning-sheet select {
  display: block;
  width: 100%;
  height: 46px;
  margin-top: 8px;
  padding: 0 12px;
  border: 1px solid #e8d0d0;
  border-radius: 10px;
  background: white;
  color: var(--plan-ink);
}
.planning-sheet > p {
  font-size: 12px;
  line-height: 1.9;
  color: var(--plan-muted);
}
.planning-sheet .generate-button {
  margin-top: 20px;
}
.history-sheet .history-record {
  padding: 12px;
}
.history-sheet .history-record > span {
  width: 40px;
  height: 40px;
}
.refresh-history,
.load-plans {
  min-height: 40px;
  padding: 8px 12px;
  font-size: 13px;
  color: #9f7272;
}
.load-plans {
  width: 100%;
  border: 1px solid #e8d0d0;
  border-radius: 12px;
}
@media (max-width: 360px) {
  .hero-title h1 {
    font-size: 26px;
    letter-spacing: 0.3px;
  }
  .hero-title p {
    font-size: 12px;
    letter-spacing: 0.3px;
  }
  .planning-config {
    padding: 24px;
  }
  .result-heading {
    gap: 8px;
    padding: 18px 16px;
  }
  .result-heading small {
    padding: 3px 7px;
  }
  .history-record {
    padding: 12px;
    gap: 10px;
  }
  .history-record > span {
    width: 48px;
    height: 48px;
  }
  .planning-section-heading button {
    font-size: 11px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .generation-progress img {
    animation: none;
  }
}
</style>
