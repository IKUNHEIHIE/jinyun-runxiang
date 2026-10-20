<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from "vue";
import { useRouter, onBeforeRouteLeave } from "vue-router";
import { api, post, mediaUrl, notify, session } from "../api";
import { categories } from "../design";
import PageHeader from "../components/PageHeader.vue";
import SectionCard from "../components/SectionCard.vue";
const router = useRouter(),
  title = ref(""),
  content = ref(""),
  category = ref("SHADOW_PUPPET"),
  gallery = ref<string[]>([]),
  busy = ref(false),
  error = ref("");
const cover = computed(() => gallery.value[0] || "");
const specifications = ref([
  { label: "尺寸规格", value: "" },
  { label: "材质工艺", value: "" },
  { label: "创作年代", value: "" },
  { label: "艺术流派", value: "" },
]);
const appreciation = ref<Array<{ title: string; body: string }>>([]);
const uploading = ref(false), uploaded = ref(0), uploadTotal = ref(0);
let alive = true, version = 0, submitted = false;
let controller: AbortController | undefined;
const dirty = computed(() => !!(title.value || content.value || gallery.value.length ||
  specifications.value.some((spec) => spec.value) || appreciation.value.length));
function context() {
  const request = ++version, token = session.token;
  return () => alive && request === version && token === session.token;
}
watch(() => session.token, () => {
  ++version; controller?.abort();
  title.value = ""; content.value = ""; gallery.value = [];
  specifications.value.forEach((spec) => { spec.value = ""; });
  appreciation.value = []; error.value = ""; busy.value = false; uploading.value = false;
});
onUnmounted(() => { alive = false; ++version; controller?.abort(); });
onBeforeRouteLeave(() => !session.token || submitted || !dirty.value ||
  window.confirm("作品还未提交，确定离开吗？留在此页可以继续编辑。"));
