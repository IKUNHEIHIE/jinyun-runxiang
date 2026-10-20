<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  api,
  post,
  mediaUrl,
  requireSession,
  notify,
  session,
  loadProfile,
} from "../api";
import { designImage, designIcon } from "../design";
import { saveAsset } from "../files";
import BronzeCanvas from "../components/BronzeCanvas.vue";
import ShadowWorkshop from "../components/ShadowWorkshop.vue";
import LacquerWorkshop from "../components/LacquerWorkshop.vue";
import WorkshopGenerationMode from "../components/WorkshopGenerationMode.vue";
import WorkshopReview from "../components/WorkshopReview.vue";
const route = useRoute(),
  router = useRouter(),
  type = computed(() => String(route.params.tool));
const toolType = computed(
  () =>
    ({ bronze: "BRONZE", shadow: "SHADOW_PUPPET", lacquer: "EMBROIDERY" })[
      type.value
    ] || "SHADOW_PUPPET",
);
const title = computed(
  () =>
    ({
      bronze: "AI青铜纹样工坊",
      shadow: "蓟州皮影 · 千年光影",
      lacquer: "漆绣智绘",
    })[type.value] || "非遗工坊",
);
const prompt = ref(""),
  role = ref("生"),
  color = ref("#B85450"),
  task = ref<any>(),
  error = ref(""),
  busy = ref(false),
  uploading = ref(false),
  publishing = ref(false);
const sketch = ref(""),
  faceStyle = ref("CLASSIC"),
  restoring = ref(false),
  favoriteBusy = ref(false),
  localPattern = ref("FLORAL"),
  selectedResult = ref("colored_image_url");
const bronzeGenerating = ref(false);
const generationMode = ref("LOCAL");
const imageCapabilities = ref({ image_generation: false, image_edit: false });
const quota = ref<{ used_today: number; remaining_today: number; daily_limit: number } | null>(null);
const online = ref(typeof navigator === "undefined" ? true : navigator.onLine);
const setOnline = () => {
  online.value = navigator.onLine;
};
window.addEventListener("online", setOnline);
window.addEventListener("offline", setOnline);
const reviewImageUrl = computed(() => {
  const result = task.value?.result;
  if (task.value?.status !== "SUCCESS" || !result) return "";
  return (
    result.colored_image_url || result.rendered_image_url || result.image_url || ""
  );
});
const reviewTitle = computed(() => task.value?.result?.title || title.value);
const reviewHeritage = computed(
  () =>
    ({ bronze: "BRONZE", shadow: "SHADOW_PUPPET", lacquer: "EMBROIDERY" })[
      type.value
    ] || "SHADOW_PUPPET",
);
let pendingCreate: { signature: string; requestId: string } | undefined;
const bronzeRenderStyle = ref("青铜氧化"),
  bronzePattern = ref("饕餮纹");
