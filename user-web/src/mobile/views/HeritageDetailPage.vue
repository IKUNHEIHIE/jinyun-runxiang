<script setup lang="ts">
import { ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api, post, requireSession, notify, mediaUrl } from "../api";
import PageHeader from "../components/PageHeader.vue";
import AsyncState from "../components/AsyncState.vue";
const route = useRoute(),
  router = useRouter(),
  entry = ref<any>(),
  loading = ref(true),
  error = ref(""),
  zoom = ref(1),
  collected = ref(false);
function back() {
  window.history.state.back ? router.back() : router.replace("/heritage");
}
async function load() {
  loading.value = true;
  error.value = "";
  zoom.value = 1;
  collected.value = false;
  try {
    entry.value = await api("/mobile/heritage/" + route.params.id);
    collected.value = Boolean(entry.value?.collected);
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
}
async function collect() {
  if (!requireSession()) return;
  try {
    collected.value = (
      await post("/mobile/collections/HERITAGE/" + entry.value.id)
    ).collected;
    notify(collected.value ? "已加入收藏" : "已取消收藏");
  } catch (e) {
    notify((e as Error).message);
  }
}
watch(() => route.params.id, load, { immediate: true });
</script>
<template>
  <div
    class="heritage-detail"
    :class="{ bronze: entry?.category === 'BRONZE' }"
    :data-design-node="entry?.category === 'BRONZE' ? '40:32808' : '40:32809'"
  >
    <header v-if="entry?.category === 'BRONZE'" class="bronze-header">
      <button aria-label="返回上一页" @click="back">‹</button>
      <h1>{{ entry.title }}</h1>
      <p>{{ entry.era }} · 青铜器</p>
    </header>
    <PageHeader v-else :title="entry?.title || '非遗典藏'">
      <span v-if="entry && !loading && !error" class="heritage-header-actions">
        <button
          aria-label="收藏典藏"
          :aria-pressed="collected"
          @click="collect"
        >
          {{ collected ? "★" : "☆" }}
        </button>
      </span></PageHeader
    ><AsyncState
      :loading="loading"
      :error="error"
      @retry="load"
      ><template v-if="entry"
        ><header
          v-if="entry.category !== 'BRONZE'"
          class="heritage-detail-title"
        >
          <p class="eyebrow">{{ entry.era }}</p>
          <h1>{{ entry.title }}</h1>
          <p>{{ entry.summary }}</p>
        </header>
        <div class="artifact-viewer">
          <img
            :src="mediaUrl(entry.content.hero_url || entry.cover_url)"
            :alt="entry.title"
            :style="{ transform: 'scale(' + zoom + ')' }"
          />
          <div class="viewer-tools">
            <button
              aria-label="缩小文物图片"
              :disabled="zoom <= 1"
              @click="zoom = Math.max(1, zoom - 0.25)"
            >
              −</button
            ><button
              aria-label="放大文物图片"
              :disabled="zoom >= 3"
              @click="zoom = Math.min(3, zoom + 0.25)"
            >
              ＋</button
            ><button @click="zoom = 1">复位</button>
          </div>
        </div>
        <p v-if="!entry.model_url" class="resource-note">
          当前提供高清图片鉴赏，三维模型尚未提供
        </p>
        <div class="page-padding">
          <section
            v-if="entry.content.metrics?.length"
            class="artifact-metrics"
          >
            <h2>核心数据</h2>
            <p class="eyebrow">Key Metrics</p>
            <div>
              <article
                v-for="metric in entry.content.metrics"
                :key="metric.label"
              >
                <strong>{{ metric.value }}</strong
                ><span>{{ metric.label }}</span>
              </article>
            </div>
          </section>
          <section
            v-for="(section, i) in entry.content.sections || []"
            :key="i"
            class="heritage-article"
          >
            <p v-if="section.eyebrow" class="eyebrow">{{ section.eyebrow }}</p>
            <h2>{{ section.title }}</h2>
            <img
              v-if="section.image_url"
              :src="mediaUrl(section.image_url)"
              :alt="section.title"
            />
            <p>{{ section.body }}</p>
            <div v-if="section.steps" class="craft-steps">
              <article v-for="(step, n) in section.steps" :key="n">
                <span>{{ String(Number(n) + 1).padStart(2, "0") }}</span>
                <h3>{{ step.title }}</h3>
                <p>{{ step.body }}</p>
              </article>
            </div>
            <div v-if="section.items" class="heritage-themes">
              <article v-for="(item, n) in section.items" :key="n">
                <div class="theme-image">
                  <img
                    v-if="item.image_url"
                    :src="mediaUrl(item.image_url)"
                    :alt="item.title"
                  />
                  <span v-if="item.badge">{{ item.badge }}</span>
                </div>
                <p v-if="item.subtitle" class="eyebrow">
                  {{ item.subtitle }}
                </p>
                <h3>{{ item.title }}</h3>
                <p>{{ item.body }}</p>
              </article>
            </div>
            <div v-if="section.timeline" class="heritage-timeline">
              <article v-for="(item, n) in section.timeline" :key="n">
                <span class="timeline-era">{{ item.era }}</span>
                <div>
                  <p class="eyebrow">{{ item.date }}</p>
                  <h3>{{ item.title }}</h3>
                  <p>{{ item.body }}</p>
                </div>
              </article>
            </div>
            <div v-if="section.features" class="heritage-features">
              <article v-for="(item, n) in section.features" :key="n">
                <h3>{{ item.title }}</h3>
                <p>{{ item.body }}</p>
              </article>
            </div>
            <blockquote v-if="section.quote" class="heritage-quote">
              <p>“{{ section.quote.text }}”</p>
              <cite>— {{ section.quote.source }}</cite>
            </blockquote>
          </section>
          <button
            class="primary-button"
            :aria-pressed="collected"
            @click="collect"
          >
            {{ collected ? "已收藏" : "收藏典藏" }}
          </button>
        </div></template
      ></AsyncState
    >
  </div>
</template>
<style scoped>
.heritage-header-actions {
  display: flex;
  align-items: center;
}
.heritage-header-actions button {
  width: 38px;
  height: 38px;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--clay);
  font-size: 20px;
  line-height: 1;
}
.heritage-header-actions button[aria-pressed="true"] {
  color: var(--gold);
}
.heritage-detail-title {
  padding: 36px 24px 24px;
  text-align: center;
}
.heritage-detail-title h1 {
  font-size: 36px;
  margin: 14px 0;
  color: var(--cinnabar);
  line-height: 1.5;
}
.heritage-detail-title > p:last-child {
  font-size: 12px;
  line-height: 2;
  color: var(--muted);
}
.artifact-viewer {
  position: relative;
  height: 370px;
  overflow: hidden;
  background: #e8dcca;
  display: grid;
  place-items: center;
}
.artifact-viewer > img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  transition: transform 0.2s;
}
.viewer-tools {
  position: absolute;
  bottom: 14px;
  right: 14px;
  display: flex;
  gap: 8px;
}
.viewer-tools button {
  background: var(--paper);
  border: 1px solid var(--gold);
  border-radius: 8px;
  min-width: 36px;
  min-height: 36px;
  font-size: 14px;
}
.resource-note {
  text-align: center;
  font-size: 10px;
  color: var(--muted);
  padding: 12px 20px;
}
.artifact-metrics > div {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin: 24px 0;
}
.artifact-metrics article {
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-bottom: 1px solid var(--gold-light);
  padding-bottom: 14px;
}
.artifact-metrics strong {
  font-family: var(--serif);
  font-size: 23px;
  color: var(--clay);
}
.artifact-metrics span {
  font-size: 11px;
  color: var(--muted);
}
.heritage-article {
  margin-bottom: 32px;
}
.heritage-article h2 {
  font-size: 23px;
  margin: 10px 0 18px;
}
.heritage-article > p:last-child,
.craft-steps p {
  font-size: 13px;
  line-height: 2;
  white-space: pre-line;
  color: var(--muted);
}
.heritage-article img {
  width: 100%;
  margin-bottom: 20px;
}
.craft-steps article {
  padding: 24px 0;
  border-bottom: 1px solid var(--gold-light);
}
.craft-steps span {
  font: 28px var(--serif);
  color: var(--gold);
}
.craft-steps h3 {
  font-size: 17px;
  margin: 12px 0;
}
.heritage-themes {
  display: grid;
  gap: 18px;
  margin-top: 22px;
}
.heritage-themes article {
  overflow: hidden;
  border: 1px solid rgba(201, 168, 76, 0.3);
  border-radius: 12px;
  background: #fdfbf5;
}
.theme-image {
  position: relative;
  height: 168px;
  background: #e8dcca;
}
.theme-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.theme-image > span {
  position: absolute;
  right: 10px;
  top: 10px;
  padding: 3px 9px;
  border-radius: 999px;
  background: rgba(196, 163, 90, 0.92);
  color: #fff;
  font-size: 9px;
}
.heritage-themes article > .eyebrow,
.heritage-themes article > h3,
.heritage-themes article > p:last-child {
  margin-left: 14px;
  margin-right: 14px;
}
.heritage-themes article > .eyebrow {
  margin-top: 12px;
}
.heritage-themes h3 {
  margin-top: 4px;
  margin-bottom: 6px;
  font-family: var(--serif);
  font-size: 19px;
}
.heritage-themes article > p:last-child {
  margin-top: 0;
  margin-bottom: 16px;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.9;
}
.heritage-timeline {
  margin-top: 18px;
  padding-left: 6px;
  border-left: 1px solid rgba(201, 168, 76, 0.45);
}
.heritage-timeline article {
  position: relative;
  display: flex;
  gap: 14px;
  padding: 0 0 22px 18px;
}
.heritage-timeline article:last-child {
  padding-bottom: 0;
}
.timeline-era {
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  display: grid;
  place-items: center;
  margin-left: -36px;
  border-radius: 50%;
  background: #f4e7d4;
  border: 1px solid rgba(201, 168, 76, 0.5);
  color: #a0522d;
  font-family: var(--serif);
  font-size: 14px;
}
.heritage-timeline h3 {
  margin: 4px 0 6px;
  font-size: 16px;
}
.heritage-timeline p:last-child {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.8;
}
.heritage-features {
  display: grid;
  gap: 10px;
  margin-top: 16px;
}
.heritage-features article {
  padding: 14px 16px;
  border-left: 2px solid var(--gold);
  background: rgba(250, 245, 240, 0.8);
}
.heritage-features h3 {
  margin: 0 0 6px;
  font-size: 15px;
}
.heritage-features p {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.9;
}
.heritage-quote {
  margin: 20px 0 0;
  padding: 20px 18px;
  border: 0;
  border-radius: 12px;
  background: #f4e7d4;
  text-align: center;
}
.heritage-quote p {
  margin: 0;
  color: #6b4a32;
  font-family: var(--serif);
  font-size: 15px;
  line-height: 1.9;
}
.heritage-quote cite {
  display: block;
  margin-top: 8px;
  color: var(--muted);
  font-size: 10px;
  font-style: normal;
}
.bronze-header {
  position: relative;
  padding: 28px 24px 22px;
  text-align: center;
  background: #372116;
  color: #e8d5a3;
}
.bronze-header > button {
  position: absolute;
  left: 16px;
  top: 24px;
  width: 38px;
  height: 38px;
  border: 1px solid rgba(232, 213, 163, 0.45);
  border-radius: 50%;
  color: #e8d5a3;
  font-size: 24px;
  line-height: 1;
}
.bronze-header h1 {
  margin: 0;
  font-family: var(--serif);
  font-size: 30px;
  letter-spacing: 4px;
  color: #e8d5a3;
}
.bronze-header p {
  margin-top: 8px;
  font-size: 12px;
  color: #bca98b;
  letter-spacing: 1px;
}
.bronze {
  min-height: 100dvh;
  background: #372116;
  color: #eadbc1;
}
.bronze .artifact-viewer {
  background: #1d1712;
}
.bronze .resource-note {
  color: #a9957c;
  background: #372116;
}
.bronze .artifact-metrics strong {
  color: #d8b56d;
}
.bronze .artifact-metrics span,
.bronze .artifact-metrics .eyebrow {
  color: #bca98b;
}
.bronze .heritage-article {
  padding: 18px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.045);
}
.bronze .heritage-article h2 {
  color: #e8d5a3;
}
.bronze .heritage-article > p:last-child,
.bronze .craft-steps p {
  color: #c9b79c;
}
.bronze .craft-steps tspan,
.bronze .craft-steps span {
  color: #d8b56d;
}
.bronze .primary-button {
  border: 1px solid #c5a059;
  background: transparent;
  color: #e8d5a3;
}
</style>
