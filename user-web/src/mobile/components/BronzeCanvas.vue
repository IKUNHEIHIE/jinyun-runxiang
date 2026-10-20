<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import {
  api,
  post,
  put,
  mediaUrl,
  requireSession,
  notify,
  session,
} from "../api";
import { designImage, designIcon } from "../design";
import { saveBlob, saveAsset } from "../files";
const props = defineProps<{ savedTask?: any; publishing?: boolean; favoriteBusy?: boolean }>();
const emit = defineEmits<{
  saved: [task: any];
  generate: [style: string, pattern: string];
  publish: [];
  favorite: [];
}>();
const patterns = [
  { label: "兽面纹", node: "5:5103", group: "饕餮纹" },
  { label: "云雷纹", node: "5:5058", group: "云雷纹" },
  { label: "回纹", node: "5:5072", group: "回纹" },
  { label: "蟠螭纹", node: "5:5088", group: "蟠螭纹" },
  { label: "凤鸟纹", node: "5:5031", group: "凤鸟纹" },
  { label: "蝉纹", node: "5:5025", group: "蝉纹" },
  { label: "夔龙纹", node: "5:5043", group: "夔龙纹" },
  { label: "蕉叶纹", node: "5:5013", group: "蕉叶纹" },
];
interface Element {
  id: string;
  label: string;
  src: string;
  x: number;
  y: number;
  scale: number;
  rotation: number;
}
interface Snapshot {
  elements: Element[];
  style: string;
}
const elements = ref<Element[]>([]),
  selected = ref(""),
  stage = ref<HTMLElement>(),
  busy = ref(false),
  style = ref("青铜氧化"),
  category = ref("全部纹样"),
  preview = ref("");
const past = ref<Snapshot[]>([]),
  future = ref<Snapshot[]>([]),
  overview = ref<any>(),
  overviewError = ref("");
const active = computed(() =>
  elements.value.find((e) => e.id === selected.value),
);
const generatingPattern = computed(() =>
  active.value?.label === "兽面纹"
    ? "饕餮纹"
    : active.value?.label ||
      (category.value === "全部纹样" ? "饕餮纹" : category.value),
);
const visiblePatterns = computed(() =>
  patterns.filter(
    (p) => category.value === "全部纹样" || p.group === category.value,
  ),
);
const patternTabs = ["全部纹样", ...Array.from(new Set(patterns.map((p) => p.group)))];
const filterFor = (value: string) =>
  value === "鎏金拓印"
    ? "sepia(1) saturate(1.4)"
    : value === "青铜氧化"
      ? "sepia(.3) hue-rotate(30deg)"
      : "none";
const renderingFilter = computed(() => filterFor(style.value));
const readyResult = computed(() =>
  props.savedTask?.status === "SUCCESS" ? props.savedTask?.result : undefined,
);
const resultUrl = computed(
  () =>
    readyResult.value?.rendered_image_url ||
    readyResult.value?.colored_image_url,
);
const icon = (node: string) => designIcon("layer-40-55030", node);
const image = (node: string) => designImage("layer-40-55030", node);
const snapshot = (): Snapshot => ({
  elements: elements.value.map((e) => ({ ...e })),
  style: style.value,
});
function checkpoint() {
  const current = snapshot();
  if (
    JSON.stringify(past.value[past.value.length - 1]) !==
    JSON.stringify(current)
  )
    past.value.push(current);
  if (past.value.length > 100) past.value.shift();
  future.value = [];
}
function restore(state: Snapshot) {
  elements.value = state.elements.map((e) => ({ ...e }));
  style.value = state.style;
  if (!elements.value.some((e) => e.id === selected.value))
    selected.value = elements.value[elements.value.length - 1]?.id || "";
}
function undo() {
  while (
    past.value.length &&
    JSON.stringify(past.value[past.value.length - 1]) ===
      JSON.stringify(snapshot())
  )
    past.value.pop();
  const previous = past.value.pop();
  if (!previous) return;
  future.value.push(snapshot());
  restore(previous);
}
function redo() {
  const next = future.value.pop();
  if (!next) return;
  past.value.push(snapshot());
  restore(next);
}
function clear() {
  if (!elements.value.length) return;
  checkpoint();
  elements.value = [];
  selected.value = "";
}
function remove() {
  if (!active.value) return;
  checkpoint();
  elements.value = elements.value.filter((e) => e.id !== selected.value);
  selected.value = "";
}
function setStyle(value: string) {
  if (style.value !== value) {
    checkpoint();
    style.value = value;
  }
}
function add(pattern: (typeof patterns)[number], x = 0.5, y = 0.5) {
  if (elements.value.length >= 100) {
    notify("每张画布最多放置100个纹样");
    return;
  }
  checkpoint();
  const id = crypto.randomUUID();
  elements.value.push({
    id,
    label: pattern.label,
    src: image(pattern.node),
    x,
    y,
    scale: 1,
    rotation: 0,
  });
  selected.value = id;
}
let dragging:
  { pointerId: number; offsetX: number; offsetY: number } | undefined;
