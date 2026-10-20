<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from "vue";
import { api, requireSession, session } from "../api";
import { categories } from "../design";
import AsyncState from "../components/AsyncState.vue";
import PageHeader from "../components/PageHeader.vue";
import PagerBar from "../components/PagerBar.vue";
import PullToRefresh from "../components/PullToRefresh.vue";
import SkeletonImage from "../components/SkeletonImage.vue";
import { useRoute, useRouter } from "vue-router";
const router = useRouter(), route = useRoute(),
  posts = ref<any[]>([]),
  loading = ref(true),
  error = ref("");
const PAGE_SIZE = 20;
const page = ref(1),
  total = ref(0);
const category = computed(() => categories.some((c) => c.value === route.query.category) ? String(route.query.category) : "");
const sort = computed(() => ["hot", "featured"].includes(String(route.query.sort)) ? String(route.query.sort) : "latest");
let version = 0;
let controller: AbortController | undefined;
function setFilters(nextCategory: string, nextSort = sort.value) {
  router.replace({ query: { ...route.query, category: nextCategory || undefined, sort: nextSort === "latest" ? undefined : nextSort } });
}
async function load(target = 1) {
  const request = ++version;
  const token = session.token;
  const current = () => request === version && token === session.token;
  controller?.abort();
  controller = new AbortController();
  loading.value = true;
  error.value = "";
  try {
    const q = new URLSearchParams({
      sort: sort.value,
      pageSize: String(PAGE_SIZE),
      page: String(target),
    });
    if (category.value) q.set("category", category.value);
    const result = await api("/community/posts?" + q, { signal: controller.signal });
    if (current()) {
      posts.value = result.list;
      total.value = result.total;
      page.value = target;
    }
  } catch (e) {
    if (current()) error.value = (e as Error).message;
  } finally {
    if (current()) loading.value = false;
  }
}
function changePage(next: number) {
  if (next === page.value) return;
  void load(next).then(() => window.scrollTo({ top: 0, behavior: "smooth" }));
}
const refresh = () => load(page.value);
function publish() {
  if (requireSession("/community/publish")) router.push("/community/publish");
}
watch([category, sort, () => session.token], () => load(1), { immediate: true });
onUnmounted(() => { ++version; controller?.abort(); });
</script>
<template>
  <div class="community-page">
    <PullToRefresh :on-refresh="refresh" />
    <PageHeader title="作品广场" subtitle="传承匠心 · 分享创意" :back="false">
      <button class="publish-action" @click="publish">发布作品 ＋</button>
    </PageHeader>
    <div class="page-padding">
      <p class="community-lead">在这里，遇见非遗创作的每一种可能</p>
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
        @retry="load(page)"
        ><div class="artwork-grid">
          <RouterLink
            v-for="post in posts"
            :key="post.id"
            :to="'/community/' + post.id"
            class="artwork-card corner-card"
            ><div class="artwork-cover">
              <SkeletonImage
                :src="post.cover_url"
                :alt="post.title"
                ratio="4 / 5"
              />
            </div>
            <div class="artwork-copy">
              <h2>{{ post.title }}</h2>
              <p>
                <span class="artwork-author">{{ post.author.nickname }}</span
                ><span class="artwork-likes">♡ {{ post.like_count }}</span>
              </p>
            </div></RouterLink
          >
        </div></AsyncState
      >
      <PagerBar
        :page="page"
        :total="total"
        :page-size="PAGE_SIZE"
        unit="件"
        @change="changePage"
      />
    </div>
  </div>
</template>
<style scoped>
.community-page {
  min-height: 100dvh;
  background: #f5ede4;
  color: #2d1810;
}
.page-padding {
  padding: 14px 16px 24px;
}
.publish-action {
  flex-shrink: 0;
  height: 30px;
  padding: 0 14px;
  border: 1px solid rgba(139, 26, 26, 0.28);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  color: #8b1a1a;
  font: 500 11px/1 var(--sans);
  letter-spacing: 1px;
  white-space: nowrap;
}
.publish-action:active {
  background: rgba(139, 26, 26, 0.08);
}
.community-lead {
  margin: 0 0 12px;
  font: 400 11px/1.6 var(--sans);
  letter-spacing: 1.2px;
  color: #8a7a70;
  text-align: center;
}
.category-tabs {
  display: flex;
  gap: 8px;
  margin: 0 -16px;
  padding: 0 16px 2px;
  overflow-x: auto;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
}
.category-tabs::-webkit-scrollbar {
  display: none;
}
.category-tabs button {
  flex: none;
  height: 30px;
  padding: 0 14px;
  border: 1px solid rgba(200, 169, 110, 0.42);
  border-radius: 999px;
  background: #fffdf8;
  color: #5a3e36;
  font: 400 12px/1 var(--sans);
  white-space: nowrap;
}
.category-tabs button.active {
  border-color: transparent;
  background: #8b1a1a;
  color: #f6ead9;
  font-weight: 500;
}
.community-sort {
  display: flex;
  gap: 20px;
  margin: 12px 0 14px;
  border-bottom: 1px solid rgba(200, 169, 110, 0.32);
}
.community-sort button {
  padding: 6px 0 8px;
  border-bottom: 2px solid transparent;
  font: 400 12px/1.2 var(--sans);
  letter-spacing: 1.2px;
  color: #8a7a70;
}
.community-sort button.active {
  border-bottom-color: #8b1a1a;
  color: #8b1a1a;
  font-weight: 500;
}
.artwork-grid {
  columns: 2;
  column-gap: 14px;
}
.artwork-card {
  display: block;
  break-inside: avoid;
  margin-bottom: 14px;
  content-visibility: auto;
  contain-intrinsic-size: auto 320px;
}
.artwork-cover {
  border-radius: 14px 14px 0 0;
  overflow: hidden;
  background: #f2e5cf;
}
.artwork-copy {
  padding: 9px 12px 12px;
}
.artwork-card h2 {
  margin: 0;
  font: 500 13px/1.55 var(--sans);
  letter-spacing: 0.4px;
  color: #2d1810;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  overflow-wrap: anywhere;
}
.artwork-card p {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin: 8px 0 0;
  font: 400 10px/1.4 var(--sans);
  color: #8a7a70;
}
.artwork-author {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.artwork-likes {
  flex-shrink: 0;
  color: #8b1a1a;
  font-variant-numeric: tabular-nums;
}

</style>
