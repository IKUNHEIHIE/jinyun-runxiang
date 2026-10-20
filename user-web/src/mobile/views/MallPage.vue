<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  api,
  post,
  notify,
  requireSession,
  session,
  loadProfile,
} from "../api";
import { designImage, designIcon } from "../design";
import decorations from "../market-decorations.json";
import PageHeader from "../components/PageHeader.vue";
import AsyncState from "../components/AsyncState.vue";
import SectionCard from "../components/SectionCard.vue";
import SkeletonImage from "../components/SkeletonImage.vue";

const route = useRoute(),
  router = useRouter();
const products = ref<any[]>([]),
  creators = ref<any[]>([]),
  rewards = ref<any[]>([]);
const summary = ref<any>({}),
  loading = ref(true),
  error = ref("");
const category = ref(route.query.category === "agri" ? "农产特产" : "全部");
const categories = ["全部", "刺绣帆布包", "青铜复刻", "非遗伴手礼", "农产特产"];
const visibleCount = ref(4),
  productsSection = ref<HTMLElement>();
const showCoCreationInfo = ref(false);
const selectedProduct = ref<any>(),
  selectedReward = ref<any>(),
  sku = ref<number>();
const quantity = ref(1),
  busy = ref(false),
  checkoutError = ref(""),
  requestId = ref("");
const emptyReceiver = () => ({
  receiver_name: "",
  receiver_phone: "",
  receiver_address: "",
});
const receiver = ref(emptyReceiver());
let openedProduct = "",
  mounted = true,
  loadVersion = 0,
  checkoutVersion = 0;
