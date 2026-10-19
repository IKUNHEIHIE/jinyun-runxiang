<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from "vue";
import { useRouter, onBeforeRouteLeave } from "vue-router";
import { api, post, mediaUrl, notify, session } from "../api";
import { categories } from "../design";
import PageHeader from "../components/PageHeader.vue";
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
  <div>
    <PageHeader title="发布作品" />
    <form class="page-padding" :aria-busy="busy" @submit.prevent="publish">
      <label
        >作品图片<input
          type="file"
          multiple
          accept="image/png,image/jpeg,image/webp"
          :disabled="busy"
          @change="upload"
      /></label>
      <p class="subtle">最多 10 张，每张不超过 20MB。第一张作为封面，上传后可调整。</p>
      <p v-if="uploading" class="upload-progress" role="status">正在上传 {{ uploaded + 1 }} / {{ uploadTotal }} 张，请稍候…</p>
      <div v-if="gallery.length" class="publish-gallery">
        <article v-for="(image, index) in gallery" :key="image">
          <img :src="mediaUrl(image)" :alt="'作品图片' + (index + 1)" /><span
            v-if="index === 0"
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
      <label
        >作品名称<input v-model.trim="title" :disabled="busy" required maxlength="128" placeholder="为你的作品起一个名字" /></label
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
      <fieldset class="artwork-spec-fields">
        <legend>作品规格（选填）</legend>
        <label v-for="spec in specifications" :key="spec.label"
          >{{ spec.label }}<input v-model.trim="spec.value" :disabled="busy" maxlength="128"
        /></label>
      </fieldset>
      <fieldset class="appreciation-fields">
        <legend>鉴赏要点（选填）</legend>
        <article v-for="(point, index) in appreciation" :key="index">
          <label
            >要点标题<input v-model.trim="point.title" :disabled="busy" maxlength="64" /></label
          ><label
            >要点内容<textarea
              v-model.trim="point.body"
              :disabled="busy"
              maxlength="2000"
            /></label
          ><button
            type="button"
            class="text-button"
            :disabled="busy"
            @click="appreciation.splice(index, 1)"
          >
            移除要点
          </button>
        </article>
        <button
          v-if="appreciation.length < 10"
          type="button"
          class="outline-button"
          :disabled="busy"
          @click="appreciation.push({ title: '', body: '' })"
        >
          添加鉴赏要点
        </button>
      </fieldset>
      <p v-if="error" class="form-error" role="alert">{{ error }}</p>
      <button class="primary-button" :disabled="busy">
        {{ uploading ? "图片上传中…" : busy ? "正在提交…" : "提交作品审核" }}
      </button>
    </form>
  </div>
</template>
<style scoped>
.publish-gallery {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin: 18px 0;
}
.publish-gallery article {
  border: 1px solid var(--gold-light);
  padding: 8px;
  border-radius: 12px;
}
.publish-gallery img {
  width: 100%;
  height: 150px;
  object-fit: contain;
  background: var(--track);
}
.publish-gallery span,
.publish-gallery button {
  font-size: 11px;
  margin-right: 8px;
}
.artwork-spec-fields,
.appreciation-fields {
  border: 1px solid var(--gold-light);
  border-radius: 12px;
  padding: 16px;
  margin: 24px 0;
}
.artwork-spec-fields legend,
.appreciation-fields legend {
  font: 15px var(--serif);
  padding: 0 8px;
}
.appreciation-fields article {
  padding-bottom: 16px;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--gold-light);
}
</style>
