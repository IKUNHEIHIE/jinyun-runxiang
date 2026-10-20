<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  api,
  post,
  mediaUrl,
  notify,
  requireSession,
  session,
  loadProfile,
} from "../api";
import { designImage, designIcon } from "../design";
import { currentLocation, distanceMeters } from "../location";
import { formatDate } from "../dates";
import AsyncState from "../components/AsyncState.vue";
import PageHeader from "../components/PageHeader.vue";
interface Landmark {
  id: number;
  name: string;
  category: string;
  district: string;
  description: string;
  address: string;
  cover_url: string;
  latitude: number;
  longitude: number;
}
interface Product {
  id: number;
  name: string;
  category: string;
  origin_place: string;
  cover_url: string;
  starting_price_yuan: number;
}
interface Footprint {
  id: number;
  landmark_id: number;
  name: string;
  cover_url: string;
  in_geofence: boolean;
  geofence_status?: "ONSITE" | "CLOUD" | "UNCERTAIN";
  checked_at: string;
}
interface Milestone {
  code: string;
  name: string;
  description: string;
  current: number;
  target: number;
  completed: boolean;
}
const router = useRouter(),
  route = useRoute(),
  screen = "layer-40-11915";
const img = (node: string) => designImage(screen, node),
  icon = (node: string) => designIcon(screen, node);
const categories = ["全部", "皮影", "大鼓", "青铜", "采摘", "农家乐"];
const landmarks = ref<Landmark[]>([]),
  products = ref<Product[]>([]),
  summary = ref<any>();
const footprints = ref<{
  list: Footprint[];
  landmark_count?: number;
  agri_order_count?: number;
  milestones?: Milestone[];
}>({ list: [] });
const privateLoading = ref(false),
  privateError = ref(""),
  loading = ref(true),
  error = ref("");
const locationError = ref("");
const locating = ref(false),
  busy = ref<number>(),
  selectedId = ref<number>(),
  zoom = ref(1),
  mapSection = ref<HTMLElement>();
const position = ref<{ latitude: number; longitude: number }>();
let mounted = true,
  loadVersion = 0,
  privateVersion = 0;
const category = computed(() =>
  categories.includes(String(route.query.category))
    ? String(route.query.category)
    : "全部",
);
const filtered = computed(() =>
  category.value === "全部"
    ? landmarks.value
    : landmarks.value.filter((l) =>
        (l.category + l.name + l.description).includes(category.value),
      ),
);
const selected = computed(
  () =>
    filtered.value.find((l) => l.id === selectedId.value) ||
    filtered.value.find((l) => l.district === "蓟州区") ||
    filtered.value[0],
);
// The supplied bitmap is not geographically calibrated and has foreign labels.
// Keep its illustrative arrangement; actual distances/geofences use server coordinates.
const MAP_W = 670,
  MAP_H = 519,
  MAP_SCALE = 288.45143,
  MAP_XOFF = 133.33,
  MAP_YOFF = 7.34,
  MAP_MIN_LON = 116.6253512,
  MAP_MAX_LAT = 40.35637;
