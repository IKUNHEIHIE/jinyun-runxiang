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
  <div
    class="walking-profile"
    data-design-node="40:07198"
    :style="{ backgroundImage: 'url(' + img('40:07200') + ')' }"
  >
    <header class="walker-header">
      <button aria-label="返回上一页" @click="router.back()">
        <img :src="icon('40:05889')" alt="" />
      </button>
      <h1>个人中心</h1>
      <button aria-label="个人资料设置" @click="editProfile">
        <img :src="icon('40:05893')" alt="" />
      </button>
    </header>
    <section class="walker-identity">
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
    <main class="walker-content">
      <section class="walking-today">
        <div class="walker-heading">
          <h2>今日行走</h2>
          <span>{{ today }}</span>
        </div>
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
      </section>
      <section class="walking-explore">
        <div class="walker-heading"><h2>探索天地</h2></div>
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
      </section>
      <section class="walking-badges">
        <div class="walker-heading">
          <h2>所获徽章</h2>
          <button
            @click="
              historyVisible = false;
              activeBadge = { catalog: true };
            "
          >
            {{
              loading
                ? "—"
                : badges.filter((b) => b.unlocked).length +
                  " / " +
                  badges.length
            }}
            ›
          </button>
        </div>
        <AsyncState
          :loading="loading"
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
      </section>
      <section class="walking-services">
        <div class="walker-heading"><h2>我的服务</h2></div>
        <div>
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
      </section>
    </main>
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
          class="auth-sheet walker-sheet"
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
  --walker-ink: #3f3830;
  --walker-green: #6b8e6b;
  --walker-muted: #9c8f7e;
}
.walking-profile {
  background-color: #d4d6c1;
  background-position: center top;
  background-size: 100% 420px;
  background-repeat: no-repeat;
  color: var(--walker-ink);
  font-family: "Noto Serif SC", serif;
  min-height: 1437px;
}
.walking-profile h1,
.walking-profile h2,
.walking-profile h3,
.walking-profile p {
  margin: 0;
  font-weight: 400;
}
.walker-header {
  height: 60px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 4px 20px 16px;
}
.walker-header h1 {
  font-size: 16px;
  line-height: 24px;
  letter-spacing: 0.6px;
  margin-top: 8px;
}
.walker-header button {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  background: #fff9;
  border-radius: 50%;
  box-shadow: 0 2px 8px #0000000f;
}
.walker-header img {
  width: 20px;
  height: 20px;
}
.walker-identity {
  padding: 8px 20px 24px;
  text-align: center;
  min-height: 329px;
}
.walking-avatar {
  width: 96px;
  height: 96px;
  position: relative;
  padding: 5px;
  background: linear-gradient(135deg, #a8c5a0 5%, #8fbc8f 50%, #6b8e6b 100%);
  border-radius: 50%;
  box-shadow: 0 8px 24px #8fbc8f4d;
  margin: auto;
  display: block;
}
.walking-avatar > span {
  width: 86px;
  height: 86px;
  border-radius: 50%;
  overflow: hidden;
  display: grid;
  place-items: center;
  background: #d4d6c1;
}
.walking-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.walking-avatar b {
  font-size: 36px;
  font-weight: 400;
  color: #556b55;
}
.walking-avatar i {
  position: absolute;
  bottom: 4px;
  right: 4px;
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #8fbc8f;
  border: 2.5px solid #fff;
  box-shadow: 0 1px 2px #0000000d;
}
.walking-avatar i img {
  width: 10px;
  height: 10px;
}
.walker-identity > h2 {
  font-size: 20px;
  line-height: 28px;
  letter-spacing: 0.6px;
  margin-top: 16px;
}
.walker-labels {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 8px;
  height: 30px;
}
.walker-labels span {
  display: flex;
  align-items: center;
  gap: 6px;
  border-radius: 15px;
  padding: 6px 12px;
  background: #ffffffb3;
  color: #556b55;
  font-size: 12px;
  line-height: 18px;
}
.walker-labels span:last-child {
  color: #8b6f47;
  background: #a88b5e1a;
  border: 1px solid #a88b5e33;
}
.walker-labels img {
  width: 10px;
  height: 10px;
}
.walking-counters {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 20px;
}
.walking-counters > * {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 99px;
  border-radius: 16px;
  background: #ffffffcc;
  border: 1px solid #e3ebde80;
  box-shadow: 0 4px 16px #0000000a;
  padding: 16px 3px;
}
.walking-counters strong {
  font-size: 20px;
  line-height: 28px;
  font-weight: 400;
  color: #556b55;
}
.walking-counters span {
  font-size: 11px;
  line-height: 16.5px;
  letter-spacing: 0.6px;
  color: var(--walker-muted);
  margin-top: 2px;
}
.walking-counters small {
  font-size: 10px;
  line-height: 15px;
  color: #b8ad9e;
  margin-top: 3px;
}
.walker-content {
  padding: 0 20px;
}
.walker-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  height: 24px;
  margin-bottom: 16px;
}
.walker-heading h2 {
  font-size: 16px;
  line-height: 24px;
  letter-spacing: 0.6px;
  padding-left: 12px;
  position: relative;
}
.walker-heading h2:before {
  content: "";
  position: absolute;
  left: 0;
  top: 2px;
  width: 4px;
  height: 20px;
  border-radius: 9px;
  background: linear-gradient(#8fbc8f, #a8c5a0);
}
.walker-heading > span,
.walker-heading > button {
  font-size: 12px;
  line-height: 16px;
  color: #b8ad9e;
}
.walk-card {
  cursor: pointer;
  padding: 20px;
  border-radius: 20px;
  background: #fff;
  box-shadow: 0 4px 20px #0000000d;
  border: 1px solid #e3ebde4d;
  min-height: 152px;
}
.walk-card:focus-visible {
  outline: 2px solid #6b8e6b;
  outline-offset: 3px;
}
.walk-card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.walk-card-top > div {
  display: flex;
  align-items: center;
  gap: 8px;
}
.walk-card-top h3 {
  font-size: 14px;
  line-height: 20px;
  letter-spacing: 0.6px;
}
.walk-card-top p {
  background: #e3ebde80;
  border-radius: 10px;
  color: #556b55;
  padding: 2px 7px;
  font-size: 10px;
  line-height: 15px;
}
.walk-card-top > strong {
  font-size: 18px;
  line-height: 28px;
  font-weight: 400;
  color: var(--walker-green);
}
.walk-progress-label {
  font-size: 12px;
  line-height: 16px;
  color: var(--walker-muted);
  margin-top: -4px !important;
}
.walk-track {
  height: 10px;
  border-radius: 9px;
  background: #e3ebde;
  overflow: hidden;
  margin-top: 16px;
}
.walk-track i {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #8fbc8f, #6b8e6b);
  border-radius: inherit;
}
.walk-notes {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}
.walk-notes p {
  font-size: 12px;
  line-height: 16px;
  flex: 1;
  color: var(--walker-muted);
}
.walk-notes p:last-child {
  flex: 1.6;
  color: var(--walker-green);
}
.walk-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}
.walk-actions button {
  flex: 1;
  min-height: 36px;
  border-radius: 12px;
  background: var(--walker-green);
  color: white;
  font-size: 12px;
  line-height: 20px;
  padding: 8px;
}
.walk-actions button + button {
  background: #e3ebde;
  color: #556b55;
}
.location-note {
  font-size: 10px;
  line-height: 16px;
  color: var(--walker-muted);
  margin-top: 8px !important;
}
.walk-error {
  font-size: 12px;
  line-height: 20px;
  color: #8b3a3a;
  margin-top: 12px !important;
}
.walk-error button {
  text-decoration: underline;
}
.walking-explore {
  min-height: 264px;
  margin-top: 24px;
}
.explore-cards {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.explore-cards > a {
  display: block;
  min-height: 220px;
  border-radius: 20px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 4px 20px #0000000d;
  border: 1px solid #e3ebde4d;
}
.explore-cover {
  height: 140px;
  position: relative;
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
  left: 12px;
  top: 12px;
  display: grid;
  place-items: center;
  height: 32px;
  width: 32px;
  border-radius: 50%;
  background: #ffffffe6;
  box-shadow: 0 1px 2px #0000000d;
}
.explore-cover > span img {
  width: 18px;
  height: 18px;
}
.explore-cards h3 {
  font-size: 14px;
  line-height: 20px;
  letter-spacing: 0.6px;
  margin: 12px 12px 4px;
}
.explore-cards p {
  font-size: 11px;
  line-height: 16px;
  letter-spacing: 0.6px;
  color: var(--walker-muted);
  margin: 0 12px 12px;
}
.walking-badges {
  min-height: 144px;
  margin-top: 20px;
}
.badge-grid {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 8px;
}
.badge-grid button {
  flex: 0 0 72px;
  display: flex;
  align-items: center;
  flex-direction: column;
  gap: 8px;
  font-size: 11px;
  line-height: 16.5px;
  letter-spacing: 0.6px;
  color: #5e5449;
}
.badge-grid span {
  position: relative;
  display: block;
  width: 72px;
  height: 72px;
  padding: 4px;
  border-radius: 50%;
  background: linear-gradient(135deg, #a8c5a0, #6b8e6b);
  box-shadow: 0 4px 12px #0000000f;
}
.badge-grid span::after {
  content: "";
  position: absolute;
  inset: 2px;
  border: 2px solid #fff;
  border-radius: 50%;
}
.badge-grid img {
  height: 64px;
  width: 64px;
  object-fit: cover;
  border-radius: 50%;
}
.badge-grid .locked {
  opacity: 0.45;
  filter: grayscale(1);
}
.badge-course-link {
  display: block;
  padding: 10px 16px;
  border-radius: 12px;
  background: #6b8e6b;
  color: white;
  text-align: center;
}
.walking-services {
  margin-top: 20px;
}
.walking-services > div:last-child {
  background: #fff;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 4px 20px #0000000d;
}
.walking-services a {
  min-height: 68px;
  padding: 16px 20px;
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 14px;
  line-height: 20px;
}
.walking-services a + a {
  border-top: 1px solid #e3ebde66;
}
.walking-services a > span {
  height: 36px;
  width: 36px;
  border-radius: 50%;
  background: #e3ebde80;
  display: grid;
  place-items: center;
}
.walking-services a > span img {
  height: 16px;
  width: 16px;
}
.walking-services a > img {
  margin-left: auto;
  height: 16px;
  width: 16px;
}
.walker-sheet {
  background: #f4f7f2;
  border-radius: 20px;
  color: #3f3830;
  position: relative;
}
.walker-sheet > p,
.walker-sheet article p {
  font-size: 12px;
  line-height: 20px;
  color: #6b8e6b;
  margin-top: 8px;
}
.walker-sheet article {
  padding: 16px 0;
  border-bottom: 1px solid #e3ebde;
}
.walker-sheet article h3 {
  font-size: 14px;
  line-height: 22px;
}
.catalog-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  text-align: left;
  width: 100%;
  padding: 12px 0;
}
.catalog-badge img {
  width: 48px;
  height: 48px;
  object-fit: contain;
}
.catalog-badge small {
  display: block;
  margin-top: 4px;
  color: #9c8f7e;
}
@media (max-width: 370px) {
  .badge-grid {
    gap: 10px;
  }
  .badge-grid span {
    width: 64px;
    height: 64px;
  }
  .badge-grid img {
    width: 56px;
    height: 56px;
  }
  .walk-card {
    padding: 16px;
  }
  .walk-card-top > div {
    gap: 4px;
  }
  .walk-card-top h3 {
    font-size: 13px;
  }
  .walker-labels {
    gap: 6px;
  }
  .walker-labels span {
    padding: 6px 10px;
  }
}
</style>
