<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api, post, session, requireSession, notify, loadProfile } from "../api";
import { designImage, designIcon, categories, categoryName } from "../design";
import AsyncState from "../components/AsyncState.vue";
import CourseCard from "../components/CourseCard.vue";
import PageHeader from "../components/PageHeader.vue";
import SectionCard from "../components/SectionCard.vue";
import SkeletonImage from "../components/SkeletonImage.vue";
const router = useRouter(),
  route = useRoute();
const category = computed(() =>
  categories.slice(0, 4).some((c) => c.value === route.query.category)
    ? String(route.query.category)
    : "",
);
const age = computed(() =>
  route.query.age === "PRIMARY_HIGH" ? "PRIMARY_HIGH" : "PRIMARY_LOW",
);
const courseLoading = ref(true),
  heritageLoading = ref(true),
  courseError = ref(""),
  heritageError = ref(""),
  summaryError = ref(""),
  summaryLoading = ref(false),
  profileRetrying = ref(false),
  personal = ref<any>({});
const courses = ref<any[]>([]),
  heritage = ref<any[]>([]),
  checkedIn = ref<boolean | null>(null),
  signing = ref(false);
const energy = computed(() =>
  session.token ? (personal.value.energy_value ?? null) : 0,
);
const levelCode = computed(() => session.profile?.level_code || "");
const nextLevelTarget = computed(() => {
  if (levelCode.value === "LV1_APPRENTICE") return 500;
  if (levelCode.value === "LV2_JOURNEYMAN") return 1000;
  return null;
});
const energyPercent = computed(() => {
  if (!session.token || energy.value == null) return 0;
  if (!nextLevelTarget.value) return levelCode.value === "LV3_CRAFTSMAN" ? 100 : 0;
  return Math.min(100, (energy.value / nextLevelTarget.value) * 100);
});
const levelLabel = computed(() =>
  session.profile?.level_code
    ? session.profile.level_code.split("_")[0].replace("LV", "LV.")
    : session.token
      ? "等级未知"
      : "LV.1",
);
let mounted = true,
  loadVersion = 0,
  summaryVersion = 0,
  checkinVersion = 0;