function start(event: PointerEvent, element: Element) {
  if (!stage.value) return;
  checkpoint();
  selected.value = element.id;
  const box = stage.value.getBoundingClientRect();
  dragging = {
    pointerId: event.pointerId,
    offsetX: event.clientX - box.left - element.x * box.width,
    offsetY: event.clientY - box.top - element.y * box.height,
  };
  (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
}
function move(event: PointerEvent) {
  if (
    !dragging ||
    dragging.pointerId !== event.pointerId ||
    !active.value ||
    !stage.value
  )
    return;
  const box = stage.value.getBoundingClientRect();
  active.value.x = Math.max(
    0,
    Math.min(1, (event.clientX - box.left - dragging.offsetX) / box.width),
  );
  active.value.y = Math.max(
    0,
    Math.min(1, (event.clientY - box.top - dragging.offsetY) / box.height),
  );
}
let libraryDrag:
  { pattern: (typeof patterns)[number]; x: number; y: number } | undefined;
let suppressClick = false;
function libraryStart(event: PointerEvent, pattern: (typeof patterns)[number]) {
  libraryDrag = { pattern, x: event.clientX, y: event.clientY };
  suppressClick = false;
  (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
}
function libraryEnd(event: PointerEvent) {
  const drag = libraryDrag;
  libraryDrag = undefined;
  if (
    !drag ||
    !stage.value ||
    Math.hypot(event.clientX - drag.x, event.clientY - drag.y) <= 8
  )
    return;
  suppressClick = true;
  const box = stage.value.getBoundingClientRect();
  if (
    event.clientX >= box.left &&
    event.clientX <= box.right &&
    event.clientY >= box.top &&
    event.clientY <= box.bottom
  )
    add(
      drag.pattern,
      (event.clientX - box.left) / box.width,
      (event.clientY - box.top) / box.height,
    );
}
function libraryClick(pattern: (typeof patterns)[number]) {
  if (!suppressClick) add(pattern);
  suppressClick = false;
}
async function render(state = snapshot()): Promise<Blob> {
  const canvas = document.createElement("canvas");
  canvas.width = 1000;
  canvas.height = 750;
  const context = canvas.getContext("2d")!;
  context.fillStyle = "#FCFBF8";
  context.fillRect(0, 0, 1000, 750);
  for (const element of state.elements) {
    const asset = new Image();
    asset.src = element.src;
    await asset.decode();
    context.save();
    context.translate(element.x * 1000, element.y * 750);
    context.rotate((element.rotation * Math.PI) / 180);
    const size = 230 * element.scale,
      ratio = Math.min(size / asset.naturalWidth, size / asset.naturalHeight);
    const width = asset.naturalWidth * ratio,
      height = asset.naturalHeight * ratio;
    context.filter = filterFor(state.style);
    context.drawImage(asset, -width / 2, -height / 2, width, height);
    context.restore();
  }
  return new Promise((resolve, reject) =>
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error("画布导出失败"))),
      "image/png",
    ),
  );
}
let savedHere = "",
  editableTaskId = "",
  alive = true,
  previewVersion = 0;
