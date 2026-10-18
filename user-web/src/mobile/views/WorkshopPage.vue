<script setup lang="ts">
import { designImage, designIcon } from "../design";
const screen = "layer-40-55029" as const;
const tools = [
  {
    type: "bronze",
    node: "40:45756",
    eyebrow: "纹样辅助",
    mark: "青铜",
    title: "青铜纹样工坊",
    description: "饕餮瑞兽 · 云雷纹饰\n纹样参考，辅助青铜纹饰设计",
    image: "40:46149",
    background: "40:45779",
    tags: ["纹样生成", "纹饰组合", "风格配色"],
    action: "进入工坊",
    arrow: "40:45798",
    decoration: "",
    color: "#1A365D",
    middle: "#2C4A6E",
    actionColor: "#E8D5A3",
  },
  {
    type: "shadow",
    node: "40:46388",
    eyebrow: "",
    mark: "皮影",
    title: "皮影角色设计",
    description: "镂影成戏 · 妙手生花\n角色参考，辅助皮影造型设计",
    image: "40:46683",
    background: "40:46412",
    tags: ["角色生成", "皮影质感", "光影配色"],
    action: "开始设计",
    arrow: "40:45810",
    decoration: "40:45799",
    color: "#8B1A1A",
    middle: "#A52A2A",
    actionColor: "#FAF8F5",
  },
  {
    type: "lacquer",
    node: "40:53879",
    eyebrow: "纹样辅助",
    mark: "漆绣",
    title: "漆绣智绘",
    description: "漆光溢彩 · 锦绣华章\n纹样参考，辅助漆绣图案设计",
    image: "40:47223",
    background: "40:46958",
    tags: ["纹样生成", "图案设计", "配色模拟"],
    action: "开始创作",
    arrow: "40:45821",
    decoration: "40:45811",
    color: "#4A7C6F",
    middle: "#5A9A8A",
    actionColor: "#FAF8F5",
  },
];
</script>
<template>
  <div class="workshop-page" data-design-node="40:55029">
    <header
      class="workshop-brand"
      data-design-node="40:51195"
      :style="{
        backgroundImage: 'url(' + designImage(screen, '40:51195') + ')',
      }"
    >
      <div class="brand-ornament" aria-hidden="true">
        <img :src="designImage(screen, '40:51197')" alt="" />
        <img :src="designIcon(screen, '40:49714')" alt="" />
        <img :src="designImage(screen, '40:51207')" alt="" />
      </div>
      <img
        class="brand-decoration"
        :src="designIcon(screen, '40:49718')"
        alt=""
      />
      <h1>AI工坊</h1>
      <p>传统与智能的碰撞</p>
      <div class="workshop-divider" aria-hidden="true">
        <i /><img :src="designImage(screen, '40:51360')" alt="" /><i />
      </div>
    </header>
    <div class="workshop-tools">
      <article
        v-for="tool in tools"
        :key="tool.type"
        class="workshop-tool"
        :class="'tool-' + tool.type"
        :data-design-node="tool.node"
        :style="{
          '--tool-color': tool.color,
          '--tool-middle': tool.middle,
          '--action-color': tool.actionColor,
          '--tool-bg': 'url(' + designImage(screen, tool.background) + ')',
        }"
      >
        <div class="tool-surface" aria-hidden="true" />
        <i class="tool-corner corner-first" aria-hidden="true" />
        <i class="tool-corner corner-top" aria-hidden="true" />
        <i class="tool-corner corner-bottom" aria-hidden="true" />
        <img
          v-if="tool.decoration"
          class="tool-decoration"
          :src="designIcon(screen, tool.decoration)"
          alt=""
        />
        <i v-else class="tool-decoration-square" aria-hidden="true" />
        <div class="tool-content">
          <span class="tool-eyebrow"
            ><i aria-hidden="true" />{{ tool.eyebrow }}</span
          >
          <div class="tool-heading">
            <span class="tool-mark">{{ tool.mark }}</span>
            <h2>{{ tool.title }}</h2>
            <p>{{ tool.description }}</p>
          </div>
          <div class="tool-illustration">
            <img :src="designImage(screen, tool.image)" :alt="tool.title" />
            <i aria-hidden="true" /><i aria-hidden="true" />
          </div>
          <div class="tool-tags">
            <span v-for="tag in tool.tags" :key="tag">{{ tag }}</span>
          </div>
          <RouterLink :to="'/ai-workshop/' + tool.type" class="tool-action">
            {{ tool.action
            }}<img :src="designIcon(screen, tool.arrow)" alt="" />
          </RouterLink>
        </div>
      </article>
    </div>
  </div>
