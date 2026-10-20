<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import { designImage } from "../design";
import AsyncState from "../components/AsyncState.vue";
import PageHeader from "../components/PageHeader.vue";
import SectionCard from "../components/SectionCard.vue";
import SkeletonImage from "../components/SkeletonImage.vue";
const router = useRouter();
const keyword = ref(""),
  entries = ref<any[]>([]),
  stats = ref<{ heritage_projects: number; teaching_resources: number } | null>(
    null,
  ),
  loading = ref(false),
  error = ref("");
let searchVersion = 0;
async function search(value?: string) {
  if (value !== undefined) keyword.value = value;
  const version = ++searchVersion;
  loading.value = true;
  error.value = "";
  try {
    const result = await api(
      "/mobile/heritage?keyword=" + encodeURIComponent(keyword.value),
    );
    if (version !== searchVersion) return;
    entries.value = result.list;
    stats.value = result.stats || null;
  } catch (e) {
    if (version === searchVersion) error.value = (e as Error).message;
  } finally {
    if (version === searchVersion) loading.value = false;
  }
}
async function quickSearch() {
  await search();
  explore();
}
function explore() {
  document
    .getElementById("heritage-results")
    ?.scrollIntoView({ block: "start", behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? "instant" : "smooth" });
}
function back() {
  window.history.state?.back ? router.back() : router.replace("/");
}
onMounted(() => search());
</script>
<template>
  <div class="heritage-page" data-design-node="40:32437">
    <PageHeader title="非遗百科" subtitle="天津非物质文化遗产" />
    <div class="heritage-body">
      <form class="heritage-quick-search" @submit.prevent="quickSearch">
        <label class="sr-only" for="heritage-quick-input"
          >搜索文物与非遗资源</label
        ><input
          id="heritage-quick-input"
          v-model="keyword"
          placeholder="搜索文物、教案、皮影戏..."
          maxlength="100"
        /><button>搜索</button>
      </form>
      <section
        class="heritage-hero corner-card"
        :style="{
          backgroundImage:
            'linear-gradient(90deg,rgba(245,240,232,.94) 0%,rgba(245,240,232,.72) 52%,rgba(245,240,232,.28) 100%),url(' +
            designImage('layer-40-32437', '5:01455') +
            ')',
        }"
      >
        <p class="eyebrow">TIANJIN HERITAGE</p>
        <h1>津门遗韵<br /><em>美育传承</em></h1>
        <p class="heritage-hero-desc">
          图文探索天津非物质文化遗产，从青铜器纹样到皮影戏光影，<br />让传统美学融入现代教育，传承津门文化根脉。
        </p>
        <div class="heritage-hero-actions">
          <button class="primary-button" type="button" @click="explore">
            开始探索</button
          ><RouterLink class="text-button" to="/teacher/lesson-plan"
            >浏览教案</RouterLink
          >
        </div>
        <div class="heritage-stats" aria-label="平台资源统计">
          <div class="heritage-stat">
            <strong
              >{{ stats ? stats.heritage_projects : "—"
              }}<span v-if="stats">+</span></strong
            ><small>非遗项目</small>
          </div>
          <i aria-hidden="true" />
          <div class="heritage-stat">
            <strong
              >{{ stats ? stats.teaching_resources : "—"
              }}<span v-if="stats">+</span></strong
            ><small>教学资源</small>
          </div>
        </div>
      </section>
      <SectionCard title="资源检索">
        <p class="card-lede">快速定位您需要的非遗教学资源</p>
        <div class="hot-searches">
          <span>热门搜索：</span
          ><button
            v-for="text in [
              '杨柳青年画',
              '泥人张',
              '风筝魏',
              '评剧',
              '京东大鼓',
              '天津时调',
            ]"
            :key="text"
            @click="search(text)"
          >
            {{ text }}
          </button>
        </div>
      </SectionCard>
      <SectionCard id="heritage-results" title="文物图文浏览">
        <p class="card-lede">探索天津非遗瑰宝，感受千年文化脉动</p>
        <AsyncState
          :loading="loading"
          :error="error"
          :empty="!entries.length"
          empty-text="没有找到相关内容，试试其他关键词"
          @retry="search()"
          ><div class="heritage-grid">
            <RouterLink
              v-for="entry in entries"
              :key="entry.id"
              :to="'/heritage/' + entry.id"
              class="heritage-card corner-card"
              ><SkeletonImage
                :src="entry.cover_url"
                :alt="entry.title"
                class="heritage-cover"
              />
              <div class="heritage-card-body">
                <p class="eyebrow">{{ entry.era }}</p>
                <h3>{{ entry.title }}</h3>
                <p class="heritage-summary">{{ entry.summary }}</p>
                <span class="heritage-more">查看图文详情 ›</span>
              </div></RouterLink
            >
          </div></AsyncState
        >
      </SectionCard>
    </div>
  </div>