let pendingSummaryToken: string | undefined;
let timer: ReturnType<typeof setInterval>;
async function load() {
  const version = ++loadVersion,
    token = session.token,
    selectedCategory = category.value,
    selectedAge = age.value;
  const current = () =>
    mounted &&
    version === loadVersion &&
    token === session.token &&
    selectedCategory === category.value &&
    selectedAge === age.value;
  courseLoading.value = heritageLoading.value = true;
  courseError.value = heritageError.value = "";
  const params = new URLSearchParams({ pageSize: "4", age_group: selectedAge });
  if (selectedCategory) params.set("category", selectedCategory);
  await Promise.all([
    (async () => {
      try {
        const data = await api("/mobile/courses?" + params);
        if (current()) courses.value = data.list;
      } catch (e) {
        if (current()) courseError.value = (e as Error).message;
      } finally {
        if (current()) courseLoading.value = false;
      }
    })(),
    (async () => {
      try {
        const data = await api(
          "/mobile/heritage?" +
            new URLSearchParams({
              page_size: "8",
              ...(selectedCategory ? { category: selectedCategory } : {}),
            }),
        );
        if (current()) heritage.value = data.list;
      } catch (e) {
        if (current()) heritageError.value = (e as Error).message;
      } finally {
        if (current()) heritageLoading.value = false;
      }
    })(),
  ]);
}
async function loadSummary(force = false) {
  const token = session.token;
  if (!mounted || !token || signing.value) return;
  if (!force && summaryLoading.value && pendingSummaryToken === token) return;
  const version = ++summaryVersion;
  pendingSummaryToken = token;
  summaryLoading.value = true;
  summaryError.value = "";
  const current = () =>
    mounted && version === summaryVersion && token === session.token;
  try {
    const data = await api("/mobile/me/summary");
    if (current()) {
      personal.value = data;
      checkedIn.value = data.checked_in;
    }
  } catch (e) {
    if (current()) summaryError.value = (e as Error).message;
  } finally {
    if (current()) summaryLoading.value = false;
  }
}
async function retryAccount() {
  if (summaryLoading.value || profileRetrying.value) return;
  profileRetrying.value = true;
  const profile = session.token && !session.profile
    ? loadProfile().catch(() => {})
    : Promise.resolve();
  try {
    await Promise.all([profile, loadSummary(true)]);
  } finally {
    profileRetrying.value = false;
  }
}
async function checkin() {
  if (!requireSession() || signing.value) return;
  const token = session.token,
    version = ++checkinVersion;
  const current = () =>
    mounted && version === checkinVersion && token === session.token;
  // Invalidate a summary started before the accepted check-in.
  summaryVersion++;
  summaryLoading.value = false;
  signing.value = true;
  try {
    const r = await post("/mobile/me/checkin");
    if (!current()) return;
    checkedIn.value =
      r.date ===
      new Intl.DateTimeFormat("sv-SE", { timeZone: "Asia/Shanghai" }).format(
        new Date(),
      );
    personal.value = { ...personal.value, energy_value: r.energy_value };
    summaryError.value = "";
    if (session.profile) session.profile.energy_value = r.energy_value;
    notify(r.already_checked_in ? "今天已经签到啦" : "签到成功，获得10能量");
  } catch (e) {
    if (current()) notify((e as Error).message);
  } finally {
    if (current()) signing.value = false;
  }
}
function changeCategory(value: string) {
  return router.replace({
    query: { ...route.query, category: value || undefined },
  });
}
function changeAge(value: string) {
  return router.replace({
    query: {
      ...route.query,
      age: value === "PRIMARY_HIGH" ? value : undefined,
    },
  });
}
function refreshVisible() {
  if (document.visibilityState !== "visible") return;
  void loadSummary();
  if (courseError.value || heritageError.value) void load();
}
watch([category, age, () => session.token], () => void load(), {
  immediate: true,
});
watch(
  () => session.token,
  () => {
    courses.value = [];
    summaryVersion++;
    checkinVersion++;
    checkedIn.value = null;
    personal.value = {};
    summaryError.value = "";
    summaryLoading.value = signing.value = false;
    pendingSummaryToken = undefined;
    if (session.token) void loadSummary();
  },
  { immediate: true, flush: "sync" },
);
onMounted(() => {
  window.addEventListener("online", refreshVisible);
  document.addEventListener("visibilitychange", refreshVisible);
  timer = setInterval(() => {
    if (document.visibilityState === "visible") void loadSummary();
  }, 60000);
});
onUnmounted(() => {
  mounted = false;
  loadVersion++;
  summaryVersion++;
  checkinVersion++;
  clearInterval(timer);
  window.removeEventListener("online", refreshVisible);
  document.removeEventListener("visibilitychange", refreshVisible);
});
</script>
<template>
  <div class="home-page" data-design-node="5:01925">
    <PageHeader title="津韵润乡" subtitle="非遗美育研习" :back="false" />
    <div class="home-body">
      <RouterLink
        to="/heritage"
        class="home-heritage corner-card"
        :style="{
          '--entry-image': 'url(' + designImage('home', '5:02020') + ')',
        }"
      >
        <h2>非遗百科库</h2>
        <span>入口</span>
      </RouterLink>
      <div
        class="home-categories"
        aria-label="非遗分类"
        data-design-node="5:06032"
      >
        <button
          v-for="c in categories.slice(0, 4)"
          :key="c.value"
          :class="{ active: category === c.value }"
          :aria-pressed="category === c.value"
          @click="changeCategory(c.value)"
        >
          {{ c.label }}
        </button>
      </div>
      <SectionCard title="美育去处">
        <div class="home-hubs">
          <RouterLink to="/landmarks" class="home-hub">
            <SkeletonImage
              class="home-hub-media"
              src="/design/images/562642870bc0dbb9f77e661a544aed0e.webp"
              alt=""
              eager
            />
            <div>
              <strong>行走的美育地图</strong>
              <span>打卡非遗地标</span>
            </div>
          </RouterLink>
          <RouterLink to="/mall" class="home-hub">
            <SkeletonImage
              class="home-hub-media"
              src="/design/images/5014bb9cd66ab39383dcfab1e6326c39.webp"
              alt=""
              eager
            />
            <div>
              <strong>非遗文创共创市集</strong>
              <span>文创与农产</span>
            </div>
          </RouterLink>
        </div>
      </SectionCard>
      <SectionCard title="今日推荐">
        <template #meta>
          <RouterLink to="/heritage" class="home-more"
            >更多 <img :src="designIcon('home', '5:02008')" alt=""
          /></RouterLink>
        </template>
        <div class="home-recommendations" data-design-node="5:01934">
          <AsyncState
            :loading="heritageLoading"
            :error="heritageError"
            :empty="!heritage.length"
            @retry="load"
            ><div class="recommendation-strip">
              <RouterLink
                v-for="entry in heritage"
                :key="entry.id"
                :to="'/heritage/' + entry.id"
                class="recommendation-card corner-card"
                ><SkeletonImage
                  class="recommendation-cover"
                  :src="entry.cover_url"
                  :alt="entry.title"
                />
                <h3>{{ entry.title }}</h3>
                <p>
                  {{ entry.era || categoryName(entry.category) }}
                </p></RouterLink
              >
            </div></AsyncState
          >
        </div>
      </SectionCard>
      <SectionCard title="修习进度" data-design-node="5:02040">
        <div class="home-growth">
          <button
            class="home-avatar"
            aria-label="打开个人中心"
            @click="session.token ? router.push('/profile') : requireSession()"
          >
            {{
              session.profile?.nickname?.slice(0, 1) ||
              (session.token ? "—" : "学")
            }}
          </button>
          <div class="home-growth-copy">
            <h3>
              {{
                session.profile?.nickname ||
                (session.token ? "账户资料暂未加载" : "小小学徒")
              }}
            </h3>
            <p>{{ levelLabel }}</p>
          </div>
        </div>
        <div class="home-energy-track">
          <i :style="{ width: energyPercent + '%' }" />
        </div>
        <p class="home-energy-caption">
          当前能量值
          {{ energy == null ? "—" : energy.toLocaleString() }}
          <template v-if="nextLevelTarget">
            / {{ nextLevelTarget.toLocaleString() }}
          </template>
          <template v-else-if="levelCode === 'LV3_CRAFTSMAN'">
            · 已达最高等级
          </template>
        </p>
        <div class="home-actions">
          <button
            class="home-checkin"
            :disabled="
              signing ||
              checkedIn === true ||
              (!!session.token && checkedIn == null)
            "
            @click="checkin"
          >
            {{
              signing
                ? "签到中…"
                : checkedIn
                  ? "今日已签到"
                  : session.token && checkedIn == null
                    ? summaryError
                      ? "签到状态未知"
                      : "正在核对…"
                    : "每日签到"
            }}</button
          ><RouterLink class="home-study" to="/courses"
            >学习打卡</RouterLink
          >
        </div>
        <div v-if="summaryError" class="home-account-error" role="alert">
          <p>账户状态暂未更新：{{ summaryError }}</p>
          <button
            class="home-retry"
            :disabled="summaryLoading || profileRetrying"
            @click="retryAccount"
          >
            {{ summaryLoading || profileRetrying ? "重试中…" : "重试账户状态" }}
          </button>
        </div>
      </SectionCard>
      <SectionCard title="非遗典藏 · 小课">
        <template #meta>
          <div class="home-age-tabs">
            <button
              :class="{ active: age === 'PRIMARY_LOW' }"
              :aria-pressed="age === 'PRIMARY_LOW'"
              @click="changeAge('PRIMARY_LOW')"
            >
              1-3年级</button
            ><button
              :class="{ active: age === 'PRIMARY_HIGH' }"
              :aria-pressed="age === 'PRIMARY_HIGH'"
              @click="changeAge('PRIMARY_HIGH')"
            >
              4-6年级
            </button>
          </div>
        </template>
        <div class="home-lessons" :class="{ 'is-loading': courseLoading }">
          <AsyncState
            :loading="courseLoading"
            :error="courseError"
            :empty="!courses.length"
            empty-text="当前分类暂无课程，试试其他分类吧"
            @retry="load"
            ><div class="home-course-list">
              <CourseCard
                v-for="course in courses"
                :key="course.id"
                :course="course"
                compact
              /></div
          ></AsyncState>
        </div>
      </SectionCard>
    </div>
  </div>
