<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api, post, session, requireSession, notify, mediaUrl, loadProfile } from "../api";
import { designImage, designIcon, categories, categoryName } from "../design";
import AsyncState from "../components/AsyncState.vue";
import CourseCard from "../components/CourseCard.vue";
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
    <header class="home-brand" data-design-node="5:02088">
      <span class="brand-corner left" /><span class="brand-corner right" />
      <h1>津韵润乡</h1>
      <p>INTANGIBLE HERITAGE</p>
      <div class="gold-divider"><i /><b /><i /></div>
    </header>
    <div class="home-content">
      <RouterLink
        to="/heritage"
        class="heritage-entry corner-card"
        :style="{
          '--entry-image': 'url(' + designImage('home', '5:02020') + ')',
        }"
        ><h2>非遗百科库</h2>
        <span>入口</span></RouterLink
      >
      <div
        class="category-tabs"
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
      <div class="home-hubs">
        <RouterLink to="/landmarks" class="home-hub home-hub-map">
          <img
            src="/design/images/562642870bc0dbb9f77e661a544aed0e.png"
            alt=""
            loading="lazy"
            decoding="async"
          />
          <div>
            <strong>行走的美育地图</strong>
            <span>打卡非遗地标</span>
          </div>
        </RouterLink>
        <RouterLink to="/mall" class="home-hub home-hub-mall">
          <img
            src="/design/images/5014bb9cd66ab39383dcfab1e6326c39.png"
            alt=""
            loading="lazy"
            decoding="async"
          />
          <div>
            <strong>非遗文创共创市集</strong>
            <span>文创与农产</span>
          </div>
        </RouterLink>
      </div>
      <div class="section-heading">
        <h2>今日推荐</h2>
        <RouterLink to="/heritage"
          >更多 <img :src="designIcon('home', '5:02008')" alt=""
        /></RouterLink>
      </div>
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
              ><img
                :src="mediaUrl(entry.cover_url)"
                :alt="entry.title"
                loading="lazy"
                decoding="async"
              />
              <h3>{{ entry.title }}</h3>
              <p>
                {{ entry.era || categoryName(entry.category) }}
              </p></RouterLink
            >
          </div></AsyncState
        >
      </div>
      <section class="growth-card corner-card" data-design-node="5:02040">
        <div class="growth-person">
          <button
            class="apprentice-avatar"
            aria-label="打开个人中心"
            @click="session.token ? router.push('/profile') : requireSession()"
          >
            {{
              session.profile?.nickname?.slice(0, 1) ||
              (session.token ? "—" : "学")
            }}
          </button>
          <div>
            <h3>
              {{
                session.profile?.nickname ||
                (session.token ? "账户资料暂未加载" : "小小学徒")
              }}
            </h3>
            <p>{{ levelLabel }}</p>
          </div>
        </div>
        <div class="progress-track">
          <i :style="{ width: energyPercent + '%' }" />
        </div>
        <p class="energy-caption">
          当前能量值
          {{ energy == null ? "—" : energy.toLocaleString() }}
          <template v-if="nextLevelTarget">
            / {{ nextLevelTarget.toLocaleString() }}
          </template>
          <template v-else-if="levelCode === 'LV3_CRAFTSMAN'">
            · 已达最高等级
          </template>
        </p>
        <div class="growth-actions">
          <button
            class="checkin-button"
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
          ><RouterLink class="primary-button" to="/courses"
            >学习打卡</RouterLink
          >
        </div>
        <div v-if="summaryError" class="home-account-error" role="alert">
          <p>账户状态暂未更新：{{ summaryError }}</p>
          <button
            class="text-button"
            :disabled="summaryLoading || profileRetrying"
            @click="retryAccount"
          >
            {{ summaryLoading || profileRetrying ? "重试中…" : "重试账户状态" }}
          </button>
        </div>
      </section>
      <div class="section-heading course-section-heading">
        <h2>非遗典藏 · 小课</h2>
        <span class="home-heading-dots" aria-hidden="true"
          ><i /><i /><i
        /></span>
        <div class="age-tabs">
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
      </div>
      <div class="gold-rule" />
      <div class="home-lessons" :class="{ 'is-loading': courseLoading }">
        <AsyncState
          :loading="courseLoading"
          :error="courseError"
          :empty="!courses.length"
          empty-text="当前分类暂无课程，试试其他分类吧"
          @retry="load"
          ><div class="compact-courses">
            <CourseCard
              v-for="course in courses"
              :key="course.id"
              :course="course"
              compact
            /></div
        ></AsyncState>
      </div>
    </div>
  </div>
</template>
<style scoped>
.home-brand {
  padding-top: 38px;
}
.home-brand > .gold-divider {
  margin-top: 16px;
}
.home-content > .section-heading > a {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.home-content > .section-heading > a img {
  width: 5.0009765625px;
  height: 8.7529296875px;
}
.home-hubs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin: 16px 0 4px;
}
.home-hub {
  position: relative;
  height: 112px;
  overflow: hidden;
  border-radius: 14px;
  color: #fffdf8;
  box-shadow: 0 8px 20px rgba(76, 46, 26, 0.14);
  -webkit-tap-highlight-color: transparent;
}
.home-hub img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s cubic-bezier(0.22, 0.61, 0.36, 1);
}
.home-hub::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    rgba(24, 12, 8, 0.04) 20%,
    rgba(24, 12, 8, 0.74) 100%
  );
}
.home-hub > div {
  position: absolute;
  z-index: 1;
  right: 12px;
  bottom: 10px;
  left: 12px;
}
.home-hub strong {
  display: block;
  font: 600 15px/21px var(--serif);
  letter-spacing: 0.5px;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.35);
}
.home-hub span {
  display: block;
  margin-top: 1px;
  font: 400 10px/15px var(--serif);
  opacity: 0.92;
}
.home-hub:active img {
  transform: scale(1.04);
}
@media (max-width: 360px) {
  .home-hub {
    height: 102px;
  }
  .home-hub strong {
    font-size: 13px;
    line-height: 19px;
  }
}
.home-recommendations {
  min-height: 170px;
}
.recommendation-card h3 {
  padding-top: 12px;
}
.recommendation-card p {
  padding-top: 3.5px;
}
.growth-person h3 {
  font-weight: 600;
}
.energy-caption {
  height: 16px;
  line-height: 16px;
}
.growth-card {
  min-height: 199px;
}
.course-section-heading {
  position: relative;
  gap: 8px;
}
.course-section-heading h2 {
  flex-shrink: 0;
  font-size: 16px;
}
.home-heading-dots {
  position: absolute;
  left: 128.25px;
  top: 12px;
  height: 6px;
  display: flex;
  gap: 4px;
  align-items: center;
}
.home-heading-dots i {
  flex-shrink: 0;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #c9a84c;
}
.home-heading-dots i:nth-child(2) {
  width: 4px;
  height: 4px;
}
.age-tabs {
  margin-left: auto;
}
.age-tabs button {
  width: 64.48px;
  padding: 0;
  color: #b85450;
}
.age-tabs button:first-child {
  width: 62.48px;
}
.age-tabs button.active {
  background: #b85450;
  border-color: #b85450;
  color: #faf5f0;
}
.home-lessons.is-loading {
  min-height: 452px;
}
.home-account-error {
  margin-top: 12px;
  color: #6c0a0a;
  font-size: 12px;
  line-height: 1.6;
  overflow-wrap: anywhere;
}
@media (max-width: 374px) {
  .home-heading-dots {
    display: none;
  }
  .course-section-heading h2 {
    font-size: 15px;
  }
}
</style>
