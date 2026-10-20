<script setup lang="ts">
import { designImage } from "../design";
import PageHeader from "../components/PageHeader.vue";

const screen = "layer-40-55029" as const;
type Feature = {
  route: string;
  eyebrow: string;
  index: string;
  seal: string;
  title: string;
  description: string;
  tags: string[];
  action: string;
  accent: string;
  image: string;
  tag?: string;
};

const featureImage = (feature: Feature) =>
  feature.image.startsWith("/")
    ? feature.image
    : designImage(screen, feature.image);

const features: Feature[] = [
  {
    route: "/ai-workshop/3d",
    eyebrow: "数字沙盘 · 古法营造",
    index: "壹",
    seal: "造",
    title: "三维非遗数字沙盘",
    description: "以三维复原器物营造，观其形、察其纹、赏其光",
    tags: ["三维复原", "材质摹写", "光影演算"],
    action: "进入数字沙盘",
    accent: "#8a6125",
    image: "/design/images/3d-stage-card.webp",
    tag: "实时演算",
  },
  {
    route: "/ai-workshop/shadow-3d",
    eyebrow: "皮影营造 · 三维工序",
    index: "贰",
    seal: "影",
    title: "一张驴皮，三千刀",
    description: "六道工序三维重演，按意生成专属剪影",
    tags: ["六道工序", "分层皮影", "剪影生成"],
    action: "进入剪影工坊",
    accent: "#8b1a1a",
    image: "/design/images/15cbc40b47a025f417fc5a7b16263fe9.webp",
    tag: "馆藏皮影",
  },
  {
    route: "/ai-workshop/bronze",
    eyebrow: "青铜纹样 · 数字工坊",
    index: "叁",
    seal: "纹",
    title: "青铜纹样工坊",
    description: "饕餮瑞兽 · 云雷纹饰，辅助青铜纹饰设计",
    tags: ["纹样生成", "纹饰组合", "风格配色"],
    action: "进入工坊",
    accent: "#1a365d",
    image: "40:46149",
  },
  {
    route: "/ai-workshop/shadow",
    eyebrow: "皮影角色 · 数字工坊",
    index: "肆",
    seal: "影",
    title: "皮影角色设计",
    description: "镂影成戏 · 妙手生花，辅助皮影造型设计",
    tags: ["角色生成", "皮影质感", "光影配色"],
    action: "开始设计",
    accent: "#8b1a1a",
    image: "40:46683",
  },
  {
    route: "/ai-workshop/lacquer",
    eyebrow: "漆绣纹样 · 数字工坊",
    index: "伍",
    seal: "漆",
    title: "漆绣智绘",
    description: "漆光溢彩 · 锦绣华章，辅助漆绣图案设计",
    tags: ["纹样生成", "图案设计", "配色模拟"],
    action: "开始创作",
    accent: "#4a7c6f",
    image: "40:47223",
  },
];
</script>

<template>
  <div class="workshop-page" data-design-node="40:55029">
    <PageHeader title="AI 工坊" subtitle="传统与智能的碰撞" :back="false">
      <RouterLink class="header-works" to="/ai-workshop/works"
        >我的作品</RouterLink
      >
    </PageHeader>

    <div class="page-padding">
      <section class="feature-list">
        <RouterLink
          v-for="feature in features"
          :key="feature.route"
          :to="feature.route"
          class="feature-card corner-card"
          :style="{ '--accent': feature.accent }"
        >
          <div class="feature-copy">
            <span class="feature-eyebrow"
              ><i aria-hidden="true" />{{ feature.eyebrow }}</span
            >
            <h2>{{ feature.title }}</h2>
            <p>{{ feature.description }}</p>
            <div class="feature-tags">
              <span v-for="tag in feature.tags" :key="tag">{{ tag }}</span>
            </div>
            <span class="feature-cta">
              {{ feature.action }}
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M9 6l6 6-6 6" />
              </svg>
            </span>
          </div>

          <div class="feature-media">
            <img :src="featureImage(feature)" :alt="feature.title" />
            <span class="media-index">{{ feature.index }}</span>
            <span class="media-seal">{{ feature.seal }}</span>
            <span class="media-tag">{{ feature.tag || "馆藏高清" }}</span>
          </div>
        </RouterLink>
      </section>
    </div>
  </div>