function openBronzeGenerator(renderStyle: string, pattern: string) {
  bronzeRenderStyle.value = renderStyle;
  bronzePattern.value = pattern;
  bronzeGenerating.value = true;
}
function backToWorkshop() {
  window.history.state.back ? router.back() : router.replace("/ai-workshop");
}
const activeResultUrl = computed(
  () =>
    task.value?.result?.[selectedResult.value] ||
    task.value?.result?.rendered_image_url,
);
const working = computed(
  () => busy.value || ["QUEUED", "RUNNING"].includes(task.value?.status),
);
let pollTimer: ReturnType<typeof setTimeout> | undefined;
let alive = true;
function context() {
  return {
    token: session.token,
    uid: session.profile?.id,
    type: type.value,
    version: restoreVersion,
  };
}
function current(c: ReturnType<typeof context>) {
  return (
    alive &&
    c.token === session.token &&
    c.uid === session.profile?.id &&
    c.type === type.value &&
    c.version === restoreVersion
  );
}
async function poll() {
  if (!alive || !task.value?.task_id) return;
  const id = task.value.task_id;
  const c = context();
  clearTimeout(pollTimer);
  try {
    const result = await api("/ai/tasks/" + id);
    if (!current(c) || task.value?.task_id !== id) return;
    task.value = result;
    if (result.status === "SUCCESS") {
      if (!result.result?.[selectedResult.value]) selectedResult.value = "colored_image_url";
      bronzeGenerating.value = false;
      try {
        await loadProfile();
      } catch {
        if (current(c)) notify("创作已保存，账户数据暂未刷新");
      }
    }
    if (["QUEUED", "RUNNING"].includes(result.status))
      pollTimer = setTimeout(poll, 1500);
    else if (result.status === "FAILED")
      error.value = result.error_message || "创作失败，请重试";
  } catch (e) {
    if (current(c)) error.value = (e as Error).message;
  }
}
async function create() {
  if (!requireSession() || working.value || restoring.value || uploading.value)
    return;
  if (!online.value) {
    error.value = "当前离线，恢复网络后才能开始创作";
    return;
  }
  if (!prompt.value.trim()) {
    error.value = "先写下你的创作灵感吧";
    return;
  }
  busy.value = true;
  error.value = "";
  clearTimeout(pollTimer);
  const c = context();
  try {
    const body = {
      tool_type: toolType.value,
      generation_mode: generationMode.value,
      input_payload: {
        prompt: prompt.value,
        role_type: role.value + "角",
        face_style: faceStyle.value,
        local_pattern:
          type.value === "lacquer" ? localPattern.value : undefined,
        color_palette:
          type.value === "lacquer"
            ? [color.value, "#D4AF37", "#2D5A4A", "#1A1817", "#F7F4ED"]
            : [color.value, "#D6A85C", "#2F4F4F", "#1A1A1A"],
        pattern_type: type.value === "bronze" ? bronzePattern.value : "饕餮纹",
        sketch_url: sketch.value || undefined,
        style: type.value === "bronze" ? bronzeRenderStyle.value : undefined,
      },
    };
    if (generationMode.value === "AI" && sketch.value && !imageCapabilities.value.image_edit) {
      throw new Error("当前模型未启用参考图编辑，请移除参考图后重试");
    }
    const signature = JSON.stringify(body);
    if (!pendingCreate || pendingCreate.signature !== signature) {
      pendingCreate = { signature, requestId: typeof crypto !== "undefined" && crypto.randomUUID
        ? crypto.randomUUID() : "create-" + Date.now().toString(36) + Math.random().toString(36).slice(2) };
    }
    const result = await post("/ai/tasks", { ...body, request_id: pendingCreate.requestId });
    if (!current(c)) return;
    if (result?.quota) quota.value = result.quota;
    pendingCreate = undefined;
    task.value = result;
    if (route.query.task_id) {
      const query = { ...route.query };
      delete query.task_id;
      await router.replace({ path: route.path, query });
      return;
    }
    await poll();
  } catch (e) {
    if (current(c)) error.value = (e as Error).message;
  } finally {
    if (current(c)) busy.value = false;
  }
}
function retry() {
  error.value = "";
  if (task.value && ["QUEUED", "RUNNING"].includes(task.value.status)) void poll();
  else void create();
}
async function cancel() {  const c = context(),
    id = task.value?.task_id;
  if (!id) return;
  try {
    await post("/ai/tasks/" + id + "/cancel");
    if (!current(c) || task.value?.task_id !== id) return;
    clearTimeout(pollTimer);
    task.value.status = "CANCELLED";
    notify("创作任务已取消");
  } catch (e) {
    if (current(c)) notify((e as Error).message);
  }
}
async function favorite() {
  if (
    !requireSession() ||
    favoriteBusy.value ||
    task.value?.status !== "SUCCESS"
  )
    return;
  const c = context(),
    id = task.value.task_id;
  favoriteBusy.value = true;
  try {
    const result = await post("/ai/tasks/" + id + "/favorite", {
      collected: !task.value.collected,
    });
    if (current(c) && task.value?.task_id === id) {
      task.value.collected = result.collected;
      notify(result.collected ? "已收藏到我的收藏" : "已取消收藏");
    }
  } catch (e) {
    if (current(c)) notify((e as Error).message);
  } finally {
    if (current(c)) favoriteBusy.value = false;
  }
}
async function upload(event: Event) {
  if (!requireSession() || working.value || uploading.value) return;
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  if (file.size > 20 * 1024 * 1024) {
    error.value = "请选择20MB以内的草图";
    return;
  }
  const c = context();
  uploading.value = true;
  error.value = "";
  try {
    const form = new FormData();
    form.append("file", file);
    const result = await api("/ai/assets/upload", {
      method: "POST",
      body: form,
    });
    if (current(c)) sketch.value = result.file_url;
  } catch (e) {
    if (current(c)) error.value = (e as Error).message;
  } finally {
    (event.target as HTMLInputElement).value = "";
    if (current(c)) uploading.value = false;
  }
}
async function download() {
  try {
    const url = activeResultUrl.value || task.value?.result?.print_template_url;
    if (url)
      await saveAsset(
        url,
        "津韵润乡-" + type.value,
        title.value,
      );
  } catch (e) {
    notify((e as Error).message);
  }
}
async function publish() {
  if (!requireSession() || publishing.value || !task.value?.result) return;
  publishing.value = true;
  const c = context();
  try {
    const p = await post("/community/posts", {
      title:
        task.value.result.title || prompt.value.slice(0, 100) || title.value,
      content:
        task.value.result.description || prompt.value || "我的青铜纹样设计",
      category: toolType.value,
      cover_url:
        task.value.result.rendered_image_url ||
        task.value.result.colored_image_url,
      source_task_id: task.value.task_id,
      gallery: [
        ...new Set(
          [
            task.value.result.rendered_image_url,
            task.value.result.colored_image_url,
            task.value.result.line_art_url,
          ].filter((url): url is string => typeof url === "string" && !!url),
        ),
      ],
    });
    if (!current(c)) return;
    notify(p.status === "APPROVED" ? "作品已发布" : "作品已提交审核");
    router.push(p.status === "APPROVED" ? "/community/" + p.id : "/me/posts");
  } catch (e) {
    if (current(c)) notify((e as Error).message);
  } finally {
    if (current(c)) publishing.value = false;
  }
}
function saved(result: any) {
  task.value = result;
  selectedResult.value = "rendered_image_url";
}
let restoreVersion = 0;
async function restore() {
  const version = ++restoreVersion,
    uid = session.profile?.id,
    token = session.token,
    requested = route.query.task_id;
  clearTimeout(pollTimer);
  task.value = undefined;
  prompt.value = "";
  error.value = "";
  bronzeGenerating.value = false;
  busy.value = false;
  uploading.value = false;
  publishing.value = false;
  favoriteBusy.value = false;
  pendingCreate = undefined;
  imageCapabilities.value = { image_generation: false, image_edit: false };
  generationMode.value = "LOCAL";
  restoring.value = false;
  role.value = "生";
  faceStyle.value = "CLASSIC";
  sketch.value = "";
  localPattern.value = "FLORAL";
  color.value =
    type.value === "shadow"
      ? "#8B1A1A"
      : type.value === "lacquer"
        ? "#C4A35A"
        : "#B85450";
  selectedResult.value =
    type.value === "shadow" ? "line_art_url" : "colored_image_url";
  if (!session.token) return;
  restoring.value = true;
  try {
    if (
      requested &&
      (typeof requested !== "string" || !/^[0-9a-f]{32}$/.test(requested))
    )
      throw new Error("创作链接无效");
    const [abilities, result] = await Promise.all([api("/ai/capabilities").catch(() => null), api(
      requested
        ? "/ai/tasks/" + requested
        : "/ai/tasks/latest?tool_type=" + toolType.value,
    )]);
    if (
      !alive ||
      version !== restoreVersion ||
      uid !== session.profile?.id ||
      token !== session.token
    )
      return;
    if (result && result.tool_type !== toolType.value)
      throw new Error("作品不属于当前工坊");
    task.value = result;
    imageCapabilities.value = { image_generation: abilities?.image_generation === true, image_edit: abilities?.image_edit === true };
    generationMode.value = result ? (result.input?._generation_mode === "AI" ? "AI" : "LOCAL")
      : imageCapabilities.value.image_generation ? "AI" : "LOCAL";
    if (result?.result?.generation_method === "ai_image") selectedResult.value = "colored_image_url";
    if (type.value === "bronze" && result?.input) {
      prompt.value = typeof result.input.prompt === "string" ? result.input.prompt : "";
      bronzeRenderStyle.value = typeof result.input.style === "string" ? result.input.style : "青铜氧化";
      bronzePattern.value = typeof result.input.pattern_type === "string" ? result.input.pattern_type : "饕餮纹";
    }
    if (type.value === "shadow" && result?.input) {
      prompt.value =
        typeof result.input.prompt === "string" ? result.input.prompt : "";
      const restoredRole = String(result.input.role_type || "").charAt(0);
      if (["生", "旦", "净", "丑"].includes(restoredRole))
        role.value = restoredRole;
      if (["CLASSIC", "FLORAL", "BOLD"].includes(result.input.face_style))
        faceStyle.value = result.input.face_style;
      const restoredColor = result.input.color_palette?.[0];
      if (
        typeof restoredColor === "string" &&
        /^#[0-9a-f]{6}$/i.test(restoredColor)
      )
        color.value = restoredColor;
      sketch.value =
        typeof result.input.sketch_url === "string"
          ? result.input.sketch_url
          : "";
    }
    if (type.value === "lacquer" && result?.input) {
      prompt.value =
        typeof result.input.prompt === "string" ? result.input.prompt : "";
      if (
        ["FLORAL", "GEOMETRIC", "AUSPICIOUS"].includes(
          result.input.local_pattern,
        )
      )
        localPattern.value = result.input.local_pattern;
      sketch.value = result.result?.reference_sketch_url || "";
      const restoredColor = result.input.color_palette?.[0];
      if (
        typeof restoredColor === "string" &&
        /^#[0-9a-f]{6}$/i.test(restoredColor)
      )
        color.value = restoredColor;
    }
    if (["QUEUED", "RUNNING"].includes(task.value?.status)) await poll();
    else if (task.value?.status === "SUCCESS") {
      try {
        await loadProfile();
      } catch {
        if (alive && version === restoreVersion && token === session.token)
          notify("创作已恢复，账户数据暂未刷新");
      }
    } else if (task.value?.status === "FAILED") {
      error.value =
        task.value.error_message || "上次创作失败，可调整参数后重新提交";
    }
  } catch (e) {
    if (alive && version === restoreVersion && token === session.token)
      error.value = (e as Error).message;
  } finally {
    if (alive && version === restoreVersion && token === session.token)
      restoring.value = false;
  }
}
watch(
  [
    type,
    () => route.query.task_id,
    () => session.token,
    () => session.profile?.id,
  ],
  restore,
  { immediate: true },
);
onUnmounted(() => {
  alive = false;
  clearTimeout(pollTimer);
  window.removeEventListener("online", setOnline);
  window.removeEventListener("offline", setOnline);
});
</script>
<template>
  <ShadowWorkshop
    v-if="type === 'shadow'"
    v-model:role="role"
    v-model:color="color"
    v-model:prompt="prompt"
    v-model:face-style="faceStyle"
    v-model:sketch="sketch"
    v-model:selected-result="selectedResult"
    :task="task"
    :working="working"
    :uploading="uploading"
    :loading="restoring"
    :error="error"
    :publishing="publishing"
    :favorite-busy="favoriteBusy"
    :generation-mode="generationMode"
    @back="backToWorkshop"
    @upload="upload"
    @generate="create"
    @cancel="cancel"
    @retry="retry"
    @export="download"
    @favorite="favorite"
    @publish="publish"
  >
    <template #generation-mode><WorkshopGenerationMode v-model="generationMode" :available="imageCapabilities.image_generation" :editable="imageCapabilities.image_edit" :disabled="working || restoring || uploading" /></template>
  </ShadowWorkshop>
  <LacquerWorkshop
    v-else-if="type === 'lacquer'"
    v-model:prompt="prompt"
    v-model:color="color"
    v-model:pattern="localPattern"
    v-model:sketch="sketch"
    :task="task"
    :result-url="activeResultUrl"
    :working="working"
    :uploading="uploading"
    :loading="restoring"
    :error="error"
    :publishing="publishing"
    :favorite-busy="favoriteBusy"
    :generation-mode="generationMode"
    @back="backToWorkshop"
    @upload="upload"
    @generate="create"
    @cancel="cancel"
    @retry="retry"
    @export="download"
    @favorite="favorite"
    @publish="publish"
  >
    <template #generation-mode><WorkshopGenerationMode v-model="generationMode" :available="imageCapabilities.image_generation" :editable="imageCapabilities.image_edit" :disabled="working || restoring || uploading" /></template>
  </LacquerWorkshop>
  <div v-else class="editor-page bronze" data-design-node="40:55030">
    <button class="bronze-back" aria-label="返回上一页" @click="backToWorkshop">
      <img :src="designIcon('layer-40-55030', '40:55060')" alt="" />
    </button>
    <header class="editor-hero">
      <img
        class="bronze-header-rule"
        :src="designImage('layer-40-55030', '5:5326')"
        alt=""
      />
      <span class="bronze-seal" aria-hidden="true">纹</span>
      <p class="eyebrow">武清仿古青铜器经典纹样 · 非遗数字工坊</p>
      <h1>{{ title }}</h1>
    </header>
    <div class="page-padding">
      <BronzeCanvas
        :saved-task="task"
        :favorite-busy="favoriteBusy"
        :publishing="publishing"
        @saved="saved"
        @favorite="favorite"
        @generate="openBronzeGenerator"
        @publish="publish"
      />
      <div v-if="bronzeGenerating" class="sheet-overlay">
        <section
          class="generation-form corner-card"
          role="dialog"
          aria-modal="true"
          aria-label="AI生成纹样"
        >
          <button
            class="sheet-close"
            aria-label="关闭生成面板"
            @click="bronzeGenerating = false"
          >
            ×
          </button>
          <h2>AI生成纹样</h2>
          <form @submit.prevent="create">
            <WorkshopGenerationMode v-model="generationMode" :available="imageCapabilities.image_generation" :editable="imageCapabilities.image_edit" :disabled="working || restoring" />
            <label
              >文字描述<textarea
                v-model.trim="prompt"
                required
                maxlength="1000"
                placeholder="描述纹样、色彩和你想表达的非遗故事…"
              />
            </label>
            <p v-if="error" class="form-error" role="alert">{{ error }}</p>
            <button class="primary-button" :disabled="working">
              {{ working ? "正在创作…" : generationMode === 'AI' ? "AI 生成纹样" : "生成本地纹样" }}
            </button>
          </form>
          <div v-if="working" class="task-progress" role="status">
            <div class="progress-track">
              <i :style="{ width: (task?.progress || 0) + '%' }" />
            </div>
            <p>创作处理中 {{ task?.progress || 0 }}%</p>
            <button class="text-button" @click="cancel">取消任务</button>
          </div>
          <button
            v-if="error && ['RUNNING', 'QUEUED'].includes(task?.status)"
            class="outline-button"
            @click="
              error = '';
              poll();
            "
          >
            重新查询任务状态
          </button>
          <button
            v-else-if="error && task?.status === 'FAILED'"
            class="outline-button"
            @click="
              error = '';
              create();
            "
          >
            重新发起创作
          </button>
        </section>
      </div>
    </div>
  </div>
  <WorkshopReview
    v-if="reviewImageUrl"
    :image-url="reviewImageUrl"
    :title="reviewTitle"
    :heritage-type="reviewHeritage"
  />