async function upload(event: Event) {
  const input = event.target as HTMLInputElement;
  const files = [...(input.files || [])];
  if (!files.length || busy.value) return;
  if (files.length + gallery.value.length > 10) {
    error.value = "图集最多10张，请减少图片后重试";
    input.value = "";
    return;
  }
  if (files.some((file) => file.size > 20 * 1024 * 1024)) {
    error.value = "请选择20MB以内的图片";
    input.value = "";
    return;
  }
  if (files.some((file) => file.type ? !["image/png", "image/jpeg", "image/webp"].includes(file.type) : !/\.(png|jpe?g|webp)$/i.test(file.name))) {
    error.value = "请选择 PNG、JPEG 或 WebP 图片";
    input.value = "";
    return;
  }
  const current = context();
  controller = new AbortController();
  uploading.value = true; uploaded.value = 0; uploadTotal.value = files.length;
  busy.value = true;
  error.value = "";
  try {
    for (const file of files) {
      const data = new FormData();
      data.append("file", file);
      const result = await api("/ai/assets/upload", {
        method: "POST",
        body: data,
        signal: controller.signal,
      });
      if (!current()) return;
      gallery.value.push(result.file_url || result.url);
      uploaded.value++;
    }
  } catch (e) {
    if (current()) error.value = (e as Error).message;
  } finally {
    if (current()) { busy.value = false; uploading.value = false; }
    input.value = "";
  }
}
async function publish() {
  if (busy.value) return;
  if (!title.value.trim() || !content.value.trim()) {
    error.value = "请填写作品名称和创作故事";
    return;
  }
  if (!cover.value) {
    error.value = "请先上传作品图片";
    return;
  }
  if (
    appreciation.value.some(
      (point) => !point.title.trim() || !point.body.trim(),
    )
  ) {
    error.value = "请填写鉴赏要点的标题与内容，或移除未完成的要点";
    return;
  }
  const current = context();
  busy.value = true;
  error.value = "";
  try {
    const result = await post("/community/posts", {
      title: title.value,
      content: content.value,
      category: category.value,
      cover_url: cover.value,
      gallery: gallery.value,
      specifications: specifications.value.filter((spec) => spec.value.trim()),
      appreciation: appreciation.value,
    });
    if (!current()) return;
    submitted = true;
    notify(
      result.status === "APPROVED" ? "作品发布成功" : "作品已提交，等待审核",
    );
    await router.replace(
      result.status === "APPROVED" ? "/community/" + result.id : "/me/posts",
    );
  } catch (e) {
    if (current()) error.value = (e as Error).message;
  } finally {
    if (current()) busy.value = false;
  }
}
</script>
<template>
  <div class="publish-page">
    <PageHeader title="发布作品" />
    <form class="publish-body" :aria-busy="busy" @submit.prevent="publish">
      <SectionCard>
        <label class="upload-field"
          >作品图片<input
            type="file"
            multiple
            accept="image/png,image/jpeg,image/webp"
            :disabled="busy"
            @change="upload"
        /></label>
        <p class="subtle upload-hint">
          最多 10 张，每张不超过 20MB。第一张作为封面，上传后可调整。
        </p>
        <p v-if="uploading" class="upload-progress" role="status">
          正在上传 {{ uploaded + 1 }} / {{ uploadTotal }} 张，请稍候…
        </p>
        <div v-if="gallery.length" class="publish-gallery">
          <article v-for="(image, index) in gallery" :key="image">
            <img :src="mediaUrl(image)" :alt="'作品图片' + (index + 1)" /><span
              v-if="index === 0"
              class="cover-tag"
              >封面</span
            >
            <button
              v-else
              type="button"
              class="text-button"
              :disabled="busy"
              @click="
                gallery = [image, ...gallery.filter((url) => url !== image)]
              "
            >
              设为封面
            </button>
            <button
              type="button"
              class="text-button"
              :disabled="busy"
              @click="gallery.splice(index, 1)"
            >
              移除
            </button>
          </article>
        </div>
      </SectionCard>
      <SectionCard>
        <div class="publish-fields">
          <label
            >作品名称<input
              v-model.trim="title"
              :disabled="busy"
              required
              maxlength="128"
              placeholder="为你的作品起一个名字" /></label
          ><label
            >非遗分类<select v-model="category" :disabled="busy">
              <option
                v-for="item in categories.filter((c) => c.value)"
                :key="item.value"
                :value="item.value"
              >
                {{ item.label }}
              </option>
            </select></label
          ><label
            >创作故事<textarea
              v-model.trim="content"
              :disabled="busy"
              required
              maxlength="5000"
              placeholder="介绍灵感、制作过程与非遗文化内涵"
            />
          </label>
        </div>
      </SectionCard>
      <fieldset class="artwork-spec-fields corner-card">
        <legend>作品规格（选填）</legend>
        <div class="publish-fields">
          <label v-for="spec in specifications" :key="spec.label"
            >{{ spec.label }}<input
              v-model.trim="spec.value"
              :disabled="busy"
              maxlength="128"
          /></label>
        </div>
      </fieldset>
      <fieldset class="appreciation-fields corner-card">
        <legend>鉴赏要点（选填）</legend>
        <article v-for="(point, index) in appreciation" :key="index">
          <label
            >要点标题<input
              v-model.trim="point.title"
              :disabled="busy"
              maxlength="64" /></label
          ><label
            >要点内容<textarea
              v-model.trim="point.body"
              :disabled="busy"
              maxlength="2000"
            /></label
          ><button
            type="button"
            class="text-button remove-point"
            :disabled="busy"
            @click="appreciation.splice(index, 1)"
          >
            移除要点
          </button>
        </article>
        <button
          v-if="appreciation.length < 10"
          type="button"
          class="outline-button add-point"
          :disabled="busy"
          @click="appreciation.push({ title: '', body: '' })"
        >
          添加鉴赏要点
        </button>
      </fieldset>
      <p v-if="error" class="form-error" role="alert">{{ error }}</p>
      <button class="primary-button publish-submit" :disabled="busy">
        {{ uploading ? "图片上传中…" : busy ? "正在提交…" : "提交作品审核" }}
      </button>
    </form>
  </div>
