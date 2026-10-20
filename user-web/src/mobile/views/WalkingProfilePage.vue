<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import {
  api,
  post,
  put,
  session,
  mediaUrl,
  requireSession,
  notify,
  loadProfile,
} from "../api";
import { currentLocation } from "../location";
import { formatDate } from "../dates";
import { useRouter } from "vue-router";
import { designImage, designIcon } from "../design";
import AsyncState from "../components/AsyncState.vue";
import PageHeader from "../components/PageHeader.vue";
import SectionCard from "../components/SectionCard.vue";
const router = useRouter(),
  screen = "layer-40-07198";
const img = (node: string) => designImage(screen, node),
  icon = (node: string) => designIcon(screen, node);
const badgeNodes: Record<string, string> = {
  BADGE_COURSE_SHADOW_PUPPET: "40:08347",
  BADGE_COURSE_BRONZE: "40:08400",
  BADGE_COURSE_PAPER_CUTTING: "40:08446",
  BADGE_COURSE_EMBROIDERY: "40:08492",
};
function badgeImage(badge: any) {
  if (badgeNodes[badge.code]) return img(badgeNodes[badge.code]);
  if (badge.code === "BADGE_COURSE_CERAMICS")
    return designImage("layer-5-00420", "5:00934");
  return mediaUrl(badge.icon_url);
}
const loading = ref(true),
  dataReady = ref(false),
  walkControlsVisible = ref(false),
  badges = ref<any[]>([]),
  activeBadge = ref<any>(),
  historyVisible = ref(false),
  calendarNow = ref(Date.now()),
  loadedActiveDistance = ref(0);
let loadVersion = 0,
  loadedDay = "",
  calendarTicker: ReturnType<typeof setInterval> | undefined;
const walking = ref<any>({
    list: [],
    total_seconds: 0,
    total_distance_meters: 0,
  }),
  footprints = ref<any>({ list: [] }),
  summary = ref<any>({}),
  active = ref<any>(),
  seconds = ref(0),
  previousTodaySeconds = ref(0),
  running = ref(false),
  busy = ref(false),
  error = ref("");
let ticker: ReturnType<typeof setInterval> | undefined,
  lastTick = 0,
  lastReportSeconds = 0,
  reportInFlight = false,
  mounted = true,
  latestPosition:
    { latitude: number; longitude: number; accuracy: number } | undefined;
