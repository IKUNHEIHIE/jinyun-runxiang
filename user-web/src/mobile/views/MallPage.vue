<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
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
import decorations from "../market-decorations.json";
import PageHeader from "../components/PageHeader.vue";
import AsyncState from "../components/AsyncState.vue";

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
  <div class="market-page" data-design-node="5:7245">
    <header class="market-hero" data-design-node="5:8152">
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
      <PageHeader title="文创共创市集" class="market-header" />
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
        <p>
          文创与农产集中展示<br />公益计提以确认入账为准
        </p>
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
      <article v-for="stat in stats" :key="stat.label">
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
    <section class="market-creators" aria-labelledby="creators-title">
      <div class="section-heading market-inset" data-design-node="5:7366">
        <div>
          <h2 id="creators-title">社区创作 · 作品故事</h2>
          <p>来自社区分享的已过审作品</p>
        </div>
        <RouterLink to="/community"
          >查看全部<img :src="designIcon('layer-5-7245', '5:7387')" alt=""
        /></RouterLink>
      </div>
      <div class="creator-stories" data-design-node="5:7388">
        <RouterLink
          v-for="creator in creators"
          :key="creator.id"
          :to="'/community/' + creator.id"
          class="creator-story"
        >
          <div class="creator-cover">
            <img
              :src="mediaUrl(creator.cover_url)"
              :alt="creator.title"
              loading="lazy"
            /><span>创作者故事</span>
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
      <article
        class="co-creation market-inset"
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
      class="market-products market-inset"
      aria-labelledby="products-title"
    >
      <div class="section-heading" data-design-node="5:8129">
        <div>
          <h2 id="products-title">非遗文创 · 农产特产</h2>
          <p>商品信息与计提比例以页面公示为准</p>
        </div>
      </div>
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
            class="market-product"
          >
            <div class="product-cover-wrap">
              <img
                :src="mediaUrl(product.cover_url)"
                :alt="product.name"
                loading="lazy"
              /><span>{{
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
    </section>
    <section
      class="market-fund market-inset"
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
      aria-labelledby="exchange-title"
    >
      <div class="section-heading market-inset">
        <h2 id="exchange-title">能量值 · 爱心兑换</h2>
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
      </div>
      <div class="exchange-products">
        <article v-for="reward in rewards" :key="reward.id">
          <img
            :src="mediaUrl(reward.cover_url)"
            :alt="reward.name"
            loading="lazy"
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
    </section>
    <footer
      class="market-thanks market-inset"
      data-design-node="5:7501"
      :style="{
        backgroundImage: 'url(' + designImage('layer-5-7245', '5:7563') + ')',
      }"
    >
      <span
        class="thanks-icon"
        :style="{
          backgroundImage: 'url(' + designImage('layer-5-7245', '5:7508') + ')',
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
    <nav class="market-records" aria-label="市集记录">
      <RouterLink to="/me/orders">查看我的订单 ›</RouterLink
      ><RouterLink to="/me/exchanges">查看兑换记录 ›</RouterLink>
    </nav>
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
  --market-green: #5a7d4a;
  --market-gold: #c4a35a;
  --market-muted: #9a9080;
  background: #c9dbcb;
  color: #2c2416;
  font-family: var(--serif);
  padding-bottom: 40px;
  overflow: clip;
}
.market-inset {
  margin-left: 20px;
  margin-right: 20px;
}
.market-hero {
  position: relative;
  height: 694px;
  overflow: hidden;
}
.hero-background,
.hero-overlay {
  position: absolute;
  left: 0;
  top: -67px;
  width: 100%;
  height: 707px;
  background-size: cover;
  background-position: center;
  object-fit: cover;
}
.market-header {
  position: absolute;
  z-index: 2;
  top: 0;
  left: 0;
  right: 0;
  color: white;
  border: 0;
  background: transparent;
}
.market-header :deep(h1) {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}
.hero-art,
.hero-copy {
  position: absolute;
  width: 375px;
  height: 694px;
  left: calc(50% - 187.5px);
  top: 0;
  pointer-events: none;
}
.hero-shape {
  position: absolute;
  display: block;
}
.hero-art > .hero-shape {
  translate: 0 -67px;
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
.market-eyebrow {
  position: absolute;
  left: 107.1px;
  top: 99.5px;
  display: flex;
  align-items: center;
  gap: 8px;
  height: 30px;
  padding: 0 16px;
  border: 1px solid #ffffff4d;
  border-radius: 9999px;
  background: #fff3;
  backdrop-filter: blur(4px);
  color: white;
  font-size: 12px;
  line-height: 16px;
  font-weight: 600;
  letter-spacing: 0.6px;
  white-space: nowrap;
}
.market-eyebrow i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--market-gold);
}
.hero-copy h1 {
  position: absolute;
  left: 88.5px;
  top: 159.5px;
  font:
    400 48px/60px "Ma Shan Zheng",
    serif;
  color: #fff;
}
.hero-copy h2 {
  position: absolute;
  left: 131.5px;
  top: 229.5px;
  font:
    400 20px/28px "Ma Shan Zheng",
    serif;
  letter-spacing: 2px;
  color: #ffffffe6;
}
.hero-copy > p {
  position: absolute;
  left: 89.5px;
  top: 264.5px;
  width: 238px;
  text-align: center;
  font-size: 14px;
  line-height: 22.75px;
  color: #fffc;
}
.market-explore {
  position: absolute;
  left: 132.5px;
  top: 333.5px;
  height: 52px;
  width: 152px;
  border-radius: 9999px;
  background: linear-gradient(90deg, #5a7d4a, #7a9d6a);
  color: #fff;
  font-size: 16px;
  line-height: 24px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow:
    0 10px 15px -3px #0000001a,
    0 4px 6px -4px #0000001a;
  pointer-events: auto;
}
.market-explore img {
  width: 10px;
  height: 5px;
}
.market-scroll {
  position: absolute;
  top: 576.96px;
  left: calc(50% - 28px);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  color: #ffffffb3;
  font-size: 10px;
  line-height: 15px;
  letter-spacing: 0.5px;
  min-height: 44px;
}
.market-scroll img {
  width: 12px;
  height: 15px;
}
.market-stats {
  min-height: 230px;
  padding: 32px 20px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}
.market-stats article {
  min-height: 166px;
  padding: 17px 5px;
  background: #ffffffd9;
  border: 1px solid #c4a35a33;
  border-radius: 16px;
  backdrop-filter: blur(20px);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}
.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-size: cover;
  display: grid;
  place-items: center;
}
.stat-icon img {
  width: 15px;
  height: 15px;
  object-fit: contain;
}
.market-stats strong {
  margin-top: 16px;
  font-size: clamp(17px, 6.4vw, 24px);
  line-height: 32px;
  color: var(--market-green);
  font-weight: 700;
  overflow-wrap: anywhere;
}
.market-stats article:nth-child(2) strong {
  color: var(--market-gold);
}
.market-stats article:nth-child(3) strong {
  color: #8b7355;
}
.market-stats article > span:last-child {
  margin-top: 4px;
  color: var(--market-muted);
  font-size: 11px;
  line-height: 16.5px;
}
.market-creators {
  padding-top: 67px;
}
.section-heading {
  margin-bottom: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: 48px;
}
.section-heading h2 {
  font-size: 20px;
  line-height: 28px;
  font-weight: 700;
}
.section-heading p {
  margin-top: 4px;
  font-size: 12px;
  line-height: 16px;
  color: var(--market-muted);
}
.section-heading a {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
  gap: 12px;
  font-size: 12px;
  line-height: 16px;
  font-weight: 600;
  color: var(--market-green);
  min-height: 44px;
}
.section-heading a img {
  width: 5px;
  height: 9px;
}
.creator-stories {
  margin-top: 24px;
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding: 0 20px 12px;
  min-height: 265px;
  scrollbar-width: none;
  scroll-behavior: smooth;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
}
.creator-story {
  flex: 0 0 170px;
  height: 253px;
  overflow: hidden;
  border-radius: 16px;
  border: 1px solid #c4a35a33;
  background: #fff;
}
.creator-cover {
  position: relative;
  height: 150px;
}
.creator-cover > img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.creator-cover > span {
  position: absolute;
  right: 10px;
  top: 10px;
  padding: 2px 4px;
  border-radius: 9999px;
  background: #c4a35ae6;
  color: #fff;
  font-size: 9px;
  line-height: 13.5px;
}
.creator-copy {
  padding: 14px;
}
.creator-copy h3 {
  font-size: 14px;
  line-height: 20px;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.creator-copy p {
  font-size: 10px;
  line-height: 15px;
  color: var(--market-muted);
  margin-top: 4px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.creator-likes {
  display: flex;
  gap: 8px;
  align-items: center;
  color: var(--market-green);
  font-size: 10px;
  line-height: 15px;
  margin-top: 10px;
}
.creator-likes b {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #f5ecd7;
  font-weight: 400;
}
.creator-empty {
  color: var(--market-muted);
  font-size: 12px;
  line-height: 20px;
  align-self: center;
}
.co-creation {
  margin-top: 20px;
  min-height: 182px;
  border: 1px solid #c4a35a33;
  border-radius: 24px;
  background-color: #ffffffc4;
  background-size: cover;
  padding: 24px;
}
.co-creation-heading {
  display: flex;
  gap: 12px;
  align-items: center;
}
.co-creation-heading > span {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
  border-radius: 16px;
  background-size: cover;
  display: grid;
  place-items: center;
}
.co-creation-heading img {
  width: 20px;
  height: 20px;
}
.co-creation-heading h3 {
  font-size: 16px;
  line-height: 24px;
}
.co-creation-heading p {
  font-size: 12px;
  line-height: 16px;
  color: var(--market-muted);
  margin-top: 2px;
}
.co-creation-steps {
  position: relative;
  display: flex;
  justify-content: space-between;
  gap: 4px;
  margin-top: 20px;
}
.co-creation-steps::before {
  content: "";
  height: 2px;
  position: absolute;
  left: 16px;
  right: 16px;
  top: 20px;
  background-image: url("/design/images/ce43aec2b92e5d0d60b773b3f1fad5f0.png");
  background-size: 100% 2px;
}
.co-creation-steps > * {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 0;
  min-width: 44px;
  font-size: 11px;
  line-height: 16.5px;
  font-weight: 600;
  white-space: nowrap;
}
.co-creation-steps b {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: linear-gradient(135deg, #5a7d4a 5%, #7a9d6a);
  color: #fff;
  font-size: 14px;
  line-height: 20px;
}
.co-creation-steps > :nth-child(2) b {
  background: linear-gradient(135deg, #c4a35a 5%, #d4b76a);
}
.co-creation-steps > :nth-child(3) b {
  background: linear-gradient(135deg, #8b7355 4%, #a69070);
}
.market-products {
  margin-top: 44px;
  scroll-margin-top: calc(var(--safe-top) + 12px);
}
.category-tabs {
  padding: 0;
  display: flex;
  gap: 10px;
  margin-top: 24px;
  margin-bottom: 24px;
  overflow-x: auto;
  scrollbar-width: none;
}
.category-tabs button {
  flex-shrink: 0;
  min-width: 64px;
  height: 38px;
  padding: 10px 20px;
  background: #fff;
  color: var(--market-muted);
  border-radius: 9999px;
  font-size: 12px;
  line-height: 16px;
  font-weight: 600;
  border: 1px solid #c4a35a33;
  white-space: nowrap;
}
.category-tabs button.active {
  background: linear-gradient(90deg, #5a7d4a, #7a9d6a);
  color: #fff;
  border-color: transparent;
}
.district-filter {
  color: var(--market-green);
  margin-bottom: 16px;
  font-size: 12px;
  min-height: 44px;
}
.market-product-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
.market-product {
  overflow: hidden;
  border: 1px solid #c4a35a33;
  border-radius: 16px;
  background: #fff;
  min-height: 354px;
}
.product-cover-wrap {
  position: relative;
  height: 170px;
}
.product-cover-wrap > img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.product-cover-wrap > span {
  position: absolute;
  top: 10px;
  left: 10px;
  max-width: calc(100% - 20px);
  padding: 4px 8px;
  color: #fff;
  background: linear-gradient(90deg, #5a7d4a, #7a9d6a);
  border-radius: 9999px;
  font-size: 10px;
  line-height: 15px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.product-copy {
  padding: 14px;
}
.product-copy h3 {
  font-size: 14px;
  line-height: 17.5px;
  font-weight: 700;
  min-height: 18px;
}
.product-story {
  font-size: 10px;
  line-height: 15px;
  color: var(--market-muted);
  min-height: 30px;
  margin-top: 6px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.product-purchase {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2px;
  margin-top: 12px;
  min-height: 36px;
}
.product-purchase strong {
  font-size: 20px;
  line-height: 28px;
  color: var(--market-green);
  font-weight: 700;
  overflow-wrap: anywhere;
}
.product-buy {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #5a7d4a, #7a9d6a);
  border-radius: 9999px;
}
.product-buy img {
  width: 11px;
  height: 11px;
}
.fund-share {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid #f5ecd7;
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--market-green);
  font-size: 10px;
  line-height: 15px;
  min-height: 41px;
}
.fund-share img {
  width: 12px;
  height: 11px;
  flex-shrink: 0;
}
.market-more {
  margin-top: 20px;
  width: 100%;
  min-height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: #fff;
  border: 1px solid #c4a35a33;
  border-radius: 16px;
  color: var(--market-green);
  font-size: 14px;
  line-height: 20px;
  font-weight: 600;
}
.market-more img {
  width: 10px;
  height: 10px;
}
.market-fund {
  position: relative;
  overflow: hidden;
  margin-top: 32px;
  padding: 24px;
  min-height: 476px;
  border-radius: 24px;
  color: #fff;
  background: linear-gradient(145deg, #4a7c59 6%, #5a966c 49%, #4a7c59 99%);
  box-shadow: 0 12px 40px #5a7d4a40;
}
.market-fund::before,
.market-fund::after {
  content: "";
  position: absolute;
  border-radius: 50%;
  background: #ffffff0d;
  pointer-events: none;
}
.market-fund::before {
  width: 160px;
  height: 160px;
  right: -80px;
  top: -80px;
}
.market-fund::after {
  width: 128px;
  height: 128px;
  left: -64px;
  bottom: -64px;
}
.fund-title {
  display: flex;
  gap: 12px;
  align-items: center;
  min-height: 40px;
}
.fund-title > span {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  background: #fff3;
  border-radius: 50%;
}
.fund-title img {
  width: 17px;
  height: 17px;
}
.fund-title h2 {
  font-size: 20px;
  line-height: 28px;
  font-weight: 700;
  color: #fff;
}
.fund-description {
  font-size: 14px;
  line-height: 22.75px;
  color: #ffffffd9;
  margin-top: 20px;
  min-height: 44px;
}
.fund-progress {
  margin-top: 24px;
  padding: 20px;
  border: 1px solid #ffffff1a;
  border-radius: 16px;
  background: #ffffff1a;
  min-height: 114px;
}
.fund-progress > div:first-child {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}
.fund-progress span {
  color: #fffc;
  font-size: 12px;
  line-height: 16px;
}
.fund-progress strong {
  color: #d4b76a;
  font-size: 14px;
  line-height: 20px;
  text-align: right;
}
.fund-track {
  margin-top: 12px;
  height: 12px;
  border-radius: 9999px;
  background: #ffffff26;
  overflow: hidden;
}
.fund-track i {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #c4a35a, #d4b76a 50%, #c4a35a);
  border-radius: inherit;
}
.fund-progress > p {
  font-size: 11px;
  line-height: 16.5px;
  color: #fff9;
  margin-top: 12px;
}
.fund-uses {
  margin-top: 20px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}
.fund-uses article {
  background: #ffffff1a;
  border: 1px solid #ffffff1a;
  border-radius: 12px;
  padding: 16px;
  min-height: 166px;
  text-align: center;
}
.fund-uses article > span {
  width: 48px;
  height: 48px;
  margin: 0 auto;
  background-size: cover;
  border-radius: 50%;
  display: grid;
  place-items: center;
}
.fund-uses img {
  width: 18px;
  height: 18px;
  object-fit: contain;
}
.fund-uses h3 {
  font-size: 14px;
  line-height: 20px;
  margin-top: 10px;
  min-height: 40px;
}
.fund-uses p {
  color: #fff9;
  font-size: 10px;
  line-height: 15px;
  margin-top: 4px;
}
.market-exchange {
  margin-top: 32px;
}
.market-exchange .section-heading {
  min-height: 28px;
}
.energy-balance {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: #5a7d4a1a;
  color: var(--market-green);
  border-radius: 9999px;
  font-size: 12px;
  line-height: 16px;
  font-weight: 600;
  white-space: nowrap;
}
.energy-balance img {
  width: 12px;
  height: 12px;
}
.exchange-products {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding: 0 20px 12px;
  margin-top: 20px;
  min-height: 217px;
  scrollbar-width: none;
  scroll-behavior: smooth;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
}
.exchange-products article {
  flex: 0 0 150px;
  min-height: 205px;
  padding: 14px;
  border: 1px solid #c4a35a33;
  border-radius: 16px;
  background: #fff;
}
.exchange-products article > img {
  width: 120px;
  height: 110px;
  border-radius: 12px;
  object-fit: cover;
}
.exchange-products h3 {
  margin-top: 12px;
  font-size: 12px;
  line-height: 16px;
}
.exchange-products article > div {
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.exchange-products strong {
  font-size: 14px;
  line-height: 20px;
  color: var(--market-gold);
}
.exchange-products button {
  min-width: 48px;
  min-height: 27px;
  padding: 6px 10px;
  border-radius: 9999px;
  background: linear-gradient(90deg, #5a7d4a, #7a9d6a);
  color: #fff;
  font-size: 10px;
  line-height: 15px;
  font-weight: 600;
}
.exchange-products > p {
  font-size: 12px;
  line-height: 20px;
  color: var(--market-muted);
  align-self: center;
}
.market-thanks {
  margin-top: 32px;
  padding: 24px;
  min-height: 281px;
  border-radius: 24px;
  background-size: cover;
  text-align: center;
}
.thanks-icon {
  display: grid;
  place-items: center;
  width: 64px;
  height: 64px;
  background-size: cover;
  border-radius: 50%;
  margin: 0 auto;
}
.thanks-icon img {
  width: 28px;
  height: 28px;
}
.market-thanks h2 {
  font-size: 18px;
  line-height: 28px;
  font-weight: 700;
  margin-top: 16px;
}
.market-thanks > p {
  color: var(--market-muted);
  font-size: 12px;
  line-height: 16px;
  margin-top: 8px;
}
.thanks-stats {
  display: flex;
  justify-content: space-around;
  gap: 12px;
  margin-top: 32px;
}
.thanks-stats span {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: var(--market-muted);
  font-size: 10px;
  line-height: 15px;
}
.thanks-stats strong {
  color: var(--market-green);
  font-size: 20px;
  line-height: 28px;
  overflow-wrap: anywhere;
}
.thanks-stats span:nth-child(2) strong {
  color: var(--market-gold);
}
.thanks-stats span:nth-child(3) strong {
  color: #8b7355;
}
.market-records {
  display: flex;
  justify-content: center;
  gap: 24px;
  padding: 20px;
  font-size: 12px;
  line-height: 20px;
  color: var(--market-green);
}
.market-records a {
  padding: 8px 0;
}
.auth-sheet fieldset {
  display: grid;
  gap: 14px;
  border: 0;
  padding: 0;
  margin: 0;
  min-width: 0;
}
.auth-sheet > p {
  font-size: 13px;
  line-height: 1.8;
  margin-top: 16px;
}
.auth-sheet > .primary-button {
  display: block;
  margin-top: 20px;
  text-align: center;
}
@media (max-width: 374px) {
  .market-creators .section-heading {
    gap: 4px;
  }
  .market-creators .section-heading h2 {
    font-size: 18px;
  }
  .section-heading a {
    gap: 6px;
  }
  .market-exchange .section-heading h2 {
    font-size: 18px;
  }
  .energy-balance {
    font-size: 10px;
    padding-left: 6px;
    padding-right: 6px;
  }
  .fund-title h2 {
    font-size: 18px;
  }
  .fund-uses article {
    padding-left: 10px;
    padding-right: 10px;
  }
}
</style>