</template>
<style scoped>
/* MasterGo 40:55029: paper, ink, gold, type and gradients copied from section styles. */
.workshop-page {
  --workshop-paper: #ebe3d5;
  --workshop-gold: #c9a84c;
  background: var(--workshop-paper);
  padding: 36px 20px 91px;
  font-family: var(--serif);
}
.workshop-brand {
  height: 177px;
  position: relative;
  text-align: center;
  background-position: center;
  background-size: cover;
}
.brand-ornament {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
  height: 20px;
}
.brand-ornament img {
  width: 40px;
  height: 1px;
}
.brand-ornament img:nth-child(2) {
  width: 16px;
  height: 16px;
  margin: 0 2px;
}
.brand-decoration {
  position: absolute;
  top: 36.8px;
  left: calc(50% - 64.25px);
  width: 40.96px;
  height: 42.88px;
  opacity: 0.1;
}
.workshop-brand h1 {
  position: absolute;
  top: 38px;
  left: 50%;
  transform: translateX(-50%);
  width: 200px;
  height: 40px;
  font-family: "Ma Shan Zheng", var(--serif);
  font-size: 64px;
  line-height: 35px;
  color: #1a365d;
  letter-spacing: 3.36px;
  font-weight: 400;
  white-space: nowrap;
}
.workshop-brand > p {
  position: absolute;
  top: 91px;
  left: calc(50% - 107.5px);
  width: 229px;
  font-family: "Ma Shan Zheng", var(--serif);
  font-size: 22px;
  line-height: 20px;
  letter-spacing: 4.9px;
  color: rgba(139, 26, 26, 0.8);
  white-space: nowrap;
}
.workshop-divider {
  position: absolute;
  top: 171px;
  left: 50%;
  transform: translateX(-50%);
  width: 108px;
  height: 6px;
}
.workshop-divider img {
  position: absolute;
  width: 80px;
  height: 1px;
  left: 14px;
  top: 2.5px;
}
.workshop-divider i {
  position: absolute;
  width: 8.49px;
  height: 8.49px;
  top: -1.24px;
  left: -1.24px;
  background: rgba(201, 168, 76, 0.5);
  border-radius: 50%;
}
.workshop-divider i:last-child {
  left: 100.76px;
}
.workshop-tools {
  display: flex;
  flex-direction: column;
  gap: 28px;
}
.workshop-tool {
  position: relative;
  height: 482px;
  flex: none;
  isolation: isolate;
}
.tool-lacquer {
  height: 469px;
}
.tool-surface {
  position: absolute;
  inset: 0;
  background: rgba(250, 248, 245, 0.8);
  border: 1px solid rgba(201, 168, 76, 0.15);
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(26, 54, 93, 0.1);
  backdrop-filter: blur(4px);
  overflow: hidden;
}
.tool-bronze .tool-surface {
  bottom: 6px;
}
/* Keep decorative fills subdued until original canvas opacity/stacking can be verified. */
.tool-surface:before {
  content: "";
  position: absolute;
  inset: 0;
  background: var(--tool-bg) center/cover;
  opacity: 0.1;
}
.tool-corner {
  position: absolute;
  pointer-events: none;
}
.corner-first {
  top: 8px;
  left: 8px;
  width: 32px;
  height: 32px;
  border: solid var(--tool-color);
  border-width: 2px 0 0 2px;
  opacity: 0.5;
}
.corner-top {
  top: 13px;
  right: 13px;
  width: 40px;
  height: 40px;
  border: solid rgba(201, 168, 76, 0.25);
  border-width: 2px 2px 0 0;
  border-radius: 0 8px 0 0;
}
.corner-bottom {
  top: 429px;
  left: 13px;
  width: 40px;
  height: 40px;
  border: solid rgba(201, 168, 76, 0.25);
  border-width: 0 0 2px 2px;
  border-radius: 0 0 0 8px;
}
.tool-decoration {
  position: absolute;
  top: 9px;
  right: 9px;
  width: 80px;
  height: 80px;
  opacity: 0.08;
  pointer-events: none;
}
.tool-decoration-square {
  position: absolute;
  top: 19px;
  right: 19px;
  width: 60px;
  height: 60px;
  border: 1px solid var(--workshop-gold);
  opacity: 0.08;
}
.tool-content {
  position: absolute;
  inset: 1px;
  height: 474px;
}
.tool-eyebrow {
  position: absolute;
  left: 24px;
  top: 24px;
  height: 28px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 12px;
  border-radius: 9999px;
  color: var(--tool-color);
  font-size: 12px;
  font-weight: 500;
  line-height: 16px;
  letter-spacing: 0.07px;
}
.tool-eyebrow i {
  width: 6px;
  height: 6px;
  flex: none;
  background: var(--tool-middle);
  border-radius: 50%;
}
.tool-bronze .tool-eyebrow i {
  background: var(--workshop-gold);
}
.tool-lacquer .tool-eyebrow {
  background: rgba(74, 124, 111, 0.1);
  letter-spacing: 0.6px;
}
.tool-heading {
  position: absolute;
  top: 68px;
  left: 24px;
  right: 24px;
  height: 77px;
}
.tool-mark {
  position: absolute;
  top: 4px;
  left: 41px;
  width: 23px;
  height: 40px;
  line-height: 24px;
  letter-spacing: 4px;
  color: color-mix(in srgb, var(--tool-color) 70%, transparent);
  font-size: 16px;
  font-weight: 700;
  overflow-wrap: anywhere;
}
.tool-heading h2 {
  position: absolute;
  left: 80px;
  top: 0;
  font-size: 22px;
  line-height: 33px;
  font-weight: 700;
  color: #1a1a2e;
  letter-spacing: 0.55px;
  white-space: nowrap;
}
.tool-heading p {
  position: absolute;
  left: 80px;
  top: 39px;
  font-size: 12px;
  line-height: 16px;
  letter-spacing: 0.3px;
  color: rgba(26, 26, 46, 0.55);
  white-space: pre;
}
.tool-shadow .tool-heading h2,
.tool-shadow .tool-heading p {
  left: 74px;
}
.tool-shadow .tool-heading p {
  top: 33px;
}
.tool-lacquer .tool-mark {
  left: 1px;
}
.tool-lacquer .tool-heading h2 {
  left: 46px;
  top: 6px;
}
.tool-lacquer .tool-heading p {
  left: 40px;
  top: 46px;
}
.tool-illustration {
  position: absolute;
  top: 161px;
  left: 24px;
  right: 24px;
  height: 178px;
  background: rgba(240, 235, 227, 0.6);
  border: 1px solid rgba(201, 168, 76, 0.15);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
}
.tool-illustration > img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.tool-illustration i {
  position: absolute;
  top: 8px;
  left: 8px;
  width: 24px;
  height: 24px;
  border: solid rgba(201, 168, 76, 0.3);
  border-width: 1px 0 0 1px;
}
.tool-illustration i:last-child {
  top: auto;
  left: auto;
  right: 8px;
  bottom: 8px;
  border-width: 0 1px 1px 0;
}
.tool-tags {
  position: absolute;
  left: 24px;
  top: 355px;
  display: flex;
  gap: 8px;
}
.tool-tags span {
  width: 66px;
  height: 29px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(201, 168, 76, 0.15);
  border-radius: 6px;
  background: color-mix(in srgb, var(--tool-color) 5%, transparent);
  color: color-mix(in srgb, var(--tool-color) 70%, transparent);
  font-size: 10px;
  line-height: 15px;
  white-space: nowrap;
}
.tool-action {
  position: absolute;
  top: 404px;
  left: 24px;
  right: 24px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: linear-gradient(
    100deg,
    var(--tool-color) -1%,
    var(--tool-middle) 50%,
    var(--tool-color) 100%
  );
  color: var(--action-color);
  font-size: 14px;
  line-height: 20px;
  letter-spacing: 1.4px;
  font-weight: 600;
  box-shadow:
    0 10px 15px -3px rgba(0, 0, 0, 0.1),
    0 4px 6px -4px rgba(0, 0, 0, 0.1);
}
.tool-action img {
  width: 12px;
  height: 5.333px;
}
@media (max-width: 360px) {
  .tool-heading h2 {
    font-size: 20px;
  }
  .tool-heading p {
    letter-spacing: 0;
  }
}
</style>
