<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { api, post, mediaUrl, notify } from "../api";
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
    return;
  }
  busy.value = true;
  error.value = "";
  try {
    for (const file of files) {
      const data = new FormData();
      data.append("file", file);
      const result = await api("/ai/assets/upload", {
        method: "POST",
        body: data,
      });
      gallery.value.push(result.file_url || result.url);
    }
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    busy.value = false;
    input.value = "";
  }
}
async function publish() {
  if (busy.value) return;
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
    notify(
      result.status === "APPROVED" ? "作品发布成功" : "作品已提交，等待审核",
    );
    router.replace(
      result.status === "APPROVED" ? "/community/" + result.id : "/me/posts",
    );
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    busy.value = false;
  }
}
</script>
<template>
  <div>
    <PageHeader title="发布作品" />
    <form class="page-padding" @submit.prevent="publish">
      <label
        >作品图片<input
          type="file"
          multiple
          accept="image/png,image/jpeg,image/webp"
          :disabled="busy"
          @change="upload"
      /></label>
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
        >作品名称<input v-model.trim="title" required maxlength="128" /></label
      ><label
        >非遗分类<select v-model="category">
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
          required
          maxlength="5000"
          placeholder="介绍灵感、制作过程与非遗文化内涵"
        />
      </label>
      <fieldset class="artwork-spec-fields">
        <legend>作品规格（选填）</legend>
        <label v-for="spec in specifications" :key="spec.label"
          >{{ spec.label }}<input v-model.trim="spec.value" maxlength="128"
        /></label>
      </fieldset>
      <fieldset class="appreciation-fields">
        <legend>鉴赏要点（选填）</legend>
        <article v-for="(point, index) in appreciation" :key="index">
          <label
            >要点标题<input v-model.trim="point.title" maxlength="64" /></label
          ><label
            >要点内容<textarea
              v-model.trim="point.body"
              maxlength="2000"
            /></label
          ><button
            type="button"
            class="text-button"
            @click="appreciation.splice(index, 1)"
          >
            移除要点
          </button>
        </article>
        <button
          v-if="appreciation.length < 10"
          type="button"
          class="outline-button"
          @click="appreciation.push({ title: '', body: '' })"
        >
          添加鉴赏要点
        </button>
      </fieldset>
      <p v-if="error" class="form-error" role="alert">{{ error }}</p>
      <button class="primary-button" :disabled="busy">
        {{ busy ? "处理中…" : "发布作品" }}
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