</template>
<style scoped>
.heritage-page {
  min-height: 100dvh;
  padding-bottom: 12px;
  background: #f5ede4;
  color: #2d1810;
}
.heritage-body {
  padding: 14px 16px 24px;
}
.heritage-quick-search {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 6px;
  height: 40px;
  margin-bottom: 14px;
  padding: 0 4px 0 14px;
  border: 1px solid rgba(200, 169, 110, 0.42);
  border-radius: 999px;
  background: rgba(255, 253, 248, 0.9);
  box-shadow: 0 4px 14px rgba(70, 42, 26, 0.05);
}
.heritage-quick-search input {
  flex: 1;
  width: 0;
  min-width: 0;
  height: 30px;
  min-height: 30px;
  padding: 0;
  border: 0;
  background: transparent;
  box-shadow: none;
  font: 400 12px/1.4 var(--sans);
}
.heritage-quick-search button {
  flex: 0 0 auto;
  height: 30px;
  min-height: 30px;
  padding: 0 14px;
  border-radius: 999px;
  background: #8b1a1a;
  color: #f6ead9;
  font: 500 11px/1 var(--sans);
  letter-spacing: 1px;
}
.heritage-hero {
  margin-bottom: 14px;
  padding: 20px 16px 16px;
  border-radius: 14px;
  background-color: #f7efe3;
  background-size: cover;
  background-position: center top;
}
.heritage-hero .eyebrow {
  color: #8a6125;
  letter-spacing: 2.4px;
}
.heritage-hero h1 {
  margin: 8px 0 0;
  font: 500 22px/1.4 var(--serif);
  letter-spacing: 3px;
  color: #2d1810;
}
.heritage-hero em {
  font-style: normal;
  color: #8b1a1a;
}
.heritage-hero-desc {
  margin-top: 8px;
  color: #8a7a70;
  font: 400 12px/1.9 var(--sans);
}
.heritage-hero-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
}
.heritage-hero-actions .primary-button {
  width: 132px;
  min-height: 40px;
  padding: 0 16px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: #8b1a1a;
  color: #f6ead9;
  font-size: 12px;
  letter-spacing: 1px;
}
.heritage-hero-actions .text-button {
  padding: 8px 6px;
  color: #8b1a1a;
  font-size: 12px;
}
.heritage-stats {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(200, 169, 110, 0.3);
}
.heritage-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.heritage-stat strong {
  display: flex;
  align-items: flex-start;
  color: #8b1a1a;
  font: 500 20px/1.2 var(--serif);
}
.heritage-stat strong span {
  margin-left: 1px;
  color: #8a6125;
  font-size: 12px;
  line-height: 1.6;
}
.heritage-stat small {
  color: #8a7a70;
  font: 400 10px/1.5 var(--sans);
  letter-spacing: 1px;
}
.heritage-stats > i {
  width: 1px;
  height: 28px;
  background: rgba(200, 169, 110, 0.4);
}
.card-lede {
  margin: -4px 0 12px;
  color: #8a7a70;
  font: 400 11px/1.7 var(--sans);
}
.heritage-search-form {
  flex-direction: row;
  align-items: center;
  gap: 8px;
}
.heritage-search-form input {
  flex: 1;
  width: 0;
  min-width: 0;
  min-height: 42px;
  padding: 10px 12px;
  border-color: rgba(200, 169, 110, 0.42);
  border-radius: 10px;
  background: #fffdf8;
  font-size: 12px;
}
.heritage-search-form .primary-button {
  flex: 0 0 auto;
  width: 76px;
  min-height: 42px;
  padding: 0 12px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: #8b1a1a;
  color: #f6ead9;
  font-size: 12px;
  letter-spacing: 1px;
}
.hot-searches {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
}
.hot-searches > span {
  color: #8a7a70;
  font: 400 10px/1.5 var(--sans);
}
.hot-searches button {
  padding: 4px 10px;
  border: 1px solid rgba(200, 169, 110, 0.42);
  border-radius: 999px;
  background: #fffdf8;
  color: #5a3e36;
  font: 400 11px/1.4 var(--sans);
}
.hot-searches button:active {
  border-color: rgba(139, 26, 26, 0.26);
  background: rgba(139, 26, 26, 0.06);
  color: #8b1a1a;
}
.heritage-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.heritage-card {
  display: block;
  content-visibility: auto;
  contain-intrinsic-size: auto 300px;
  border: 1px solid rgba(200, 169, 110, 0.3);
  border-radius: 14px;
  background: #fffdf8;
}
.heritage-card > .heritage-cover {
  height: 156px;
  border-radius: 14px 14px 0 0;
}
.heritage-card-body {
  padding: 12px;
}
.heritage-card-body .eyebrow {
  color: #8a6125;
}
.heritage-card h3 {
  margin: 4px 0 6px;
  color: #2d1810;
  font: 500 15px/1.45 var(--serif);
  letter-spacing: 1px;
}
.heritage-summary {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  color: #8a7a70;
  font: 400 12px/1.8 var(--sans);
}
.heritage-more {
  display: block;
  margin-top: 8px;
  color: #8b1a1a;
  font: 400 11px/1.5 var(--sans);
  letter-spacing: 0.5px;
}
.heritage-page :deep(.async-state) {
  padding: 6px 2px 2px;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
}
</style>
