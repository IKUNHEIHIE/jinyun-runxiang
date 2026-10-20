<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from "vue";
import { designIcon, designImage } from "../design";
import { mediaUrl, notify, requireSession, session } from "../api";
import GenerationTheater from "./GenerationTheater.vue";

const screen = "layer-40-55031";
const props = defineProps<{
  generationMode: string;
  task?: any;
  resultUrl?: string;
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
const prompt = defineModel<string>("prompt", { required: true });
const color = defineModel<string>("color", { required: true });
const pattern = defineModel<string>("pattern", { required: true });
const sketch = defineModel<string>("sketch", { required: true });
const editorOpen = ref(false),
  input = ref<HTMLInputElement>();
const workbench = ref<HTMLElement>(), showShortcut = ref(true);
let workbenchObserver: IntersectionObserver | undefined;
onMounted(() => {
  if (!workbench.value || typeof IntersectionObserver === "undefined") return;
  workbenchObserver = new IntersectionObserver(([entry]) => {
    showShortcut.value = !entry.isIntersecting;
  }, { rootMargin: "0px 0px -80px 0px" });
  workbenchObserver.observe(workbench.value);
});
onUnmounted(() => workbenchObserver?.disconnect());
function openWorkbench() {
  workbench.value?.scrollIntoView({ block: "start", behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? "instant" : "smooth" });
  workbench.value?.focus({ preventScroll: true });
}
watch(
  () => session.token,
  () => {
    editorOpen.value = false;
  },
);
const hasResult = computed(
  () => props.task?.status === "SUCCESS" && !!props.task.result,
);
const disabled = computed(
  () => props.working || props.loading || props.uploading,
);
const processing = computed(() =>
  ["QUEUED", "RUNNING"].includes(props.task?.status),
);
const palette = [
  { name: "藤黄", value: "#C4A35A" },
  { name: "石绿", value: "#2D5A4A" },
  { name: "赭石", value: "#8B4513" },
  { name: "朱砂", value: "#C85A54" },
  { name: "草绿", value: "#4A6741" },
  { name: "泥金", value: "#D4AF37" },
];
const patternOptions = [
  { value: "FLORAL", label: "花鸟纹样" },
  { value: "GEOMETRIC", label: "几何纹样" },
  { value: "AUSPICIOUS", label: "吉祥文字" },
];
const theater = ref(false);
const theaterElapsed = ref(0);
const resultSize = ref("");
let generationStartedAt = 0;
watch(
  () => props.working,
  (working) => {
    if (!working || props.loading) return;
    theater.value = true;
    theaterElapsed.value = 0;
    resultSize.value = "";
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
/** 结果图分层：仅当接口真的返回多张图时才逐层描金，否则按单张处理。 */
const resultLayers = computed<string[]>(() => {
  const result = props.task?.result;
  if (!result) return [];
  for (const candidate of [result.layers, result.layer_urls, result.image_urls]) {
    if (!Array.isArray(candidate)) continue;
    const urls = [
      ...new Set(
        candidate.filter(
          (item): item is string => typeof item === "string" && !!item,
        ),
      ),
    ];
    if (urls.length > 1) return urls;
  }
  const single = props.resultUrl || result.colored_image_url || "";
  return single ? [single] : [];
});
const mainColor = computed(
  () => resultColors.value[0] || props.task?.result?.color_palette?.[0] || "",
);
const mainColorName = computed(() => {
  const matched = palette.find(
    (item) => item.value.toUpperCase() === mainColor.value.toUpperCase(),
  );
  return matched ? matched.name : mainColor.value || "—";
});
const patternLabel = computed(() => {
  const key = props.task?.result?.local_pattern;
  return patternOptions.find((item) => item.value === key)?.label || "—";
});
const theaterPreview = computed(() =>
  hasResult.value && resultLayers.value.length
    ? mediaUrl(resultLayers.value[0])
    : "",
);
const theaterStats = computed(() => [
  { label: "画幅", value: resultSize.value || "—" },
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
    ? "AI 图像生成 · 结果为二维创意参考，不是可编辑矢量"
    : "本地规则纹样模板 · 按纹样类型与配色绘制，不调用外部生成模型",
);
function measureResult(event: Event) {
  const image = event.target as HTMLImageElement;
  if (!image.naturalWidth || !image.naturalHeight) return;
  resultSize.value = image.naturalWidth + "×" + image.naturalHeight;
}
function choosePattern(value: string) {
  if (disabled.value || !requireSession()) return;
  pattern.value = value;
  editorOpen.value = true;
}
const intro =
  "宁氏漆艺镶嵌与联升斋刺\n绣，均为津门非遗工艺。\n以数字化纹样辅助设计，\n让传统工艺在当下焕发新\n生。";
function chooseUpload() {
  if (!disabled.value && requireSession()) input.value?.click();
}
function uploaded(event: Event) {
  if (!(event.target as HTMLInputElement).files?.length) return;
  editorOpen.value = true;
  emit("upload", event);
}
function edit() {
  if (!disabled.value && requireSession()) editorOpen.value = true;
}
function generate() {
  if (disabled.value) return;
  if (!prompt.value.trim()) {
    notify("先写下你的创作灵感吧");
    return;
  }
  emit("generate");
  editorOpen.value = false;
}
</script>

<template>
  <div class="lacquer-workshop" data-design-node="40:55031">
    <GenerationTheater
      v-if="theater"
      title="正在描金"
      :steps="['解析纹样与主色', '起稿分线', '逐层描金', '合成纹样参考']"
      :preview="theaterPreview"
      :stats="theaterStats"
      :caption="theaterCaption"
      :waiting="working"
      @done="theater = false"
    />
    <div class="presentation">
      <img
        class="paper-texture silk"
        :src="designImage(screen, '5:00403')"
        alt=""
      />
      <img
        class="paper-texture fibers"
        :src="designImage(screen, '5:9689')"
        alt=""
      />
      <img
        class="halo first-halo"
        :src="designImage(screen, '5:00402')"
        alt=""
      />
      <div
        class="landscape"
        :style="{
          backgroundImage: 'url(' + designImage(screen, '5:9918') + ')',
        }"
      />
      <header class="lacquer-header">
        <button
          class="lacquer-back"
          aria-label="返回上一页"
          @click="emit('back')"
        >
          <img :src="designIcon(screen, '40:55065')" alt="" />
        </button>
        <p class="eyebrow">津门非遗 · 传统工艺</p>
        <h1>漆绣智绘</h1>
        <img
          class="title-underline"
          :src="designImage(screen, '5:00377')"
          alt=""
        />
        <span class="title-english">LACQUER &amp; EMBROIDERY</span>
        <img
          class="vertical-rule"
          :src="designImage(screen, '5:00387')"
          alt=""
        />
        <i class="hero-corner top-corner" /><i
          class="hero-corner bottom-corner"
        />
        <img class="hero-shadow" :src="designImage(screen, '5:00390')" alt="" />
        <img
          class="hero-art"
          :src="designImage(screen, '5:00396')"
          alt="漆绣工艺展示"
        />
        <div class="hero-motto">
          <img :src="designImage(screen, '5:00357')" alt="" /><span
            >千年工艺 · 智绘新生</span
          ><img :src="designImage(screen, '5:00367')" alt="" />
        </div>
        <div class="hero-quote">
          <img :src="designImage(screen, '5:00010')" alt="" />
          <p>一针一线绣乾坤，一漆一镶嵌日月</p>
          <p>纹样参考，古今交融谱新篇</p>
        </div>
      </header>
      <section class="intro-section art-section">
        <span class="section-number">壹</span>
        <div class="framed-art left-art">
          <img
            :src="designImage(screen, '5:00257')"
            alt="宁氏漆艺与联升斋刺绣"
          /><i class="art-seal" />
        </div>
        <div class="right-copy">
          <h2 class="section-tag"><span>◆</span>项目简介</h2>
          <p class="intro-copy">{{ intro }}</p>
          <img
            class="caption-rule"
            :src="designImage(screen, '5:00233')"
            alt=""
          />
          <p class="article-caption">江南丝绣，漆韵流光</p>
        </div>
      </section>
      <div class="ornament first-ornament">
        <img :src="designImage(screen, '5:9940')" alt="" /><span>◆</span>
      </div>
      <section class="features-section art-section">
        <div class="panel-backdrop" />
        <div class="left-copy">
          <h2 class="section-tag"><span>◆</span>艺术特点</h2>
          <ul class="paired-list">
            <li>细腻雅洁</li>
            <li class="emphasized">设色柔和</li>
            <li>双面精绣</li>
            <li>形神兼备</li>
          </ul>
          <img
            class="caption-rule"
            :src="designImage(screen, '5:00007')"
            alt=""
          />
          <p class="article-caption">丝光流转，色韵天成</p>
        </div>
        <div class="framed-art right-art">
          <img :src="designImage(screen, '5:9953')" alt="丝绣艺术特点" /><i
            class="art-seal"
          />
        </div>
        <span class="section-number right-number">贰</span>
      </section>
      <div class="ornament second-ornament">
        <img :src="designImage(screen, '5:00284')" alt="" /><span>◆</span>
      </div>
      <section class="process-section art-section">
        <div class="panel-backdrop" />
        <span class="section-number">叁</span>
        <div class="framed-art process-art">
          <img :src="designImage(screen, '5:9815')" alt="丝绣核心工艺" /><b
            class="craft-stamp"
            >匠心</b
          >
        </div>
        <div class="right-copy">
          <h2 class="section-tag"><span>◆</span>核心工艺</h2>
          <ol class="process-list">
            <li
              v-for="(step, index) in ['起稿', '分线', '配色', '运针', '收绣']"
              :key="step"
              :class="{ emphasized: index === 0 }"
            >
              <small>{{ index + 1 }}</small
              >{{ step }}
            </li>
          </ol>
          <img
            class="caption-rule"
            :src="designImage(screen, '5:9890')"
            alt=""
          />
          <p class="article-caption">五道工序，百年传承</p>
        </div>
      </section>
      <div class="ornament third-ornament">
        <img :src="designImage(screen, '5:00277')" alt="" /><span>◆</span>
      </div>
      <section class="themes-section art-section">
        <div class="panel-backdrop" />
        <div class="left-copy">
          <h2 class="section-tag"><span>◆</span>经典题材</h2>
          <ul class="paired-list topic-list">
            <li class="emphasized">花鸟</li>
            <li>山水</li>
            <li>人物</li>
            <li>园林</li>
          </ul>
          <img
            class="caption-rule"
            :src="designImage(screen, '5:00312')"
            alt=""
          />
          <p class="article-caption">四时花鸟，山水人物</p>
        </div>
        <div class="framed-art right-art">
          <img :src="designImage(screen, '5:00297')" alt="漆绣经典题材" /><i
            class="art-seal"
          />
        </div>
        <span class="section-number right-number">肆</span>
      </section>
      <div class="ornament fourth-ornament">
        <img :src="designImage(screen, '5:9932')" alt="" /><span>◆</span>
      </div>
      <section class="applications-section art-section">
        <span class="section-number">伍</span>
        <div class="framed-art left-art">
          <img :src="designImage(screen, '5:9793')" alt="漆绣的生活应用" /><i
            class="art-seal"
          />
        </div>
        <div class="right-copy">
          <h2 class="section-tag"><span>◆</span>应用之美</h2>
          <ul class="paired-list application-list">
            <li
              v-for="(item, index) in [
                '屏风摆件',
                '团扇挂画',
                '服饰配饰',
                '文创家居',
              ]"
              :key="item"
              :class="{ emphasized: index === 1 }"
            >
              <span>{{ item.slice(0, 2) }}<br />{{ item.slice(2) }}</span>
            </li>
          </ul>
          <img
            class="caption-rule"
            :src="designImage(screen, '5:9759')"
            alt=""
          />
          <p class="article-caption">绣入生活，美在方寸</p>
        </div>
      </section>
      <div class="ornament fifth-ornament">
        <img :src="designImage(screen, '5:00268')" alt="" /><span>◆</span>
      </div>
    </div>
    <Teleport to="body"><button v-if="showShortcut && !editorOpen && !session.authVisible" type="button" class="creation-shortcut" aria-controls="lacquer-workbench" @click="openWorkbench">
      前往纹样创作 <span aria-hidden="true">↓</span>
    </button></Teleport>
    <section ref="workbench" id="lacquer-workbench" class="workbench" tabindex="-1" aria-label="漆绣创作">
      <img
        class="halo second-halo"
        :src="designImage(screen, '5:9686')"
        alt=""
      />
      <div class="workbench-heading">
        <span class="section-number">陆</span>
        <h2 class="section-tag">纹样创作<span>◆</span></h2>
        <small>灵感成形</small>
      </div>
      <div class="workbench-grid">
        <div class="workbench-description">
          <p>
            以丝为墨，以针为笔。选择纹样与配色，用本地模板或 AI 图像生成创作。上传参考图后，可使用支持图片编辑的模型重绘。
          </p>
          <div class="model-options" role="group" aria-label="选择漆绣纹样">
            <button
              v-for="item in patternOptions"
              :key="item.value"
              :disabled="disabled"
              :aria-pressed="pattern === item.value"
              @click="choosePattern(item.value)"
            >
              {{ item.label }}
            </button>
          </div>
        </div>
        <div class="workbench-images">
          <button
            class="upload-target"
            :disabled="disabled"
            @click="chooseUpload"
          >
            <img
              v-if="sketch"
              class="uploaded-sketch"
              :src="mediaUrl(sketch)"
              alt="已上传的参考草图"
            /><template v-else
              ><img
                class="upload-icon"
                :src="designIcon(screen, '5:00095')"
                alt=""
              /><span>点击上传</span><small>草图/照片</small></template
            ></button
          ><input
            ref="input"
            class="file-input"
            type="file"
            accept="image/png,image/jpeg,image/webp"
            @change="uploaded"
          /><button
            class="reference-preview"
            :disabled="disabled"
            aria-label="查看创作参数或结果"
            @click="edit"
          >
            <template v-if="hasResult">
              <img
                v-for="(url, index) in resultLayers"
                :key="index + '-' + url"
                :class="resultLayers.length > 1 ? 'layer-art' : 'result-art'"
                :style="
                  resultLayers.length > 1
                    ? { animationDelay: index * 0.12 + 's' }
                    : undefined
                "
                :src="mediaUrl(url)"
                alt="当前纹样创作结果"
                @load="measureResult"
              />
              <i
                v-if="resultLayers.length < 2"
                class="gild-sweep"
                aria-hidden="true"
              />
            </template>
            <template v-else>
              <img
                :src="designImage(screen, '5:00086')"
                alt="设计中的工艺参考示例"
              />
              <img
                class="preview-frame"
                :src="designImage(screen, '5:00089')"
                alt=""
              />
            </template>
            <span>{{
              uploading
                ? "上传中…"
                : processing
                  ? "创作中 " + (task?.progress || 0) + "%"
                  : working
                    ? "提交中…"
                    : hasResult
                      ? task.result.generation_method === 'ai_image' ? 'AI 图像' : "本地纹样"
                      : "参考示例"
            }}</span>
          </button>
        </div>
      </div>
      <div v-if="hasResult" class="craft-readout" aria-label="工艺读数">
        <span
          ><em>主色</em
          ><i class="readout-dot" :style="{ backgroundColor: mainColor }" /><b>{{
            mainColorName
          }}</b></span
        >
        <span><em>纹样</em><b>{{ patternLabel }}</b></span>
        <span
          ><em>取色</em
          ><b>{{ resultColors.length ? resultColors.length + " 色" : "—" }}</b></span
        >
      </div>
      <div class="traditional-palette">
        <h3><img :src="designIcon(screen, '5:00217')" alt="" />传统配色参考</h3>
        <div class="swatches">
          <button
            v-for="item in palette"
            :key="item.value"
            :disabled="disabled"
            :aria-label="item.name + ' ' + item.value"
            :aria-pressed="color === item.value"
            @click="color = item.value"
          >
            <i :style="{ backgroundColor: item.value }" /><span>{{
              item.name
            }}</span>
          </button>
        </div>
        <span
          v-if="!palette.some((item) => item.value === color)"
          class="custom-color"
          >历史配色 {{ color }}</span
        >
      </div>
      <p v-if="loading" class="workbench-status" role="status">
        正在恢复上次创作…
      </p>
      <p v-if="uploading" class="workbench-status" role="status">
        正在上传参考草图…
      </p>
      <div v-if="processing" class="workbench-status" role="status">
        <progress :value="task?.progress || 0" max="100" /><button
          @click="emit('cancel')"
        >
          取消任务
        </button>
      </div>
      <div v-if="error" class="workbench-error" role="alert">
        {{ error
        }}<button
          v-if="task && ['QUEUED', 'RUNNING'].includes(task.status)"
          @click="emit('retry')"
        >
          重新查询任务状态
        </button>
      </div>
      <div class="workbench-actions">
        <button class="create-button" :disabled="disabled" @click="edit">
          {{ hasResult ? "调整参数重新创作" : "开始创作" }}</button
        ><template v-if="hasResult"
          ><button @click="emit('export')">导出设计图</button
          ><button
            :disabled="favoriteBusy"
            :aria-pressed="!!task.collected"
            @click="emit('favorite')"
          >
            {{ task.collected ? "取消收藏" : "收藏创作" }}</button
          ><button :disabled="publishing" @click="emit('publish')">
            {{ publishing ? "正在发布…" : "分享至社区" }}
          </button></template
        >
      </div>
      <details v-if="hasResult" class="result-description">
        <summary>查看创作说明</summary>
        <p>{{ task.result.description }}</p>
      </details>
      <p class="capability-note">
        配色仅供参考，非实物材料色号。本地模板不会重绘草图；AI 模式需开启图片编辑能力。
      </p>
    </section>
    <footer class="lacquer-footer">
      <div class="footer-divider">
        <img :src="designImage(screen, '5:00047')" alt="" /><img
          :src="designIcon(screen, '5:00052')"
          alt=""
        /><img :src="designImage(screen, '5:00044')" alt="" />
      </div>
      <div
        class="footer-motto"
        :style="{
          backgroundImage: 'url(' + designImage(screen, '5:00055') + ')',
        }"
      >
        <p>丝线入画，针意传神</p>
        <p>绣承古韵，艺焕新生</p>
      </div>
    </footer>
    <Teleport to="body"
      ><div
        v-if="editorOpen"
        class="lacquer-editor-overlay"
        @click.self="editorOpen = false"
      >
        <section
          class="lacquer-editor"
          role="dialog"
          aria-modal="true"
          aria-label="漆绣创作参数"
        >
          <button
            class="sheet-close"
            aria-label="关闭创作参数"
            @click="editorOpen = false"
          >
            关闭
          </button>
          <h2>纹样创作</h2>
          <p>
            根据文字和配色生成二维纹样参考；AI 模式可用已启用图片编辑的模型重绘参考草图。
          </p>
          <figure v-if="hasResult" class="editor-result">
            <img :src="mediaUrl(resultUrl)" alt="当前生成的纹样参考" />
            <figcaption>{{ task.result.generation_method === 'ai_image' ? 'AI 图像创作' : '本地纹样参考' }}</figcaption>
            <p>{{ task.result.description }}</p>
          </figure>
          <form @submit.prevent="generate">
            <slot name="generation-mode" />
            <label
              >纹样类型<select v-model="pattern" :disabled="disabled">
                <option v-for="item in patternOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
              </select></label
            ><label
              >文字描述<textarea
                v-model.trim="prompt"
                required
                maxlength="1000"
                :disabled="disabled"
                placeholder="描述花鸟、几何组合或福寿喜和等吉祥文字…"
              /></label
            ><label
              >主色<input
                v-model="color"
                type="color"
                :disabled="disabled" /></label
            ><img
              v-if="sketch"
              class="editor-sketch"
              :src="mediaUrl(sketch)"
              alt="上传的创作参考"
            />
            <p v-if="error" class="workbench-error" role="alert">{{ error }}</p>
            <button class="create-button" :disabled="disabled">
              {{ working ? "正在创作…" : generationMode === 'AI' ? "AI 生成纹样" : "生成本地纹样参考" }}
            </button>
          </form>
        </section>
      </div></Teleport
    >
  </div>
</template>

<style scoped>
.lacquer-workshop {
  --lacquer-paper: #f0ebe0;
  --lacquer-green: #2d4a3e;
  --lacquer-gold: #b8a67a;
  background: var(--lacquer-paper);
  color: #5c5c5c;
  font-family: var(--serif);
  overflow: hidden;
}
.lacquer-workshop h1,
.lacquer-workshop h2,
.lacquer-workshop h3,
.lacquer-workshop p {
  margin: 0;
}
.presentation {
  position: relative;
  height: 1741px;
}
.paper-texture {
  position: absolute;
  inset: 0 0 auto;
  width: 100%;
  height: 667px;
  object-fit: cover;
  pointer-events: none;
}
.silk {
  opacity: 0.06;
}
.fibers {
  opacity: 0.04;
}
.halo {
  position: absolute;
  object-fit: cover;
  border-radius: 50%;
  pointer-events: none;
}
.first-halo {
  left: -48px;
  top: 949.66px;
  width: 192px;
  height: 192px;
  opacity: 0.4;
}
.landscape {
  position: absolute;
  top: 684px;
  width: 100%;
  height: 785px;
  background-size: cover;
  background-position: center;
}
.lacquer-header {
  position: absolute;
  inset: 0 0 auto;
  height: 464px;
}
.lacquer-back {
  position: absolute;
  left: 8px;
  top: 10px;
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  padding: 0;
  background: rgba(240, 230, 208, 0.8);
  border: 1px solid rgba(184, 166, 122, 0.4);
  border-radius: 50%;
  z-index: 1;
}
.lacquer-back img {
  width: 5.833px;
  height: 11.667px;
}
.eyebrow {
  position: absolute;
  top: 38px;
  left: 50%;
  transform: translateX(-50%);
  width: 226.08px;
  height: 42px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(184, 166, 122, 0.4);
  background: rgba(247, 244, 237, 0.8);
  color: #2d4a3e;
  font-size: 12px;
  letter-spacing: 2px;
}
.lacquer-header h1 {
  position: absolute;
  left: 6.4%;
  top: 100px;
  width: 56px;
  height: 256px;
  writing-mode: vertical-rl;
  text-orientation: upright;
  font:
    56px/1 "Ma Shan Zheng",
    var(--serif);
  letter-spacing: 8px;
  color: #1a1a1a;
}
.title-underline {
  position: absolute;
  left: 5.3333%;
  top: 349px;
  width: 64px;
  height: 3px;
}
.title-english {
  position: absolute;
  left: 29.0667%;
  top: 108px;
  height: 170.69px;
  width: 15px;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  font-size: 10px;
  line-height: 15px;
  letter-spacing: 2px;
  white-space: nowrap;
  color: #8b8273;
}
.vertical-rule {
  position: absolute;
  left: 25.6%;
  top: 100px;
  width: 2px;
  height: 120px;
}
.hero-art {
  position: absolute;
  left: 34.9333%;
  top: 100px;
  width: 57.0667%;
  height: 280px;
  object-fit: cover;
  border: 2px solid #c8b896;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.hero-corner {
  position: absolute;
  width: 32px;
  height: 32px;
  border-color: #c8b896;
  border-style: solid;
}
.top-corner {
  left: 87.7333%;
  top: 94px;
  border-width: 2px 2px 0 0;
}
.bottom-corner {
  left: 40%;
  top: 274px;
  border-width: 0 0 2px 2px;
}
.hero-shadow {
  position: absolute;
  left: 45.8667%;
  top: 292px;
  width: 44.5333%;
  height: 16px;
  border-radius: 50%;
}
.hero-motto {
  position: absolute;
  top: 392px;
  left: 5.3333%;
  right: 5.3333%;
  display: flex;
  align-items: center;
  gap: 12px;
  height: 16px;
  color: #a69472;
  font-size: 11px;
  letter-spacing: 3.76px;
  white-space: nowrap;
}
.hero-motto img {
  flex: 1;
  min-width: 0;
  height: 1px;
}
.hero-quote {
  position: absolute;
  left: 12.8%;
  top: 429.5px;
  font-size: 13px;
  line-height: 18px;
}
.hero-quote p + p {
  margin-top: 4.5px;
  color: #4a6b8a;
}
.hero-quote > img {
  position: absolute;
  left: -16px;
  top: 0.5px;
  width: 2px;
  height: 44px;
}
.art-section {
  position: absolute;
  width: 100%;
}
.intro-section {
  top: 464px;
  height: 250px;
}
.features-section {
  top: 714px;
  height: 192px;
}
.process-section {
  top: 920px;
  height: 226px;
}
.themes-section {
  top: 1206px;
  height: 192px;
}
.applications-section {
  top: 1480px;
  height: 261px;
  background: #dbccaf;
}
.section-number {
  position: absolute;
  left: 7.2%;
  top: 24px;
  font:
    28px/32px "Ma Shan Zheng",
    var(--serif);
  letter-spacing: 4px;
  color: #b8a67a;
  opacity: 0.6;
}
.right-number {
  left: auto;
  right: 7.2%;
}
.framed-art {
  position: absolute;
  width: 29.3333%;
  height: 130px;
  border: 1px solid #c8b896;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  z-index: 1;
}
.framed-art::after {
  content: "";
  position: absolute;
  inset: 7px -1px -1px 7px;
  border: 1px solid rgba(184, 166, 122, 0.4);
  border-radius: 12px;
  transform: translate(1px, 1px);
  z-index: -1;
}
.framed-art > img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 11px;
}
.left-art {
  left: 17.6%;
  top: 16px;
}
.right-art {
  left: 53.6%;
  top: 16px;
}
.process-art {
  left: 16.5333%;
  top: 47px;
}
.art-seal {
  position: absolute;
  right: 8px;
  bottom: 8px;
  width: 16px;
  height: 16px;
  border: 1px solid rgba(74, 107, 138, 0.2);
  background: rgba(74, 107, 138, 0.1);
  border-radius: 50%;
}
.right-art .art-seal {
  right: auto;
  left: 8px;
  top: 8px;
  width: 12px;
  height: 12px;
}
.right-copy {
  position: absolute;
  left: 53.3333%;
  right: 0;
  top: 25px;
}
.left-copy {
  position: absolute;
  left: 4.2667%;
  top: 25px;
  width: 46.6667%;
}
.section-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 14px;
  border: 1px solid #b8a67a;
  background: rgba(45, 74, 62, 0.06);
  color: #2d4a3e;
  font-size: 13px;
  font-weight: 400;
  line-height: 19px;
  letter-spacing: 2px;
  width: max-content;
  height: 29px;
  white-space: nowrap;
}
.section-tag span {
  color: #b8a67a;
  font-size: 8px;
  line-height: 12px;
}
.intro-copy {
  margin-top: 12px !important;
  white-space: pre-line;
  font-size: 13px;
  line-height: 26px;
}
.caption-rule {
  display: block;
  width: 163px;
  height: 1px;
  margin-top: 12px;
}
.article-caption {
  margin-top: 8px !important;
  color: #8b8273;
  font:
    11px/17.88px "Source Han Sans",
    sans-serif;
  white-space: nowrap;
}
.panel-backdrop {
  position: absolute;
  top: 16px;
  left: 4.2667%;
  right: 5.3333%;
  height: 165px;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(184, 166, 122, 0.2);
  border-radius: 12px;
}
.paired-list {
  display: grid;
  grid-template-columns: 77.5px 77.5px;
  gap: 10px 8px;
  margin: 14px 0 0;
  padding: 0;
  list-style: none;
  font-size: 12px;
  line-height: 18px;
}
.paired-list li {
  display: flex;
  align-items: center;
  gap: 2px;
}
.paired-list li::before {
  content: "";
  flex: 0 0 6px;
  height: 6px;
  border-radius: 50%;
  background: #c8b896;
}
.paired-list .emphasized {
  color: #2d4a3e;
  font-weight: 600;
}
.paired-list .emphasized::before {
  background: #2d4a3e;
}
.features-section .caption-rule {
  margin-top: 12px;
}
.features-section .art-seal {
  background: rgba(74, 107, 138, 0.2);
}
.process-section .panel-backdrop {
  left: 5.3333%;
  height: 194px;
}
.craft-stamp {
  position: absolute;
  right: 6px;
  bottom: 8px;
  font-size: 8px;
  color: #8b3a3a;
}
.process-list {
  margin: 12px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  grid-template-columns: 66px 66px;
  gap: 8px;
  font-size: 11px;
  line-height: 16px;
}
.process-list li {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 30px;
  border-radius: 99px;
  background: rgba(200, 184, 150, 0.1);
}
.process-list small {
  font-size: 9px;
  color: #8b8273;
}
.process-list .emphasized {
  background: rgba(45, 74, 62, 0.05);
  color: #2d4a3e;
}
.themes-section .panel-backdrop {
  left: 3.4667%;
  top: 0;
  height: 185px;
}
.themes-section .left-copy {
  left: 3.4667%;
  top: 9px;
}
.themes-section .right-art {
  left: 55.7333%;
  top: 29px;
}
.themes-section .right-number {
  top: 8px;
}
.topic-list {
  gap: 8px;
  margin-top: 12px;
}
.topic-list li {
  height: 32px;
  gap: 2px;
  padding-left: 9px;
  border-radius: 8px;
}
.topic-list li::before {
  flex-basis: 8px;
  height: 8px;
}
.topic-list .emphasized {
  background: rgba(45, 74, 62, 0.05);
}
.themes-section .caption-rule {
  margin-top: 12px;
}
.application-list {
  margin-top: 12px;
  gap: 8px;
  font-size: 11px;
  line-height: 16px;
}
.application-list li {
  height: 46px;
  padding-left: 9px;
  gap: 8px;
  border-radius: 8px;
}
.application-list li::before {
  flex-basis: 8px;
  height: 8px;
}
.application-list .emphasized {
  background: rgba(45, 74, 62, 0.05);
}
.applications-section .caption-rule {
  margin-top: 12px;
}
.ornament {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  width: 200px;
  height: 12px;
  display: grid;
  place-items: center;
}
.ornament img {
  position: absolute;
  top: 5.5px;
  width: 200px;
  height: 1px;
}
.ornament span {
  position: relative;
  padding: 0 12px;
  background: #f0ebe0;
  color: rgba(184, 166, 122, 0.4);
  font-size: 8px;
  line-height: 12px;
  letter-spacing: 2px;
}
.first-ornament {
  top: 708px;
}
.second-ornament {
  top: 876px;
}
.third-ornament {
  top: 1170px;
}
.fourth-ornament {
  top: 1433px;
}
.fifth-ornament {
  top: 1694px;
}
.workbench {
  position: relative;
  padding: 16px 20px 16px;
  background: #dbccaf;
}
.second-halo {
  right: 0;
  top: 171.75px;
  width: 224px;
  height: 224px;
  opacity: 0.3;
}
.workbench > :not(.halo) {
  position: relative;
}
.workbench-heading {
  height: 40px;
  display: flex;
  align-items: flex-start;
  padding-left: 54px;
  gap: 8px;
}
.workbench-heading .section-number {
  left: 7px;
  top: 8px;
}
.workbench-heading > small {
  font-size: 10px;
  line-height: 29px;
  color: #8b8273;
}
.workbench-grid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 120px;
  gap: 11px;
  min-height: 188px;
}
.workbench-description > p {
  font-size: 13px;
  line-height: 26px;
}
.model-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}
.model-options button {
  min-height: 36px;
  padding: 7px 10px;
  border: 0;
  border-radius: 99px;
  background: rgba(45, 74, 62, 0.05);
  color: #2d4a3e;
  font-size: 11px;
  line-height: 18px;
}
.model-options button:nth-child(2) {
  background: rgba(74, 107, 138, 0.05);
  color: #4a6b8a;
}
.model-options button:nth-child(3) {
  background: rgba(200, 184, 150, 0.1);
  color: #8b8273;
}
.model-options button:disabled {
  opacity: 0.6;
}
.model-options button[aria-pressed="true"] { box-shadow: inset 0 0 0 1px currentColor; }
.creation-shortcut {
  position: fixed; z-index: 40;
  left: 50%; transform: translateX(-50%);
  bottom: calc(16px + var(--safe-bottom));
  width: min(calc(100% - 32px), 448px); min-height: 46px;
  display: flex; align-items: center; justify-content: center; gap: 18px;
  padding: 10px 20px; border-radius: 12px;
  border: 1px solid #b8a67a;
  background: #2d4a3e; color: #faf7ee;
  font: 15px var(--serif); box-shadow: 0 4px 16px #2d4a3e24;
}
.workbench { scroll-margin-top: calc(20px + var(--safe-top)); }
.workbench-images {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.upload-target {
  position: relative;
  width: 120px;
  height: 100px;
  padding: 0;
  border: 2px solid #2d4a3e;
  border-radius: 12px;
  background: rgba(45, 74, 62, 0.06);
  color: #2d4a3e;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  font-size: 10px;
  line-height: 12.5px;
  overflow: hidden;
}
.upload-icon {
  width: 16px;
  height: 16px;
  margin-bottom: 8px;
}
.upload-target small {
  font-size: 10px;
}
.uploaded-sketch {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.file-input {
  display: none;
}
.reference-preview {
  position: relative;
  padding: 0;
  width: 118px;
  height: 78px;
  margin: 0 1px;
  border: 0;
  background: rgba(45, 74, 62, 0.2);
  overflow: hidden;
}
.reference-preview > img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.reference-preview .preview-frame {
  position: absolute;
  inset: 0;
}
.reference-preview > img.result-art {
  animation: gild-reveal 0.9s ease-out both;
}
.reference-preview > img.layer-art {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  opacity: 0;
  animation: layer-in 0.42s ease-out forwards;
}
.gild-sweep {
  position: absolute;
  inset: 0;
  display: block;
  pointer-events: none;
  background: linear-gradient(
    100deg,
    transparent 24%,
    rgba(212, 175, 55, 0.45) 45%,
    rgba(255, 240, 200, 0.92) 52%,
    rgba(212, 175, 55, 0.42) 58%,
    transparent 78%
  );
  transform: translateX(-130%);
  animation: gild-scan 1s ease-out 0.12s both;
}
@keyframes gild-reveal {
  from {
    clip-path: inset(0 100% 0 0);
    opacity: 0.4;
  }
  to {
    clip-path: inset(0 0 0 0);
    opacity: 1;
  }
}
@keyframes layer-in {
  from {
    opacity: 0;
    transform: translateY(3px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
@keyframes gild-scan {
  0% {
    transform: translateX(-130%);
    opacity: 0;
  }
  18% {
    opacity: 1;
  }
  100% {
    transform: translateX(130%);
    opacity: 0;
  }
}
.craft-readout {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
  margin-top: 12px;
  padding: 9px 12px;
  border: 1px solid #b8a67a;
  border-radius: 10px;
  background: rgba(247, 244, 237, 0.6);
  font-size: 11px;
  line-height: 17px;
  color: #5c5c5c;
}
.craft-readout > span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.craft-readout em {
  font-style: normal;
  letter-spacing: 1.6px;
  color: #8b8273;
}
.craft-readout b {
  font-weight: 600;
  color: #2d4a3e;
}
.readout-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 1px solid rgba(45, 74, 62, 0.35);
}
.reference-preview span {
  position: absolute;
  left: 50%;
  top: 28px;
  transform: translateX(-50%);
  padding: 4px 8px;
  font-size: 10px;
  line-height: 15px;
  color: white;
  background: rgba(45, 74, 62, 0.6);
  border-radius: 4px;
  white-space: nowrap;
}
.traditional-palette {
  min-height: 113px;
  margin-top: 20px;
  padding: 17px 16px 13px;
  border: 1px solid #b8a67a;
  border-radius: 12px;
  background: rgba(247, 244, 237, 0.6);
}
.traditional-palette h3 {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  font-weight: 600;
  line-height: 18px;
  color: #4a6b8a;
}
.traditional-palette h3 img {
  width: 12px;
  height: 12px;
}
.swatches {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}
.swatches button {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  width: 32px;
  padding: 0;
  border: 0;
  background: none;
  color: #5c5c5c;
  font-size: 9px;
  line-height: 13.5px;
}
.swatches i {
  width: 32px;
  height: 32px;
  border-radius: 50%;
}
.swatches [aria-pressed="true"] i {
  outline: 2px solid #2d4a3e;
  outline-offset: 2px;
}
.custom-color {
  display: block;
  margin-top: 8px;
  font-size: 10px;
}
.workbench-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}
.workbench-actions button,
.workbench-status button,
.workbench-error button {
  padding: 8px 10px;
  border: 1px solid #b8a67a;
  border-radius: 8px;
  background: #f7f4ed;
  color: #2d4a3e;
  font-size: 12px;
}
.create-button {
  padding: 10px 16px;
  border: 0;
  border-radius: 8px;
  background: #2d4a3e !important;
  color: #f7f4ed !important;
  font-size: 13px;
}
.workbench-status {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px !important;
  font-size: 12px;
}
.workbench-status progress {
  flex: 1;
  min-width: 0;
  accent-color: #2d4a3e;
}
.workbench-error {
  margin-top: 12px;
  color: #8b3a3a;
  font-size: 12px;
}
.workbench-error button {
  margin-left: 8px;
}
.capability-note {
  margin-top: 12px !important;
  font-size: 11px;
  line-height: 18px;
  color: #5c5c5c;
}
.result-description {
  margin-top: 12px;
  font-size: 12px;
  line-height: 22px;
}
.result-description p {
  margin-top: 8px;
}
.lacquer-footer {
  height: 238px;
  padding: 31px 20px 84px;
  background: #f0ebe0;
}
.footer-divider {
  display: flex;
  align-items: center;
  gap: 14px;
  height: 12.333px;
}
.footer-divider img {
  flex: 1;
  min-width: 0;
  height: 1px;
}
.footer-divider img:nth-child(2) {
  flex: 0 0 12px;
  width: 12px;
  height: 12.333px;
}
.footer-motto {
  height: 89px;
  margin-top: 9px;
  background-size: cover;
  background-position: center;
  padding-top: 14px;
}
.footer-motto p {
  font:
    22px/35.75px "Ma Shan Zheng",
    var(--serif);
  letter-spacing: 3px;
  margin-left: 48px;
  color: #8de4c0;
}
.footer-motto p + p {
  color: #50aaff;
}
.lacquer-editor-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: flex-end;
  background: rgba(0, 0, 0, 0.45);
  padding-top: 24px;
}
.lacquer-editor {
  position: relative;
  width: min(100%, 480px);
  margin: 0 auto;
  max-height: 90vh;
  max-height: 90dvh;
  overflow: auto;
  padding: 28px 20px max(24px, env(safe-area-inset-bottom));
  border-radius: 20px 20px 0 0;
  color: #2d4a3e;
  background: #f7f4ed;
  font-family: var(--serif);
}
.lacquer-editor .sheet-close {
  display: block;
  margin-left: auto;
  border: 0;
  background: none;
  color: #2d4a3e;
  padding: 8px;
  font-size: 12px;
  width: auto;
  min-width: 44px;
  min-height: 40px;
  white-space: nowrap;
}
.lacquer-editor h2 {
  font-size: 20px;
  margin: 8px 0;
}
.lacquer-editor > p {
  font-size: 12px;
  line-height: 20px;
}
.lacquer-editor form {
  display: grid;
  gap: 12px;
  margin-top: 16px;
}
.lacquer-editor label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
}
.lacquer-editor select,
.lacquer-editor textarea {
  width: 100%;
  border: 1px solid #c8b896;
  border-radius: 8px;
  padding: 10px;
  background: white;
  color: #2d4a3e;
  font: 14px/22px var(--serif);
}
.lacquer-editor textarea {
  min-height: 100px;
  resize: vertical;
}
.lacquer-editor input[type="color"] {
  width: 64px;
  height: 40px;
  padding: 2px;
  border: 1px solid #c8b896;
  border-radius: 6px;
}
.editor-sketch {
  max-width: 100%;
  max-height: 180px;
  object-fit: contain;
}
.editor-result {
  margin: 16px 0;
  text-align: center;
  font-size: 11px;
}
.editor-result img {
  display: block;
  width: 100%;
  max-height: 320px;
  object-fit: contain;
  border-radius: 8px;
  margin-bottom: 8px;
}
@media (max-width: 374px) {
  .intro-copy {
    font-size: 12px;
  }
  .article-caption {
    font-size: 10px;
  }
  .workbench-grid {
    grid-template-columns: minmax(0, 1fr) 112px;
    gap: 10px;
  }
  .upload-target {
    width: 112px;
  }
  .reference-preview {
    width: 110px;
  }
  .workbench-description > p {
    font-size: 12px;
  }
  .swatches {
    gap: 10px;
  }
  .hero-quote {
    font-size: 12px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .reference-preview > img.result-art,
  .reference-preview > img.layer-art,
  .gild-sweep {
    animation: none;
    opacity: 1;
    clip-path: none;
    transform: none;
  }
  .gild-sweep {
    display: none;
  }
}
</style>
