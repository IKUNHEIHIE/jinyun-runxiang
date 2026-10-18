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
    <header
      class="map-hero"
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
      <button class="map-back" aria-label="返回上一页" @click="router.back()">
        <img :src="icon('40:10947')" alt="" />
      </button>
      <p class="hero-tag">津门非遗</p>
      <h1>行走的<br />美育地图</h1>
      <p class="hero-subtitle">打卡非遗地标，品味乡土风物</p>
      <RouterLink class="map-market-link" to="/mall"
        >探索市集<img :src="icon('5:04924')" alt=""
      /></RouterLink>
    </header>
    <div class="map-impact" data-design-node="5:04984">
      <article>
        <strong>{{
          summary ? Number(summary.creative_works).toLocaleString() : "—"
        }}</strong
        ><span>创意作品</span>
      </article>
      <article>
        <strong class="fund">{{
          summary ? "¥" + Number(summary.fund_total_yuan).toLocaleString() : "—"
        }}</strong
        ><span>公益助农</span>
      </article>
      <article>
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
        <article v-if="selected" class="selected-landmark">
          <img :src="mediaUrl(selected.cover_url)" :alt="selected.name" />
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
          class="district-card"
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
                <img :src="mediaUrl(product.cover_url)" :alt="product.name" />
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
            class="footprint-row"
            @click="selectRecord(record)"
          >
            <img :src="mediaUrl(record.cover_url)" alt="" /><span
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
            }}<button v-if="!session.token" @click="requireSession">
              登录
            </button>
          </p>
        </AsyncState>
        <div class="footprint-card">
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
      <footer class="map-thanks">
        <img :src="icon('5:02918')" alt="" />
        <h2>感谢您的每一份支持</h2>
        <p>
          您的每一次打卡、每一次浏览，都是对非遗文化的关注与传播。让我们携手同行，让传统文化被更多人看见。
        </p>
      </footer>
    </AsyncState>
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
  --map-green: #4a7c59;
  --map-red: #8b3a3a;
  --map-muted: #8a7e6b;
  background: #f5f0e8;
  color: var(--map-green);
  font-family: "Noto Serif SC", var(--serif);
}
.map-page h2,
.map-page h3,
.map-page h4,
.map-page p {
  margin: 0;
}
.map-hero {
  height: 352px;
  position: relative;
  overflow: hidden;
  background-size: cover;
  background-position: center;
  text-align: center;
  color: #f5f0e8;
}
.hero-wash {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
.hero-fade {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 96px;
}
.hero-cloud {
  position: absolute;
  pointer-events: none;
}
.hero-cloud-left {
  width: 96px;
  height: 96px;
  left: 16px;
  top: 64px;
  opacity: 0.3;
}
.hero-cloud-right {
  width: 80px;
  height: 80px;
  right: 16px;
  top: 80px;
  opacity: 0.2;
}
.map-back {
  position: absolute;
  left: 8px;
  top: 6px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: rgba(240, 230, 208, 0.8);
  z-index: 1;
}
.map-back img {
  width: 20px;
  height: 20px;
}
.map-hero .hero-tag {
  position: absolute;
  top: 46px;
  left: 50%;
  transform: translateX(-50%);
  border-radius: 16px;
  background: rgba(245, 240, 232, 0.8);
  color: var(--map-red);
  font:
    14px/20px "Ma Shan Zheng",
    cursive;
  padding: 6px 10px;
}
.map-hero h1 {
  position: absolute;
  top: 88px;
  width: 100%;
  margin: 0;
  font:
    48px/60px "Ma Shan Zheng",
    cursive;
  letter-spacing: 4.8px;
  text-shadow: 0 4px 3px #0002;
}
.map-hero .hero-subtitle {
  position: absolute;
  top: 220px;
  width: 100%;
  font:
    18px/28px "Source Han Sans",
    sans-serif;
  color: rgba(245, 240, 232, 0.9);
}
.map-market-link {
  position: absolute;
  top: 272px;
  left: 50%;
  transform: translateX(-50%);
  width: 172px;
  height: 48px;
  border-radius: 24px;
  background: var(--map-green);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}
.map-market-link img {
  width: 16px;
  height: 16px;
}
.map-impact {
  margin: 94px 20px 24px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}
.map-impact article {
  height: 118px;
  border-radius: 12px;
  background: #ffffffb3;
  text-align: center;
  padding: 17px 4px;
  box-shadow: 0 4px 8px #4a7c5914;
}
.map-impact strong {
  display: block;
  font:
    600 28px/35px "Source Han Sans",
    sans-serif;
  overflow-wrap: anywhere;
}
.map-impact .fund {
  color: var(--map-red);
}
.map-impact span {
  display: block;
  margin-top: 1px;
  color: var(--map-muted);
  font-size: 12px;
  line-height: 16px;
}
.map-section,
.district-section,
.footprint-section {
  margin: 0 20px;
}
.map-section {
  scroll-margin-top: calc(var(--safe-top) + 12px);
}
.map-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 28px;
  gap: 12px;
}
.map-heading h2 {
  padding-left: 12px;
  border-left: 4px solid var(--map-green);
  font:
    20px/28px "Source Han Sans",
    sans-serif;
}
.map-heading > span,
.map-heading > button {
  color: var(--map-muted);
  font-size: 12px;
  line-height: 16px;
}
.map-categories {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  margin: 16px 0;
  scrollbar-width: none;
}
.map-categories button {
  flex: none;
  height: 34px;
  min-width: 56px;
  padding: 7px 14px;
  border-radius: 17px;
  background: #fff9;
  color: var(--map-muted);
  font-size: 14px;
  line-height: 20px;
}
.map-categories .active {
  background: var(--map-green);
  color: #f5f0e8;
}
.heritage-map {
  position: relative;
  height: 260px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 16px #4a7c5914;
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
  padding: 8px 12px;
  border-radius: 8px;
  background: #ffffffe6;
  font-size: 12px;
  line-height: 16px;
}
.map-pin {
  position: absolute;
  transform: translate(-50%, -16px);
  display: flex;
  flex-direction: column;
  align-items: center;
  color: var(--pin-color);
  max-width: 112px;
}
.map-pin b {
  display: grid;
  place-items: center;
  height: 32px;
  width: 32px;
  background: var(--pin-color);
  border-radius: 50%;
  box-shadow: 0 2px 4px #0002;
}
.map-pin b img {
  width: 16px;
  height: 16px;
}
.map-pin span {
  background: var(--pin-color);
  color: #fff;
  border-radius: 4px;
  padding: 2px 8px;
  max-width: 112px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-size: 10px;
  line-height: 16px;
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
  background: #fffffff2;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  font: 24px/36px sans-serif;
  box-shadow: 0 2px 4px #0002;
}
.map-controls button:disabled {
  opacity: 1;
  color: #8a7e6b;
  background: #f5f0e8;
}
.map-empty {
  position: absolute;
  top: 40%;
  left: 10%;
  width: 80%;
  padding: 16px;
  background: #fffffff0;
  border-radius: 12px;
  text-align: center;
  font-size: 12px;
  line-height: 22px;
}
.map-empty button {
  color: var(--map-red);
  text-decoration: underline;
}
.map-caption {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
  margin: 8px 0 12px;
  color: var(--map-muted);
  font-size: 10px;
  line-height: 16px;
}
.map-caption button {
  color: var(--map-green);
  min-height: 32px;
  flex: none;
  font-size: 12px;
}
.map-location-error {
  color: var(--map-red);
  font-size: 12px;
  line-height: 20px;
  padding: 0 0 12px;
}
.selected-landmark {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border-radius: 16px;
  background: #ffffffcc;
  box-shadow: 0 4px 8px #4a7c5914;
}
.selected-landmark > img {
  width: 96px;
  height: 96px;
  border-radius: 12px;
  object-fit: cover;
  flex: none;
}
.selected-content {
  min-width: 0;
  flex: 1;
}
.selected-content h3 {
  font-size: 16px;
  line-height: 24px;
  font-weight: 600;
}
.selected-content h3 span {
  display: inline-block;
  font:
    12px/16px "Ma Shan Zheng",
    cursive;
  color: var(--map-red);
  margin-left: 4px;
}
.landmark-description {
  font-size: 12px;
  line-height: 16px;
  color: var(--map-muted);
  margin-top: 4px !important;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.landmark-address {
  font-size: 12px;
  line-height: 16px;
  color: #c4a882;
  margin-top: 8px !important;
}
.landmark-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}
.landmark-actions > * {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  min-height: 32px;
  padding: 6px 4px;
  border-radius: 8px;
  background: var(--map-green);
  color: #f5f0e8;
  font-size: 12px;
  line-height: 20px;
  white-space: nowrap;
}
.landmark-actions > a {
  background: var(--map-red);
}
.district-section {
  margin-top: 32px;
}
.district-intro {
  color: var(--map-muted);
  font-size: 12px;
  line-height: 16px;
  margin-bottom: 24px !important;
}
.district-card {
  display: flex;
  overflow: hidden;
  margin-bottom: 24px;
  border-radius: 16px;
  background: #fff9;
  box-shadow:
    0 4px 8px #4a7c5914,
    0 12px 24px #4a7c591f;
}
.district-photo {
  width: 40%;
  flex: none;
  position: relative;
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
  background: var(--map-green);
  color: #f5f0e8;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 17px;
}
.district-content {
  padding: 16px;
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.district-content > h3 {
  font:
    18px/28px "Source Han Sans",
    sans-serif;
}
.district-content > p {
  font-size: 12px;
  line-height: 16px;
  color: var(--map-muted);
}
.district-products {
  display: grid;
  gap: 8px;
  margin: 4px 0;
}
.district-product {
  display: flex;
  gap: 8px;
  align-items: center;
  min-height: 56px;
  background: rgba(232, 240, 224, 0.5);
  border-radius: 8px;
  padding: 8px;
  position: relative;
}
.district-product > img {
  height: 40px;
  width: 40px;
  border-radius: 4px;
  object-fit: cover;
  flex: none;
}
.district-product > div {
  min-width: 0;
  flex: 1;
  padding-right: 20px;
}
.district-product h4 {
  font-size: 11px;
  line-height: 16px;
  font-weight: 500;
  overflow-wrap: anywhere;
}
.district-product strong {
  font:
    600 14px/20px "Source Han Sans",
    sans-serif;
  color: var(--map-red);
}
.district-product > button {
  position: absolute;
  right: 6px;
  bottom: 10px;
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--map-green);
}
.district-product > button img {
  width: 12px;
  height: 12px;
}
.district-empty {
  min-height: 104px;
  display: grid;
  place-items: center;
  color: var(--map-muted);
  font-size: 12px;
}
.district-buy {
  min-height: 40px;
  border-radius: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  background: var(--map-green);
  color: #f5f0e8;
  font-size: 14px;
  line-height: 20px;
  margin-top: auto;
}
.district-buy img {
  width: 16px;
  height: 16px;
}
.footprint-section {
  margin-top: 48px;
}
.footprint-heading {
  font:
    20px/28px "Source Han Sans",
    sans-serif;
  margin-bottom: 20px !important;
}
.footprint-row {
  width: 100%;
  padding: 12px;
  background: #fff9;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  text-align: left;
}
.footprint-row > img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}
.footprint-row > span {
  flex: 1;
  min-width: 0;
}
.footprint-row strong {
  display: block;
  font-size: 14px;
  line-height: 20px;
  color: var(--map-red);
}
.footprint-row i {
  font-style: normal;
  color: var(--map-green);
}
.footprint-row small {
  display: block;
  font-size: 12px;
  line-height: 16px;
  margin-top: 4px;
  color: var(--map-muted);
}
.footprint-row b {
  flex: none;
  font:
    12px/16px "Ma Shan Zheng",
    cursive;
  color: var(--map-red);
}
.footprint-empty {
  font-size: 12px;
  line-height: 22px;
  padding: 16px 0;
  color: var(--map-muted);
}
.footprint-empty button {
  color: var(--map-red);
  margin-left: 12px;
}
.footprint-card {
  padding: 20px;
  border-radius: 16px;
  background: var(--map-green);
  color: #f5f0e8;
  margin-top: 16px;
}
.footprint-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.footprint-title h2 {
  font:
    18px/28px "Source Han Sans",
    sans-serif;
}
.footprint-title a {
  font-size: 12px;
  line-height: 16px;
  color: #f5f0e8b3;
}
.footprint-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin: 20px 0;
  text-align: center;
}
.footprint-stats strong {
  font:
    600 30px/36px "Source Han Sans",
    sans-serif;
  display: block;
}
.footprint-stats span {
  font-size: 12px;
  line-height: 16px;
  color: #f5f0e8b3;
}
.footprint-links {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}
.footprint-links button {
  display: flex;
  align-items: center;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  line-height: 17px;
}
.footprint-links .locked {
  color: #f5f0e8a6;
}
.footprint-links .locked img {
  opacity: 0.35;
  filter: grayscale(1);
}
.milestone-sheet {
  color: var(--map-green, #4a7c59);
}
.milestone-sheet > p {
  font-size: 14px;
  line-height: 24px;
}
.milestone-sheet .milestone-state {
  color: #8a7e6b;
  font-size: 12px;
}
.milestone-sheet .milestone-progress {
  margin-top: 20px;
}
.footprint-links span {
  height: 48px;
  width: 48px;
  border-radius: 50%;
  background: #ffffff33;
  display: grid;
  place-items: center;
}
.footprint-links img {
  height: 24px;
  width: 24px;
}
.season-section {
  margin-top: 40px;
}
.season-section > .map-heading {
  margin: 0 20px 24px;
}
.season-cards {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding: 0 20px 8px;
  scrollbar-width: none;
}
.season-cards > button {
  width: 256px;
  flex: none;
  border-radius: 16px;
  overflow: hidden;
  background: #ffffffb3;
  text-align: left;
  padding-bottom: 16px;
  border: 1px solid #c4a8824d;
}
.season-cards > button > div {
  height: 144px;
  position: relative;
}
.season-cards img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.season-cards span {
  position: absolute;
  left: 12px;
  top: 12px;
  color: #f5f0e8;
  background: var(--map-green);
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 17px;
}
.season-cards h3 {
  font-size: 16px;
  line-height: 24px;
  margin: 12px 16px 4px;
}
.season-cards p {
  color: var(--map-muted);
  font-size: 12px;
  line-height: 16px;
  margin: 0 16px;
}
.map-thanks {
  margin-top: 40px;
  padding: 24px 20px 32px;
  background: var(--map-green);
  color: #f5f0e8;
  text-align: center;
}
.map-thanks > img {
  width: 32px;
  height: 32px;
  display: block;
  margin: 0 auto 8px;
}
.map-thanks h2 {
  font:
    24px/32px "Ma Shan Zheng",
    cursive;
  margin-bottom: 16px;
}
.map-thanks p {
  font-size: 14px;
  line-height: 22.75px;
  color: #f5f0e8cc;
}
@media (max-width: 370px) {
  .district-content {
    padding: 12px;
  }
  .district-product {
    gap: 6px;
  }
  .district-product > img {
    width: 32px;
    height: 40px;
  }
  .selected-landmark {
    padding: 12px;
    gap: 10px;
  }
  .map-hero .hero-subtitle {
    font-size: 16px;
  }
}
</style>