</template>
<style scoped>
.home-page {
  min-height: 100dvh;
  padding-bottom: 12px;
  background: #f5ede4;
  color: #2d1810;
}
.home-body {
  padding: 14px 16px 24px;
}
.home-heritage {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 64px;
  margin-bottom: 14px;
  padding: 16px 18px;
  border-radius: 14px;
  background: #8b1a1a;
  color: #f7ecdc;
  isolation: isolate;
}
.home-heritage:before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  border-radius: inherit;
  background: var(--entry-image) center/cover;
  opacity: 0.22;
}
.home-heritage h2 {
  font: 500 16px/1.4 var(--serif);
  letter-spacing: 2px;
  color: #f9f0e2;
}
.home-heritage > span {
  flex-shrink: 0;
  padding: 5px 12px;
  border: 1px solid rgba(232, 217, 168, 0.6);
  border-radius: 999px;
  color: #f0dfc0;
  font: 400 10px/1.4 var(--sans);
  letter-spacing: 1.5px;
}
.home-heritage:active {
  opacity: 0.92;
}
.home-categories {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
  padding-bottom: 2px;
  overflow-x: auto;
  scrollbar-width: none;
}
.home-categories::-webkit-scrollbar {
  display: none;
}
.home-categories button {
  flex-shrink: 0;
  height: 30px;
  padding: 0 14px;
  border: 1px solid rgba(200, 169, 110, 0.42);
  border-radius: 999px;
  background: #fffdf8;
  color: #5a3e36;
  font: 400 12px/1 var(--sans);
  letter-spacing: 0.5px;
  white-space: nowrap;
}
.home-categories button.active {
  border-color: transparent;
  background: #8b1a1a;
  color: #f6ead9;
  font-weight: 500;
}
.home-hubs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.home-hub {
  position: relative;
  height: 104px;
  overflow: hidden;
  border-radius: 10px;
  color: #fffdf8;
  box-shadow: 0 6px 16px rgba(76, 46, 26, 0.12);
  -webkit-tap-highlight-color: transparent;
}
.home-hub .home-hub-media {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  transition: transform 0.5s cubic-bezier(0.22, 0.61, 0.36, 1);
}
.home-hub:after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    rgba(24, 12, 8, 0.02) 18%,
    rgba(24, 12, 8, 0.76) 100%
  );
}
.home-hub > div {
  position: absolute;
  z-index: 1;
  right: 10px;
  bottom: 9px;
  left: 10px;
}
.home-hub strong {
  display: block;
  font: 500 13px/1.4 var(--serif);
  letter-spacing: 0.5px;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.35);
}
.home-hub > div span {
  display: block;
  margin-top: 2px;
  color: #f0dfc0;
  font: 400 10px/1.4 var(--sans);
}
.home-hub:active .home-hub-media {
  transform: scale(1.04);
}
.home-more {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  gap: 4px;
  color: #8a6125;
  font: 400 10px/1.4 var(--sans);
  letter-spacing: 0.5px;
}
.home-more img {
  width: 5px;
  height: 8.75px;
}
.home-recommendations {
  min-height: 130px;
}
.recommendation-card .recommendation-cover {
  width: 100%;
  height: 100px;
  border-radius: 14px 14px 0 0;
}
.home-growth {
  display: flex;
  align-items: center;
  gap: 12px;
}
.home-avatar {
  width: 46px;
  height: 46px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  overflow: hidden;
  border: 2px solid rgba(200, 169, 110, 0.85);
  border-radius: 50%;
  background: #8b1a1a;
  color: #f6ead9;
  font: 400 20px/1 var(--serif);
  box-shadow: 0 4px 12px rgba(139, 26, 26, 0.16);
}
.home-growth-copy {
  min-width: 0;
}
.home-growth-copy h3 {
  color: #2d1810;
  font: 500 14px/1.5 var(--sans);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.home-growth-copy p {
  margin-top: 3px;
  color: #8a6125;
  font: 400 10px/1.4 var(--sans);
  letter-spacing: 1.2px;
}
.home-energy-track {
  height: 6px;
  margin-top: 14px;
  overflow: hidden;
  border-radius: 999px;
  background: #f0e3d6;
}
.home-energy-track i {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: #8b1a1a;
  transition: width 0.3s;
}
.home-energy-caption {
  margin-top: 8px;
  color: #8a7a70;
  font: 400 10px/1.5 var(--sans);
}
.home-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}
.home-checkin,
.home-study {
  display: grid;
  place-items: center;
  min-height: 42px;
  padding: 0 10px;
  border-radius: 10px;
  font: 500 13px/1.4 var(--sans);
  letter-spacing: 0.5px;
  text-align: center;
}
.home-checkin {
  border: 1px solid #8b1a1a;
  background: #8b1a1a;
  color: #fdf6ec;
}
.home-study {
  border: 1px solid rgba(138, 97, 37, 0.38);
  background: rgba(255, 255, 255, 0.45);
  color: #8a6125;
}
.home-account-error {
  margin-top: 12px;
  color: #8b1a1a;
  font-size: 11px;
  line-height: 1.7;
  overflow-wrap: anywhere;
}
.home-retry {
  margin-top: 4px;
  padding: 6px 0;
  color: #8b1a1a;
  font: 500 11px/1.4 var(--sans);
  text-decoration: underline;
  text-underline-offset: 3px;
}
.home-age-tabs {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}
.home-age-tabs button {
  height: 24px;
  padding: 0 6px;
  border: 1px solid rgba(200, 169, 110, 0.42);
  border-radius: 999px;
  background: rgba(255, 253, 248, 0.7);
  color: #8a7a70;
  font: 400 10px/1 var(--sans);
  white-space: nowrap;
}
.home-age-tabs button.active {
  border-color: rgba(139, 26, 26, 0.26);
  background: rgba(139, 26, 26, 0.08);
  color: #8b1a1a;
  font-weight: 500;
}
.home-lessons {
  min-height: 104px;
}
.home-lessons.is-loading {
  min-height: 200px;
}
.home-course-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.home-page :deep(.async-state) {
  padding: 6px 2px 2px;
}
@media (max-width: 350px) {
  .home-age-tabs button {
    padding: 0 4px;
  }
}
@media (max-width: 360px) {
  .home-hub {
    height: 96px;
  }
  .home-hub strong {
    font-size: 12px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .home-hub .home-hub-media,
  .home-energy-track i {
    transition: none;
  }
}
</style>