</template>

<style scoped>
.workshop-page {
  min-height: 100dvh;
  background: #f5ede4;
  color: #2d1810;
}
.page-padding {
  padding: 14px 16px 24px;
}
.header-works {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  height: 30px;
  padding: 0 13px;
  border: 1px solid rgba(139, 26, 26, 0.28);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  color: #8b1a1a;
  font: 500 11px/1 var(--sans);
  letter-spacing: 1px;
  white-space: nowrap;
}
.header-works:active {
  background: rgba(139, 26, 26, 0.08);
}
.feature-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.feature-card {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 112px;
  gap: 12px;
  height: 206px;
  padding: 14px;
}
.feature-card:active {
  transform: scale(0.992);
}
.feature-copy {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 0;
}
.feature-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  height: 20px;
  padding: 0 8px;
  overflow: hidden;
  border: 1px solid rgba(200, 169, 110, 0.36);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.5);
  color: #8a6125;
  font: 400 10px/1 var(--sans);
  letter-spacing: 0.5px;
  white-space: nowrap;
}
.feature-eyebrow i {
  width: 5px;
  height: 5px;
  flex: none;
  border-radius: 50%;
  background: var(--accent);
}
.feature-copy h2 {
  margin: 9px 0 0;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font: 500 16px/1.35 var(--serif);
  letter-spacing: 0.6px;
  color: #2d1810;
}
.feature-copy p {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  margin: 5px 0 0;
  font: 400 11px/1.65 var(--sans);
  letter-spacing: 0.2px;
  color: #8a7a70;
}
.feature-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 8px;
}
.feature-tags span {
  padding: 1px 6px;
  border: 1px solid rgba(200, 169, 110, 0.36);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.5);
  color: #8a6125;
  font: 400 10px/15px var(--sans);
  letter-spacing: 0.4px;
}
.feature-cta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 26px;
  margin-top: auto;
  padding: 0 11px;
  border: 1px solid rgba(139, 26, 26, 0.4);
  border-radius: 999px;
  background: #fff0f0;
  color: #8b1a1a;
  font: 500 11px/1 var(--sans);
  letter-spacing: 1.2px;
}
.feature-cta svg {
  width: 12px;
  height: 12px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.feature-media {
  position: relative;
  height: 100%;
  overflow: hidden;
  border: 1px solid rgba(200, 169, 110, 0.5);
  border-radius: 10px;
  background: #f2e5cf;
}
.feature-media img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.media-index {
  position: absolute;
  top: 7px;
  left: 7px;
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  border: 1px solid rgba(200, 169, 110, 0.6);
  border-radius: 4px;
  background: rgba(253, 249, 242, 0.9);
  color: #8a6125;
  font: 500 11px/1 var(--serif);
}
.media-seal {
  position: absolute;
  right: 7px;
  bottom: 7px;
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  border: 1.5px solid rgba(139, 26, 26, 0.72);
  border-radius: 2px;
  background: rgba(253, 249, 242, 0.78);
  color: #8b1a1a;
  font: 500 11px/1 var(--serif);
  transform: rotate(-4deg);
}
.media-tag {
  position: absolute;
  left: 7px;
  bottom: 7px;
  padding: 2px 5px;
  border: 1px solid rgba(200, 169, 110, 0.42);
  border-radius: 3px;
  background: rgba(253, 249, 242, 0.92);
  color: #8a6125;
  font: 400 10px/12px var(--sans);
  letter-spacing: 0.5px;
}
</style>