</template>
<style scoped>
.editor-page {
  background: #faf7f0;
}
.bronze {
  position: relative;
  background: #f5f0e6;
}
.bronze-back {
  position: absolute;
  top: 16px;
  left: 16px;
  width: 38px;
  height: 38px;
  padding: 0;
  z-index: 4;
  display: grid;
  place-items: center;
  border: 1px solid rgba(139, 105, 48, 0.38);
  border-radius: 8px;
  background: rgba(250, 246, 238, 0.9);
}
.bronze-back img {
  width: 16px;
  height: 16px;
  object-fit: contain;
}
.bronze .editor-hero {
  height: 168px;
  padding: 56px 20px 0;
  display: flex;
  flex-direction: column;
  position: relative;
  background: transparent;
}
.bronze .editor-hero::before {
  content: "";
  position: absolute;
  left: 10px;
  right: 10px;
  top: 18px;
  height: 132px;
  border: 1px solid rgba(201, 168, 76, 0.28);
  border-radius: 10px;
  background:
    radial-gradient(circle at 82% 20%, rgba(201, 168, 76, 0.18), transparent 55%),
    linear-gradient(135deg, rgba(201, 168, 76, 0.12), rgba(139, 26, 26, 0.035) 58%, rgba(201, 168, 76, 0.08)),
    #f5f0e6;
}
.bronze .editor-hero > *:not(.bronze-seal) {
  position: relative;
}
.bronze .editor-hero .bronze-header-rule {
  position: absolute;
  left: 10px;
  top: 18px;
  width: calc(100% - 6px);
  height: 3px;
  margin: 0;
  object-fit: fill;
}
.bronze .editor-hero h1 {
  order: 0;
  margin: 0 0 8px;
  font:
    400 35px/36px "Ma Shan Zheng",
    var(--serif);
  color: #1a365d;
  letter-spacing: 2.4px;
}
.bronze .editor-hero .eyebrow {
  order: 1;
  font:
    400 11px/16px "Noto Sans SC",
    sans-serif;
  letter-spacing: 1.6px;
  color: #8a6a37;
}
.bronze-seal {
  position: absolute;
  right: 22px;
  top: 34px;
  z-index: 2;
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border: 1.5px solid rgba(139, 26, 26, 0.7);
  border-radius: 3px;
  color: #8b1a1a;
  background: rgba(250, 246, 238, 0.65);
  font-family: var(--serif);
  font-size: 16px;
  line-height: 1;
  transform: rotate(-4deg);
}
.bronze .page-padding {
  padding: 0;
  width: calc(100% - 6px);
}
.bronze .generation-form {
  position: relative;
  margin: 0;
  width: calc(100% - 36px);
  max-width: 460px;
  max-height: 80dvh;
  overflow: auto;
  background: #faf7f0;
}
.bronze .generation-form > .sheet-close {
  position: absolute;
  right: 12px;
  top: 12px;
  color: #8a6125;
}
.editor-hero {
  text-align: center;
  padding: 36px 20px 24px;
}
.editor-hero h1 {
  font-size: 30px;
  line-height: 1.6;
  color: #8a6125;
  margin: 14px 0;
}
.editor-hero > p:last-of-type {
  font-size: 12px;
  line-height: 1.9;
  color: var(--muted);
}
.editor-hero > img {
  width: 100%;
  max-height: 300px;
  object-fit: contain;
  margin-top: 24px;
}
.lacquer {
  background: #f7f3eb;
}
.lacquer .editor-hero h1 {
  color: #4a7c6f;
}
.design-steps {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 11px;
  margin: 20px 0;
}
.design-steps > span {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
.design-steps b {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 1px solid var(--gold);
  color: var(--clay);
  font-size: 12px;
}
.lacquer-intro {
  padding: 24px;
  margin-bottom: 28px;
}
.lacquer-intro > p {
  font-size: 13px;
  line-height: 2;
  margin-top: 16px;
  color: var(--muted);
}
.lacquer-intro h3 {
  font-size: 16px;
  font-family: var(--serif);
  margin: 24px 0 14px;
}
.craft-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.craft-tags span {
  padding: 7px 10px;
  border: 1px solid var(--gold-light);
  border-radius: 6px;
  font-size: 11px;
}
.generation-form {
  padding: 24px 20px;
  margin: 28px 0;
}
.generation-form > p {
  margin-top: 12px;
}
.generation-form form {
  margin-top: 24px;
}
.sketch-preview {
  width: 100%;
  max-height: 240px;
  object-fit: contain;
  background: white;
  border-radius: 10px;
}
.task-progress {
  margin-top: 20px;
  text-align: center;
  font-size: 12px;
  color: var(--muted);
}
.task-progress > p {
  margin-top: 12px;
}
.generation-result {
  padding: 22px 18px;
  margin: 28px 0;
}
.generated-art {
  width: 100%;
  max-height: 430px;
  object-fit: contain;
  background: #f5f1e8;
  border-radius: 12px;
  margin: 20px 0;
}
.result-tabs {
  display: flex;
  gap: 10px;
  justify-content: center;
}
.result-tabs button {
  font-size: 10px;
  padding: 8px 10px;
  border-radius: 20px;
  border: 1px solid var(--gold-light);
}
.result-tabs .active {
  background: var(--clay);
  color: var(--paper);
}
.result-palette {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin: 20px 0;
}
.result-palette span {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 1px solid var(--gold-light);
}
.result-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}
.result-actions > * {
  flex: 1;
  font-size: 12px;
}
.local-generation-note {
  font-size: 10px;
  line-height: 1.8;
  color: var(--muted);
  padding: 12px 0;
}
</style>