function pinStyle(landmark: Landmark, index: number) {
  const x = MAP_XOFF + (landmark.longitude - MAP_MIN_LON) * MAP_SCALE;
  const y = MAP_YOFF + (MAP_MAX_LAT - landmark.latitude) * MAP_SCALE;
  return {
    left: Math.max(4, Math.min(96, (x / MAP_W) * 100)) + "%",
    top: Math.max(6, Math.min(94, (y / MAP_H) * 100)) + "%",
    "--pin-color": ["#4A7C59", "#8B3A3A", "#C4A882"][index % 3],
  };
}
async function loadPrivate() {
  const version = ++privateVersion,
    token = session.token;
  footprints.value = { list: [] };
  privateError.value = "";
  if (!token) {
    privateLoading.value = false;
    return;
  }
  privateLoading.value = true;
  try {
    const result = await api("/mobile/me/footprints");
    if (mounted && version === privateVersion && token === session.token)
      footprints.value = result;
  } catch (e) {
    if (mounted && version === privateVersion && token === session.token)
      privateError.value = (e as Error).message;
  } finally {
    if (mounted && version === privateVersion) privateLoading.value = false;
  }
}
async function load() {
  const version = ++loadVersion;
  loading.value = true;
  error.value = "";
  try {
    const [places, impact, catalog] = await Promise.all([
      api<Landmark[]>("/activities/landmarks"),
      api("/mobile/market/summary"),
      api<Product[]>("/mall/products?category=AGRI_PRODUCT"),
    ]);
    if (!mounted || version !== loadVersion) return;
    landmarks.value = places;
    summary.value = impact;
    products.value = catalog;
  } catch (e) {
    if (mounted && version === loadVersion) error.value = (e as Error).message;
  } finally {
    if (mounted && version === loadVersion) loading.value = false;
  }
}
function chooseCategory(value: string, scroll = false) {
  router.replace({
    query: { ...route.query, category: value === "全部" ? undefined : value },
  });
  if (scroll)
    mapSection.value?.scrollIntoView({ behavior: "smooth", block: "start" });
}
function openAgriMarket() {
  router.push({ path: "/mall", query: { category: "agri" } });
}
function meters(l: Landmark) {
  return position.value
    ? distanceMeters(
        position.value.latitude,
        position.value.longitude,
        l.latitude,
        l.longitude,
      )
    : Infinity;
}
function distance(l: Landmark) {
  const m = meters(l);
  return m >= 1000 ? (m / 1000).toFixed(1) + "公里" : m + "米";
}
async function locate() {
  if (locating.value) return;
  locating.value = true;
  locationError.value = "";
  try {
    const result = await currentLocation();
    if (!mounted) return;
    position.value = {
      latitude: result.coords.latitude,
      longitude: result.coords.longitude,
    };
    const nearest = [...filtered.value].sort(
      (a, b) => meters(a) - meters(b),
    )[0];
    if (nearest) selectedId.value = nearest.id;
    notify("位置已更新，已选中当前分类中距离最近的基地");
  } catch (e) {
    if (mounted) locationError.value = (e as Error).message;
  } finally {
    if (mounted) locating.value = false;
  }
}
async function checkin(l: Landmark) {
  if (!requireSession() || busy.value) return;
  const token = session.token;
  busy.value = l.id;
  locationError.value = "";
  try {
    const geo = await currentLocation();
    if (!mounted || token !== session.token) return;
    position.value = {
      latitude: geo.coords.latitude,
      longitude: geo.coords.longitude,
    };
    const result = await post("/activities/checkin", {
      landmark_id: l.id,
      ...position.value,
      accuracy: geo.coords.accuracy,
    });
    if (!mounted || token !== session.token) return;
    notify(
      (result.geofence_status === "UNCERTAIN"
        ? "探访已记录，定位精度不足以确认现场打卡"
        : result.in_geofence
          ? "现场打卡成功"
          : "云端探访已记录") +
        "，" +
        (result.energy_added
          ? "获得" + result.energy_added + "能量"
          : "该基地奖励已领取"),
    );
    await Promise.all([loadPrivate(), loadProfile()]);
  } catch (e) {
    if (mounted && token === session.token)
      locationError.value = (e as Error).message;
  } finally {
    if (mounted) busy.value = undefined;
  }
}
const districts = [
  {
    name: "蓟州",
    title: "皮影工坊 × 山野珍味",
    subtitle: "打卡皮影基地，了解山野农产",
    photo: "5:03110",
    names: ["蓟州薄皮核桃", "燕山板栗"],
    plus: ["5:03139", "5:03164"],
    buy: "5:03173",
  },
  {
    name: "宝坻",
    title: "大鼓传承 × 红高粱",
    subtitle: "鼓声悠扬，酒香醇厚",
    photo: "5:03028",
    names: ["宝坻红高粱酒", "有机红高粱米"],
    plus: ["5:03005", "5:02989"],
    buy: "5:02970",
  },
  {
    name: "武清",
    title: "青铜铸造 × 农家时蔬",
    subtitle: "千年青铜技艺，了解农家时蔬",
    photo: "5:03401",
    names: ["武清农家蔬菜礼盒", "散养土鸡蛋30枚"],
    plus: ["5:03410", "5:03435"],
    buy: "5:03458",
  },
];
function districtProducts(d: (typeof districts)[number]) {
  const rank = (p: Product) => {
    const i = d.names.indexOf(p.name);
    return i < 0 ? 100 : i;
  };
  return products.value
    .filter((p) => p.origin_place?.includes(d.name))
    .sort((a, b) => rank(a) - rank(b))
    .slice(0, 2);
}
function buy(p: Product) {
  router.push({ path: "/mall", query: { product: p.id } });
}
const recent = computed(() => footprints.value.list.slice(0, 2));
function selectRecord(record: Footprint) {
  router.replace({ query: {} });
  selectedId.value = record.landmark_id;
  mapSection.value?.scrollIntoView({ behavior: "smooth", block: "start" });
}
function personal(value?: number) {
  return !session.token || privateLoading.value || privateError.value
    ? "—"
    : (value || 0).toLocaleString();
}
const activeMilestone = ref<Milestone>();
const milestones = computed(() =>
  [
    { code: "FIRST_VISIT", name: "初识非遗", icon: "5:03493" },
    { code: "FIRST_ONSITE", name: "寻访匠人", icon: "5:03505" },
    { code: "FIRST_AGRI_PURCHASE", name: "品味乡土", icon: "5:03510" },
    { code: "ALL_ACTIVE_ONSITE", name: "非遗达人", icon: "5:03525" },
  ].map((item) => ({
    ...item,
    record: footprints.value.milestones?.find((m) => m.code === item.code),
  })),
);
function showMilestone(record?: Milestone) {
  if (!requireSession()) return;
  if (record) activeMilestone.value = record;
  else notify(privateError.value || "足迹进度尚未加载，请重试");
}
onMounted(() => {
  load();
  loadPrivate();
});
watch(
  () => session.token,
  () => {
    position.value = undefined;
    activeMilestone.value = undefined;
    loadPrivate();
  },
);
onUnmounted(() => {
  mounted = false;
  ++loadVersion;
  ++privateVersion;
});
</script>
<template>
  <div class="map-page" data-design-node="40:11915">
    <PageHeader title="行走的美育地图" subtitle="打卡非遗地标，品味乡土风物" />
    <div class="map-body">
      <header
        class="map-hero corner-card"
        data-design-node="5:04889"
        :style="{ backgroundImage: 'url(' + img('5:04905') + ')' }"
      >
        <img class="hero-wash" :src="img('5:04890')" alt="" /><img
          class="hero-fade"
          :src="img('5:04893')"
          alt=""
        />
        <img class="hero-cloud hero-cloud-left" :src="icon('5:04898')" alt="" />
        <img class="hero-cloud hero-cloud-right" :src="icon('5:04911')" alt="" />
        <p class="hero-tag">津门非遗</p>
        <h1>行走的<br />美育地图</h1>
        <p class="hero-subtitle">打卡非遗地标，品味乡土风物</p>
        <RouterLink class="map-market-link" to="/mall"
          >探索市集<img :src="icon('5:04924')" alt=""
        /></RouterLink>
      </header>
      <div class="map-impact" data-design-node="5:04984">
        <article class="corner-card">
          <strong>{{
            summary ? Number(summary.creative_works).toLocaleString() : "—"
          }}</strong
          ><span>创意作品</span>
        </article>
        <article class="corner-card">
          <strong class="fund">{{
            summary
              ? "¥" + Number(summary.fund_total_yuan).toLocaleString()
              : "—"
          }}</strong
          ><span>公益助农</span>
        </article>
        <article class="corner-card">
          <strong>{{
            summary ? Number(summary.student_count).toLocaleString() : "—"
          }}</strong
          ><span>在册学生</span>
        </article>
      </div>
      <AsyncState :loading="loading" :error="error" @retry="load">
        <section ref="mapSection" class="map-section">
          <div class="map-heading">
            <h2>非遗地图</h2>
            <span>探索 · 发现 · 传承</span>
          </div>
          <div class="map-categories" aria-label="基地分类">
            <button
              v-for="c in categories"
              :key="c"
              :aria-pressed="category === c"
              :class="{ active: category === c }"
              @click="chooseCategory(c)"
            >
              {{ c }}
            </button>
          </div>
          <div class="heritage-map">
            <div
              class="map-art"
              :style="{
                backgroundImage:
                  'url(/design/maps/tianjin-districts.svg)',
                transform: 'scale(' + zoom + ')',
              }"
            >
              <button
                v-for="(landmark, index) in filtered"
                :key="landmark.id"
                class="map-pin"
                :style="pinStyle(landmark, index)"
                :class="{ selected: selected?.id === landmark.id }"
                :aria-label="'选择基地：' + landmark.name"
                :aria-pressed="selected?.id === landmark.id"
                @click="selectedId = landmark.id"
              >
                <b
                  ><img
                    :src="icon(['5:03079', '5:03085', '5:03065'][index % 3])"
                    alt="" /></b
                ><span>{{ landmark.name }}</span>
              </button>
            </div>
            <span class="map-region">天津基地 · 分布示意</span>
            <div class="map-controls">
              <button
                :disabled="zoom >= 2"
                aria-label="放大地图示意"
                @click="zoom = Math.min(2, zoom + 0.25)"
              >
                +</button
              ><button
                :disabled="zoom <= 1"
                aria-label="缩小地图示意"
                @click="zoom = Math.max(1, zoom - 0.25)"
              >
                −
              </button>
            </div>
            <p v-if="!filtered.length" class="map-empty">
              当前分类暂无开放基地<br /><button @click="chooseCategory('全部')">
                查看全部基地
              </button>
            </p>
          </div>
          <div class="map-caption">
            <span>底图为设计示意，距离按实时位置计算</span
            ><button :disabled="locating" @click="locate">
              {{ locating ? "定位中…" : "我的位置" }}
            </button>
          </div>
          <p v-if="locationError" class="map-location-error" role="alert">
            {{ locationError }}
          </p>
          <article v-if="selected" class="selected-landmark corner-card">
            <img
              :src="mediaUrl(selected.cover_url)"
              :alt="selected.name"
              loading="lazy"
              decoding="async"
            />
            <div class="selected-content">
              <h3>{{ selected.name }} <span>{{ selected.category }}</span></h3>
              <p class="landmark-description">{{ selected.description }}</p>
              <p class="landmark-address">
                {{ selected.district }} ·
                {{ position ? "距你" + distance(selected) : selected.category }}
              </p>
              <div class="landmark-actions">
                <button :disabled="!!busy" @click="checkin(selected)">
                  {{ busy === selected.id ? "打卡中…" : "去打卡" }}</button
                ><RouterLink
                  :to="{
                    path: '/mall',
                    query: { district: selected.district, category: 'agri' },
                  }"
                  >查看特产</RouterLink
                >
              </div>
            </div>
          </article>
        </section>
        <section class="district-section">
          <p class="district-intro">打卡非遗基地，查看地道农产</p>
          <article
            v-for="district in districts"
            :key="district.name"
            class="district-card corner-card"
          >
            <div class="district-photo">
              <img
                :src="img(district.photo)"
                :alt="district.name + '非遗文化示意图'"
              /><span>{{ district.name }}</span>
            </div>
            <div class="district-content">
              <h3>{{ district.title }}</h3>
              <p>{{ district.subtitle }}</p>
              <div class="district-products">
                <article
                  v-for="(product, index) in districtProducts(district)"
                  :key="product.id"
                  class="district-product"
                >
                  <img
                    :src="mediaUrl(product.cover_url)"
                    :alt="product.name"
                    loading="lazy"
                    decoding="async"
                  />
                  <div>
                    <h4>{{ product.name }}</h4>
                    <strong
                      >¥{{
                        Number(product.starting_price_yuan).toFixed(2)
                      }}</strong
                    >
                  </div>
                  <button
                    :aria-label="'查看' + product.name"
                    @click="buy(product)"
                  >
                    <img :src="icon(district.plus[index])" alt="" />
                  </button>
                </article>
                <p
                  v-if="!districtProducts(district).length"
                  class="district-empty"
                >
                  该地区暂无上架农产
                </p>
              </div>
              <RouterLink
                class="district-buy"
                :to="{
                  path: '/mall',
                  query: { district: district.name + '区', category: 'agri' },
                }"
                ><img :src="icon(district.buy)" alt="" />查看农产商品</RouterLink
              >
            </div>
          </article>
        </section>
        <section class="footprint-section">
          <h2 class="footprint-heading">打卡有礼，足迹成诗</h2>
          <AsyncState
            :loading="privateLoading"
            :error="privateError"
            @retry="loadPrivate"
          >
            <button
              v-for="record in recent"
              :key="record.id"
              class="footprint-row corner-card"
              @click="selectRecord(record)"
            >
              <img
                :src="mediaUrl(record.cover_url)"
                alt=""
                loading="lazy"
                decoding="async"
              /><span
                ><strong
                  >{{ session.profile?.nickname }}
                  <i
                    >{{ record.in_geofence ? "打卡了" : "探访了" }}
                    {{ record.name }}</i
                  ></strong
                ><small
                  >{{ formatDate(record.checked_at) }} · 我的探访记录</small
                ></span
              ><b>{{
                record.in_geofence
                  ? "已打卡"
                  : record.geofence_status === "UNCERTAIN"
                    ? "待确认"
                    : "云探访"
              }}</b>
            </button>
            <p v-if="!recent.length" class="footprint-empty">
              {{
                session.token
                  ? "还没有探访记录，选择基地开启第一站吧"
                  : "登录后查看自己的探访记录"
              }}<button v-if="!session.token" @click="requireSession()">
                登录
              </button>
            </p>
          </AsyncState>
          <div class="footprint-card corner-card">
            <div class="footprint-title">
              <h2>我的足迹</h2>
              <RouterLink to="/profile/walking"
                >{{
                  session.token
                    ? "已探访 " +
                      personal(footprints.landmark_count) +
                      "/" +
                      landmarks.length +
                      " 处"
                    : "登录记录足迹"
                }}
                ›</RouterLink
              >
            </div>
            <div class="footprint-stats">
              <article>
                <strong>{{ personal(footprints.landmark_count) }}</strong
                ><span>非遗探访</span>
              </article>
              <article>
                <strong>{{ personal(footprints.agri_order_count) }}</strong
                ><span>农产订单</span>
              </article>
              <article>
                <strong>{{ personal(session.profile?.energy_value) }}</strong
                ><span>能量</span>
              </article>
            </div>
            <nav class="footprint-links" aria-label="足迹成就">
              <button
                v-for="milestone in milestones"
                :key="milestone.code"
                :class="{ locked: !milestone.record?.completed }"
                :disabled="privateLoading"
                :aria-label="
                  milestone.name +
                  (milestone.record?.completed ? '，已达成' : '，未达成')
                "
                @click="showMilestone(milestone.record)"
              >
                <span><img :src="icon(milestone.icon)" alt="" /></span
                >{{ milestone.name }}
              </button>
            </nav>
          </div>
        </section>
        <section class="season-section">
          <div class="map-heading">
            <h2>主题推荐</h2>
            <button @click="openAgriMarket">查看更多 ›</button>
          </div>
          <div class="season-cards">
            <button @click="openAgriMarket">
              <div>
                <img :src="img('5:03205')" alt="田园风物示意图" /><span
                  >田园</span
                >
              </div>
              <h3>田园风物</h3>
              <p>查看乡村农产商品</p></button
            ><button @click="openAgriMarket">
              <div>
                <img :src="img('5:03210')" alt="农家风味示意图" /><span
                  >农家</span
                >
              </div>
              <h3>农家风味</h3>
              <p>查看农家米面、时蔬与山货</p>
            </button>
          </div>
        </section>
        <footer class="map-thanks corner-card">
          <img :src="icon('5:02918')" alt="" />
          <h2>感谢您的每一份支持</h2>
          <p>
            您的每一次打卡、每一次浏览，都是对非遗文化的关注与传播。让我们携手同行，让传统文化被更多人看见。
          </p>
        </footer>
      </AsyncState>
    </div>
    <Teleport to="body"
      ><div
        v-if="activeMilestone"
        class="sheet-overlay"
        @click.self="activeMilestone = undefined"
      >
        <section
          class="auth-sheet corner-card milestone-sheet"
          role="dialog"
          aria-modal="true"
          aria-labelledby="milestone-title"
        >
          <button
            class="sheet-close"
            aria-label="关闭成就进度"
            @click="activeMilestone = undefined"
          >
            ×
          </button>
          <p class="milestone-state">
            {{ activeMilestone.completed ? "已达成" : "未达成" }} · 足迹成就
          </p>
          <h2 id="milestone-title">{{ activeMilestone.name }}</h2>
          <p>{{ activeMilestone.description }}</p>
          <p class="milestone-progress">
            {{
              activeMilestone.target > 0
                ? "当前进度 " +
                  Math.min(activeMilestone.current, activeMilestone.target) +
                  " / " +
                  activeMilestone.target
                : "当前暂无开放基地"
            }}
          </p>
        </section>
      </div></Teleport
    >
  </div>