let previewTimer: ReturnType<typeof setTimeout> | undefined;
watch(
  [elements, style],
  () => {
    clearTimeout(previewTimer);
    const version = ++previewVersion;
    previewTimer = setTimeout(async () => {
      try {
        const blob = await render();
        if (!alive || version !== previewVersion) return;
        if (preview.value) URL.revokeObjectURL(preview.value);
        preview.value = URL.createObjectURL(blob);
      } catch {
        if (alive) notify("纹样图片暂未加载完成，请重试");
      }
    }, 120);
  },
  { deep: true, immediate: true },
);
watch(
  [() => props.savedTask?.task_id, () => props.savedTask?.status],
  () => {
    const task = props.savedTask;
    if (!task) {
      editableTaskId = "";
      return;
    }
    if (task.status !== "SUCCESS") {
      editableTaskId = "";
      return;
    }
    if (task.task_id === savedHere) return;
    if (task.result?.source !== "user_canvas") {
      editableTaskId = "";
      if (elements.value.length) {
        checkpoint();
        elements.value = [];
        selected.value = "";
        notify("AI 结果已替换画布，可点撤销找回之前的手绘排版");
      }
      return;
    }
    if (!Array.isArray(task.input?.composition)) return;
    editableTaskId = task.task_id;
    const restored: Element[] = task.input.composition.flatMap((item: any) => {
      const pattern = patterns.find((p) => p.label === item.label);
      if (
        !pattern ||
        ![item.x, item.y, item.scale, item.rotation].every(Number.isFinite) ||
        item.x < 0 ||
        item.x > 1 ||
        item.y < 0 ||
        item.y > 1 ||
        item.scale < 0.5 ||
        item.scale > 2 ||
        Math.abs(item.rotation) > 180
      )
        return [];
      return [{ ...item, src: image(pattern.node) }];
    });
    restore({
      elements: restored,
      style: ["青铜氧化", "鎏金拓印", "彩色渲染"].includes(
        task.input.render_style,
      )
        ? task.input.render_style
        : "青铜氧化",
    });
    past.value = [];
    future.value = [];
  },
  { immediate: true },
);
async function save() {
  if (!requireSession() || busy.value) return;
  if (!elements.value.length) {
    notify("先从纹样库选择一个纹样吧");
    return;
  }
  busy.value = true;
  const state = snapshot();
  const uid = session.profile?.id;
  const targetTaskId = editableTaskId;
  try {
    const form = new FormData();
    const blob = await render(state);
    if (uid !== session.profile?.id) return;
    form.append("file", blob, "青铜纹样设计.png");
    const asset = await api("/ai/assets/upload", {
      method: "POST",
      body: form,
    });
    if (uid !== session.profile?.id) return;
    const payload = {
      cover_url: asset.file_url,
      composition: state.elements,
      render_style: state.style,
      title: state.elements
        .map((e) => e.label)
        .join(" · ")
        .slice(0, 128),
    };
    const updating = Boolean(targetTaskId);
    const task = updating
      ? await put("/mobile/workshop/designs/" + targetTaskId, payload)
      : await post("/mobile/workshop/designs", payload);
    if (uid !== session.profile?.id) return;
    editableTaskId = task.task_id;
    savedHere = task.task_id;
    emit("saved", task);
    notify(updating ? "设计已更新" : "设计已保存到你的创作记录");
    return task;
  } catch (e) {
    notify((e as Error).message);
  } finally {
    busy.value = false;
  }
}
async function download() {
  try {
    if (elements.value.length)
      await saveBlob(await render(), "青铜纹样设计.png");
    else if (resultUrl.value)
      await saveAsset(
        resultUrl.value,
        "青铜纹样设计" + (resultUrl.value.match(/\.(svg|png|jpe?g|webp)$/i)?.[0] || ".png"),
      );
  } catch (e) {
    notify((e as Error).message);
  }
}
async function share() {
  if (elements.value.length ? await save() : readyResult.value) emit("publish");
}
async function loadOverview() {
  overviewError.value = "";
  try {
    overview.value = await api("/mobile/workshop/bronze");
  } catch (e) {
    overviewError.value = (e as Error).message;
  }
}
watch(
  () => session.profile?.id,
  () => {
    elements.value = [];
    selected.value = "";
    past.value = [];
    future.value = [];
    savedHere = "";
    editableTaskId = "";
  },
);
onMounted(loadOverview);
onUnmounted(() => {
  alive = false;
  clearTimeout(previewTimer);
  if (preview.value) URL.revokeObjectURL(preview.value);
});
</script>
<template>
  <section class="bronze-editor">
    <nav class="pattern-tabs" aria-label="纹样分类">
      <button
        v-for="tab in patternTabs"
        :key="tab"
        :aria-pressed="category === tab"
        :class="{ active: category === tab }"
        @click="category = tab"
      >
        {{ tab }}
      </button>
    </nav>
    <section class="pattern-library">
      <div class="bronze-heading">
        <h2>纹样库</h2>
        <span>滑动浏览更多</span>
      </div>
      <div v-if="visiblePatterns.length" class="pattern-grid">
        <button
          v-for="pattern in visiblePatterns"
          :key="pattern.node"
          :aria-label="'添加' + pattern.label"
          @pointerdown="libraryStart($event, pattern)"
          @pointerup="libraryEnd"
          @pointercancel="libraryDrag = undefined"
          @click="libraryClick(pattern)"
        >
          <span
            class="pattern-image"
            :class="{ chosen: active?.label === pattern.label }"
            ><img :src="image(pattern.node)" alt="" draggable="false" /><i
              v-if="active?.label === pattern.label"
              ><img :src="icon('5:5100')" alt="" /></i></span
          ><span>{{ pattern.label }}</span>
        </button>
      </div>
      <p v-else class="empty-patterns">该分类暂无可用纹样</p>
    </section>
    <section class="canvas-card">
      <div class="canvas-heading">
        <h2>设计画布</h2>
        <button aria-label="移除选中纹样" :disabled="!active" @click="remove">
          <i /><i /><i />
        </button>
      </div>
      <div ref="stage" class="pattern-canvas" aria-label="青铜纹样设计画布">
        <div class="ruler ruler-x" aria-hidden="true">
          <span v-for="n in [0, 50, 100, 150, 200, 250, 300]" :key="n">{{
            n
          }}</span>
        </div>
        <div class="ruler ruler-y" aria-hidden="true">
          <span v-for="n in [0, 50, 100, 150, 200]" :key="n">{{ n }}</span>
        </div>
        <div v-if="!elements.length" class="canvas-empty">
          <i><img :src="icon('5:4922')" alt="" /></i>
          <p>拖拽纹样至此处</p>
          <span>点击选中可编辑</span>
        </div>
        <button
          v-for="element in elements"
          :key="element.id"
          :class="{ selected: selected === element.id }"
          :aria-label="'移动或编辑' + element.label"
          :style="{
            left: element.x * 100 + '%',
            top: element.y * 100 + '%',
            transform:
              'translate(-50%,-50%) rotate(' +
              element.rotation +
              'deg) scale(' +
              element.scale +
              ')',
          }"
          @pointerdown="start($event, element)"
          @pointermove="move"
          @pointerup="dragging = undefined"
          @pointercancel="dragging = undefined"
        >
          <img
            :src="element.src"
            :style="{ filter: renderingFilter }"
            alt=""
            draggable="false"
          />
        </button>
      </div>
      <div class="canvas-actions">
        <button
          :disabled="!elements.length"
          aria-label="清空画布"
          @click="clear"
        >
          <img :src="icon('5:4978')" alt="" /></button
        ><button :disabled="!past.length" aria-label="撤销编辑" @click="undo">
          <img :src="icon('5:4988')" alt="" /></button
        ><button :disabled="!future.length" aria-label="重做编辑" @click="redo">
          <img :src="icon('5:4984')" alt="" /></button
        ><button class="complete-design" :disabled="busy" @click="save">
          {{ busy ? "保存中…" : "完成设计" }}
        </button>
      </div>
    </section>
    <div v-if="active" class="canvas-controls">
      <label
        >纹样大小<input
          v-model.number="active.scale"
          type="range"
          min=".5"
          max="2"
          step=".1"
          @pointerdown="checkpoint"
          @keydown="checkpoint" /></label
      ><label
        >旋转角度<input
          v-model.number="active.rotation"
          type="range"
          min="-180"
          max="180"
          step="5"
          @pointerdown="checkpoint"
          @keydown="checkpoint"
      /></label>
    </div>
    <section class="render-section">
      <div class="bronze-heading">
        <h2>效果渲染</h2>
        <span>实时预览</span>
      </div>
      <div class="render-styles">
        <button
          v-for="(effect, i) in ['青铜氧化', '鎏金拓印', '彩色渲染']"
          :key="effect"
          :aria-pressed="style === effect"
          :class="{ active: style === effect }"
          @click="setStyle(effect)"
        >
          <img :src="image(['5:4791', '5:4814', '5:4768'][i])" alt="" /><span>{{
            effect
          }}</span>
        </button>
      </div>
      <div class="render-preview">
        <img
          v-if="elements.length ? preview : resultUrl"
          :src="elements.length ? preview : mediaUrl(resultUrl)"
          alt="当前设计效果"
        />
        <p v-else>
          {{ elements.length ? "正在更新预览…" : "添加纹样后预览你的设计" }}
        </p>
        <span>{{ style }}效果</span>
      </div>
      <button
        class="generate-button"
        @click="emit('generate', style, generatingPattern)"
      >
        <img :src="icon('5:4832')" alt="" />AI生成纹样
      </button>
      <p
        v-if="
          readyResult &&
          readyResult.source !== 'user_canvas' &&
          !readyResult.llm_generated && readyResult.generation_method !== 'ai_image'
        "
        class="local-generation-note"
      >
        本次采用本地纹样模板生成，可导出或收藏作品。
      </p>
      <p v-if="readyResult?.generation_method === 'ai_image'" class="local-generation-note">{{ readyResult.description }}</p>
      <div v-if="elements.length || readyResult" class="result-actions">
        <button class="outline-button" @click="download">导出设计图</button
        ><button v-if="!elements.length && readyResult?.generation_method === 'ai_image'" class="outline-button" :disabled="favoriteBusy" :aria-pressed="!!savedTask.collected" @click="emit('favorite')">{{ savedTask.collected ? '取消收藏' : '收藏创作' }}</button
        ><button
          class="primary-button"
          :disabled="busy || publishing"
          @click="share"
        >
          {{ publishing ? "发布中…" : "分享至社区" }}
        </button>
      </div>
    </section>
    <div class="bronze-stats">
      <article
        v-for="(stat, i) in [
          { label: '可选纹样', value: patterns.length },
          { label: '画布元素', value: elements.length },
          { label: '设计师', value: overview?.designer_count },
          { label: '设计作品', value: overview?.design_count },
        ]"
        :key="i"
      >
        <strong>{{ stat.value ?? "—" }}</strong
        ><span>{{ stat.label }}</span>
      </article>
    </div>
    <section class="bronze-culture">
      <h2>武清青铜文化</h2>
      <div>
        <img :src="image('5:5126')" alt="武清青铜器" />
        <article>
          <p>
            武清区位于天津市西北部，历史悠久，文化底蕴深厚。作为京津冀文化交汇之地，武清拥有丰富的青铜文化遗存，其仿古青铜器制作技艺传承数百年，以精湛的铸造工艺和典雅的装饰设计闻名。
          </p>
          <div class="culture-tags">
            <span>青铜历史</span><span>非遗技艺</span><span>数字传承</span>
          </div>
        </article>
      </div>
    </section>
    <section class="bronze-gallery">
      <div class="bronze-heading">
        <h2>设计作品展示</h2>
        <span>滑动浏览</span>
      </div>
      <p v-if="overviewError" class="gallery-state" role="alert">
        {{ overviewError }} <button @click="loadOverview">重试</button>
      </p>
      <p v-else-if="!overview" class="gallery-state">正在加载作品…</p>
      <div v-else-if="overview.works.length" class="work-gallery">
        <RouterLink
          v-for="work in overview.works"
          :key="work.id"
          :to="'/community/' + work.id"
          ><img
            v-if="work.cover_url"
            :src="mediaUrl(work.cover_url)"
            :alt="work.title"
          />
          <div v-else class="work-placeholder">暂无封面</div>
          <h3>{{ work.title }}</h3>
          <p>设计师 · {{ work.nickname }}</p></RouterLink
        >
      </div>
      <p v-else class="gallery-state">
        还没有公开的青铜设计，完成创作后分享你的作品吧
      </p>
    </section>
    <nav class="bronze-toolbar" aria-label="画布操作">
      <button :disabled="!elements.length" @click="clear">
        <img :src="icon('5:5278')" alt="" /><span>清空</span></button
      ><button :disabled="!past.length" @click="undo">
        <img :src="icon('5:5288')" alt="" /><span>撤销</span></button
      ><button :disabled="!future.length" @click="redo">
        <img :src="icon('5:5268')" alt="" /><span>重做</span></button
      ><button class="toolbar-save" :disabled="busy" @click="save">
        {{ busy ? "保存中…" : "生成设计" }}
      </button>
    </nav>
  </section>
