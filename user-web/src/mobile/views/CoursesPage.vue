<script setup lang="ts">
import { computed, ref, watch, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api";
import { categories, designImage, designIcon } from "../design";
import AsyncState from "../components/AsyncState.vue";
import PageHeader from "../components/PageHeader.vue";
import SectionCard from "../components/SectionCard.vue";
import CourseCard from "../components/CourseCard.vue";
import PagerBar from "../components/PagerBar.vue";
import PullToRefresh from "../components/PullToRefresh.vue";
import BannerCarousel from "../components/BannerCarousel.vue";
const route = useRoute(), router = useRouter();
const PAGE_SIZE = 20;
const banners = [
  { src: designImage("layer-40-32392", "5:06022/5:05671"), alt: "津门非遗课堂", caption: "首讲 · 走进津门非遗" },
  { src: "/design/banners/banner-shadow.webp", alt: "皮影戏人物", caption: "皮影 · 灯影成戏" },
  { src: "/design/banners/banner-kite.webp", alt: "潍坊国际风筝会", caption: "风筝 · 一线扶摇" },
  { src: "/design/banners/banner-porcelain.webp", alt: "瓷器陈列", caption: "瓷器 · 青花入釉" },
  { src: "/design/banners/banner-embroidery.webp", alt: "刺绣龙袍", caption: "苏绣 · 金线盘龙" },
];
const courses = ref<any[]>([]),
  loading = ref(false),
  error = ref("");
const page = ref(1),
  total = ref(0);
const categoryTabs = ref<HTMLDivElement | null>(null);
const category = computed(() =>
  categories.some((c) => c.value === route.query.category)
    ? String(route.query.category)
    : "",
);
const age = computed(() =>
  route.query.age === "PRIMARY_HIGH" ? "PRIMARY_HIGH" : "PRIMARY_LOW",
);
function setFilters(nextCategory: string, nextAge = age.value) {
  return router.replace({
    query: {
      ...route.query,
      category: nextCategory || undefined,
      age: nextAge === "PRIMARY_HIGH" ? nextAge : undefined,
    },
  });
}
let loadVersion = 0;
async function load(target = 1) {
  const version = ++loadVersion;
  loading.value = true;
  error.value = "";
  try {
    const q = new URLSearchParams({
      pageSize: String(PAGE_SIZE),
      page: String(target),
      age_group: age.value,
    });
    if (category.value) q.set("category", category.value);
    const result = await api("/mobile/courses?" + q);
    if (version === loadVersion) {
      courses.value = result.list;
      total.value = result.total;
      page.value = target;
    }
  } catch (e) {
    if (version === loadVersion) error.value = (e as Error).message;
  } finally {
    if (version === loadVersion) loading.value = false;
  }
}
function changePage(next: number) {
  if (next === page.value) return;
  void load(next).then(() => window.scrollTo({ top: 0, behavior: "smooth" }));
}
const refresh = () => load(page.value);
watch([category, age], () => load(1), { immediate: true });
onMounted(() => {
  const tabs = categoryTabs.value;
  const active = tabs?.querySelector<HTMLButtonElement>(".active");
  if (!tabs || !active) return;
  const container = tabs.getBoundingClientRect();
  const item = active.getBoundingClientRect();
  if (item.left < container.left || item.right > container.right) {
    tabs.scrollLeft += item.left - container.left - 8;
  }
});
</script>
<template>
  <div class="courses-page" data-design-node="40:32392">
    <PullToRefresh :on-refresh="refresh" />
    <PageHeader title="小课堂" subtitle="非遗美育课程" :back="false" />
    <div class="courses-body">
      <BannerCarousel :slides="banners" />
      <SectionCard title="非遗典藏 · 小课">
        <template #meta>
          <div class="course-tools">
            <span class="course-heading-dots" aria-hidden="true"
              ><i /><i /><i
            /></span>
            <div class="age-tabs">
              <button
                :class="{ active: age === 'PRIMARY_LOW' }"
                :aria-pressed="age === 'PRIMARY_LOW'"
                @click="setFilters(category, 'PRIMARY_LOW')"
              >
                1-3年级</button
              ><button
                :class="{ active: age === 'PRIMARY_HIGH' }"
                :aria-pressed="age === 'PRIMARY_HIGH'"
                @click="setFilters(category, 'PRIMARY_HIGH')"
              >
                4-6年级
              </button>
            </div>
          </div>
        </template>
        <div ref="categoryTabs" class="category-tabs" aria-label="课程分类">
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
        <AsyncState
          :loading="loading"
          :error="error"
          :empty="!courses.length"
          @retry="load(page)"
          ><div class="course-grid">
            <CourseCard
              v-for="course in courses"
              :key="course.id"
              :course="course"
            /></div
        ></AsyncState>
        <PagerBar
          :page="page"
          :total="total"
          :page-size="PAGE_SIZE"
          unit="门"
          @change="changePage"
        />
      </SectionCard>
      <footer
        class="course-brand corner-card"
        :style="{
          backgroundImage:
            'linear-gradient(rgba(92,64,51,.3),rgba(92,64,51,.3)),url(' +
            designImage('layer-40-32392', '5:05321') +
            ')',
        }"
      >
        <div class="course-brand-ornament">
          <i /><img :src="designIcon('layer-40-32392', '5:05297')" alt="" /><i />
        </div>
        <h1>非遗典藏 · 小课堂</h1>
        <p>传承千年技艺，点亮文化之光</p>
      </footer>
    </div>
  </div>