</template>
<style scoped>
.map-page {
  min-height: 100dvh;
  padding-bottom: 12px;
  background: #f5ede4;
  color: #2d1810;
  font-family: var(--sans);
}
.map-page h2,
.map-page h3,
.map-page h4,
.map-page p {
  margin: 0;
}
.map-body {
  padding: 14px 16px 24px;
}
.map-hero {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 188px;
  margin-bottom: 14px;
  padding: 18px 16px;
  overflow: hidden;
  border-radius: 14px;
  background-color: #6b2a2a;
  background-size: cover;
  background-position: center;
  color: #f6ead9;
  text-align: center;
}
.map-hero::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 0;
  background: linear-gradient(
    160deg,
    rgba(45, 24, 16, 0.62),
    rgba(45, 24, 16, 0.3) 58%,
    rgba(45, 24, 16, 0.52)
  );
  pointer-events: none;
}
.hero-wash,
.hero-fade {
  position: absolute;
  inset: 0;
  z-index: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.5;
  pointer-events: none;
}
.hero-fade {
  inset: auto 0 0;
  height: 70px;
}
.hero-cloud {
  position: absolute;
  z-index: 1;
  opacity: 0.28;
  pointer-events: none;
}
.hero-cloud-left {
  width: 64px;
  height: 64px;
  left: 6px;
  top: 6px;
}
.hero-cloud-right {
  width: 52px;
  height: 52px;
  right: 8px;
  top: 16px;
  opacity: 0.2;
}
.hero-tag {
  position: relative;
  z-index: 2;
  padding: 3px 10px;
  border: 1px solid rgba(232, 217, 168, 0.45);
  border-radius: 999px;
  background: rgba(45, 24, 16, 0.3);
  color: #e8d9a8;
  font: 400 10px/1.4 var(--sans);
  letter-spacing: 2px;
}
.map-hero h1 {
  position: relative;
  z-index: 2;
  margin-top: 8px;
  font: 500 24px/1.4 var(--serif);
  letter-spacing: 5px;
  color: #fff;
  text-shadow: 0 2px 10px rgba(30, 14, 8, 0.4);
}
.hero-subtitle {
  position: relative;
  z-index: 2;
  margin-top: 4px;
  font: 400 10.5px/1.6 var(--sans);
  letter-spacing: 1px;
  color: rgba(246, 234, 217, 0.85);
}
.map-market-link {
  position: relative;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 32px;
  margin-top: 12px;
  padding: 0 16px;
  border: 1px solid rgba(232, 217, 168, 0.5);
  border-radius: 999px;
  background: #8b1a1a;
  color: #f6ead9;
  font: 500 11px/1 var(--sans);
  letter-spacing: 2px;
  box-shadow: 0 4px 12px rgba(60, 20, 16, 0.25);
}
.map-market-link img {
  width: 12px;
  height: 12px;
}
.map-impact {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}
.map-impact article {
  min-width: 0;
  padding: 13px 4px 11px;
  border: 1px solid rgba(200, 169, 110, 0.28);
  border-radius: 14px;
  text-align: center;
}
.map-impact strong {
  display: block;
  font: 500 18px/1.3 var(--serif);
  color: #8b1a1a;
  overflow-wrap: anywhere;
}
.map-impact .fund {
  color: #8a6125;
}
.map-impact span {
  display: block;
  margin-top: 3px;
  font: 400 10px/1.4 var(--sans);
  letter-spacing: 0.5px;
  color: #8a7a70;
}
.map-section {
  scroll-margin-top: calc(var(--safe-top) + 12px);
}
.map-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 24px;
  margin-bottom: 12px;
}
.map-heading h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  font: 500 16px/1.3 var(--serif);
  letter-spacing: 1.6px;
  color: #2d1810;
}
.map-heading h2::before {
  content: "";
  width: 3px;
  height: 15px;
  border-radius: 2px;
  background: #8b1a1a;
}
.map-heading > span,
.map-heading > button {
  font: 400 10px/1.4 var(--sans);
  letter-spacing: 0.5px;
  color: #8a7a70;
}
.map-heading > button {
  color: #8b1a1a;
}
.map-categories {
  display: flex;
  gap: 8px;
  margin: 0 -16px 12px;
  padding: 0 16px 2px;
  overflow-x: auto;
  scrollbar-width: none;
  scroll-behavior: smooth;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
}
.map-categories::-webkit-scrollbar {
  display: none;
}
.map-categories button {
  flex: none;
  height: 30px;
  padding: 0 14px;
  border: 1px solid rgba(200, 169, 110, 0.42);
  border-radius: 999px;
  background: #fffdf8;
  color: #5a3e36;
  font: 400 12px/1 var(--sans);
  white-space: nowrap;
}
.map-categories .active {
  border-color: transparent;
  background: #8b1a1a;
  color: #f6ead9;
  font-weight: 500;
}
.heritage-map {
  position: relative;
  height: 260px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 20px rgba(70, 42, 26, 0.12);
}
.map-art {
  position: absolute;
  inset: 0;
  background-position: center;
  background-size: cover;
  transition: transform 0.2s;
}
.map-region {
  position: absolute;
  top: 12px;
  left: 12px;
  padding: 6px 10px;
  border: 1px solid rgba(200, 169, 110, 0.35);
  border-radius: 8px;
  background: rgba(255, 253, 248, 0.92);
  font: 400 10px/1.5 var(--sans);
  letter-spacing: 0.5px;
  color: #8a6125;
}
.map-pin {
  position: absolute;
  transform: translate(-50%, -16px);
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 112px;
  color: var(--pin-color);
}
.map-pin b {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--pin-color);
  box-shadow: 0 2px 4px #0002;
}
.map-pin b img {
  width: 16px;
  height: 16px;
}
.map-pin span {
  max-width: 112px;
  padding: 2px 8px;
  overflow: hidden;
  border-radius: 4px;
  background: var(--pin-color);
  color: #fff;
  font: 400 10px/16px var(--sans);
  white-space: nowrap;
  text-overflow: ellipsis;
}
.map-pin.selected b {
  outline: 4px solid #ffffff90;
}
.map-controls {
  position: absolute;
  right: 12px;
  bottom: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.map-controls button {
  width: 36px;
  height: 36px;
  border: 1px solid rgba(200, 169, 110, 0.35);
  border-radius: 8px;
  background: #fffdf8;
  color: #8b1a1a;
  font: 22px/34px sans-serif;
  box-shadow: 0 2px 4px #0002;
}
.map-controls button:disabled {
  opacity: 1;
  background: #f5ede4;
  color: #b9a48c;
}
.map-empty {
  position: absolute;
  top: 40%;
  left: 10%;
  width: 80%;
  padding: 14px;
  border: 1px solid rgba(200, 169, 110, 0.35);
  border-radius: 12px;
  background: rgba(255, 253, 248, 0.96);
  color: #5a3e36;
  text-align: center;
  font: 400 11px/1.8 var(--sans);
}
.map-empty button {
  color: #8b1a1a;
  text-decoration: underline;
}
.map-caption {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin: 8px 0 10px;
  font: 400 10px/1.5 var(--sans);
  color: #8a7a70;
}
.map-caption button {
  flex: none;
  min-height: 30px;
  padding: 0 12px;
  border: 1px solid rgba(139, 26, 26, 0.26);
  border-radius: 999px;
  background: #fffdf8;
  color: #8b1a1a;
  font: 500 10px/1 var(--sans);
  letter-spacing: 0.5px;
}
.map-location-error {
  padding: 0 0 10px;
  font: 400 10px/1.6 var(--sans);
  color: #8b1a1a;
}
.selected-landmark {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border: 1px solid rgba(200, 169, 110, 0.32);
  border-radius: 14px;
  background: #fdf9f2;
}
.selected-landmark > img {
  width: 88px;
  height: 88px;
  flex: none;
  border-radius: 10px;
  background: #f2e5cf;
  object-fit: cover;
}
.selected-content {
  flex: 1;
  min-width: 0;
}
.selected-content h3 {
  font: 500 14px/1.5 var(--sans);
  color: #2d1810;
}
.selected-content h3 span {
  display: inline-block;
  margin-left: 4px;
  padding: 1px 6px;
  border-radius: 999px;
  background: rgba(139, 26, 26, 0.08);
  color: #8b1a1a;
  font: 400 10px/1.5 var(--sans);
  vertical-align: 1px;
}
.landmark-description {
  margin-top: 4px !important;
  font: 400 10.5px/1.6 var(--sans);
  color: #8a7a70;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.landmark-address {
  margin-top: 6px !important;
  font: 400 10px/1.5 var(--sans);
  color: #8a6125;
}
.landmark-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}
.landmark-actions > * {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-height: 32px;
  padding: 0 8px;
  border-radius: 999px;
  font: 500 11px/1 var(--sans);
  letter-spacing: 1px;
  white-space: nowrap;
}
.landmark-actions > button {
  background: #8b1a1a;
  color: #f6ead9;
}
.landmark-actions > a {
  border: 1px solid rgba(139, 26, 26, 0.26);
  background: #fffdf8;
  color: #8b1a1a;
}
.district-section {
  margin-top: 14px;
}
.district-intro {
  margin-bottom: 10px !important;
  font: 400 10px/1.6 var(--sans);
  letter-spacing: 0.5px;
  color: #8a7a70;
}
.district-card {
  display: flex;
  margin-bottom: 12px;
  overflow: hidden;
  border: 1px solid rgba(200, 169, 110, 0.3);
  border-radius: 14px;
  background: #fdf9f2;
}
.district-photo {
  position: relative;
  width: 38%;
  flex: none;
  min-height: 190px;
  background: #f2e5cf;
}
.district-photo > img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.district-photo > span {
  position: absolute;
  left: 8px;
  top: 8px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(139, 26, 26, 0.9);
  color: #f6ead9;
  font: 400 10px/1.5 var(--serif);
  letter-spacing: 1px;
}
.district-content {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  padding: 12px;
}
.district-content > h3 {
  font: 500 14px/1.5 var(--serif);
  letter-spacing: 0.5px;
  color: #2d1810;
}
.district-content > p {
  font: 400 10px/1.5 var(--sans);
  color: #8a7a70;
}
.district-products {
  display: grid;
  gap: 6px;
  margin: 2px 0;
}
.district-product {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 48px;
  padding: 6px 8px;
  border: 1px solid rgba(200, 169, 110, 0.22);
  border-radius: 8px;
  background: rgba(255, 253, 248, 0.8);
}
.district-product > img {
  width: 34px;
  height: 34px;
  flex: none;
  border-radius: 6px;
  background: #f2e5cf;
  object-fit: cover;
}
.district-product > div {
  flex: 1;
  min-width: 0;
  padding-right: 18px;
}
.district-product h4 {
  font: 400 10px/1.45 var(--sans);
  color: #5a3e36;
  overflow-wrap: anywhere;
}
.district-product strong {
  font: 500 12px/1.4 var(--serif);
  color: #8b1a1a;
}
.district-product > button {
  position: absolute;
  right: 6px;
  bottom: 8px;
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #8b1a1a;
}
.district-product > button img {
  width: 10px;
  height: 10px;
}
.district-empty {
  display: grid;
  place-items: center;
  min-height: 48px;
  font: 400 10px/1.5 var(--sans);
  color: #8a7a70;
}
.district-buy {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 32px;
  margin-top: auto;
  border-radius: 999px;
  background: #8b1a1a;
  color: #f6ead9;
  font: 500 11px/1 var(--sans);
  letter-spacing: 1px;
}
.district-buy img {
  width: 12px;
  height: 12px;
}
.footprint-section {
  margin-top: 14px;
}
.footprint-heading {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px !important;
  font: 500 16px/1.3 var(--serif);
  letter-spacing: 1.6px;
  color: #2d1810;
}
.footprint-heading::before {
  content: "";
  width: 3px;
  height: 15px;
  border-radius: 2px;
  background: #8b1a1a;
}
.footprint-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  margin-bottom: 10px;
  padding: 11px 12px;
  border: 1px solid rgba(200, 169, 110, 0.3);
  border-radius: 14px;
  background: #fdf9f2;
  text-align: left;
}
.footprint-row > img {
  width: 36px;
  height: 36px;
  flex: none;
  border-radius: 50%;
  background: #f2e5cf;
  object-fit: cover;
}
.footprint-row > span {
  flex: 1;
  min-width: 0;
}
.footprint-row strong {
  display: block;
  font: 500 11.5px/1.5 var(--sans);
  color: #2d1810;
}
.footprint-row i {
  font-style: normal;
  color: #8b1a1a;
}
.footprint-row small {
  display: block;
  margin-top: 2px;
  font: 400 10px/1.5 var(--sans);
  color: #8a7a70;
}
.footprint-row > b {
  flex: none;
  padding: 2px 7px;
  border-radius: 999px;
  background: rgba(139, 26, 26, 0.08);
  color: #8b1a1a;
  font: 400 10px/1.5 var(--sans);
}
.footprint-empty {
  padding: 14px 2px;
  font: 400 10.5px/1.8 var(--sans);
  color: #8a7a70;
}
.footprint-empty button {
  margin-left: 8px;
  color: #8b1a1a;
  text-decoration: underline;
}
.footprint-card {
  margin-top: 12px;
  padding: 16px 14px;
  border: 1px solid rgba(200, 169, 110, 0.3);
  border-radius: 14px;
  background: #fdf9f2;
  color: #2d1810;
}
.footprint-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.footprint-title h2 {
  font: 500 16px/1.3 var(--serif);
  letter-spacing: 1.4px;
  color: #2d1810;
}
.footprint-title a {
  flex: none;
  font: 400 10px/1.4 var(--sans);
  color: #8b1a1a;
  white-space: nowrap;
}
.footprint-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin: 12px 0;
  padding: 10px 0;
  border-top: 1px solid rgba(200, 169, 110, 0.26);
  border-bottom: 1px solid rgba(200, 169, 110, 0.26);
  text-align: center;
}
.footprint-stats strong {
  display: block;
  font: 500 20px/1.3 var(--serif);
  color: #8b1a1a;
}
.footprint-stats article:nth-child(2) strong {
  color: #8a6125;
}
.footprint-stats span {
  font: 400 10px/1.4 var(--sans);
  color: #8a7a70;
}
.footprint-links {
  display: flex;
  justify-content: space-between;
  gap: 6px;
}
.footprint-links button {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font: 400 10px/1.3 var(--sans);
  color: #5a3e36;
}
.footprint-links .locked {
  color: #b9a48c;
}
.footprint-links span {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border: 1px solid rgba(200, 169, 110, 0.28);
  border-radius: 50%;
  background: #f6ead9;
}
.footprint-links img {
  width: 20px;
  height: 20px;
}
.footprint-links .locked img {
  opacity: 0.35;
  filter: grayscale(1);
}
.season-section {
  margin-top: 14px;
}
.season-cards {
  display: flex;
  gap: 12px;
  margin: 0 -16px;
  padding: 0 16px 4px;
  overflow-x: auto;
  scrollbar-width: none;
  scroll-behavior: smooth;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
}
.season-cards::-webkit-scrollbar {
  display: none;
}
.season-cards > button {
  flex: none;
  width: 206px;
  padding: 0 0 12px;
  overflow: hidden;
  border: 1px solid rgba(200, 169, 110, 0.3);
  border-radius: 14px;
  background: #fffdf8;
  text-align: left;
}
.season-cards > button > div {
  position: relative;
  height: 112px;
  background: #f2e5cf;
}
.season-cards img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.season-cards span {
  position: absolute;
  left: 10px;
  top: 10px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(139, 26, 26, 0.88);
  color: #f6ead9;
  font: 400 10px/1.5 var(--sans);
  letter-spacing: 1px;
}
.season-cards h3 {
  margin: 10px 12px 0;
  font: 500 13px/1.5 var(--sans);
  color: #2d1810;
}
.season-cards p {
  margin: 3px 12px 0;
  font: 400 10px/1.6 var(--sans);
  color: #8a7a70;
}
.map-thanks {
  margin: 14px 0 0;
  padding: 22px 16px;
  border: 1px solid rgba(200, 169, 110, 0.3);
  border-radius: 14px;
  background: #fdf9f2;
  color: #2d1810;
  text-align: center;
}
.map-thanks > img {
  width: 26px;
  height: 26px;
  margin: 0 auto 8px;
  opacity: 0.9;
}
.map-thanks h2 {
  margin-bottom: 8px;
  font: 500 16px/1.4 var(--serif);
  letter-spacing: 1.5px;
  color: #2d1810;
}
.map-thanks p {
  font: 400 10.5px/1.9 var(--sans);
  color: #8a7a70;
}
.milestone-sheet {
  color: #2d1810;
}
.milestone-sheet > p {
  font: 400 13px/1.8 var(--sans);
}
.milestone-sheet h2 {
  font: 500 20px/1.35 var(--serif);
  letter-spacing: 1.5px;
  color: #2d1810;
}
.milestone-sheet .milestone-state {
  color: #8a7a70;
  font-size: 10px;
  letter-spacing: 1px;
}
.milestone-sheet .milestone-progress {
  margin-top: 16px;
  color: #8b1a1a;
  font-size: 12px;
}
@media (max-width: 370px) {
  .district-content {
    padding: 10px;
  }
  .district-photo {
    width: 34%;
  }
  .map-hero h1 {
    font-size: 22px;
  }
  .selected-landmark {
    padding: 10px;
    gap: 10px;
  }
  .selected-landmark > img {
    width: 76px;
    height: 76px;
  }
}
</style>