</template>
<style scoped>
.bronze-editor {
  color: #3d3d3d;
  padding-bottom: calc(96px + var(--safe-bottom));
}
.pattern-tabs {
  display: flex;
  gap: 8px;
  padding: 12px 16px 17px;
  height: 66px;
  overflow: auto;
  background: rgba(250, 247, 240, 0.94);
  border-bottom: 1px solid rgba(201, 168, 76, 0.3);
}
.pattern-tabs button {
  flex-shrink: 0;
  border: 1px solid rgba(201, 168, 76, 0.32);
  background: #fffdf8;
  color: #6b5634;
  height: 37px;
  border-radius: 30px;
  padding: 0 20px;
  font-size: 13px;
  font-weight: 500;
}
.pattern-tabs button.active {
  background: linear-gradient(100deg, #6b4a1f, #8a6125);
  color: #fbf3e0;
  border-color: rgba(201, 168, 76, 0.7);
  box-shadow: 0 4px 12px rgba(107, 74, 31, 0.2);
}
.pattern-library {
  padding: 24px 16px 8px;
}
.bronze-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 28px;
  margin-bottom: 16px;
  gap: 12px;
}
.bronze-heading h2,
.bronze-culture h2 {
  font: 600 18px/28px var(--serif);
  letter-spacing: 0.45px;
}
.bronze-heading > span {
  color: #888;
  font-size: 11px;
  line-height: 16.5px;
  letter-spacing: 0.55px;
}
.pattern-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}
.pattern-grid > button {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  min-width: 0;
  padding: 0;
  color: #6b5634;
  font-size: 11px;
  line-height: 16px;
  touch-action: pan-x;
}
.pattern-image {
  width: 100%;
  aspect-ratio: 1;
  position: relative;
  background: #fffdf8;
  border: 1px solid rgba(201, 168, 76, 0.3);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(80, 58, 28, 0.06);
}
.pattern-image > img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  pointer-events: none;
}
.pattern-image.chosen {
  border: 2px solid #b8862f;
  box-shadow: 0 0 0 3px rgba(201, 168, 76, 0.12);
}
.pattern-image > i {
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  position: absolute;
  right: 6px;
  top: 6px;
  border-radius: 50%;
  background: #b07d2e;
}
.pattern-image > i img {
  width: 12px;
  height: 12px;
}
.empty-patterns {
  min-height: 210.5px;
  display: grid;
  place-items: center;
  color: #888;
  font-size: 12px;
}
.canvas-card {
  margin: 24px 16px 0;
  background: #fffdf8;
  border: 1px solid rgba(201, 168, 76, 0.32);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 2px 16px #0000000a;
}
.canvas-heading {
  height: 49px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px solid #f6f6f6;
}
.canvas-heading h2 {
  font: 600 16px/24px var(--serif);
  letter-spacing: 0.4px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.canvas-heading h2::before,
.bronze-culture h2::before {
  content: "";
  width: 6px;
  height: 20px;
  background: #c9953a;
  border-radius: 9px;
  display: inline-block;
}
.canvas-heading button {
  display: flex;
  gap: 6px;
  padding: 12px 0 12px 12px;
}
.canvas-heading i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d1d1d1;
}
.pattern-canvas {
  width: 100%;
  aspect-ratio: 4/3;
  position: relative;
  background: #fcfbf8;
  overflow: hidden;
}
.canvas-empty {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}
.canvas-empty > i {
  display: grid;
  place-items: center;
  width: 56px;
  height: 56px;
  border: 1px solid #f9f0dc;
  background: #fdf9f0;
  border-radius: 16px;
  margin-bottom: 12px;
}
.canvas-empty img {
  width: 24px;
  height: 24px;
}
.canvas-empty p {
  font-size: 14px;
  line-height: 20px;
  font-weight: 500;
  color: #888;
}
.canvas-empty > span {
  font-size: 12px;
  line-height: 16px;
  color: #b0b0b0;
  margin-top: 4px;
}
.ruler {
  position: absolute;
  display: flex;
  color: #d1d1d1;
  font: 9px/13.5px var(--serif);
  pointer-events: none;
}
.ruler-x {
  left: 16px;
  right: 16px;
  top: 8px;
  justify-content: space-between;
}
.ruler-y {
  left: 8px;
  top: 16px;
  bottom: 16px;
  flex-direction: column;
  justify-content: space-between;
}
.pattern-canvas > button {
  position: absolute;
  width: 23%;
  aspect-ratio: 1;
  padding: 0;
  touch-action: none;
  cursor: grab;
  border: 1px solid transparent;
}
.pattern-canvas > button.selected {
  border-color: #b07d2e;
}
.pattern-canvas > button img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  pointer-events: none;
}
.canvas-actions {
  height: 65px;
  padding: 12px 16px;
  background: #f6f6f680;
  display: flex;
  gap: 4px;
  align-items: center;
}
.canvas-actions > button {
  background: #fff;
  border: 1px solid #e7e7e7;
  border-radius: 12px;
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}
.canvas-actions > button img {
  width: 16px;
  height: 16px;
}
.canvas-actions > button.complete-design {
  margin-left: auto;
  width: auto;
  padding: 0 16px;
  font-size: 14px;
  font-weight: 500;
  background: #b07d2e;
  color: #fff;
  border-color: #b07d2e;
}
.canvas-controls {
  display: flex;
  gap: 18px;
  margin: 16px 16px 0;
}
.canvas-controls label {
  flex: 1;
  font-size: 11px;
}
.canvas-controls input {
  padding: 0;
  min-height: 28px;
  accent-color: #8a6125;
}
.render-section {
  padding: 24px 16px 0;
}
.render-styles {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}
.render-styles button {
  padding: 0;
  position: relative;
  height: 78.23px;
  border: 1px solid #e7e7e7;
  border-radius: 12px;
  overflow: hidden;
}
.render-styles img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.render-styles span {
  position: absolute;
  inset: auto 0 0;
  padding: 6px 2px;
  font-size: 11px;
  line-height: 16.5px;
  background: #0008;
  color: #fff;
}
.render-styles button.active {
  border: 2px solid #d9ae5e;
}
.render-preview {
  position: relative;
  width: 100%;
  aspect-ratio: 335/188.44;
  margin-top: 12px;
  border: 1px solid #e7e7e7;
  border-radius: 16px;
  overflow: hidden;
  background: #fcfbf8;
  display: grid;
  place-items: center;
}
.render-preview > img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.render-preview > p {
  color: #888;
  font-size: 12px;
}
.render-preview > span {
  position: absolute;
  left: 12px;
  bottom: 12px;
  border-radius: 8px;
  padding: 4px 10px;
  background: #ffffffe6;
  color: #4f4f4f;
  font-size: 11px;
  line-height: 16px;
}
.generate-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  gap: 10px;
  height: 56px;
  border-radius: 16px;
  margin-top: 16px;
  color: #fff;
  background: linear-gradient(90deg, #b07d2e, #8a6125);
  font: 600 16px/24px var(--serif);
  letter-spacing: 0.8px;
}
.generate-button img {
  width: 20px;
  height: 20px;
}
.result-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}
.result-actions > button {
  flex: 1;
  font-size: 13px;
}
.bronze-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: 32px 16px;
}
.bronze-stats article {
  height: 100px;
  border: 1px solid #f6f6f6;
  border-radius: 16px;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 8px;
  gap: 4px;
}
.bronze-stats strong {
  color: #b07d2e;
  font: 700 24px/32px var(--serif);
}
.bronze-stats span {
  width: 44px;
  color: #888;
  font-size: 10px;
  line-height: 15px;
  letter-spacing: 0.5px;
  text-align: center;
}
.bronze-culture {
  margin: 0 16px;
  border: 1px solid #f9f0dc;
  border-radius: 16px;
  padding: 20px;
  background: #fff;
}
.bronze-culture h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.bronze-culture > div {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}
.bronze-culture > div > img {
  width: 112px;
  aspect-ratio: 3/4;
  object-fit: cover;
  border-radius: 12px;
  flex-shrink: 0;
}
.bronze-culture article {
  min-width: 0;
}
.bronze-culture article > p {
  color: #5d5d5d;
  font-size: 13px;
  line-height: 22.1px;
}
.culture-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}
.culture-tags span {
  padding: 7px 12px;
  border-radius: 8px;
  background: #f6f6f6;
  font-size: 11px;
  line-height: 16px;
  color: #5d5d5d;
}
.culture-tags span:first-child {
  background: #fdf9f0;
  color: #8a6125;
}
.bronze-gallery {
  margin-top: 32px;
}
.bronze-gallery > .bronze-heading {
  padding: 0 16px;
}
.work-gallery {
  display: flex;
  gap: 16px;
  overflow: auto;
  padding: 0 16px 8px;
}
.work-gallery > a {
  display: block;
  flex: 0 0 280px;
  border: 1px solid #e7e7e7;
  border-radius: 16px;
  background: #fff;
  overflow: hidden;
}
.work-gallery img,
.work-placeholder {
  width: 100%;
  height: 208px;
  object-fit: cover;
}
.work-placeholder {
  display: grid;
  place-items: center;
  background: #f5f0e6;
  color: #888;
  font-size: 12px;
}
.work-gallery h3 {
  margin: 16px 16px 4px;
  font: 600 14px/20px var(--serif);
}
.work-gallery p {
  margin: 0 16px 16px;
  color: #888;
  font-size: 11px;
  line-height: 16.5px;
}
.gallery-state {
  margin: 0 16px;
  padding: 24px 20px;
  border-radius: 16px;
  background: #fff;
  color: #888;
  font-size: 12px;
  line-height: 1.8;
}
.gallery-state button {
  color: #8a6125;
  text-decoration: underline;
}
.bronze-toolbar {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: min(100%, 480px);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  height: calc(72px + var(--safe-bottom));
  padding: 12px 20px calc(12px + var(--safe-bottom));
  z-index: 20;
  border-top: 1px solid #f9f0dc;
  background: #fffffff2;
  backdrop-filter: blur(24px);
  box-shadow: 0 -4px 24px #0000000f;
}
.bronze-toolbar > button {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: #888;
  font-size: 10px;
  line-height: 15px;
  min-width: 32px;
  padding: 0;
}
.bronze-toolbar img {
  width: 20px;
  height: 20px;
}
.bronze-toolbar .toolbar-save {
  background: #b07d2e;
  color: #fff;
  border-radius: 16px;
  padding: 12px 20px;
  font-size: 14px;
  line-height: 20px;
  font-weight: 600;
}
</style>