</template>
<style scoped>
.courses-page {
  min-height: 100dvh;
  padding-bottom: 12px;
  background: #f5ede4;
  color: #2d1810;
}
.courses-body {
  padding: 14px 16px 24px;
}

.course-banner > p {
  padding: 2px 10px;
  border: 1px solid rgba(200, 169, 110, 0.4);
  border-radius: 999px;
  color: #e8d9a8;
  background: rgba(60, 24, 24, 0.28);
  font: 500 10px/1.5 var(--sans);
  letter-spacing: 1px;
}
.course-banner h2 {
  margin-top: 8px;
  font: 500 18px/1.4 var(--serif);
  letter-spacing: 1.5px;
  color: #fff;
  text-shadow: 0 1px 8px rgba(40, 16, 12, 0.35);
}
.course-banner > span {
  margin-top: 4px;
  color: rgba(246, 234, 217, 0.85);
  font: 400 11px/1.6 var(--sans);
  letter-spacing: 0.6px;
}
.course-tools {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.course-heading-dots {
  display: flex;
  gap: 4px;
}
.course-heading-dots i {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(200, 169, 110, 0.6);
}
.course-heading-dots i:nth-child(2) {
  background: rgba(200, 169, 110, 0.85);
}
.age-tabs {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}
.age-tabs button {
  height: 24px;
  padding: 0 6px;
  border: 1px solid rgba(200, 169, 110, 0.42);
  border-radius: 999px;
  background: rgba(255, 253, 248, 0.7);
  color: #8a7a70;
  font: 400 10px/1 var(--sans);
  white-space: nowrap;
}
.age-tabs button.active {
  border-color: rgba(139, 26, 26, 0.26);
  background: rgba(139, 26, 26, 0.08);
  color: #8b1a1a;
  font-weight: 500;
}
.category-tabs {
  display: flex;
  gap: 8px;
  overflow: auto;
  margin: 0 -14px 12px;
  padding: 0 14px 2px;
  scrollbar-width: none;
}
.category-tabs::-webkit-scrollbar {
  display: none;
}
.category-tabs button {
  flex-shrink: 0;
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
.course-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.courses-page :deep(.async-state) {
  padding: 6px 2px 2px;
}
.course-brand {
  height: 112px;
  padding: 20px 12px 16px;
  border-radius: 14px;
  text-align: center;
  background-size: cover;
  background-position: center;
}
.course-brand-ornament {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 16px;
}
.course-brand-ornament img {
  width: 16px;
  height: 16px;
}
.course-brand-ornament i {
  width: 32px;
  height: 1px;
  background: rgba(232, 217, 168, 0.7);
}
.course-brand h1 {
  margin-top: 4px;
  font: 500 16px/1.7 var(--serif);
  letter-spacing: 3.2px;
  color: #fff;
}
.course-brand p {
  margin-top: 2px;
  color: rgba(246, 234, 217, 0.9);
  font: 400 10px/1.6 var(--sans);
  letter-spacing: 0.6px;
}
@media (max-width: 350px) {
  .course-heading-dots {
    display: none;
  }
  .course-tools {
    gap: 4px;
  }
  .age-tabs button {
    padding: 0 4px;
  }
}
</style>
