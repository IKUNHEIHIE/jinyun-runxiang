<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api, mediaUrl, requireSession } from "../api";
import { categories } from "../design";
import AsyncState from "../components/AsyncState.vue";
import { useRouter } from "vue-router";
const router = useRouter(),
  posts = ref<any[]>([]),
  loading = ref(true),
  error = ref(""),
  category = ref(""),
  sort = ref("latest");
async function load() {
  loading.value = true;
  error.value = "";
  try {
    const q = new URLSearchParams({ sort: sort.value, pageSize: "50" });
    if (category.value) q.set("category", category.value);
    posts.value = (await api("/community/posts?" + q)).list;
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
}
function publish() {
  if (requireSession()) router.push("/community/publish");
}
onMounted(load);
</script>
<template>
  <div class="community-page">
    <header class="community-header">
      <p class="eyebrow">传承匠心 · 分享创意</p>
      <h1>作品广场</h1>
      <p class="subtle">在这里，遇见非遗创作的每一种可能</p>
      <button class="outline-button" @click="publish">发布作品 ＋</button>
    </header>
    <div class="category-tabs">
      <button
        v-for="c in categories"
        :key="c.value"
        :class="{ active: category === c.value }"
        @click="
          category = c.value;
          load();
        "
      >
        {{ c.label }}
      </button>
    </div>
    <div class="community-sort">
      <button
        v-for="s in [
          { label: '最新', value: 'latest' },
          { label: '热门', value: 'hot' },
          { label: '精选', value: 'featured' },
        ]"
        :key="s.value"
        :class="{ active: sort === s.value }"
        @click="
          sort = s.value;
          load();
        "
      >
        {{ s.label }}
      </button>
    </div>
    <AsyncState
      :loading="loading"
      :error="error"
      :empty="!posts.length"
      empty-text="还没有作品，分享你的第一件非遗创作吧"
      @retry="load"
      ><div class="artwork-grid">
        <RouterLink
          v-for="post in posts"
          :key="post.id"
          :to="'/community/' + post.id"
          class="artwork-card corner-card"
          ><img
            :src="mediaUrl(post.cover_url)"
            :alt="post.title"
            loading="lazy"
          />
          <div>
            <h2>{{ post.title }}</h2>
            <p>
              <span>{{ post.author.nickname }}</span
              ><span>♡ {{ post.like_count }}</span>
            </p>
          </div></RouterLink
        >
      </div></AsyncState
    >
  </div>
</template>
<style scoped>
.community-page {
  padding: 0 20px 30px;
}
.community-header {
  text-align: center;
  padding: 30px 0 20px;
}
.community-header h1 {
  font-size: 27px;
  margin: 10px 0;
}
.community-header > .outline-button {
  margin: 20px auto 0;
  display: inline-flex;
}
.community-page > .category-tabs {
  margin: 0 -20px;
  padding-left: 20px;
  padding-right: 20px;
}
.community-sort {
  display: flex;
  gap: 22px;
  border-bottom: 1px solid var(--gold-light);
  margin-bottom: 20px;
}
.community-sort button {
  padding: 8px 0 12px;
  font-size: 12px;
  color: var(--muted);
}
.community-sort button.active {
  color: var(--cinnabar);
  border-bottom: 2px solid var(--cinnabar);
  font-weight: 600;
}
.artwork-grid {
  columns: 2;
  column-gap: 12px;
}
.artwork-card {
  display: block;
  break-inside: avoid;
  margin-bottom: 16px;
  overflow: hidden;
}
.artwork-card > img {
  width: 100%;
  min-height: 160px;
  max-height: 260px;
  object-fit: cover;
}
.artwork-card > div {
  padding: 12px;
}
.artwork-card h2 {
  font-size: 13px;
  line-height: 1.7;
}
.artwork-card p {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 10px;
  color: var(--muted);
  margin-top: 10px;
}
</style>