</template>
<style scoped>
.publish-page {
  min-height: 100dvh;
  padding-bottom: 12px;
  background: #f5ede4;
  color: #2d1810;
}
.publish-body {
  gap: 0;
  padding: 14px 16px 24px;
}
.publish-body label {
  gap: 6px;
  color: #8a7a70;
  font: 400 11px/1.4 var(--sans);
  letter-spacing: 1px;
}
.publish-body input:not([type="file"]),
.publish-body select,
.publish-body textarea {
  min-height: 42px;
  padding: 10px 12px;
  border: 1px solid rgba(200, 169, 110, 0.45);
  border-radius: 10px;
  background: #fffdf8;
  color: #2d1810;
  font: 400 14px/1.6 var(--sans);
  letter-spacing: 0;
}
.publish-body textarea {
  min-height: 108px;
  resize: vertical;
}
.publish-body .upload-field {
  gap: 8px;
  color: #5a3e36;
  font: 500 13px/1.4 var(--sans);
  letter-spacing: 0.5px;
}
.upload-field input[type="file"] {
  min-height: 46px;
  padding: 9px 10px;
  border: 1px dashed rgba(200, 169, 110, 0.55);
  border-radius: 10px;
  background: #fffdf8;
  color: #8a7a70;
  font: 400 11px/1.5 var(--sans);
  letter-spacing: 0;
}
.upload-field input[type="file"]::file-selector-button {
  margin-right: 10px;
  padding: 6px 12px;
  border: 1px solid rgba(139, 26, 26, 0.22);
  border-radius: 999px;
  background: rgba(139, 26, 26, 0.06);
  color: #8b1a1a;
  font: 500 11px/1.4 var(--sans);
  letter-spacing: 0.5px;
}
.upload-hint {
  margin-top: 8px;
  color: #8a7a70;
  font: 400 10px/1.7 var(--sans);
}
.upload-progress {
  margin-top: 8px;
  color: #8b1a1a;
  font: 400 11px/1.6 var(--sans);
}
.publish-gallery {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 12px;
}
.publish-gallery article {
  position: relative;
  padding: 6px;
  border: 1px solid rgba(200, 169, 110, 0.28);
  border-radius: 10px;
  background: #fffdf8;
}
.publish-gallery img {
  width: 100%;
  height: 132px;
  border-radius: 8px;
  object-fit: cover;
  background: #f0e3d6;
}
.cover-tag {
  display: inline-block;
  margin-top: 6px;
  padding: 2px 8px;
  border-radius: 4px;
  background: #8b1a1a;
  color: #f6ead9;
  font: 400 10px/1.5 var(--sans);
  letter-spacing: 1px;
}
.publish-gallery .text-button {
  display: inline-block;
  margin-top: 4px;
  margin-right: 10px;
  padding: 2px 0;
  color: #8a6125;
  font: 400 10px/1.5 var(--sans);
  letter-spacing: 0.5px;
}
.publish-fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.artwork-spec-fields,
.appreciation-fields {
  margin: 0 0 14px;
  padding: 16px 14px;
  border: 0;
}
.artwork-spec-fields legend,
.appreciation-fields legend {
  position: relative;
  margin-bottom: 14px;
  padding: 0 0 0 11px;
  color: #2d1810;
  font: 500 16px/1.4 var(--serif);
  letter-spacing: 1.6px;
}
.artwork-spec-fields legend::before,
.appreciation-fields legend::before {
  content: "";
  position: absolute;
  left: 0;
  top: 3px;
  width: 3px;
  height: 15px;
  border-radius: 2px;
  background: #8b1a1a;
}
.appreciation-fields article {
  margin-bottom: 10px;
  padding: 12px;
  border: 1px dashed rgba(200, 169, 110, 0.4);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.45);
}
.appreciation-fields .remove-point {
  display: inline-block;
  margin-top: 8px;
  padding: 4px 0;
  color: #8b1a1a;
  font: 400 10px/1.5 var(--sans);
}
.add-point {
  width: 100%;
  min-height: 38px;
  border: 1px dashed rgba(139, 26, 26, 0.3);
  border-radius: 10px;
  background: rgba(139, 26, 26, 0.04);
  color: #8b1a1a;
  font: 500 12px/1.4 var(--sans);
  letter-spacing: 1px;
}
.form-error {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-left: 2px solid #8b1a1a;
  border-radius: 0 8px 8px 0;
  background: #fff0f0;
  color: #8b1a1a;
  font: 400 12px/1.7 var(--sans);
}
.publish-submit {
  width: 100%;
  min-height: 46px;
  border: 1px solid rgba(232, 217, 168, 0.55);
  border-radius: 10px;
  background: #8b1a1a;
  color: #f6ead9;
  font: 500 14px/1.4 var(--sans);
  letter-spacing: 3px;
  box-shadow: 0 8px 20px rgba(139, 26, 26, 0.18);
}
</style>

