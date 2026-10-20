<script setup lang="ts">
import { ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api, post, requireSession, notify, mediaUrl } from "../api";
import PageHeader from "../components/PageHeader.vue";
import SectionCard from "../components/SectionCard.vue";
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
    :data-design-node="entry?.category === 'BRONZE' ? '40:32808' : '40:32809'"
  >
    <PageHeader :title="entry?.title || '非遗典藏'" back-to="/heritage">
      <span v-if="entry && !loading && !error" class="heritage-header-actions">
        <button
          aria-label="收藏典藏"
          :aria-pressed="collected"
          @click="collect"
        >
          {{ collected ? "★" : "☆" }}
        </button>
      </span>
    </PageHeader>
    <AsyncState :loading="loading" :error="error" @retry="load"
      ><template v-if="entry">
        <div class="detail-body">
          <SectionCard class="heritage-detail-title">
            <p class="eyebrow">{{ entry.era }}</p>
            <h1>{{ entry.title }}</h1>
            <p class="detail-summary">{{ entry.summary }}</p>
          </SectionCard>
          <section class="artifact-viewer corner-card">
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
          </section>
          <p v-if="!entry.model_url" class="resource-note">
            当前提供高清图片鉴赏，三维模型尚未提供
          </p>
          <SectionCard
            v-if="entry.content.metrics?.length"
            class="artifact-metrics"
            title="核心数据"
          >
            <template #meta>
              <span class="eyebrow">Key Metrics</span>
            </template>
            <div class="metric-grid">
              <article
                v-for="metric in entry.content.metrics"
                :key="metric.label"
              >
                <strong>{{ metric.value }}</strong
                ><span>{{ metric.label }}</span>
              </article>
            </div>
          </SectionCard>
          <SectionCard
            v-for="(section, i) in entry.content.sections || []"
            :key="i"
            class="heritage-article"
            :title="section.title"
          >
            <template #meta>
              <span v-if="section.eyebrow" class="eyebrow">{{
                section.eyebrow
              }}</span>
            </template>
            <img
              v-if="section.image_url"
              :src="mediaUrl(section.image_url)"
              :alt="section.title"
            />
            <p class="article-body">{{ section.body }}</p>
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
          </SectionCard>
          <button
            class="primary-button detail-collect"
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
.heritage-detail {
  min-height: 100dvh;
  padding-bottom: 12px;
  background: #f5ede4;
  color: #2d1810;
}
.detail-body {
  padding: 14px 16px 24px;
}
.heritage-header-actions {
  display: flex;
  align-items: center;
}
.heritage-header-actions button {
  width: 32px;
  height: 32px;
  padding: 0;
  border: 1px solid rgba(200, 169, 110, 0.45);
  border-radius: 50%;
  background: rgba(255, 253, 248, 0.8);
  color: #8a6125;
  font-size: 16px;
  line-height: 1;
}
.heritage-header-actions button[aria-pressed="true"] {
  border-color: rgba(139, 26, 26, 0.3);
  color: #8b1a1a;
}
.heritage-detail-title {
  padding: 16px 14px;
}
.heritage-detail-title .eyebrow {
  color: #8a6125;
}
.heritage-detail-title h1 {
  margin: 6px 0 8px;
  color: #2d1810;
  font: 500 18px/1.5 var(--serif);
  letter-spacing: 1.5px;
}
.detail-summary {
  color: #8a7a70;
  font: 400 13px/1.9 var(--sans);
}
.artifact-viewer {
  position: relative;
  height: 300px;
  margin-bottom: 14px;
  border: 1px solid rgba(200, 169, 110, 0.35);
  border-radius: 14px;
  overflow: hidden;
  background: #f0e3d2;
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
  bottom: 12px;
  right: 12px;
  display: flex;
  gap: 6px;
}
.viewer-tools button {
  min-width: 32px;
  min-height: 32px;
  padding: 0 8px;
  border: 1px solid rgba(200, 169, 110, 0.5);
  border-radius: 8px;
  background: rgba(255, 253, 248, 0.92);
  color: #5a3e36;
  font: 400 12px/1 var(--sans);
}
.viewer-tools button:disabled {
  opacity: 0.4;
}
.resource-note {
  margin: -4px 2px 12px;
  text-align: center;
  color: #8a7a70;
  font: 400 10px/1.7 var(--sans);
}
.artifact-metrics .eyebrow {
  color: #8a6125;
}
.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.metric-grid article {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  border: 1px solid rgba(200, 169, 110, 0.24);
  border-radius: 10px;
  background: #fffdf8;
}
.metric-grid strong {
  color: #8b1a1a;
  font: 500 18px/1.3 var(--serif);
}
.metric-grid span {
  color: #8a7a70;
  font: 400 10px/1.5 var(--sans);
  letter-spacing: 0.5px;
}
.heritage-article img {
  width: 100%;
  margin-bottom: 12px;
  border: 1px solid rgba(200, 169, 110, 0.28);
  border-radius: 10px;
}
.article-body {
  color: #5a3e36;
  font: 400 13px/2 var(--sans);
  white-space: pre-line;
}
.craft-steps {
  margin-top: 6px;
}
.craft-steps article {
  padding: 12px 0;
  border-bottom: 1px solid rgba(200, 169, 110, 0.2);
}
.craft-steps article:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}
.craft-steps span {
  display: block;
  color: #8a6125;
  font: 500 16px/1.4 var(--serif);
  letter-spacing: 1px;
}
.craft-steps h3 {
  margin: 4px 0 6px;
  color: #2d1810;
  font: 500 14px/1.5 var(--serif);
}
.craft-steps p {
  color: #5a3e36;
  font: 400 13px/1.9 var(--sans);
  white-space: pre-line;
}
.heritage-themes {
  display: grid;
  gap: 12px;
  margin-top: 6px;
}
.heritage-themes article {
  overflow: hidden;
  border: 1px solid rgba(200, 169, 110, 0.3);
  border-radius: 12px;
  background: #fffdf8;
}
.theme-image {
  position: relative;
  height: 150px;
  background: #f0e3d2;
}
.heritage-article .theme-image img {
  width: 100%;
  height: 100%;
  margin: 0;
  border: 0;
  border-radius: 0;
  object-fit: cover;
}
.theme-image > span {
  position: absolute;
  right: 10px;
  top: 10px;
  padding: 3px 9px;
  border-radius: 999px;
  background: rgba(139, 97, 37, 0.92);
  color: #fffdf8;
  font: 400 10px/1.4 var(--sans);
}
.heritage-themes article > .eyebrow {
  margin: 12px 12px 0;
  color: #8a6125;
}
.heritage-themes h3 {
  margin: 4px 12px 6px;
  color: #2d1810;
  font: 500 14px/1.5 var(--serif);
}
.heritage-themes article > p:last-child {
  margin: 0 12px 14px;
  color: #8a7a70;
  font: 400 12px/1.85 var(--sans);
}
.heritage-timeline {
  margin-top: 6px;
  padding-left: 6px;
  border-left: 1px solid rgba(200, 169, 110, 0.45);
}
.heritage-timeline article {
  position: relative;
  display: flex;
  gap: 12px;
  padding: 0 0 18px 16px;
}
.heritage-timeline article:last-child {
  padding-bottom: 0;
}
.timeline-era {
  width: 30px;
  height: 30px;
  flex: 0 0 30px;
  display: grid;
  place-items: center;
  margin-left: -32px;
  border-radius: 50%;
  background: #f6ecdd;
  border: 1px solid rgba(200, 169, 110, 0.5);
  color: #8b1a1a;
  font: 500 12px/1 var(--serif);
}
.heritage-timeline h3 {
  margin: 2px 0 4px;
  color: #2d1810;
  font: 500 14px/1.5 var(--serif);
}
.heritage-timeline p:last-child {
  margin: 0;
  color: #8a7a70;
  font: 400 12px/1.8 var(--sans);
}
.heritage-timeline .eyebrow {
  color: #8a6125;
}
.heritage-features {
  display: grid;
  gap: 8px;
  margin-top: 6px;
}
.heritage-features article {
  padding: 10px 12px;
  border-left: 2px solid #c8a96e;
  border-radius: 0 8px 8px 0;
  background: rgba(200, 169, 110, 0.1);
}
.heritage-features h3 {
  margin: 0 0 4px;
  color: #2d1810;
  font: 500 13px/1.5 var(--serif);
}
.heritage-features p {
  margin: 0;
  color: #8a7a70;
  font: 400 12px/1.8 var(--sans);
}
.heritage-quote {
  margin: 12px 0 0;
  padding: 14px 12px;
  border: 0;
  border-radius: 12px;
  background: #f6ecdd;
  text-align: center;
}
.heritage-quote p {
  color: #6b4a32;
  font: 400 14px/1.9 var(--serif);
}
.heritage-quote cite {
  display: block;
  margin-top: 6px;
  color: #8a7a70;
  font: 400 10px/1.6 var(--sans);
  font-style: normal;
}
.detail-collect {
  width: 100%;
  margin: 0 0 8px;
  border: 1px solid transparent;
  border-radius: 12px;
  background: #8b1a1a;
  color: #f6ead9;
  font-size: 13px;
  letter-spacing: 1px;
}
</style>