function schoolDay(value: string | number) {
  return new Date(value).toLocaleDateString("en-CA", {
    timeZone: "Asia/Shanghai",
  });
}
function recordDay(value: string) {
  return schoolDay(value.endsWith("Z") ? value : value + "Z");
}
const todayDay = computed(() => schoolDay(calendarNow.value));
const activeOldDay = computed(
  () => !!active.value && recordDay(active.value.started_at) !== todayDay.value,
);
const todaySeconds = computed(
  () =>
    (loadedDay === todayDay.value ? previousTodaySeconds.value : 0) +
    (active.value && !activeOldDay.value ? seconds.value : 0),
);
const minutes = computed(() => Math.floor(todaySeconds.value / 60));
const percent = computed(() =>
  Math.min(100, (todaySeconds.value / 3600) * 100),
);
const totalDistance = computed(() =>
  Math.max(
    0,
    walking.value.total_distance_meters -
      loadedActiveDistance.value +
      (active.value?.distance_meters ?? loadedActiveDistance.value),
  ),
);
const pathfinder = computed(() =>
  badges.value.find((b) => b.code === "BADGE_WALK_PATHFINDER"),
);
const remainingMinutes = computed(() =>
  Math.max(0, Math.ceil((3600 - todaySeconds.value) / 60)),
);
const today = computed(() => {
  try {
    const parts = new Intl.DateTimeFormat("zh-CN-u-ca-chinese", {
      year: "numeric",
      month: "long",
      day: "numeric",
      timeZone: "Asia/Shanghai",
    }).formatToParts(new Date(calendarNow.value));
    const part = (type: string) =>
      parts.find((p) => (p.type as string) === type)?.value || "";
    const day = Number(part("day")),
      digits = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"];
    const lunarDay =
      day <= 10
        ? "初" + digits[day]
        : day < 20
          ? "十" + digits[day - 10]
          : day === 20
            ? "二十"
            : day < 30
              ? "廿" + digits[day - 20]
              : "三十";
    if (!part("yearName") || !Number.isInteger(day) || day < 1 || day > 30)
      throw new Error("Calendar unavailable");
    return part("yearName") + "年" + part("month") + lunarDay;
  } catch {
    return formatDate(new Date(calendarNow.value).toISOString(), false);
  }
});
function count(value: number) {
  return loading.value || !dataReady.value
    ? "—"
    : Number(value || 0).toLocaleString();
}
function visitLabel(record: any) {
  return record.in_geofence
    ? "现场打卡"
    : record.geofence_status === "UNCERTAIN"
      ? "定位待确认"
      : "云端探访";
}
function editProfile() {
  router.push({ path: "/profile", query: { edit: "1" } });
}
const cacheKey = () => "jinyun-walk-" + session.profile?.id;
async function load() {
  const version = ++loadVersion,
    token = session.token;
  if (!token) {
    loading.value = false;
    return;
  }
  loading.value = true;
  dataReady.value = false;
  error.value = "";
  try {
    if (!session.profile?.id) await loadProfile();
    if (!mounted || version !== loadVersion || token !== session.token) return;
    const [walkData, footprintData, summaryData, badgeData] = await Promise.all(
      [
        api("/mobile/walks"),
        api("/mobile/me/footprints"),
        api("/mobile/me/summary"),
        api("/mobile/badges"),
      ],
    );
    if (!mounted || version !== loadVersion || token !== session.token) return;
    walking.value = walkData;
    footprints.value = footprintData;
    summary.value = summaryData;
    badges.value = badgeData;
    dataReady.value = true;
    calendarNow.value = Date.now();
    loadedDay = todayDay.value;
    active.value = walking.value.list.find((w: any) => w.status === "ACTIVE");
    loadedActiveDistance.value = active.value?.distance_meters || 0;
    previousTodaySeconds.value = Math.max(
      0,
      (walkData.today_seconds || 0) -
        (active.value && !activeOldDay.value ? active.value.active_seconds : 0),
    );
    seconds.value = active.value?.active_seconds || 0;
    try {
      const cached = JSON.parse(localStorage.getItem(cacheKey()) || "null");
      if (
        active.value &&
        cached?.id === active.value.id &&
        Number.isFinite(cached.seconds) &&
        cached.seconds >= 0 &&
        cached.seconds <= 86400
      )
        seconds.value = Math.max(seconds.value, cached.seconds);
    } catch {}
    if (activeOldDay.value)
      error.value =
        "已进入新的一天，请先结束并保存上一段研学，再开启今日研学。";
  } catch (e) {
    if (mounted && version === loadVersion && token === session.token)
      error.value = (e as Error).message;
  } finally {
    if (mounted && version === loadVersion) loading.value = false;
  }
}
async function report(completed = false, locate = false) {
  if (!active.value) return;
  const recordId = active.value.id,
    token = session.token;
  if (locate && running.value) {
    const position = await currentLocation();
    if (!mounted || token !== session.token || !running.value) return;
    latestPosition = {
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      accuracy: position.coords.accuracy,
    };
  }
  const result = await put("/mobile/walks/" + recordId, {
    active_seconds: seconds.value,
    ...latestPosition,
    completed,
  });
  if (!mounted || token !== session.token || active.value?.id !== recordId)
    return;
  if (completed) {
    localStorage.removeItem(cacheKey());
    active.value = undefined;
    await load();
  } else {
    active.value = result;
    if (result.badge_unlocked_code) {
      const freshBadges = await api("/mobile/badges");
      if (mounted && token === session.token) {
        badges.value = freshBadges;
        await loadProfile();
        notify("已解锁「探路者」徽章");
      }
    }
  }
}
async function start() {
  if (!requireSession() || busy.value || loading.value) return;
  calendarNow.value = Date.now();
  if (activeOldDay.value) {
    error.value = "请先结束并保存上一段研学，再开启今日研学。";
    return;
  }
  busy.value = true;
  error.value = "";
  try {
    const token = session.token;
    const position = await currentLocation();
    if (!mounted || token !== session.token) return;
    latestPosition = {
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      accuracy: position.coords.accuracy,
    };
    const result = await post("/mobile/walks");
    if (!mounted || token !== session.token) return;
    if (active.value?.id !== result.id) seconds.value = result.active_seconds;
    active.value = result;
    seconds.value = Math.max(seconds.value, result.active_seconds);
    running.value = true;
    lastTick = Date.now();
    lastReportSeconds = seconds.value;
    clearInterval(ticker);
    ticker = setInterval(() => {
      if (!running.value || !active.value || !session.token) return;
      const now = Date.now();
      calendarNow.value = now;
      if (activeOldDay.value) {
        clearInterval(ticker);
        running.value = false;
        error.value =
          "已进入新的一天，请先结束并保存上一段研学，再开启今日研学。";
        return;
      }
      const delta = Math.min(2, Math.floor((now - lastTick) / 1000));
      if (delta < 1) return;
      lastTick = now;
      seconds.value += delta;
      localStorage.setItem(
        cacheKey(),
        JSON.stringify({ id: active.value.id, seconds: seconds.value }),
      );
      if (seconds.value - lastReportSeconds >= 30 && !reportInFlight) {
        lastReportSeconds = seconds.value;
        reportInFlight = true;
        report(false, true)
          .catch((e) => {
            error.value = (e as Error).message;
          })
          .finally(() => {
            reportInFlight = false;
          });
      }
    }, 1000);
    await report(false, false);
  } catch (e) {
    error.value = (e as Error).message;
    running.value = false;
    clearInterval(ticker);
  } finally {
    busy.value = false;
  }
}
async function pause() {
  clearInterval(ticker);
  running.value = false;
  try {
    await report(false, false);
  } catch (e) {
    error.value = (e as Error).message;
  }
}
async function finish() {
  if (busy.value || !active.value) return;
  const token = session.token;
  error.value = "";
  clearInterval(ticker);
  running.value = false;
  busy.value = true;
  try {
    await report(true, false);
    if (mounted && token === session.token) notify("研学记录已保存");
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    busy.value = false;
  }
}
function visibility() {
  calendarNow.value = Date.now();
  if (document.hidden && running.value) pause();
  else if (!document.hidden && !running.value) load();
}
onMounted(() => {
  load();
  calendarTicker = setInterval(() => {
    calendarNow.value = Date.now();
  }, 15000);
  document.addEventListener("visibilitychange", visibility);
});
onUnmounted(() => {
  clearInterval(ticker);
  if (running.value) pause();
  mounted = false;
  ++loadVersion;
  clearInterval(calendarTicker);
  document.removeEventListener("visibilitychange", visibility);
});
watch(
  () => session.token,
  () => {
    clearInterval(ticker);
    running.value = false;
    active.value = undefined;
    latestPosition = undefined;
    seconds.value = 0;
    previousTodaySeconds.value = 0;
    walking.value = { list: [], total_seconds: 0, total_distance_meters: 0 };
    footprints.value = { list: [] };
    summary.value = {};
    badges.value = [];
    activeBadge.value = undefined;
    historyVisible.value = false;
    walkControlsVisible.value = false;
    dataReady.value = false;
    ++loadVersion;
    if (session.token) load();
  },
);
</script>
<template>
  <div class="walking-profile" data-design-node="40:07198">
    <PageHeader title="个人中心" subtitle="文化行者">
      <button
        class="walker-settings"
        aria-label="个人资料设置"
        @click="editProfile"
      >
        <img :src="icon('40:05893')" alt="" />
      </button>
    </PageHeader>
    <div class="walker-content">
      <section class="walker-identity corner-card">
        <button
          class="walking-avatar"
          aria-label="编辑个人资料"
          @click="editProfile"
        >
          <span
            ><img
              v-if="session.profile?.avatar_url"
              :src="mediaUrl(session.profile.avatar_url)"
              alt=""
            /><b v-else>{{
              session.profile?.nickname?.slice(0, 1) || "学"
            }}</b></span
          ><i><img :src="icon('40:05897')" alt="" /></i>
        </button>
        <h2>{{ session.profile?.nickname || "文化行者" }}</h2>
        <div class="walker-labels">
          <span><img :src="icon('40:05901')" alt="" />行走 · 非遗</span
          ><span><img :src="icon('40:05905')" alt="" />文化行者</span>
        </div>
        <div class="walking-counters">
          <button @click="historyVisible = true">
            <strong>{{ count(footprints.landmark_count) }}</strong
            ><span>足迹</span
            ><small
              >已探
              {{ loading ? "—" : (totalDistance / 1000).toFixed(2) }}km</small
            ></button
          ><RouterLink to="/me/collections"
            ><strong>{{ count(summary.collection_count) }}</strong
            ><span>收藏</span><small>非遗好物</small></RouterLink
          ><RouterLink to="/me/posts"
            ><strong>{{ count(summary.like_count) }}</strong
            ><span>获赞</span><small>知音共赏</small></RouterLink
          >
        </div>
      </section>
      <SectionCard title="今日行走">
        <template #meta>
          <span class="walker-lunar">{{ today }}</span>
        </template>
        <article
          v-if="dataReady"
          class="walk-card"
          role="button"
          tabindex="0"
          aria-label="管理今日研学"
          @click="walkControlsVisible = true"
          @keydown.enter="walkControlsVisible = true"
          @keydown.space.prevent="walkControlsVisible = true"
        >
          <div class="walk-card-top">
            <div>
              <h3>行走的美育地图</h3>
              <p>
                {{
                  activeOldDay
                    ? "昨日记录待保存"
                    : running
                      ? "进行中"
                      : active
                        ? "已暂停"
                        : "待开启"
                }}
              </p>
            </div>
            <strong>{{ Math.floor(percent) }}%</strong>
          </div>
          <p class="walk-progress-label">
            已行走 {{ minutes }} 分钟 · 目标 60 分钟
          </p>
          <div
            class="walk-track"
            role="progressbar"
            aria-label="今日研学目标"
            :aria-valuenow="Math.floor(percent)"
            :aria-valuemin="0"
            :aria-valuemax="100"
          >
            <i :style="{ width: percent + '%' }" />
          </div>
          <div class="walk-notes">
            <p>
              今日已打卡 {{ count(footprints.today_landmark_count) }} 处非遗点
            </p>
            <p v-if="!loading">
              {{
                pathfinder?.unlocked
                  ? "已获得「探路者」徽章"
                  : "再行走 " + remainingMinutes + " 分钟解锁「探路者」徽章"
              }}
            </p>
          </div>
          <p v-if="error" class="walk-error" role="alert">
            {{ error }}
          </p>
        </article>
        <AsyncState v-else :loading="loading" :error="error" @retry="load" />
      </SectionCard>
      <SectionCard title="探索天地">
        <div class="explore-cards">
          <RouterLink to="/landmarks"
            ><div class="explore-cover">
              <img :src="img('40:08092')" alt="研学地图文化示意图" /><img
                class="explore-overlay"
                :src="img('40:08115')"
                alt=""
              /><span><img :src="icon('40:05913')" alt="" /></span>
            </div>
            <h3>行走的美育地图</h3>
            <p>探寻非遗足迹，丈量文化之美</p></RouterLink
          ><RouterLink to="/mall"
            ><div class="explore-cover">
              <img :src="img('40:08117')" alt="文创市集文化示意图" /><img
                class="explore-overlay"
                :src="img('40:08201')"
                alt=""
              /><span><img :src="icon('40:05917')" alt="" /></span>
            </div>
            <h3>非遗文创共创市集</h3>
            <p>匠心手作，共创文化新生</p></RouterLink
          >
        </div>
      </SectionCard>
      <SectionCard title="所获徽章">
        <template #meta>
          <button
            class="badge-more"
            :disabled="loading || (!badges.length && !!error)"
            @click="
              historyVisible = false;
              activeBadge = { catalog: true };
            "
          >
            {{
              loading || (!badges.length && error)
                ? "—"
                : badges.filter((b) => b.unlocked).length +
                  " / " +
                  badges.length
            }}
            ›
          </button>
        </template>
        <AsyncState
          :loading="loading"
          :error="badges.length ? '' : error"
          :empty="!badges.length"
          empty-text="暂无开放徽章"
          @retry="load"
          ><div class="badge-grid">
            <button
              v-for="badge in badges"
              :key="badge.id"
              :class="{ locked: !badge.unlocked }"
              @click="activeBadge = badge"
            >
              <span><img :src="badgeImage(badge)" :alt="badge.name" /></span
              >{{ badge.name }}
            </button>
          </div></AsyncState
        >
      </SectionCard>
      <SectionCard title="我的服务">
        <div class="service-links">
          <RouterLink to="/me/reviews"
            ><span><img :src="icon('40:05945')" alt="" /></span>我的评价<img
              :src="icon('40:05949')"
              alt="" /></RouterLink
          ><RouterLink to="/me/feedback"
            ><span><img :src="icon('40:08880')" alt="" /></span>帮助与反馈<img
              :src="icon('40:08884')"
              alt=""
          /></RouterLink>
        </div>
      </SectionCard>
    </div>
    <Teleport to="body"
      ><div
        v-if="activeBadge || historyVisible || walkControlsVisible"
        class="sheet-overlay"
        @click.self="
          activeBadge = undefined;
          historyVisible = false;
          walkControlsVisible = false;
        "
      >
        <section
          class="auth-sheet corner-card walker-sheet"
          role="dialog"
          aria-modal="true"
          :aria-label="
            walkControlsVisible
              ? '管理今日研学'
              : historyVisible
                ? '我的足迹'
                : activeBadge?.catalog
                  ? '全部徽章'
                  : activeBadge?.name
          "
        >
          <button
            class="sheet-close"
            aria-label="关闭详情"
            @click="
              activeBadge = undefined;
              historyVisible = false;
              walkControlsVisible = false;
            "
          >
            ×
          </button>
          <template v-if="walkControlsVisible"
            ><h2>研学行走</h2>
            <p>今日已行走 {{ minutes }} 分钟 · 目标 60 分钟</p>
            <p v-if="error" class="walk-error" role="alert">
              {{ error }}
              <button v-if="!active && !running" @click="load">重新加载</button>
            </p>
            <div class="walk-actions">
              <button
                v-if="!running && !activeOldDay"
                :disabled="busy || loading"
                @click="start"
              >
                {{
                  busy ? "请稍候…" : active ? "继续研学" : "开始研学"
                }}</button
              ><button v-if="running" :disabled="busy" @click="pause">
                暂停研学</button
              ><button v-if="active" :disabled="busy" @click="finish">
                结束并保存
              </button>
            </div>
            <p class="location-note">
              仅在此页开始研学后记录位置；离开页面或切至后台会暂停。
            </p> </template
          ><template v-else-if="historyVisible"
            ><h2>我的足迹</h2>
            <p v-if="!footprints.list.length && !walking.list.length">
              还没有探访或研学记录
            </p>
            <article
              v-for="record in footprints.list"
              :key="'visit-' + record.id"
            >
              <h3>{{ record.name }}</h3>
              <p>
                {{ formatDate(record.checked_at) }} · {{ visitLabel(record) }}
              </p>
            </article>
            <article v-for="record in walking.list" :key="'walk-' + record.id">
              <h3>
                研学 {{ record.active_seconds }} 秒 ·
                {{ (record.distance_meters / 1000).toFixed(2) }}km
              </h3>
              <p>
                {{ formatDate(record.started_at) }} ·
                {{ record.status === "COMPLETED" ? "已保存" : "未结束" }}
              </p>
            </article></template
          >
          <template v-else-if="activeBadge?.catalog"
            ><h2>全部徽章</h2>
            <button
              v-for="badge in badges"
              :key="badge.id"
              class="catalog-badge"
              @click="activeBadge = badge"
            >
              <img :src="badgeImage(badge)" alt="" /><span
                >{{ badge.name
                }}<small>{{
                  badge.unlocked ? "已解锁" : "未解锁"
                }}</small></span
              >
            </button></template
          >
          <template v-else
            ><h2>{{ activeBadge?.name }}</h2>
            <p>{{ activeBadge?.description }}</p>
            <p>
              {{
                activeBadge?.unlocked
                  ? "已解锁 · " + formatDate(activeBadge.unlocked_at)
                  : "尚未解锁"
              }}
            </p>
            <template v-if="activeBadge?.course_progress">
              <p>
                已完成
                {{ activeBadge.course_progress.completed_courses ?? "—" }} /
                {{ activeBadge.course_progress.required_courses }} 门课程
              </p>
              <RouterLink
                v-if="activeBadge.course_progress.recommended_course_id"
                class="badge-course-link"
                :to="
                  '/courses/' +
                  activeBadge.course_progress.recommended_course_id
                "
                >{{ activeBadge.unlocked ? "重温课程" : "去学习" }}</RouterLink
              >
              <p v-else>此类课程尚未开放</p>
            </template></template
          >
        </section>
      </div></Teleport
    >
  </div>
