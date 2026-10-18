<script setup lang="ts">
import { computed, ref, watch, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api";
import { categories, designImage, designIcon } from "../design";
import AsyncState from "../components/AsyncState.vue";
import CourseCard from "../components/CourseCard.vue";
const route = useRoute(), router = useRouter();
const courses = ref<any[]>([]),
  loading = ref(false),
  error = ref("");
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
async function load() {
  const version = ++loadVersion;
  loading.value = true;
  error.value = "";
  try {
    const q = new URLSearchParams({ pageSize: "50", age_group: age.value });
    if (category.value) q.set("category", category.value);
    const result = await api("/mobile/courses?" + q);
    if (version === loadVersion) courses.value = result.list;
  } catch (e) {
    if (version === loadVersion) error.value = (e as Error).message;
  } finally {
    if (version === loadVersion) loading.value = false;
  }
}
watch([category, age], load, { immediate: true });
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
    <section
      class="course-banner"
      :style="{
        backgroundImage:
          'url(' +
          designImage('layer-40-32392', '5:06022/5:05686') +
          '),linear-gradient(rgba(107,42,42,.19),rgba(107,42,42,.19)),url(' +
          designImage('layer-40-32392', '5:06022/5:05671') +
          ')',
      }"
    >
      <p>非遗美育课程</p>
      <h2>津门非遗 · 线上小课</h2>
      <span>按学段选课，观看视频并完成随堂鉴赏</span>
    </section>
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
    <div class="section-heading course-section-heading">
      <h2>非遗典藏 · 小课</h2>
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
    <AsyncState
      :loading="loading"
      :error="error"
      :empty="!courses.length"
      @retry="load"
      ><div class="course-grid">
        <CourseCard
          v-for="course in courses"
          :key="course.id"
          :course="course"
        /></div
    ></AsyncState>
    <footer
      class="course-brand"
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
</template>
<style scoped>
.courses-page {
  padding: 0 20px 24px;
  background: #f5f0e6;
  color: #5c4033;
  min-height: calc(100dvh - 74px - var(--safe-top) - var(--safe-bottom));
}
.course-banner {
  height: 155px;
  margin: 0 -20px;
  padding: 20px;
  border-radius: 0;
  overflow: hidden;
  background-color: #6b2a2a;
  background-size: cover;
  background-position: center;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
}
.course-banner > p {
  padding: 2px 10px;
  border: 1px solid rgba(196, 162, 101, 0.3);
  border-radius: 30px;
  color: #d4bc8a;
  background: rgba(196, 162, 101, 0.2);
  font-size: 10px;
  font-weight: 500;
  line-height: 15px;
  letter-spacing: 0.25px;
}
.course-banner h2 {
  margin-top: 6px;
  font: 700 20px/25px var(--serif);
  letter-spacing: 0.5px;
  color: #fff;
}
.course-banner > span {
  margin-top: 4px;
  color: rgba(232, 220, 192, 0.8);
  font-size: 12px;
  line-height: 18px;
  letter-spacing: 0.6px;
}
.courses-page .category-tabs {
  display: flex;
  gap: 10px;
  overflow: auto;
  margin: 10px -20px 20px;
  padding: 0 8px;
}
.category-tabs button {
  height: 37px;
  min-width: 68px;
  padding: 0 20px;
  border: 1px solid #e0d5c5;
  border-radius: 30px;
  background: #fffdf8;
  color: #5c4033;
  font-size: 13px;
  font-weight: 500;
  line-height: 20px;
  flex-shrink: 0;
}
.category-tabs button.active {
  min-width: 66px;
  border: 0;
  background: #8b3a3a;
  color: #fff;
  box-shadow: 0 2px 5px rgba(92, 64, 51, 0.14);
}
.course-section-heading {
  height: 42px;
  margin: 0 0 8px;
  gap: 8px;
}
.course-section-heading h2 {
  font: 700 17px/25.5px var(--serif);
  letter-spacing: 0.43px;
}
.age-tabs {
  gap: 8px;
  margin-left: auto;
}
.course-heading-dots {
  display: flex;
  gap: 4px;
}
.course-heading-dots i {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(196, 162, 101, 0.5);
}
.course-heading-dots i:nth-child(2) {
  background: rgba(196, 162, 101, 0.7);
}
.age-tabs button {
  height: 26px;
  padding: 0 11px;
  border: 1px solid #ebe3d5;
  background: #fffdf8;
  color: #a89880;
  font-size: 11px;
  line-height: 16px;
}
.age-tabs button.active {
  border-color: transparent;
  background: rgba(139, 58, 58, 0.1);
  color: #8b3a3a;
  font-weight: 500;
}
.course-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.course-brand {
  height: 120px;
  margin-top: 24px;
  border-radius: 16px;
  overflow: hidden;
  text-align: center;
  background-size: cover;
  background-position: center;
  padding: 26px 8px 20px;
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
  background: rgba(196, 162, 101, 0.7);
}
.course-brand h1 {
  margin-top: 4px;
  font: 700 18px/27px var(--serif);
  letter-spacing: 3.6px;
  color: #fff;
}
.course-brand p {
  margin-top: 4px;
  color: rgba(232, 220, 192, 0.9);
  font-size: 11px;
  line-height: 16.5px;
  letter-spacing: 0.55px;
}
@media (max-width: 350px) {
  .course-section-heading {
    height: auto;
    flex-wrap: wrap;
    padding: 8px 0;
  }
}
</style>