const filtered = computed(() =>
  products.value.filter((product) => {
    const matchCategory =
      category.value === "全部" ||
      (category.value === "农产特产"
        ? product.category === "AGRI_PRODUCT"
        : category.value === "非遗伴手礼"
          ? /皮影|香囊|伴手礼/.test(product.name)
          : (product.name + product.category).includes(
              category.value.replace("复刻", "").replace("伴手礼", ""),
            ));
    return (
      matchCategory &&
      (!route.query.district ||
        product.origin_place?.includes(
          String(route.query.district).replace("区", ""),
        ))
    );
  }),
);
const visibleProducts = computed(() =>
  filtered.value.slice(0, visibleCount.value),
);
const fundPercent = computed(() =>
  summary.value.fund_goal_yuan
    ? Math.min(
        100,
        (summary.value.fund_total_yuan / summary.value.fund_goal_yuan) * 100,
      )
    : 0,
);
const total = computed(() =>
  selectedProduct.value
    ? (selectedProduct.value.skus.find((s: any) => s.id === sku.value)
        ?.price_yuan || 0) * quantity.value
    : 0,
);
const stats = computed(() => [
  {
    value: summary.value.creator_count ?? "—",
    label: "社区创作者",
    image: "5:7739",
    icon: "5:7742",
  },
  {
    value: money(summary.value.fund_total_yuan),
    label: "公益基金累计",
    image: "5:7714",
    icon: "5:7719",
  },
  {
    value: summary.value.creative_works ?? "—",
    label: "已过审作品",
    image: "5:7731",
    icon: "5:7736",
  },
]);
const fundUses = [
  {
    title: "美育基金",
    caption: "公益计提归集",
    image: "5:7850",
    icon: "5:7855",
  },
  {
    title: "奖学金",
    caption: "用途以公示为准",
    image: "5:7829",
    icon: "5:7834",
  },
  {
    title: "能量值兑换",
    caption: "能量兑换物资",
    image: "5:7867",
    icon: "5:7870",
  },
];
function money(value: number | null | undefined) {
  return value == null
    ? "—"
    : "¥" + Number(value).toLocaleString("zh-CN", { maximumFractionDigits: 2 });
}
function shapeStyle(shape: any) {
  return {
    left: shape.relativeX + "px",
    top: shape.relativeY + "px",
    width: shape.width + "px",
    height: shape.height + "px",
    background: shape.color,
    opacity: shape.opacity,
    borderRadius: shape.radius || "50%",
    transform:
      shape.rotate == null ? undefined : "rotate(" + shape.rotate + "deg)",
  };
}
function explore() {
  productsSection.value?.scrollIntoView({ behavior: "smooth", block: "start" });
}
function moreProducts() {
  visibleCount.value += 4;
}
function available(product: any) {
  return product.skus.some((s: any) => s.stock > 0);
}
async function load() {
  const version = ++loadVersion,
    token = session.token;
  loading.value = true;
  error.value = "";
  try {
    const [items, totals, exchangeItems, posts] = await Promise.all([
      api("/mall/products"),
      api("/mobile/market/summary"),
      api("/mobile/market/exchange-items"),
      api("/community/posts?sort=latest&pageSize=4"),
    ]);
    if (!mounted || version !== loadVersion || token !== session.token) return;
    products.value = items;
    summary.value = totals;
    rewards.value = exchangeItems;
    creators.value = posts.list;
  } catch (e) {
    if (mounted && version === loadVersion && token === session.token)
      error.value = (e as Error).message;
  } finally {
    if (mounted && version === loadVersion && token === session.token)
      loading.value = false;
  }
  if (mounted && version === loadVersion && token === session.token)
    openRequestedProduct();
}
function openRequestedProduct() {
  const target = String(route.query.product || "");
  if (
    !target ||
    target === openedProduct ||
    loading.value ||
    error.value ||
    busy.value
  )
    return;
  const product = products.value.find((p) => String(p.id) === target);
  if (!product) {
    openedProduct = target;
    notify("该商品暂未上架，请选择其他商品");
    return;
  }
  if (!requireSession()) return;
  openedProduct = target;
  buy(product);
  router.replace({ query: { ...route.query, product: undefined } });
}
function resetCheckout() {
  checkoutVersion++;
  selectedProduct.value = undefined;
  selectedReward.value = undefined;
  receiver.value = emptyReceiver();
  sku.value = undefined;
  requestId.value = "";
  checkoutError.value = "";
  busy.value = false;
}
function closeCheckout() {
  if (!busy.value) resetCheckout();
}
function buy(product: any) {
  if (busy.value || !requireSession()) return;
  resetCheckout();
  selectedProduct.value = product;
  sku.value = product.skus.find((s: any) => s.stock > 0)?.id;
  quantity.value = 1;
  requestId.value = crypto.randomUUID();
  receiver.value.receiver_name = session.profile?.nickname || "";
}
function redeem(reward: any) {
  if (busy.value || !requireSession()) return;
  resetCheckout();
  selectedReward.value = reward;
  requestId.value = crypto.randomUUID();
  receiver.value.receiver_name = session.profile?.nickname || "";
}
async function submit() {
  if (
    busy.value ||
    (!selectedProduct.value && !selectedReward.value) ||
    !requireSession()
  )
    return;
  const token = session.token,
    version = checkoutVersion,
    reward = selectedReward.value;
  const current = () =>
    mounted && token === session.token && version === checkoutVersion;
  const body = reward
    ? { request_id: requestId.value, item_id: reward.id, ...receiver.value }
    : {
        request_id: requestId.value,
        items: [
          {
            product_id: selectedProduct.value.id,
            sku_id: sku.value,
            quantity: Number(quantity.value),
          },
        ],
        ...receiver.value,
      };
  busy.value = true;
  checkoutError.value = "";
  try {
    await post(reward ? "/mobile/market/exchanges" : "/mall/orders", body);
    if (!current()) return;
    resetCheckout();
    if (reward) {
      notify("兑换申请已提交，等待平台安排发放");
      // A profile-refresh failure must not turn an accepted exchange into a failed submission.
      void loadProfile().catch(() => {});
      void load();
    } else {
      notify("订单已创建，尚未支付；公益金额将在付款确认后计入");
      router.push("/me/orders");
    }
  } catch (e) {
    if (current()) checkoutError.value = (e as Error).message;
  } finally {
    if (current()) busy.value = false;
  }
}
onMounted(load);
onUnmounted(() => {
  mounted = false;
  loadVersion++;
  resetCheckout();
});
watch(
  () => route.query.product,
  () => {
    openedProduct = "";
    openRequestedProduct();
  },
);
watch(
  () => route.query.category,
  (value) => {
    category.value = value === "agri" ? "农产特产" : "全部";
  },
);
watch(
  () => [category.value, route.query.district],
  () => {
    visibleCount.value = 4;
  },
);
watch(
  () => session.token,
  () => {
    resetCheckout();
    showCoCreationInfo.value = false;
    void load();
  },
  { flush: "sync" },
);
</script>
<template>
  <div class="market-page" data-design-node="5:7245" :data-page-ready="!loading">
    <PageHeader title="文创共创市集" subtitle="非遗文创 · 乡村风物" />
    <div class="market-body">
      <header class="market-hero corner-card" data-design-node="5:8152">
        <div
          class="hero-background"
          :style="{
            backgroundImage: 'url(' + designImage('layer-5-7245', '5:8209') + ')',
          }"
          aria-hidden="true"
        />
        <img
          class="hero-overlay"
          :src="designImage('layer-5-7245', '5:8185')"
          alt=""
        />
        <div class="hero-art" aria-hidden="true">
          <i
            v-for="shape in decorations.particles"
            :key="shape.id"
            class="hero-shape"
            :style="shapeStyle(shape)"
          />
          <div
            v-for="(wheat, index) in decorations.wheats"
            :key="index"
            class="hero-wheat"
            :class="'wheat-' + index"
          >
            <img
              :src="designIcon('layer-5-7245', index ? '5:8214' : '5:8190')"
              alt=""
            />
            <i
              v-for="shape in wheat"
              :key="shape.id"
              class="hero-shape"
              :style="shapeStyle(shape)"
            />
          </div>
          <img
            class="hero-detail detail-one"
            :src="designImage('layer-5-7245', '5:8275')"
            alt=""
          />
          <img
            class="hero-detail detail-two"
            :src="designImage('layer-5-7245', '5:8280')"
            alt=""
          />
        </div>
        <div class="hero-copy">
          <span class="market-eyebrow"><i />非遗文创 · 乡村风物市集</span>
          <h1>稻香非遗</h1>
          <h2>文创共创市集</h2>
          <p>文创与农产集中展示<br />公益计提以确认入账为准</p>
          <button class="market-explore" @click="explore">
            探索市集<img :src="designIcon('layer-5-7245', '5:8263')" alt="" />
          </button>
        </div>
        <button class="market-scroll" @click="explore">
          向下滑动<img :src="designIcon('layer-5-7245', '5:8175')" alt="" />
        </button>
      </header>
      <section
        class="market-stats"
        data-design-node="5:7695"
        aria-label="市集数据"
      >
        <article
          v-for="stat in stats"
          :key="stat.label"
          class="corner-card"
        >
          <span
            class="stat-icon"
            :style="{
              backgroundImage:
                'url(' + designImage('layer-5-7245', stat.image) + ')',
            }"
            ><img :src="designIcon('layer-5-7245', stat.icon)" alt=""
          /></span>
          <strong>{{ stat.value }}</strong
          ><span>{{ stat.label }}</span>
        </article>
      </section>
      <section class="market-creators" aria-label="社区创作 · 作品故事">
        <SectionCard title="社区创作 · 作品故事" data-design-node="5:7366">
          <template #meta>
            <RouterLink to="/community" class="panel-more"
              >查看全部<img :src="designIcon('layer-5-7245', '5:7387')" alt=""
            /></RouterLink>
          </template>
          <p class="panel-lead">来自社区分享的已过审作品</p>
          <div class="creator-stories" data-design-node="5:7388">
            <RouterLink
              v-for="creator in creators"
              :key="creator.id"
              :to="'/community/' + creator.id"
              class="creator-story"
            >
              <div class="creator-cover">
                <SkeletonImage
                  :src="creator.cover_url"
                  :alt="creator.title"
                /><span class="creator-tag">创作者故事</span>
              </div>
              <div class="creator-copy">
                <h3>{{ creator.title }}</h3>
                <p>创作者：{{ creator.author.nickname }}</p>
                <span class="creator-likes"
                  ><b>{{ creator.author.nickname.slice(0, 1) }}</b
                  >{{ creator.like_count ?? 0 }} 次点赞</span
                >
              </div>
            </RouterLink>
            <p v-if="!creators.length" class="creator-empty">
              {{
                loading
                  ? "正在寻找创作故事…"
                  : error
                    ? "创作故事暂未加载"
                    : "还没有公开作品，来分享你的创意吧"
              }}
            </p>
          </div>
        </SectionCard>
        <article
          class="co-creation corner-card"
          data-design-node="5:7607"
          :style="{
            backgroundImage: 'url(' + designImage('layer-5-7245', '5:7607') + ')',
          }"
        >
          <div class="co-creation-heading">
            <span
              :style="{
                backgroundImage:
                  'url(' + designImage('layer-5-7245', '5:7678') + ')',
              }"
              ><img :src="designIcon('layer-5-7245', '5:7683')" alt=""
            /></span>
            <div>
              <h3>创意 → 授权 → 生产</h3>
              <p>流程示意 · 授权与生产暂未开放</p>
            </div>
          </div>
          <div class="co-creation-steps">
            <RouterLink to="/ai-workshop"
              ><b>1</b><span>工坊创作</span></RouterLink
            >
            <button @click="showCoCreationInfo = true">
              <b>2</b><span>平台授权</span>
            </button>
            <button @click="showCoCreationInfo = true">
              <b>3</b><span>合作社生产</span>
            </button>
            <button @click="explore"><b>4</b><span>电商销售</span></button>
          </div>
        </article>
      </section>
      <section
        id="market-products"
        ref="productsSection"
        class="market-products"
        aria-label="非遗文创 · 农产特产"
      >
        <SectionCard title="非遗文创 · 农产特产" data-design-node="5:8129">
          <p class="panel-lead">商品信息与计提比例以页面公示为准</p>
          <div
            class="category-tabs"
            role="group"
            aria-label="商品分类"
            data-design-node="5:8108"
          >
            <button
              v-for="c in categories"
              :key="c"
              :class="{ active: category === c }"
              :aria-pressed="category === c"
              @click="category = c"
            >
              {{ c }}
            </button>
          </div>
          <button
            v-if="route.query.district"
            class="district-filter"
            @click="router.replace('/mall')"
          >
            {{ route.query.district }} · 查看所有地区
          </button>
          <AsyncState
            :loading="loading"
            :error="error"
            :empty="!filtered.length"
            empty-text="当前分类暂无在售商品，试试其他分类吧"
            @retry="load"
          >
            <div class="market-product-grid" data-design-node="5:7886">
              <article
                v-for="product in visibleProducts"
                :key="product.id"
                class="market-product corner-card"
              >
                <div class="product-cover-wrap">
                  <SkeletonImage
                    :src="product.cover_url"
                    :alt="product.name"
                  /><span class="product-tag">{{
                    product.category === "AGRI_PRODUCT"
                      ? "农产特产"
                      : product.origin_place || "非遗文创"
                  }}</span>
                </div>
                <div class="product-copy">
                  <h3>{{ product.name }}</h3>
                  <p class="product-story">{{ product.story }}</p>
                  <div class="product-purchase">
                    <strong>{{ money(product.starting_price_yuan) }}</strong
                    ><button
                      class="product-buy"
                      :disabled="!available(product)"
                      :aria-label="
                        (available(product) ? '选购' : '已售罄') + product.name
                      "
                      @click="buy(product)"
                    >
                      <img :src="designIcon('layer-5-7245', '5:8102')" alt="" />
                    </button>
                  </div>
                  <p class="fund-share">
                    <img
                      :src="designIcon('layer-5-7245', '5:8053')"
                      alt=""
                    />公益计提 {{ product.fund_rate_percent }}% · 以确认入账为准
                  </p>
                </div>
              </article>
            </div>
            <button
              v-if="visibleCount < filtered.length"
              class="market-more"
              data-design-node="5:8141"
              @click="moreProducts"
            >
              浏览更多文创商品<img
                :src="designIcon('layer-5-7245', '5:8146')"
                alt=""
              />
            </button>
          </AsyncState>
        </SectionCard>
      </section>
      <section
        class="market-fund corner-card"
        data-design-node="5:7753"
        aria-labelledby="fund-title"
      >
        <div class="fund-title">
          <span><img :src="designIcon('layer-5-7245', '5:7777')" alt="" /></span>
          <h2 id="fund-title">公益基金 · 入账公示</h2>
        </div>
        <p class="fund-description">
          基金累计来自已确认入账的公益计提；目标与用途以平台公示为准
        </p>
        <div class="fund-progress">
          <div>
            <span>乡村美育基金</span
            ><strong
              >{{ money(summary.fund_total_yuan)
              }}<template v-if="summary.fund_goal_yuan">
                / {{ money(summary.fund_goal_yuan) }}</template
              ></strong
            >
          </div>
          <div
            class="fund-track"
            role="progressbar"
            aria-label="美育基金目标进度"
            :aria-valuenow="fundPercent"
            aria-valuemin="0"
            aria-valuemax="100"
          >
            <i :style="{ width: fundPercent + '%' }" />
          </div>
          <p>
            {{
              summary.fund_goal_yuan
                ? fundPercent >= 100
                  ? "已达成目标"
                  : "还差 " +
                    money(summary.fund_goal_yuan - summary.fund_total_yuan) +
                    " 达成目标"
                : "目标待公布"
            }}
          </p>
        </div>
        <div class="fund-uses" aria-label="基金用途方向">
          <article v-for="use in fundUses" :key="use.title">
            <span
              :style="{
                backgroundImage:
                  'url(' + designImage('layer-5-7245', use.image) + ')',
              }"
              ><img :src="designIcon('layer-5-7245', use.icon)" alt=""
            /></span>
            <h3>{{ use.title }}</h3>
            <p>{{ use.caption }}</p>
          </article>
        </div>
      </section>
      <section
        class="market-exchange"
        data-design-node="5:7250"
        aria-label="能量值 · 爱心兑换"
      >
        <SectionCard title="能量值 · 爱心兑换">
          <template #meta>
            <span class="energy-balance"
              ><img
                :src="designIcon('layer-5-7245', '5:7354')"
                alt=""
              />我的能量：{{
                session.token && !session.profile
                  ? "—"
                  : session.profile?.energy_value || 0
              }}</span
            >
          </template>
          <div class="exchange-products">
            <article v-for="reward in rewards" :key="reward.id">
              <SkeletonImage
                :src="reward.cover_url"
                :alt="reward.name"
                class="exchange-cover"
              />
              <h3>{{ reward.name }}</h3>
              <div>
                <strong>{{ reward.energy_cost }}</strong
                ><button :disabled="reward.stock < 1" @click="redeem(reward)">
                  {{ reward.stock < 1 ? "缺货" : "兑换" }}
                </button>
              </div>
            </article>
            <p v-if="!rewards.length">
              {{
                loading
                  ? "兑换物资加载中…"
                  : error
                    ? "兑换物资暂未加载，请重试"
                    : "兑换物资准备中，继续学习积累能量吧"
              }}
            </p>
          </div>
        </SectionCard>
      </section>
      <footer
        class="market-thanks corner-card"
        data-design-node="5:7501"
        :style="{
          backgroundImage: 'url(' + designImage('layer-5-7245', '5:7563') + ')',
        }"
      >
        <span
          class="thanks-icon"
          :style="{
            backgroundImage:
              'url(' + designImage('layer-5-7245', '5:7508') + ')',
          }"
          ><img :src="designIcon('layer-5-7245', '5:7518')" alt=""
        /></span>
        <h2>感谢您的每一份支持</h2>
        <p>
          从稻田到指尖，从创意到现实<br />让非遗在新时代绽放，让美育在乡村生根<br />稻香非遗，因您而美好
        </p>
        <div class="thanks-stats">
          <span
            ><strong>{{ summary.creator_count ?? "—" }}</strong
            >社区创作者</span
          ><span
            ><strong>{{ money(summary.fund_total_yuan) }}</strong
            >累计入账</span
          ><span
            ><strong>{{ summary.creative_works ?? "—" }}</strong
            >已过审作品</span
          >
        </div>
      </footer>
      <nav class="market-records corner-card" aria-label="市集记录">
        <RouterLink to="/me/orders">查看我的订单 ›</RouterLink
        ><RouterLink to="/me/exchanges">查看兑换记录 ›</RouterLink>
      </nav>
    </div>
    <Teleport to="body"
      ><div
        v-if="showCoCreationInfo"
        class="sheet-overlay"
        @click.self="showCoCreationInfo = false"
      >
        <section
          class="auth-sheet corner-card"
          role="dialog"
          aria-modal="true"
          aria-labelledby="co-creation-info-title"
        >
          <button
            class="sheet-close"
            aria-label="关闭共创流程说明"
            @click="showCoCreationInfo = false"
          >
            ×
          </button>
          <h2 id="co-creation-info-title">共创流程说明</h2>
          <p>你可以在 AI 工坊创作并发布作品，也可以浏览和选购已上架商品。</p>
          <p>
            作品授权协议、合作社生产对接暂未开放。发布作品不代表已完成商业授权，也不会自动安排生产。
          </p>
          <RouterLink
            class="primary-button"
            to="/ai-workshop"
            @click="showCoCreationInfo = false"
            >前往 AI 工坊</RouterLink
          >
        </section>
      </div></Teleport
    >
    <Teleport to="body"
      ><div
        v-if="selectedProduct || selectedReward"
        class="sheet-overlay"
        @click.self="closeCheckout"
      >
        <section
          class="auth-sheet corner-card"
          role="dialog"
          aria-modal="true"
          aria-labelledby="checkout-title"
        >
          <button
            class="sheet-close"
            aria-label="关闭确认订单"
            @click="closeCheckout"
            :disabled="busy"
          >
            ×
          </button>
          <h2 id="checkout-title">
            {{ selectedReward ? "确认兑换" : "确认订单" }}
          </h2>
          <p class="subtle">
            {{ selectedReward?.name || selectedProduct?.name }}
          </p>
          <form @submit.prevent="submit">
            <fieldset :disabled="busy">
              <template v-if="selectedProduct"
                ><label
                  >商品规格<select v-model="sku" required>
                    <option
                      v-for="s in selectedProduct.skus"
                      :key="s.id"
                      :value="s.id"
                      :disabled="s.stock < 1"
                    >
                      {{ s.name }} · ¥{{ s.price_yuan }} · 库存{{ s.stock }}
                    </option>
                  </select></label
                ><label
                  >数量<input
                    v-model.number="quantity"
                    type="number"
                    min="1"
                    :max="
                      selectedProduct.skus.find((s: any) => s.id === sku)
                        ?.stock || 1
                    "
                    required /></label></template
              ><label
                >收件人<input
                  v-model.trim="receiver.receiver_name"
                  required
                  maxlength="64"
                  autocomplete="name" /></label
              ><label
                >联系电话<input
                  v-model.trim="receiver.receiver_phone"
                  type="tel"
                  required
                  minlength="5"
                  maxlength="32"
                  autocomplete="tel" /></label
              ><label
                >收件地址<textarea
                  v-model.trim="receiver.receiver_address"
                  required
                  maxlength="255"
                  autocomplete="street-address"
                />
              </label>
              <p v-if="selectedProduct" class="subtle">
                订单金额 ¥{{
                  total.toFixed(2)
                }}。提交后为待支付状态；当前尚未接入在线付款渠道。
              </p>
              <p v-else class="subtle">
                将扣除
                {{ selectedReward.energy_cost }}
                能量，物资由平台确认后安排发放。
              </p>
              <p v-if="checkoutError" class="form-error" role="alert">
                {{ checkoutError }}
              </p>
              <button class="primary-button" :disabled="busy">
                {{
                  busy
                    ? "提交中…"
                    : selectedReward
                      ? "确认兑换"
                      : "创建待支付订单"
                }}
              </button>
            </fieldset>
          </form>
        </section>
      </div></Teleport
    >
  </div>