</template>
<style scoped>
.walking-profile,
.walker-sheet {
  --walker-muted: #8a7a70;
  --walker-gold: #8a6125;
  --walker-red: #8b1a1a;
}
.walking-profile {
  min-height: 100dvh;
  padding-bottom: 12px;
  background: #f5ede4;
  color: #2d1810;
}
.walking-profile h2,
.walking-profile h3,
.walking-profile p {
  margin: 0;
  font-weight: 400;
}
.walker-settings {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(139, 105, 48, 0.18);
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.6);
}
.walker-settings img {
  width: 16px;
  height: 16px;
}
.walker-content {
  padding: 14px 16px 24px;
}
.walker-identity {
  margin-bottom: 14px;
  padding: 18px 16px 0;
  overflow: hidden;
  background: #fdf9f2;
  text-align: center;
}
.walking-avatar {
  position: relative;
  display: block;
  width: 86px;
  height: 86px;
  margin: 0 auto;
  padding: 4px;
  border: 2px solid rgba(200, 169, 110, 0.85);
  border-radius: 50%;
  background: #8b1a1a;
  box-shadow: 0 8px 20px rgba(139, 26, 26, 0.18);
}
.walking-avatar > span {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: 50%;
  background: #8b1a1a;
}
.walking-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.walking-avatar b {
  color: #f6ead9;
  font: 400 30px/1 var(--serif);
}
.walking-avatar i {
  position: absolute;
  right: 0;
  bottom: 2px;
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  border: 2px solid #fdf9f2;
  border-radius: 50%;
  background: #8b1a1a;
}
.walking-avatar i img {
  width: 10px;
  height: 10px;
}
.walker-identity > h2 {
  margin-top: 14px;
  color: #2d1810;
  font: 500 20px/1.4 var(--serif);
  letter-spacing: 2px;
}
.walker-labels {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 8px;
}
.walker-labels span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 11px;
  border: 1px solid rgba(200, 169, 110, 0.4);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.6);
  color: #8b1a1a;
  font: 400 10px/1.5 var(--sans);
  letter-spacing: 1px;
}
.walker-labels span:last-child {
  border-color: rgba(200, 169, 110, 0.5);
  background: rgba(200, 169, 110, 0.12);
  color: #8a6125;
}
.walker-labels img {
  width: 10px;
  height: 10px;
  opacity: 0.8;
}
.walking-counters {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 16px;
  padding: 12px 0 6px;
  border-top: 1px solid rgba(200, 169, 110, 0.28);
}
.walking-counters > * {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  min-width: 0;
  padding: 4px 2px 8px;
}
.walking-counters > * + * {
  border-left: 1px solid rgba(200, 169, 110, 0.2);
}
.walking-counters strong {
  color: #8b1a1a;
  font: 500 19px/1.3 var(--serif);
}
.walking-counters span {
  color: #8a7a70;
  font: 400 10px/1.4 var(--sans);
  letter-spacing: 1px;
}
.walking-counters small {
  color: #8a6125;
  font: 400 10px/1.4 var(--sans);
}
.walker-lunar {
  color: #8a7a70;
  font: 400 10px/1.4 var(--sans);
  letter-spacing: 0.5px;
  white-space: nowrap;
}
.walk-card {
  padding: 14px;
  border: 1px solid rgba(200, 169, 110, 0.28);
  border-radius: 12px;
  background: #fffdf8;
  cursor: pointer;
}
.walk-card:focus-visible {
  outline: 2px solid rgba(139, 26, 26, 0.4);
  outline-offset: 3px;
}
.walk-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}
.walk-card-top > div {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.walk-card-top h3 {
  color: #2d1810;
  font: 500 14px/1.5 var(--sans);
}
.walk-card-top p {
  flex-shrink: 0;
  padding: 2px 7px;
  border: 1px solid rgba(139, 26, 26, 0.2);
  border-radius: 999px;
  background: #fff0f0;
  color: #8b1a1a;
  font: 400 10px/1.5 var(--sans);
}
.walk-card-top > strong {
  flex-shrink: 0;
  color: #8b1a1a;
  font: 500 20px/1.2 var(--serif);
}
.walk-progress-label {
  margin-top: 6px;
  color: #8a7a70;
  font: 400 10px/1.5 var(--sans);
  letter-spacing: 0.5px;
}
.walk-track {
  height: 6px;
  margin-top: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: #f0e3d6;
}
.walk-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #c8a96e, #8b1a1a);
  transition: width 0.3s;
}
.walk-notes {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}
.walk-notes p {
  flex: 1;
  color: #8a7a70;
  font: 400 10px/1.6 var(--sans);
}
.walk-notes p:last-child {
  flex: 1.4;
  color: #8a6125;
}
.walk-error {
  margin-top: 10px;
  color: #8b1a1a;
  font: 400 11px/1.7 var(--sans);
}
.walk-error button {
  text-decoration: underline;
}
.explore-cards {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.explore-cards > a {
  display: block;
  overflow: hidden;
  border: 1px solid rgba(200, 169, 110, 0.28);
  border-radius: 12px;
  background: #fffdf8;
}
.explore-cards > a:active {
  background: #fbf4ea;
}
.explore-cover {
  position: relative;
  height: 112px;
  overflow: hidden;
}
.explore-cover > img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.explore-cover > span {
  position: absolute;
  left: 8px;
  top: 8px;
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: rgba(255, 253, 248, 0.9);
  box-shadow: 0 1px 4px rgba(60, 38, 24, 0.12);
}
.explore-cover > span img {
  width: 14px;
  height: 14px;
}
.explore-cards h3 {
  margin: 10px 10px 4px;
  color: #2d1810;
  font: 500 13px/1.5 var(--sans);
}
.explore-cards p {
  margin: 0 10px 12px;
  color: #8a7a70;
  font: 400 10px/1.5 var(--sans);
}
.badge-grid {
  display: flex;
  gap: 14px;
  overflow-x: auto;
  padding: 2px 2px 8px;
  scrollbar-width: none;
}
.badge-grid::-webkit-scrollbar {
  display: none;
}
.badge-grid button {
  flex: 0 0 64px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 7px;
  color: #5a3e36;
  font: 400 10px/1.5 var(--sans);
  letter-spacing: 0.5px;
  text-align: center;
}
.badge-grid span {
  position: relative;
  width: 64px;
  height: 64px;
  padding: 4px;
  border-radius: 50%;
  background: linear-gradient(135deg, #e8d9a8, #c8a96e);
  box-shadow: 0 4px 12px rgba(138, 97, 37, 0.16);
}
.badge-grid span::after {
  content: "";
  position: absolute;
  inset: 2px;
  border: 2px solid #fffdf8;
  border-radius: 50%;
}
.badge-grid img {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  object-fit: cover;
}
.badge-grid .locked {
  opacity: 0.45;
  filter: grayscale(1);
}
.badge-more {
  flex-shrink: 0;
  padding: 3px 0;
  color: #8a6125;
  font: 400 10px/1.4 var(--sans);
  letter-spacing: 1px;
}
.service-links {
  overflow: hidden;
  border-radius: 10px;
}
.service-links a {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 48px;
  padding: 0 2px;
  color: #2d1810;
  font: 400 14px/1.4 var(--sans);
}
.service-links a + a {
  border-top: 1px solid rgba(200, 169, 110, 0.2);
}
.service-links a > span {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: rgba(200, 169, 110, 0.16);
}
.service-links a > span img {
  width: 14px;
  height: 14px;
}
.service-links a > img {
  width: 12px;
  height: 12px;
  margin-left: auto;
  opacity: 0.55;
}
.walker-sheet {
  background: #fdf9f2;
  color: #2d1810;
}
.walker-sheet h2 {
  margin: 4px 0 10px;
  color: #2d1810;
  font: 500 20px/1.35 var(--serif);
  letter-spacing: 2px;
}
.walker-sheet > p,
.walker-sheet article p {
  margin-top: 8px;
  color: #5a3e36;
  font: 400 12px/1.8 var(--sans);
}
.walker-sheet .walk-error {
  color: #8b1a1a;
}
.walker-sheet article {
  padding: 12px 0;
  border-bottom: 1px solid rgba(200, 169, 110, 0.22);
}
.walker-sheet article h3 {
  color: #2d1810;
  font: 500 13px/1.7 var(--sans);
}
.walk-actions {
  display: flex;
  gap: 8px;
  margin-top: 14px;
}
.walk-actions button {
  flex: 1;
  min-height: 42px;
  padding: 8px 10px;
  border: 1px solid rgba(200, 169, 110, 0.5);
  border-radius: 10px;
  background: rgba(200, 169, 110, 0.14);
  color: #8a6125;
  font: 500 12px/1.4 var(--sans);
  letter-spacing: 1px;
}
.walk-actions button:last-child {
  border-color: #8b1a1a;
  background: #8b1a1a;
  color: #f6ead9;
}
.location-note {
  margin-top: 10px;
  color: #8a7a70;
  font: 400 10px/1.6 var(--sans);
}
.catalog-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 10px 0;
  text-align: left;
}
.catalog-badge img {
  width: 44px;
  height: 44px;
  object-fit: contain;
}
.catalog-badge > span {
  color: #2d1810;
  font: 500 13px/1.5 var(--sans);
}
.catalog-badge small {
  display: block;
  margin-top: 2px;
  color: #8a7a70;
  font: 400 10px/1.5 var(--sans);
}
.badge-course-link {
  display: grid;
  place-items: center;
  min-height: 42px;
  margin-top: 12px;
  border-radius: 10px;
  background: #8b1a1a;
  color: #f6ead9;
  font: 500 13px/1.4 var(--sans);
  letter-spacing: 1px;
}
</style>

