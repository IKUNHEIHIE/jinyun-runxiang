<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from "vue";
import { api, mediaUrl, requireSession, session } from "../api";
import { categories } from "../design";
import AsyncState from "../components/AsyncState.vue";
import { useRoute, useRouter } from "vue-router";
const router = useRouter(), route = useRoute(),
  posts = ref<any[]>([]),
  loading = ref(true),
  error = ref("");
const category = computed(() => categories.some((c) => c.value === route.query.category) ? String(route.query.category) : "");
const sort = computed(() => ["hot", "featured"].includes(String(route.query.sort)) ? String(route.query.sort) : "latest");
let version = 0;
let controller: AbortController | undefined;
function setFilters(nextCategory: string, nextSort = sort.value) {
  router.replace({ query: { ...route.query, category: nextCategory || undefined, sort: nextSort === "latest" ? undefined : nextSort } });
}
async function load() {
  const request = ++version;
  const token = session.token;
  const current = () => request === version && token === session.token;
  controller?.abort();
  controller = new AbortController();
  loading.value = true;
  error.value = "";
  try {
    const q = new URLSearchParams({ sort: sort.value, pageSize: "50" });
    if (category.value) q.set("category", category.value);
    const result = await api("/community/posts?" + q, { signal: controller.signal });
    if (current()) posts.value = result.list;
  } catch (e) {
    if (current()) error.value = (e as Error).message;
  } finally {
    if (current()) loading.value = false;
  }
}
function publish() {
  if (requireSession("/community/publish")) router.push("/community/publish");
}
watch([category, sort, () => session.token], load, { immediate: true });
onUnmounted(() => { ++version; controller?.abort(); });
</script>
<template>
  <div class="community-page">
    <header class="community-header">
      <p class="eyebrow">传承匠心 · 分享创意</p>
      <h1>作品广场</h1>
      <p class="subtle">在这里，遇见非遗创作的每一种可能</p>
      <button class="outline-button" @click="publish">发布作品 ＋</button>
    </header>
    <div class="category-tabs" role="group" aria-label="作品分类">
      <button
        v-for="c in categories"
        :key="c.value"
        :class="{ active: category === c.value }"
        :aria-pressed="category === c.value"
        @click="setFilters(c.value)"
      >
        {{ c.label }}
      </button>
    </div>
    <div class="community-sort" role="group" aria-label="作品排序">
      <button
        v-for="s in [
          { label: '最新', value: 'latest' },
          { label: '热门', value: 'hot' },
          { label: '精选', value: 'featured' },
        ]"
        :key="s.value"
        :class="{ active: sort === s.value }"
        :aria-pressed="sort === s.value"
        @click="setFilters(category, s.value)"
      >
        {{ s.label }}
      </button>
    </div>
    <AsyncState
      :loading="loading"
      :error="error"
      :empty="!posts.length"
      :empty-text="category ? '这个分类还没有作品，来分享你的非遗创作吧' : '还没有作品，分享你的第一件非遗创作吧'"
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
  aspect-ratio: 4 / 5;
  object-fit: cover;
}
.artwork-card > div {
  padding: 12px;
}
.artwork-card h2 {
  font-size: 13px;
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  overflow-wrap: anywhere;
}
.artwork-card p {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 10px;
  color: var(--muted);
  margin-top: 10px;
}
.artwork-card p > span:first-child {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.artwork-card p > span:last-child { flex-shrink: 0; font-variant-numeric: tabular-nums; }
</style>