</template>
<style scoped>
.market-page {
  min-height: 100dvh;
  padding-bottom: 12px;
  background: #f5ede4;
  color: #2d1810;
}
.market-body {
  padding: 14px 16px 24px;
}
.market-hero {
  position: relative;
  height: 252px;
  margin-bottom: 14px;
  overflow: hidden;
  border-radius: 14px;
  background: #6b2a2a;
  color: #f6ead9;
  isolation: isolate;
}
.market-hero::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 1;
  background: linear-gradient(
    100deg,
    rgba(45, 24, 16, 0.68) 10%,
    rgba(45, 24, 16, 0.24) 62%,
    rgba(45, 24, 16, 0.44)
  );
  pointer-events: none;
}
.hero-background,
.hero-overlay {
  position: absolute;
  inset: 0;
  z-index: 0;
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  object-fit: cover;
}
.hero-overlay {
  opacity: 0.45;
}
.hero-art {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 1;
  width: 375px;
  height: 694px;
  transform: scale(0.5);
  transform-origin: top right;
  opacity: 0.32;
  pointer-events: none;
}
.hero-shape {
  position: absolute;
  display: block;
}
.hero-wheat {
  position: absolute;
}
.wheat-0 {
  left: -32.54px;
  top: 395.69px;
  width: 176px;
  height: 256px;
}
.wheat-1 {
  left: 247px;
  top: 424px;
  width: 160px;
  height: 224px;
}
.hero-wheat > img {
  position: absolute;
  max-width: none;
}
.wheat-0 > img {
  left: 28.27px;
  top: 16.79px;
  width: 119.47px;
  height: 239.3px;
}
.wheat-1 > img {
  left: 27.73px;
  top: 14.69px;
  width: 104.53px;
  height: 209.39px;
}
.hero-detail {
  position: absolute;
}
.detail-one {
  left: 187px;
  top: 469.05px;
  width: 57.02px;
  height: 64.89px;
}
.detail-two {
  left: 256.02px;
  top: 477.18px;
  width: 48.89px;
  height: 56.76px;
}
.hero-copy {
  position: relative;
  z-index: 2;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  padding: 18px 18px 36px;
}
.market-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 20px;
  padding: 0 9px;
  border: 1px solid rgba(232, 217, 168, 0.45);
  border-radius: 999px;
  background: rgba(45, 24, 16, 0.26);
  color: #f0e2c6;
  font: 400 10px/1 var(--sans);
  letter-spacing: 1px;
  white-space: nowrap;
}
.market-eyebrow i {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #c8a96e;
}
.hero-copy h1 {
  margin: 10px 0 0;
  font: 500 30px/1.15 var(--serif);
  letter-spacing: 4px;
  color: #fff;
  text-shadow: 0 2px 10px rgba(30, 14, 8, 0.35);
}
.hero-copy h2 {
  margin: 4px 0 0;
  font: 400 13px/1.3 var(--serif);
  letter-spacing: 3px;
  color: #e8d9a8;
}
.hero-copy p {
  margin: 8px 0 0;
  font: 400 11px/1.75 var(--sans);
  letter-spacing: 0.4px;
  color: rgba(246, 234, 217, 0.84);
}
.market-explore {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 34px;
  margin-top: 14px;
  padding: 0 16px;
  border: 1px solid rgba(232, 217, 168, 0.5);
  border-radius: 999px;
  background: #8b1a1a;
  color: #f6ead9;
  font: 500 12px/1 var(--sans);
  letter-spacing: 2px;
  box-shadow: 0 4px 12px rgba(60, 20, 16, 0.25);
}
.market-explore img {
  width: 8px;
  height: 5px;
}
.market-scroll {
  position: absolute;
  right: 14px;
  bottom: 9px;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 2px;
  color: rgba(246, 234, 217, 0.66);
  font: 400 10px/1 var(--sans);
  letter-spacing: 1px;
}
.market-scroll img {
  width: 9px;
  height: 11px;
}
.market-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}
.market-stats article {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 0;
  padding: 13px 6px 11px;
  border: 1px solid rgba(200, 169, 110, 0.28);
  border-radius: 14px;
  text-align: center;
}
.stat-icon {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background-size: cover;
  background-position: center;
}
.stat-icon img {
  width: 13px;
  height: 13px;
  object-fit: contain;
}
.market-stats strong {
  margin-top: 8px;
  font: 500 17px/1.25 var(--serif);
  color: #8b1a1a;
  overflow-wrap: anywhere;
}
.market-stats article:nth-child(2) strong {
  color: #8a6125;
}
.market-stats article:nth-child(3) strong {
  color: #5a3e36;
}
.market-stats article > span:last-child {
  margin-top: 3px;
  font: 400 10px/1.4 var(--sans);
  letter-spacing: 0.5px;
  color: #8a7a70;
}
.market-creators {
  margin-bottom: 0;
}
.panel-more {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  flex-shrink: 0;
  color: #8b1a1a;
  font: 400 10px/1.4 var(--sans);
  letter-spacing: 0.5px;
  white-space: nowrap;
}
.panel-more img {
  width: 5px;
  height: 9px;
}
.panel-lead {
  margin: -4px 0 12px;
  font: 400 10px/1.6 var(--sans);
  letter-spacing: 0.6px;
  color: #8a7a70;
}
.creator-stories {
  display: flex;
  gap: 12px;
  margin: 0 -14px;
  padding: 0 14px 4px;
  overflow-x: auto;
  scrollbar-width: none;
  scroll-behavior: smooth;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
}
.creator-stories::-webkit-scrollbar {
  display: none;
}
.creator-story {
  flex: 0 0 152px;
  min-width: 0;
  overflow: hidden;
  border: 1px solid rgba(200, 169, 110, 0.32);
  border-radius: 12px;
  background: #fffdf8;
}
.creator-cover {
  position: relative;
  height: 108px;
  background: #f2e5cf;
}
.creator-cover .creator-tag {
  position: absolute;
  left: 8px;
  top: 8px;
  padding: 2px 7px;
  border-radius: 999px;
  background: rgba(45, 24, 16, 0.55);
  color: #f6ead9;
  font: 400 10px/1.5 var(--sans);
  letter-spacing: 0.4px;
}
.creator-copy {
  padding: 9px 10px 10px;
}
.creator-copy h3 {
  margin: 0;
  min-height: 38px;
  font: 500 13px/1.45 var(--sans);
  color: #2d1810;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  overflow-wrap: anywhere;
}
.creator-copy p {
  margin: 4px 0 0;
  font: 400 10px/1.5 var(--sans);
  color: #8a7a70;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.creator-likes {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 7px;
  font: 400 10px/1.4 var(--sans);
  color: #8a6125;
}
.creator-likes b {
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #f6ead9;
  color: #8b1a1a;
  font: 500 10px/1 var(--serif);
}
.creator-empty {
  flex: 1 0 100%;
  align-self: center;
  padding: 18px 4px;
  text-align: center;
  font: 400 11px/1.8 var(--sans);
  color: #8a7a70;
}
.co-creation {
  margin: 0 0 14px;
  padding: 16px 14px;
  border: 1px solid rgba(200, 169, 110, 0.3);
  border-radius: 14px;
  background-color: #fdf9f2;
  background-size: cover;
  background-position: center;
}
.co-creation-heading {
  display: flex;
  align-items: center;
  gap: 10px;
}
.co-creation-heading > span {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border: 1px solid rgba(200, 169, 110, 0.3);
  border-radius: 12px;
  background-size: cover;
  background-position: center;
}
.co-creation-heading img {
  width: 18px;
  height: 18px;
}
.co-creation-heading h3 {
  margin: 0;
  font: 500 14px/1.4 var(--serif);
  letter-spacing: 1px;
  color: #2d1810;
}
.co-creation-heading p {
  margin: 3px 0 0;
  font: 400 10px/1.5 var(--sans);
  color: #8a7a70;
}
.co-creation-steps {
  position: relative;
  display: flex;
  justify-content: space-between;
  gap: 4px;
  margin-top: 16px;
  padding-top: 2px;
}
.co-creation-steps::before {
  content: "";
  position: absolute;
  left: 16px;
  right: 16px;
  top: 19px;
  height: 1px;
  background: repeating-linear-gradient(
    90deg,
    rgba(200, 169, 110, 0.55) 0 4px,
    transparent 4px 8px
  );
}
.co-creation-steps > * {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  min-width: 44px;
  padding: 0;
  font: 400 10px/1.4 var(--sans);
  color: #5a3e36;
  white-space: nowrap;
}
.co-creation-steps b {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #8b1a1a;
  color: #f6ead9;
  font: 500 12px/1 var(--serif);
}
.co-creation-steps > :nth-child(2) b {
  background: #8a6125;
}
.co-creation-steps > :nth-child(3) b {
  background: #a0522d;
}
.market-products {
  scroll-margin-top: calc(var(--safe-top) + 12px);
}
.category-tabs {
  display: flex;
  gap: 8px;
  margin: 0 -14px 12px;
  padding: 0 14px 2px;
  overflow: auto;
  scrollbar-width: none;
  scroll-behavior: smooth;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
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
.district-filter {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  margin: 0 0 10px;
  padding: 0 10px;
  border: 1px solid rgba(200, 169, 110, 0.4);
  border-radius: 999px;
  background: #fffdf8;
  color: #8b1a1a;
  font: 400 10px/1 var(--sans);
  letter-spacing: 0.5px;
}
.market-product-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.market-product {
  content-visibility: auto;
  contain-intrinsic-size: auto 280px;
  border: 1px solid rgba(200, 169, 110, 0.34);
  border-radius: 14px;
  background: #fffdf8;
}
.product-cover-wrap {
  position: relative;
  height: 122px;
  overflow: hidden;
  border-radius: 13px 13px 0 0;
  background: #f2e5cf;
}
.product-cover-wrap > .product-tag {
  position: absolute;
  top: 8px;
  left: 8px;
  max-width: calc(100% - 16px);
  padding: 2px 7px;
  border-radius: 999px;
  background: rgba(139, 26, 26, 0.9);
  color: #f6ead9;
  font: 400 10px/1.5 var(--sans);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.product-copy {
  padding: 10px 10px 11px;
}
.product-copy h3 {
  margin: 0;
  min-height: 38px;
  font: 500 13px/1.45 var(--sans);
  color: #2d1810;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  overflow-wrap: anywhere;
}
.product-story {
  margin: 4px 0 0;
  min-height: 30px;
  font: 400 10px/1.5 var(--sans);
  color: #8a7a70;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.product-purchase {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  min-height: 30px;
  margin-top: 8px;
}
.product-purchase strong {
  font: 500 17px/1.2 var(--serif);
  color: #8b1a1a;
  overflow-wrap: anywhere;
}
.product-buy {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  border-radius: 50%;
  background: #8b1a1a;
}
.product-buy img {
  width: 10px;
  height: 10px;
}
.product-buy:disabled {
  opacity: 0.45;
}
.fund-share {
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 8px 0 0;
  padding-top: 7px;
  border-top: 1px solid rgba(200, 169, 110, 0.28);
  font: 400 10px/1.5 var(--sans);
  letter-spacing: 0.2px;
  color: #8a6125;
}
.fund-share img {
  width: 10px;
  height: 9px;
  flex-shrink: 0;
}
.market-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  min-height: 38px;
  margin-top: 12px;
  border: 1px solid rgba(200, 169, 110, 0.42);
  border-radius: 10px;
  background: #fffdf8;
  color: #8b1a1a;
  font: 500 12px/1 var(--sans);
  letter-spacing: 1px;
}
.market-more img {
  width: 8px;
  height: 8px;
}
.market-fund {
  position: relative;
  overflow: hidden;
  margin-bottom: 14px;
  padding: 16px 14px;
  border: 1px solid rgba(200, 169, 110, 0.3);
  border-radius: 14px;
  background: linear-gradient(150deg, #fdf9f2 0%, #f7ecdd 100%);
  color: #2d1810;
}
.market-fund::before {
  content: "";
  position: absolute;
  width: 120px;
  height: 120px;
  right: -60px;
  top: -60px;
  border-radius: 50%;
  background: rgba(200, 169, 110, 0.12);
  pointer-events: none;
}
.fund-title {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
}
.fund-title > span {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border: 1px solid rgba(200, 169, 110, 0.4);
  border-radius: 50%;
  background: #f6ead9;
}
.fund-title img {
  width: 16px;
  height: 16px;
}
.fund-title h2 {
  margin: 0;
  font: 500 16px/1.3 var(--serif);
  letter-spacing: 1.4px;
  color: #2d1810;
}
.fund-description {
  position: relative;
  margin: 10px 0 0;
  font: 400 11px/1.7 var(--sans);
  color: #8a7a70;
}
.fund-progress {
  position: relative;
  margin-top: 12px;
  padding: 12px;
  border: 1px solid rgba(200, 169, 110, 0.35);
  border-radius: 10px;
  background: #fffdf8;
}
.fund-progress > div:first-child {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.fund-progress span {
  font: 400 10px/1.4 var(--sans);
  color: #8a7a70;
}
.fund-progress strong {
  font: 500 12.5px/1.3 var(--serif);
  color: #8a6125;
  text-align: right;
}
.fund-track {
  height: 6px;
  margin-top: 10px;
  border-radius: 999px;
  background: #f0e2cf;
  overflow: hidden;
}
.fund-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #c8a96e, #8a6125);
}
.fund-progress > p {
  margin-top: 8px;
  font: 400 10px/1.5 var(--sans);
  color: #8a7a70;
}
.fund-uses {
  position: relative;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-top: 12px;
}
.fund-uses article {
  min-width: 0;
  padding: 12px 6px 10px;
  border: 1px solid rgba(200, 169, 110, 0.28);
  border-radius: 10px;
  background: #fffdf8;
  text-align: center;
}
.fund-uses article > span {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  margin: 0 auto;
  border-radius: 50%;
  background-size: cover;
  background-position: center;
}
.fund-uses img {
  width: 15px;
  height: 15px;
  object-fit: contain;
}
.fund-uses h3 {
  margin: 8px 0 0;
  font: 500 12px/1.4 var(--sans);
  color: #2d1810;
}
.fund-uses p {
  margin: 2px 0 0;
  font: 400 10px/1.45 var(--sans);
  color: #8a7a70;
}
.energy-balance {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  padding: 4px 8px;
  border: 1px solid rgba(139, 26, 26, 0.16);
  border-radius: 999px;
  background: rgba(139, 26, 26, 0.07);
  color: #8b1a1a;
  font: 500 10px/1 var(--sans);
  white-space: nowrap;
}
.energy-balance img {
  width: 10px;
  height: 10px;
}
.exchange-products {
  display: flex;
  gap: 12px;
  margin: 0 -14px;
  padding: 0 14px 4px;
  overflow-x: auto;
  scrollbar-width: none;
  scroll-behavior: smooth;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
}
.exchange-products::-webkit-scrollbar {
  display: none;
}
.exchange-products article {
  flex: 0 0 138px;
  min-width: 0;
  padding: 10px;
  border: 1px solid rgba(200, 169, 110, 0.32);
  border-radius: 12px;
  background: #fffdf8;
}
.exchange-products article > .exchange-cover {
  height: 88px;
  border-radius: 8px;
}
.exchange-products h3 {
  margin: 8px 0 0;
  min-height: 34px;
  font: 500 11.5px/1.5 var(--sans);
  color: #2d1810;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.exchange-products article > div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-top: 8px;
}
.exchange-products strong {
  font: 500 13px/1.2 var(--serif);
  color: #8a6125;
}
.exchange-products button {
  min-height: 26px;
  padding: 0 9px;
  border-radius: 999px;
  background: #8b1a1a;
  color: #f6ead9;
  font: 500 10px/1 var(--sans);
}
.exchange-products > p {
  flex: 0 0 100%;
  align-self: center;
  padding: 16px 0;
  text-align: center;
  font: 400 11px/1.8 var(--sans);
  color: #8a7a70;
}
.market-thanks {
  position: relative;
  overflow: hidden;
  margin-bottom: 14px;
  padding: 22px 16px 20px;
  border: 1px solid rgba(200, 169, 110, 0.3);
  border-radius: 14px;
  background-color: #fdf9f2;
  background-size: cover;
  background-position: center;
  text-align: center;
}
.market-thanks::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    rgba(253, 249, 242, 0.92),
    rgba(250, 241, 229, 0.82)
  );
  pointer-events: none;
}
.market-thanks > * {
  position: relative;
}
.thanks-icon {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  margin: 0 auto;
  border-radius: 50%;
  background-size: cover;
  background-position: center;
}
.thanks-icon img {
  width: 20px;
  height: 20px;
}
.market-thanks h2 {
  margin: 10px 0 0;
  font: 500 16px/1.4 var(--serif);
  letter-spacing: 1.5px;
  color: #2d1810;
}
.market-thanks > p {
  margin: 6px 0 0;
  font: 400 10px/1.8 var(--sans);
  letter-spacing: 0.4px;
  color: #8a7a70;
}
.thanks-stats {
  display: flex;
  justify-content: space-around;
  gap: 8px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid rgba(200, 169, 110, 0.28);
}
.thanks-stats span {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  font: 400 10px/1.4 var(--sans);
  color: #8a7a70;
}
.thanks-stats strong {
  font: 500 16px/1.3 var(--serif);
  color: #8b1a1a;
  overflow-wrap: anywhere;
}
.thanks-stats span:nth-child(2) strong {
  color: #8a6125;
}
.thanks-stats span:nth-child(3) strong {
  color: #5a3e36;
}
.market-records {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  overflow: hidden;
  border: 1px solid rgba(200, 169, 110, 0.3);
  border-radius: 14px;
  background: #fdf9f2;
}
.market-records a {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 46px;
  font: 400 12px/1.4 var(--sans);
  letter-spacing: 0.5px;
  color: #8b1a1a;
}
.market-records a + a {
  border-left: 1px solid rgba(200, 169, 110, 0.28);
}
.auth-sheet form {
  margin-top: 18px;
}
.auth-sheet fieldset {
  display: grid;
  gap: 14px;
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
}
.auth-sheet > p {
  margin-top: 14px;
  font: 400 13px/1.8 var(--sans);
  color: #8a7a70;
}
.auth-sheet > .primary-button {
  display: block;
  width: 100%;
  margin-top: 18px;
  border: 1px solid rgba(200, 169, 110, 0.5);
  border-radius: 10px;
  background: #8b1a1a;
  color: #f6ead9;
  font: 500 13px/1 var(--sans);
  text-align: center;
}
.market-page :deep(.async-state) {
  padding: 16px 4px 6px;
}
@media (max-width: 374px) {
  .hero-copy h1 {
    font-size: 27px;
  }
  .market-product-grid {
    gap: 10px;
  }
  .market-product {
    border-radius: 12px;
  }
  .creator-story {
    flex-basis: 142px;
  }
}
</style>
