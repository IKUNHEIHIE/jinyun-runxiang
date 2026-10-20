<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { designImage, designIcon } from "../design";
import { mediaUrl, notify, requireSession } from "../api";
import GenerationTheater from "./GenerationTheater.vue";
const props = defineProps<{
  generationMode: string;
  task?: any;
  working: boolean;
  uploading: boolean;
  loading: boolean;
  error: string;
  publishing: boolean;
  favoriteBusy: boolean;
}>();
const emit = defineEmits<{
  back: [];
  generate: [];
  cancel: [];
  retry: [];
  export: [];
  favorite: [];
  publish: [];
  upload: [event: Event];
}>();
const role = defineModel<string>("role", { required: true });
const color = defineModel<string>("color", { required: true });
const prompt = defineModel<string>("prompt", { required: true });
const faceStyle = defineModel<string>("faceStyle", { required: true });
const sketch = defineModel<string>("sketch", { required: true });
const selectedResult = defineModel<string>("selectedResult", {
  required: true,
});
const screen = "layer-5-3193" as const;
const roleBox = ref<HTMLElement | null>(null),
  paletteBox = ref<HTMLElement | null>(null),
  description = ref<HTMLTextAreaElement | null>(null),
  history = ref<HTMLElement | null>(null),
  fileInput = ref<HTMLInputElement | null>(null);
