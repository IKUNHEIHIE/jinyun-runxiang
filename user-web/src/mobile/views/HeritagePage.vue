<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { api, mediaUrl } from "../api";
import { designImage } from "../design";
import AsyncState from "../components/AsyncState.vue";
const router = useRouter();
const keyword = ref(""),
  entries = ref<any[]>([]),
  stats = ref<{ heritage_projects: number; teaching_resources: number } | null>(
    null,
  ),
  loading = ref(false),
  error = ref("");
async function search(value?: string) {
  if (value !== undefined) keyword.value = value;
  loading.value = true;
  error.value = "";
  try {
    const result = await api(
      "/mobile/heritage?keyword=" + encodeURIComponent(keyword.value),
    );
    entries.value = result.list;
    stats.value = result.stats || null;
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
}
async function quickSearch() {
  await search();
  document
    .getElementById("heritage-results")
    ?.scrollIntoView({ block: "start", behavior: "smooth" });
}
function back() {
  window.history.state?.back ? router.back() : router.replace("/");
}
onMounted(() => search());
</script>
<template>
  <div class="heritage-page" data-design-node="40:32437">
    <div class="heritage-top">
      <button class="heritage-back" aria-label="返回上一页" @click="back">
        ‹
      </button>
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
    </div>
    <section
      class="heritage-hero"
      :style="{
        backgroundImage:
          'linear-gradient(90deg,rgba(245,240,232,.94) 0%,rgba(245,240,232,.72) 52%,rgba(245,240,232,.28) 100%),url(' +
          designImage('layer-40-32437', '5:01455') +
          ')',
      }"
    >
      <p class="eyebrow">TIANJIN HERITAGE</p>
      <h1>津门遗韵<br /><em>美育传承</em></h1>
      <p class="subtle">
        沉浸式探索天津非物质文化遗产，从青铜器纹样到皮影戏光影，<br />让传统美学融入现代教育，传承津门文化根脉。
      </p>
      <a class="primary-button" href="#heritage-results">开始探索</a
      ><RouterLink class="text-button" to="/teacher/lesson-plan"
        >浏览教案</RouterLink
      >
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
    <div class="page-padding">
      <section class="heritage-search corner-card">
        <h2>资源检索</h2>
        <p class="subtle">快速定位您需要的非遗教学资源</p>
        <form @submit.prevent="search()">
          <label class="sr-only" for="heritage-search">搜索文物与非遗资源</label
          ><input
            id="heritage-search"
            v-model="keyword"
            placeholder="搜索文物、教案、皮影戏..."
            maxlength="100"
          /><button class="primary-button">搜索</button>
        </form>
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
      </section>
      <section id="heritage-results" class="heritage-results">
        <h2>沉浸式文物浏览</h2>
        <p class="subtle">探索天津非遗瑰宝，感受千年文化脉动</p>
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
              ><img
                :src="mediaUrl(entry.cover_url)"
                :alt="entry.title"
                loading="lazy"
              />
              <div>
                <p class="eyebrow">{{ entry.era }}</p>
                <h3>{{ entry.title }}</h3>
                <p class="subtle">{{ entry.summary }}</p>
                <span class="text-button">进入沉浸模式 ›</span>
              </div></RouterLink
            >
          </div></AsyncState
        >
      </section>
    </div>
  </div>
</template>
<style scoped>
.heritage-page {
  position: relative;
}
.heritage-top {
  position: absolute;
  top: calc(10px + var(--safe-top));
  left: 16px;
  right: 16px;
  z-index: 6;
  display: flex;
  align-items: center;
  gap: 10px;
}
.heritage-back {
  width: 38px;
  height: 38px;
  flex: 0 0 38px;
  padding: 0 0 3px;
  border-radius: 50%;
  border: 1px solid rgba(201, 168, 76, 0.4);
  background: rgba(250, 246, 238, 0.86);
  color: #6b5b45;
  font-size: 24px;
  line-height: 1;
  backdrop-filter: blur(6px);
}
.heritage-quick-search {
  flex: 1 1 0;
  width: 0;
  min-width: 0;
  height: 38px;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 6px;
  padding: 3px 4px 3px 14px;
  border-radius: 999px;
  border: 1px solid rgba(201, 168, 76, 0.4);
  background: rgba(250, 246, 238, 0.9);
  backdrop-filter: blur(6px);
  box-shadow: 0 4px 16px rgba(61, 35, 20, 0.06);
}
.heritage-quick-search input {
  flex: 1 1 0;
  width: 0;
  min-width: 0;
  height: 30px;
  min-height: 30px;
  padding: 0;
  border: 0;
  background: transparent;
  box-shadow: none;
  font-size: 12px;
}
.heritage-quick-search button {
  height: 28px;
  min-height: 28px;
  padding: 0 13px;
  border: 0;
  border-radius: 999px;
  background: #a0522d;
  color: #fffaf2;
  font-size: 11px;
  flex: 0 0 auto;
}
.heritage-hero {
  text-align: left;
  padding: 108px 24px 40px;
  min-height: 560px;
  position: relative;
  overflow: hidden;
  background-size: cover;
  background-position: center top;
}
.heritage-hero h1 {
  font-size: 44px;
  line-height: 1.3;
  margin: 14px 0;
  color: var(--clay);
}
.heritage-hero em {
  font-style: normal;
  color: var(--cinnabar);
}
.heritage-hero > .primary-button {
  width: 150px;
  display: inline-flex;
}
.heritage-hero > .text-button {
  display: inline-block;
  padding: 14px;
}
.heritage-stats {
  display: flex;
  align-items: center;
  gap: 32px;
  margin-top: 26px;
  padding-top: 32px;
}
.heritage-stat {
  display: flex;
  flex-direction: column;
}
.heritage-stat strong {
  display: flex;
  align-items: flex-start;
  color: #5c4033;
  font-family: var(--serif);
  font-size: 30px;
  font-weight: 700;
  line-height: 36px;
  letter-spacing: -0.25px;
}
.heritage-stat strong span {
  margin-left: 1px;
  color: #c5a059;
  font-size: 18px;
  font-weight: 700;
  line-height: 28px;
}
.heritage-stat small {
  margin-top: 5px;
  color: #9b7b6a;
  font-size: 14px;
  line-height: 20px;
}
.heritage-stats > i {
  width: 1px;
  height: 40px;
  background: rgba(197, 160, 89, 0.35);
}
.heritage-search {
  padding: 24px 18px;
}
.heritage-search > p {
  margin: 8px 0 18px;
}
.heritage-search form {
  flex-direction: row;
  gap: 8px;
}
.heritage-search input {
  min-width: 0;
  font-size: 12px;
}
.heritage-search button {
  flex-shrink: 0;
}
.hot-searches {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 10px;
  margin-top: 18px;
  line-height: 1.8;
}
.hot-searches button {
  padding: 0;
  color: var(--clay);
}
.heritage-results {
  padding-top: 32px;
  scroll-margin-top: 20px;
}
.heritage-results > p {
  margin: 8px 0 20px;
}
.heritage-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.heritage-card {
  overflow: hidden;
}
.heritage-card > img {
  width: 100%;
  height: 210px;
  object-fit: cover;
}
.heritage-card > div {
  padding: 20px;
}
.heritage-card h3 {
  font-family: var(--serif);
  font-size: 20px;
  margin: 6px 0 12px;
}
.heritage-card .text-button {
  display: block;
  padding: 14px 0 0;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
}
</style>