const disabled = computed(
  () => props.working || props.loading || props.uploading,
);
const hasResult = computed(
  () => props.task?.status === "SUCCESS" && !!props.task?.result,
);
const resultUrl = computed(
  () =>
    props.task?.result?.[selectedResult.value] ||
    props.task?.result?.colored_image_url,
);
const roles = [
  { key: "生", text: "男性角色" },
  { key: "旦", text: "女性角色" },
  { key: "净", text: "花脸角色" },
  { key: "丑", text: "喜剧角色" },
];
const colors = ["#8B1A1A", "#2D5A3D", "#CA8A04", "#111827", "#E8E0D0"];
const swatches = computed(() =>
  colors.includes(color.value.toUpperCase())
    ? colors
    : [...colors, color.value.toUpperCase()],
);
const faces = [
  { key: "CLASSIC", label: "经典脸谱", image: "5:3289" },
  { key: "FLORAL", label: "花纹脸谱", image: "5:3294" },
  { key: "BOLD", label: "醒目脸谱", image: "5:3299" },
];
const crafts = [
  {
    mark: "刻",
    title: "镂空雕镂",
    image: "5:3780",
    body: "刀法流畅，阴阳相济，虚实相生，以刀代笔刻画人物神韵",
  },
  {
    mark: "彩",
    title: "平涂敷彩",
    image: "5:3419",
    body: "红绿黄黑白五色为主，纯色平涂，对比强烈，光影穿透时色彩斑斓",
  },
  {
    mark: "材",
    title: "驴皮选材",
    image: "5:3698",
    body: "精选上等驴皮，泡制刮薄至半透明，质地坚韧，透光性佳",
  },
];
const steps = [
  { text: "选角", icon: "5:3489" },
  { text: "配色", icon: "5:3465" },
  { text: "生成", icon: "5:3454" },
  { text: "导出", icon: "5:3480" },
];
const eras = [
  {
    age: "汉",
    title: "汉代起源",
    body: "皮影戏发源于西汉，距今两千余年，是世界上最古老的民间艺术之一",
  },
  {
    age: "唐",
    title: "唐代兴盛",
    body: "盛于唐宋，宫廷民间皆盛行，技艺日臻成熟，流派纷呈",
  },
  {
    age: "清",
    title: "清代鼎盛",
    body: "蓟州皮影自成一派，以精细镂刻、鲜明敷彩著称，享誉京津冀",
  },
  {
    age: "今",
    title: "AI新生",
    body: "非遗传承融合人工智能，让千年皮影在数字时代焕发新生",
  },
];
const theater = ref(false);
const theaterElapsed = ref(0);
const artSize = ref("");
let generationStartedAt = 0;
watch(
  () => props.working,
  (working) => {
    if (!working || props.loading) return;
    theater.value = true;
    theaterElapsed.value = 0;
    artSize.value = "";
    generationStartedAt = performance.now();
  },
);
watch(
  () => props.error,
  (message) => {
    if (message) theater.value = false;
  },
);
watch(
  () => props.task?.status,
  (status) => {
    if (status === "SUCCESS" && generationStartedAt) {
      theaterElapsed.value = (performance.now() - generationStartedAt) / 1000;
    }
    if (status === "FAILED" || status === "CANCELLED") theater.value = false;
  },
);
const resultColors = computed<string[]>(() => {
  const list = props.task?.result?.color_palette;
  if (!Array.isArray(list)) return [];
  const hexes = list
    .map((item) => {
      if (typeof item !== "string") return "";
      const match = item.match(/#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}/);
      if (!match) return "";
      const hex = match[0].toUpperCase();
      return hex.length === 4
        ? "#" + hex[1] + hex[1] + hex[2] + hex[2] + hex[3] + hex[3]
        : hex;
    })
    .filter((item) => !!item);
  return [...new Set(hexes)].slice(0, 6);
});
const resultFace = computed(
  () =>
    faces.find((item) => item.key === props.task?.result?.face_style)?.label ||
    "—",
);
const theaterPreview = computed(() =>
  hasResult.value ? mediaUrl(resultUrl.value) : "",
);
const theaterStats = computed(() => [
  { label: "画幅", value: artSize.value || "—" },
  {
    label: "取色",
    value: resultColors.value.length ? resultColors.value.length + " 色" : "—",
  },
  {
    label: "耗时",
    value: theaterElapsed.value ? theaterElapsed.value.toFixed(1) + "s" : "—",
  },
]);
const theaterCaption = computed(() =>
  props.generationMode === "AI"
    ? "AI 图像生成 · 结果为二维创意参考，不是可编辑矢量或切割纸样"
    : "本地规则模板 · 按行当、脸谱与配色拼装，不调用外部生成模型",
);
function measureArt(event: Event) {
  const image = event.target as HTMLImageElement;
  if (!image.naturalWidth || !image.naturalHeight) return;
  artSize.value = image.naturalWidth + "×" + image.naturalHeight;
}
function generate() {
  if (!prompt.value.trim()) description.value?.focus();
  emit("generate");
}
function chooseUpload() {
  if (!disabled.value && requireSession()) fileInput.value?.click();
}
function uploaded(event: Event) {
  if (!(event.target as HTMLInputElement).files?.length) return;
  emit("upload", event);
}
function exportResult() {
  if (hasResult.value) emit("export");
  else notify("请先生成皮影角色");
}
function printResult() {
  if (!hasResult.value) return notify("请先生成皮影角色");
  if (!props.task.result.print_template_url) return notify("此 AI 图像没有切割纸样，可导出图片作为创作参考");
  selectedResult.value = "print_template_url";
  emit("export");
}
function step(index: number) {
  if (index === 0) {
    roleBox.value?.scrollIntoView({ behavior: "smooth", block: "center" });
    roleBox.value?.querySelector("button")?.focus({ preventScroll: true });
  } else if (index === 1) {
    paletteBox.value?.scrollIntoView({ behavior: "smooth", block: "center" });
    paletteBox.value?.querySelector("button")?.focus({ preventScroll: true });
  } else if (index === 2) generate();
  else exportResult();
}
function publish() {
  if (hasResult.value) emit("publish");
  else notify("请先生成皮影角色");
}
</script>
<template>
  <div class="shadow-workshop" data-design-node="5:3193">
    <GenerationTheater
      v-if="theater"
      title="正在镂刻"
      :steps="['解析行当与配色', '描样勾脸谱', '镂空分层', '合成皮影成品']"
      :preview="theaterPreview"
      :stats="theaterStats"
      :caption="theaterCaption"
      @done="theater = false"
    />
    <header class="shadow-header">
      <img class="hero-photo" :src="designImage(screen, '5:3835')" alt="" />
      <div class="hero-veil" aria-hidden="true" />
      <button class="shadow-back" aria-label="返回上一页" @click="emit('back')">
        <img :src="designIcon(screen, '40:55070')" alt="" />
      </button>
      <span class="shadow-seal" aria-hidden="true">影</span>
      <div class="shadow-hero-copy">
        <span class="shadow-kicker">蓟州皮影 · 非遗数字工坊</span>
        <h1><span>AI</span>皮影角色设计</h1>
        <p>一刀一刻承古韵 · 一光一影舞千秋</p>
        <div class="shadow-meta">
          <i />千年光影<i />数字新生
        </div>
      </div>
    </header>
    <form
      class="shadow-form"
      @submit.prevent="generate"
      :aria-busy="working || loading"
    >
      <div class="design-columns">
        <div class="preview-column">
          <section class="puppet-preview" aria-label="皮影预览">
            <span v-if="hasResult" class="preview-title">{{
              task.result.title || task.result.role_type
            }}</span>
            <img
              v-if="hasResult"
              class="result-art"
              :src="mediaUrl(resultUrl)"
              alt="当前皮影创作结果"
              @load="measureArt"
            />
            <template v-else
              ><img
                class="example-art"
                :src="designImage(screen, '5:3240')"
                alt="设计稿中的皮影参考示例"
              />
              <p class="example-label">
                {{
                  loading
                    ? "正在加载创作…"
                    : working
                      ? "正在生成 · 参考示例"
                      : "参考示例 · 先生成你的皮影"
                }}
              </p></template
            >
            <template v-if="hasResult">
              <i class="lamp-veil" aria-hidden="true" />
              <i class="lamp-glow" aria-hidden="true" />
            </template>
            <i class="preview-corner top-left" aria-hidden="true" /><i
              class="preview-corner top-right"
              aria-hidden="true"
            /><i class="preview-corner bottom-left" aria-hidden="true" /><i
              class="preview-corner bottom-right"
              aria-hidden="true"
            />
            <div class="preview-toolbar">
              <select
                v-model="selectedResult"
                aria-label="预览内容"
                :disabled="!hasResult"
              >
                <option v-if="!hasResult || task.result.line_art_url" value="line_art_url">镂空轮廓图</option>
                <option value="colored_image_url">彩色皮影</option>
                <option v-if="!hasResult || task.result.print_template_url" value="print_template_url">线稿纸样</option>
              </select>
              <div>
                <button
                  type="button"
                  aria-label="导出当前预览"
                  :disabled="!hasResult"
                  @click="exportResult"
                >
                  <img :src="designIcon(screen, '5:3258')" alt="" /></button
                ><button
                  type="button"
                  :aria-label="
                    task?.collected ? '取消收藏当前皮影' : '收藏当前皮影'
                  "
                  :aria-pressed="!!task?.collected"
                  :disabled="!hasResult || favoriteBusy"
                  @click="emit('favorite')"
                >
                  <img :src="designIcon(screen, '5:3266')" alt="" />
                </button>
              </div>
            </div>
          </section>
          <div v-if="hasResult" class="craft-readout" aria-label="工艺读数">
            <span><em>行当</em><b>{{ task.result.role_type || "—" }}</b></span>
            <span><em>脸谱</em><b>{{ resultFace }}</b></span>
            <span class="readout-colors">
              <em>取色</em>
              <i
                v-for="hex in resultColors"
                :key="hex"
                :style="{ backgroundColor: hex }"
              />
              <b>{{ resultColors.length ? resultColors.length + " 色" : "—" }}</b>
            </span>
          </div>
          <section class="control-card face-card">
            <h2>脸谱样式</h2>
            <div class="face-options">
              <button
                v-for="face in faces"
                :key="face.key"
                type="button"
                :aria-label="face.label"
                :aria-pressed="faceStyle === face.key"
                :class="{ active: faceStyle === face.key }"
                :disabled="working || loading"
                @click="faceStyle = face.key"
              >
                <img :src="designImage(screen, face.image)" alt="" />
              </button>
            </div>
          </section>
          <section class="control-card description-card">
            <label for="shadow-prompt">文字描述</label
            ><textarea
              id="shadow-prompt"
              ref="description"
              v-model.trim="prompt"
              maxlength="1000"
              :disabled="working || loading"
              placeholder="一个穿红袍的将军&#10;一只会跳舞的仙鹤"
            />
          </section>
        </div>
        <div class="settings-column">
          <section ref="roleBox" class="control-card role-card">
            <h2>角色类型</h2>
            <div class="role-options">
              <button
                v-for="item in roles"
                :key="item.key"
                type="button"
                :aria-pressed="role === item.key"
                :class="{ active: role === item.key }"
                :disabled="working || loading"
                @click="role = item.key"
              >
                <b>{{ item.key }}</b
                ><span>{{ item.text }}</span>
              </button>
            </div>
          </section>
          <section ref="paletteBox" class="control-card palette-card">
            <h2>服饰颜色</h2>
            <div class="palette-options">
              <button
                v-for="value in swatches"
                :key="value"
                type="button"
                :aria-label="'服饰颜色 ' + value"
                :aria-pressed="color.toUpperCase() === value"
                :class="{ active: color.toUpperCase() === value }"
                :style="{ '--swatch': value }"
                :disabled="working || loading"
                @click="color = value"
              >
                <i />
              </button>
            </div>
          </section>
          <section class="control-card reference-card">
            <h2>参考图 · 选填</h2>
            <div class="reference-body">
              <button
                class="upload-target"
                :class="{ filled: !!sketch }"
                :disabled="disabled"
                :aria-label="sketch ? '重新上传参考图' : '上传皮影参考图'"
                @click="chooseUpload"
              >
                <img
                  v-if="sketch"
                  class="uploaded-sketch"
                  :src="mediaUrl(sketch)"
                  alt="已上传的参考图"
                />
                <template v-else
                  ><b aria-hidden="true">+</b
                  ><span>{{ uploading ? "上传中…" : "点击上传" }}</span
                  ><small>草图 / 照片</small></template
                >
              </button>
              <input
                ref="fileInput"
                class="file-input"
                type="file"
                accept="image/png,image/jpeg,image/webp"
                @change="uploaded"
              />
              <div class="reference-copy">
                <p>
                  {{
                    generationMode === "AI"
                      ? sketch
                        ? "AI 模式会按这张参考图重绘轮廓与配色"
                        : "选择或拍摄一张皮影、照片，AI 模式可按图重绘"
                      : sketch
                        ? "本地模板不识别图片，参考图仅作构图记录"
                        : "本地模板按角色与配色生成，不读取图片内容"
                  }}
                </p>
                <button
                  v-if="sketch"
                  type="button"
                  :disabled="disabled"
                  @click="sketch = ''"
                >
                  移除参考图
                </button>
              </div>
            </div>
          </section>
        </div>
      </div>
      <slot name="generation-mode" />
      <button class="generate-button" :disabled="disabled">
        <img :src="designIcon(screen, '5:3663')" alt="" />{{
          working ? "正在创作…" : generationMode === 'AI' ? "AI 生成皮影" : "生成本地皮影"
        }}
      </button>
      <div v-if="working" class="generation-status" role="status">
        <progress :value="task?.progress || 0" max="100" /><span
          >创作处理中 {{ task?.progress || 0 }}%</span
        ><button type="button" @click="emit('cancel')">取消任务</button>
      </div>
      <div v-if="error" class="generation-status form-error" role="alert">
        {{ error
        }}<button
          v-if="task && ['QUEUED', 'RUNNING'].includes(task.status)"
          type="button"
          @click="emit('retry')"
        >
          重新查询任务状态
        </button>
      </div>
      <details v-if="hasResult" class="result-information">
        <summary>
          {{
            task.result.generation_method === 'ai_image' ? "AI 图像创作 · 查看说明" : task.result.llm_generated
              ? "文字分析由模型辅助，图片使用本地模板"
              : "本地工艺辅助 · 查看创作说明"
          }}
        </summary>
        <p>{{ task.result.description }}</p>
        <p>纸样仅供参考，未验证实体装配或设备切割。三维生成尚未接入。</p>
        <button type="button" :disabled="publishing" @click="publish">
          {{ publishing ? "正在发布…" : "分享至社区" }}
        </button>
      </details>
    </form>
    <div
      class="craft-region"
      :style="{ backgroundImage: 'url(' + designImage(screen, '5:3831') + ')' }"
    >
      <h2 class="section-title">皮影工艺</h2>
      <div class="craft-cards">
        <article v-for="craft in crafts" :key="craft.mark">
          <img :src="designImage(screen, craft.image)" :alt="craft.title" />
          <div>
            <h3>
              <span>{{ craft.mark }}</span
              >{{ craft.title }}
            </h3>
            <p>{{ craft.body }}</p>
          </div>
        </article>
      </div>
      <h2 class="section-title process-title">设计流程</h2>
      <div class="design-steps">
        <button
          v-for="(item, index) in steps"
          :key="item.text"
          type="button"
          @click="step(index)"
        >
          <i><img :src="designIcon(screen, item.icon)" alt="" /></i
          ><span>{{ item.text }}</span>
        </button>
      </div>
    </div>
    <div
      class="history-region"
      :style="{ backgroundImage: 'url(' + designImage(screen, '5:3632') + ')' }"
    >
      <section ref="history" class="history-section">
        <h2 class="section-title">历史传承</h2>
        <div class="history-list">
          <article v-for="era in eras" :key="era.age">
            <span>{{ era.age }}</span>
            <div>
              <h3>{{ era.title }}</h3>
              <p>{{ era.body }}</p>
            </div>
          </article>
        </div>
      </section>
      <section class="feature-section">
        <h2 class="section-title">功能特色</h2>
        <div class="features">
          <button type="button" @click="generate">
            <img :src="designIcon(screen, '5:3602')" alt="" />
            <h3>一键生成</h3>
            <p>生成镂空轮廓<br />无需手绘基础</p></button
          ><button
            type="button"
            @click="history?.scrollIntoView({ behavior: 'smooth' })"
          >
            <img :src="designIcon(screen, '5:3588')" alt="" />
            <h3>非遗传承</h3>
            <p>认识蓟州皮影<br />传统技艺数字化</p></button
          ><button type="button" @click="printResult">
            <img :src="designIcon(screen, '5:3557')" alt="" />
            <h3>线稿打印</h3>
            <p>导出线稿参考<br />供线下观察上色</p></button
          ><button type="button" :disabled="publishing" @click="publish">
            <img :src="designIcon(screen, '5:3582')" alt="" />
            <h3>社区收藏</h3>
            <p>分享创作成果<br />交流皮影技艺</p>
          </button>
        </div>
        <p class="closing-motto">千年光影 · 一刹新生</p>
      </section>
    </div>
  </div>
</template>
<style scoped>
/* MasterGo 5:3193: source typefaces, gold/paper colors, controls and 531px columns. */
.shadow-workshop {
  --shadow-gold: #c9a84c;
  --shadow-ink: #2c1810;
  --shadow-muted: #5c4a3a;
  --shadow-paper: #faf6ee;
  color: var(--shadow-ink);
  background: var(--shadow-paper);
  font-family: var(--serif);
  padding-bottom: 122px;
}
.shadow-header {
  position: relative;
  height: 276px;
  overflow: hidden;
}
.shadow-header {
  position: relative;
  height: 286px;
  overflow: hidden;
  background: #f7f0e2;
}
.hero-photo {
  position: absolute;
  right: 0;
  top: 0;
  width: 72%;
  height: 100%;
  object-fit: cover;
  object-position: center top;
}
.hero-veil {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(250, 246, 238, 0.99) 0%, rgba(250, 246, 238, 0.96) 46%, rgba(250, 246, 238, 0.32) 72%, rgba(250, 246, 238, 0.08) 100%),
    linear-gradient(180deg, transparent 58%, rgba(250, 246, 238, 0.94) 100%);
}
.shadow-back {
  position: absolute;
  left: 16px;
  top: 16px;
  width: 38px;
  height: 38px;
  padding: 0;
  border: 1px solid rgba(139, 105, 48, 0.4);
  border-radius: 8px;
  background: rgba(250, 246, 238, 0.88);
  display: grid;
  place-items: center;
  z-index: 3;
}
.shadow-back img {
  width: 6px;
  height: 12px;
}
.shadow-seal {
  position: absolute;
  right: 22px;
  top: 22px;
  z-index: 3;
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border: 1.5px solid rgba(139, 26, 26, 0.75);
  border-radius: 3px;
  color: #8b1a1a;
  background: rgba(250, 246, 238, 0.55);
  font-family: var(--serif);
  font-size: 18px;
  line-height: 1;
  transform: rotate(-4deg);
}
.shadow-hero-copy {
  position: absolute;
  left: 20px;
  top: 74px;
  z-index: 2;
  max-width: 86%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.shadow-kicker {
  padding: 4px 9px;
  border: 1px solid rgba(139, 105, 48, 0.35);
  border-radius: 999px;
  color: #8a6a37;
  background: rgba(250, 246, 238, 0.72);
  font-size: 9px;
  letter-spacing: 1.8px;
}
.shadow-hero-copy h1 {
  margin: 14px 0 0;
  font-family: "Ma Shan Zheng", var(--serif);
  font-size: 42px;
  line-height: 1.18;
  font-weight: 400;
  letter-spacing: 2px;
  color: #2c1810;
  text-shadow: 0 1px rgba(255, 250, 238, 0.7);
}
.shadow-hero-copy h1 span {
  margin-right: 6px;
  color: #8b1a1a;
  font-size: 36px;
}
.shadow-hero-copy > p {
  margin: 10px 0 0;
  font-size: 11px;
  line-height: 1.7;
  letter-spacing: 1px;
  color: rgba(60, 40, 24, 0.68);
}
.shadow-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  font-size: 9px;
  letter-spacing: 2px;
  color: #9a7a3e;
}
.shadow-meta i {
  width: 12px;
  height: 1px;
  background: rgba(139, 105, 48, 0.45);
}
.shadow-form {
  display: block;
  margin: 16px 16px 0;
}
.design-columns {
  display: grid;
  grid-template-columns: minmax(0, 192.366fr) minmax(0, 145.172fr);
  gap: 14px;
  min-height: 531px;
  background: transparent;
}
.preview-column,
.settings-column {
  min-width: 0;
}
.puppet-preview {
  height: 251px;
  border: 1px solid rgba(201, 168, 76, 0.3);
  border-radius: 16px;
  overflow: hidden;
  position: relative;
  background: linear-gradient(180deg, #ede4d4, #e8dcc8);
  box-shadow: 0 0 30px rgba(201, 168, 76, 0.08);
}
.puppet-preview > img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.puppet-preview .example-art {
  object-fit: cover;
  opacity: 0.81;
}
.puppet-preview > img.result-art {
  animation: shadow-develop 0.6s ease-out both;
}
.lamp-veil,
.lamp-glow {
  position: absolute;
  inset: 0;
  display: block;
  pointer-events: none;
}
.lamp-veil {
  background: radial-gradient(
    ellipse at 50% 38%,
    rgba(38, 20, 12, 0.45),
    rgba(24, 12, 8, 0.82) 76%
  );
  animation: lamp-veil-lift 0.6s ease-out both;
}
.lamp-glow {
  background: radial-gradient(
    circle at 50% 36%,
    rgba(255, 206, 128, 0.62),
    rgba(255, 168, 84, 0.2) 44%,
    transparent 70%
  );
  mix-blend-mode: screen;
  animation: lamp-glow 1.6s ease-out both;
}
@keyframes shadow-develop {
  0% {
    opacity: 0.24;
    filter: brightness(0.32) grayscale(1) contrast(1.35);
  }
  55% {
    opacity: 0.9;
    filter: brightness(0.86) grayscale(0.45) saturate(0.8);
  }
  100% {
    opacity: 1;
    filter: brightness(1) grayscale(0) saturate(1);
  }
}
@keyframes lamp-veil-lift {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}
@keyframes lamp-glow {
  0% {
    opacity: 0;
    transform: scale(0.92);
  }
  24% {
    opacity: 0.92;
  }
  100% {
    opacity: 0.32;
    transform: scale(1.03);
  }
}
.craft-readout {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 14px;
  margin-top: 10px;
  padding: 8px 10px;
  border: 1px solid rgba(201, 168, 76, 0.3);
  border-radius: 10px;
  background: var(--shadow-paper);
  font-size: 9px;
  line-height: 16px;
  letter-spacing: 1px;
  color: var(--shadow-muted);
}
.craft-readout > span {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}
.craft-readout em {
  font-style: normal;
  letter-spacing: 1.4px;
  color: #8a6a37;
}
.craft-readout b {
  font-weight: 700;
  color: var(--shadow-ink);
}
.craft-readout .readout-colors i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  border: 1px solid rgba(44, 24, 16, 0.25);
}
.example-label {
  position: absolute;
  top: 12px;
  left: 8px;
  right: 8px;
  font-size: 10px;
  line-height: 15px;
  color: var(--shadow-ink);
  padding: 4px;
  background: rgba(250, 246, 238, 0.9);
  border-radius: 4px;
  text-align: center;
}
.preview-corner {
  position: absolute;
  width: 24px;
  height: 24px;
  border: solid rgba(201, 168, 76, 0.4);
  pointer-events: none;
}
.top-left {
  left: 8px;
  top: 8px;
  border-width: 1px 0 0 1px;
}
.top-right {
  right: 8px;
  top: 8px;
  border-width: 1px 1px 0 0;
}
.bottom-left {
  left: 8px;
  bottom: 8px;
  border-width: 0 0 1px 1px;
}
.bottom-right {
  right: 8px;
  bottom: 8px;
  border-width: 0 1px 1px 0;
}
.preview-toolbar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  min-height: 57px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 10px 8px;
  background: linear-gradient(transparent, rgba(250, 246, 238, 0.97));
}
.preview-title {
  pointer-events: none;
  position: absolute;
  left: 8px;
  right: 8px;
  bottom: 40px;
  z-index: 1;
  font-size: 12px;
  line-height: 16px;
  font-weight: 700;
  color: #73590f;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.preview-toolbar select {
  min-width: 0;
  width: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  font-size: 10px;
  color: var(--shadow-muted);
}
.preview-toolbar > div {
  display: flex;
  gap: 6px;
  flex: none;
}
.preview-toolbar button {
  width: 32px;
  height: 32px;
  padding: 8px;
  border: 1px solid rgba(201, 168, 76, 0.3);
  border-radius: 50%;
  background: rgba(245, 237, 224, 0.6);
}
.preview-toolbar button:last-child {
  background: rgba(201, 168, 76, 0.2);
}
.preview-toolbar button[aria-pressed="true"] {
  box-shadow: 0 0 0 2px var(--shadow-gold);
}
.preview-toolbar img {
  width: 16px;
  height: 16px;
  object-fit: contain;
}
.control-card {
  background: var(--shadow-paper);
  border: 1px solid rgba(201, 168, 76, 0.3);
  border-radius: 12px;
  padding: 12px;
}
.control-card h2,
.description-card > label {
  display: block;
  margin: 0;
  padding-left: 10px;
  border-left: 4px solid var(--shadow-gold);
  color: var(--shadow-gold);
  font-size: 12px;
  font-weight: 700;
  line-height: 16px;
  letter-spacing: 2.24px;
  white-space: nowrap;
}
.face-card {
  margin: 20px 23px 0;
  min-height: 85.45px;
}
.face-options {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}
.face-options button {
  flex: 1;
  min-width: 0;
  height: 33.45px;
  border: 1px solid rgba(201, 168, 76, 0.2);
  border-radius: 8px;
  padding: 1px;
  background: #f5ede0;
  overflow: hidden;
}
.face-options img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.6;
}
.face-options button.active {
  border-color: var(--shadow-gold);
  box-shadow: 0 0 0 2px rgba(201, 168, 76, 0.3);
}
.face-options button.active img {
  opacity: 0.8;
}
.description-card {
  margin: 20px 23px 0;
  height: 125px;
}
.description-card textarea {
  width: 100%;
  height: 70px;
  min-height: 70px;
  resize: none;
  margin-top: 10px;
  padding: 8px;
  border: 1px solid rgba(201, 168, 76, 0.2);
  border-radius: 8px;
  background: #f5ede0;
  color: var(--shadow-ink);
  font-size: 12px;
  line-height: 16px;
}
.description-card textarea::placeholder {
  color: var(--shadow-muted);
  opacity: 0.8;
}
.role-card {
  height: 240px;
}
.role-options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 10px;
}
.role-options button {
  height: 90px;
  border: 1px solid rgba(201, 168, 76, 0.2);
  border-radius: 8px;
  padding: 7px 1px;
  color: var(--shadow-muted);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.role-options b {
  font: 400 18px/26px var(--serif);
}
.role-options span {
  font-size: 10px;
  line-height: 15px;
  white-space: nowrap;
}
.role-options button.active {
  background: rgba(201, 168, 76, 0.15);
  border-color: var(--shadow-gold);
}
.role-options button.active b {
  color: var(--shadow-gold);
}
.palette-card {
  margin-top: 12px;
  min-height: 124px;
}
.palette-options {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-top: 10px;
}
.palette-options button {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  padding: 0;
  background: var(--swatch);
  border: 0;
}
.palette-options button.active {
  transform: scale(1.15);
  box-shadow:
    0 0 15px rgba(201, 168, 76, 0.3),
    0 0 0 2px var(--shadow-gold);
}
.reference-card {
  margin-top: 12px;
  min-height: 118px;
}
.reference-body {
  display: flex;
  gap: 10px;
  margin-top: 10px;
  align-items: flex-start;
}
.upload-target {
  flex: none;
  width: 76px;
  height: 76px;
  padding: 0;
  border: 1px dashed rgba(139, 26, 26, 0.45);
  border-radius: 10px;
  background: rgba(245, 237, 224, 0.7);
  color: var(--shadow-muted);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  overflow: hidden;
}
.upload-target.filled {
  border-style: solid;
  border-color: rgba(201, 168, 76, 0.55);
}
.upload-target b {
  font: 400 22px/22px var(--serif);
  color: rgba(139, 26, 26, 0.7);
}
.upload-target span {
  font-size: 10px;
  line-height: 15px;
  font-weight: 700;
  color: var(--shadow-ink);
}
.upload-target small {
  font-size: 9px;
  line-height: 13px;
}
.uploaded-sketch {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: var(--shadow-paper);
}
.file-input {
  display: none;
}
.reference-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.reference-copy p {
  margin: 0;
  font-size: 10px;
  line-height: 16px;
  color: var(--shadow-muted);
}
.reference-copy button {
  align-self: flex-start;
  padding: 5px 9px;
  border: 1px solid rgba(139, 26, 26, 0.4);
  border-radius: 7px;
  color: #8b1a1a;
  font-size: 10px;
  line-height: 14px;
}
.generate-button {
  margin: 35px 14.92px 0;
  width: calc(100% - 29.84px);
  height: 52px;
  border-radius: 12px;
  background: linear-gradient(99deg, #8b1a1a, #5c0f0f);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 16px;
  line-height: 24px;
  letter-spacing: 2.24px;
  font-weight: 700;
  color: #f5f0e8;
}
.generate-button img {
  width: 13.333px;
  height: 15px;
}
.generation-status {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  align-items: center;
  padding: 12px 14px;
  font-size: 12px;
  line-height: 18px;
}
.generation-status progress {
  width: 100%;
  accent-color: #8b1a1a;
}
.generation-status button,
.result-information button {
  padding: 8px 12px;
  border: 1px solid var(--shadow-gold);
  border-radius: 8px;
  color: #8b1a1a;
}
.result-information {
  font-size: 10px;
  line-height: 17px;
  margin: 8px 15px 0;
}
.result-information summary {
  cursor: pointer;
  color: var(--shadow-muted);
}
.result-information p {
  margin-top: 8px;
}
.result-information button {
  margin-top: 8px;
}
.craft-region {
  margin: 0 4.2px 0 20.6px;
  padding-top: 14px;
  background-position: center;
  background-size: cover;
}
.section-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 0;
  color: #73602b;
  font-size: 16px;
  line-height: 24px;
  letter-spacing: 2.24px;
  font-weight: 700;
  height: 24px;
}
.section-title:before,
.section-title:after {
  content: "";
  width: 32px;
  height: 1px;
  background: rgba(201, 168, 76, 0.5);
}
.craft-cards {
  margin: 0 18.65px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.craft-cards article {
  height: 88px;
  padding: 12px;
  border: 1px solid rgba(201, 168, 76, 0.3);
  border-radius: 12px;
  background: var(--shadow-paper);
  display: flex;
  gap: 12px;
}
.craft-cards article > img {
  width: 56px;
  height: 56px;
  flex: none;
  object-fit: cover;
  padding: 1px;
  border: 1px solid rgba(201, 168, 76, 0.2);
  border-radius: 8px;
  background: #f5ede0;
}
.craft-cards article > div {
  min-width: 0;
}
.craft-cards h3 {
  font-size: 14px;
  font-weight: 700;
  line-height: 20px;
  letter-spacing: 2.24px;
  display: flex;
  gap: 6px;
  align-items: center;
  margin: -5px 0 0;
  white-space: nowrap;
}
.craft-cards h3 span {
  font-size: 10px;
  line-height: 15px;
  color: var(--shadow-gold);
  width: 20px;
  height: 20px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(201, 168, 76, 0.3);
  border-radius: 50%;
}
.craft-cards p {
  font-size: 12px;
  line-height: 16px;
  margin-top: 0;
  color: var(--shadow-muted);
}
.process-title {
  margin-top: 24px;
}
.design-steps {
  position: relative;
  height: 145px;
  margin-top: 17px;
  display: flex;
  justify-content: space-between;
  padding: 29px 20px 0;
}
.design-steps:before {
  content: "";
  position: absolute;
  left: 52px;
  right: 52px;
  top: 49px;
  height: 1px;
  background: rgba(201, 168, 76, 0.3);
}
.design-steps button {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 0;
  height: 79px;
  font-size: 12px;
  font-weight: 700;
  line-height: 16px;
  letter-spacing: 2.24px;
}
.design-steps i {
  width: 40px;
  height: 40px;
  border: 1px solid rgba(201, 168, 76, 0.3);
  border-radius: 50%;
  background: var(--shadow-paper);
  display: grid;
  place-items: center;
}
.design-steps img {
  width: 15px;
  height: 15px;
  object-fit: contain;
}
.design-steps button:nth-child(3) {
  color: var(--shadow-gold);
}
.history-region {
  margin: 0 4.2px 0 20.6px;
  background-position: center;
  background-size: cover;
}
.history-list {
  margin: 30px 18.65px 0;
}
.history-list article {
  display: flex;
  gap: 12px;
  min-height: 76px;
  margin-bottom: 16px;
}
.history-list article:nth-child(2) {
  min-height: 57px;
}
.history-list article:nth-child(3) {
  margin-bottom: 9px;
}
.history-list article:last-child {
  min-height: 60px;
  margin-bottom: 0;
}
.history-list article > span {
  width: 32px;
  height: 32px;
  border: 1px solid rgba(201, 168, 76, 0.4);
  border-radius: 50%;
  display: grid;
  place-items: center;
  flex: none;
  background: #f5ede0;
  color: var(--shadow-gold);
  font-size: 10px;
  line-height: 15px;
  font-weight: 700;
}
.history-list article > div {
  min-width: 0;
}
.history-list h3 {
  font-size: 14px;
  line-height: 20px;
  letter-spacing: 2.24px;
  font-weight: 700;
  margin: 0;
}
.history-list p {
  margin-top: 3px;
  font-size: 12px;
  line-height: 16px;
  color: var(--shadow-muted);
}
.feature-section {
  margin: 9px -15px 0;
  padding-top: 20px;
}
.features {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin: 23px 20px 0;
  row-gap: 12px;
}
.features button {
  min-height: 136px;
  padding: 0 6px 12px;
  color: var(--shadow-ink);
  display: flex;
  flex-direction: column;
  align-items: center;
}
.features img {
  width: 20px;
  height: 20px;
  object-fit: contain;
  margin-top: 4px;
}
.features h3 {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 2.24px;
  line-height: 20px;
  margin-top: 12px;
}
.features p {
  font-size: 10px;
  line-height: 16.25px;
  color: var(--shadow-muted);
  margin-top: 12px;
  text-align: center;
}
.closing-motto {
  margin: 22px 0 0;
  font-size: 10px;
  line-height: 15px;
  letter-spacing: 2.24px;
  font-weight: 700;
  color: #8b7355;
  text-align: center;
}
@media (max-width: 360px) {
  .face-card,
  .description-card {
    margin-left: 16px;
    margin-right: 16px;
  }
  .craft-cards h3 {
    letter-spacing: 1px;
  }
  .craft-cards p {
    font-size: 11px;
    line-height: 16px;
  }
  .palette-options {
    gap: 8px 5px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .puppet-preview > img.result-art,
  .lamp-veil,
  .lamp-glow {
    animation: none;
  }
  .lamp-veil,
  .lamp-glow {
    display: none;
  }
}
</style>
