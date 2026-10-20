<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";

export type BannerSlide = { src: string; alt: string; caption: string };

const props = withDefaults(
  defineProps<{
    slides: BannerSlide[];
    eyebrow?: string;
    title?: string;
    interval?: number;
  }>(),
  { eyebrow: "非遗美育课程", title: "津门非遗 · 线上小课", interval: 4500 },
);

const track = ref<HTMLElement | null>(null);
const active = ref(0);
let timer = 0;
let paused = false;
let frame = 0;

function goTo(index: number, smooth = true) {
  const node = track.value;
  if (!node) return;
  const next = (index + props.slides.length) % props.slides.length;
  node.scrollTo({ left: next * node.clientWidth, behavior: smooth ? "smooth" : "auto" });
  active.value = next;
}

function schedule() {
  window.clearInterval(timer);
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  timer = window.setInterval(() => {
    if (paused || document.hidden) return;
    goTo(active.value + 1);
  }, props.interval);
}

function onScroll() {
  if (frame) return;
  frame = requestAnimationFrame(() => {
    frame = 0;
    const node = track.value;
    if (!node || !node.clientWidth) return;
    active.value = Math.round(node.scrollLeft / node.clientWidth);
  });
}

function pause() {
  paused = true;
}
function resume() {
  paused = false;
}

onMounted(() => {
  schedule();
  track.value?.addEventListener("pointerdown", pause, { passive: true });
  track.value?.addEventListener("touchstart", pause, { passive: true });
  window.addEventListener("pointerup", resume, { passive: true });
  window.addEventListener("touchend", resume, { passive: true });
});
onBeforeUnmount(() => {
  window.clearInterval(timer);
  if (frame) cancelAnimationFrame(frame);
});
</script>

<template>
  <section class="banner-carousel" :aria-label="title">
    <div ref="track" class="banner-track" @scroll="onScroll">
      <article
        v-for="(slide, index) in slides"
        :key="slide.src"
        class="banner-slide"
        :aria-hidden="index === active ? undefined : 'true'"
      >
        <img
          :src="slide.src"
          :alt="slide.alt"
          :loading="index === 0 ? 'eager' : 'lazy'"
          :fetchpriority="index === 0 ? 'high' : 'low'"
          decoding="async"
          draggable="false"
        />
        <div class="banner-scrim" aria-hidden="true" />
        <div class="banner-copy">
          <p>{{ eyebrow }}</p>
          <h2>{{ title }}</h2>
          <span>{{ slide.caption }}</span>
        </div>
      </article>
    </div>
    <div class="banner-dots" role="tablist" aria-label="轮播图">
      <button
        v-for="(slide, index) in slides"
        :key="slide.src"
        role="tab"
        :aria-selected="index === active"
        :aria-label="'查看第 ' + (index + 1) + ' 张：' + slide.caption"
        :class="{ on: index === active }"
        @click="goTo(index)"
      />
    </div>
  </section>
</template>

<style scoped>
.banner-carousel {
  position: relative;
  height: 156px;
  margin-bottom: 14px;
  border-radius: 14px;
  overflow: hidden;
  background: #6b2a2a;
}
.banner-track {
  display: flex;
  height: 100%;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-x: contain;
}
.banner-track::-webkit-scrollbar {
  display: none;
}
.banner-slide {
  position: relative;
  flex: 0 0 100%;
  height: 100%;
  scroll-snap-align: center;
  scroll-snap-stop: always;
}
.banner-slide img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  pointer-events: none;
}
.banner-scrim {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    rgba(46, 20, 16, 0.78) 0%,
    rgba(46, 20, 16, 0.55) 46%,
    rgba(46, 20, 16, 0.12) 100%
  );
}
.banner-copy {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 6px;
  padding: 0 18px;
  color: #f8f0e4;
}
.banner-copy p {
  margin: 0;
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid rgba(248, 240, 228, 0.5);
  font: 400 10px/1.4 var(--sans);
  letter-spacing: 2px;
}
.banner-copy h2 {
  margin: 2px 0 0;
  font: 500 21px/1.25 var(--serif);
  letter-spacing: 2px;
  text-shadow: 0 2px 10px rgba(30, 12, 8, 0.35);
}
.banner-copy span {
  font: 400 11px/1.5 var(--sans);
  letter-spacing: 0.6px;
  color: rgba(248, 240, 228, 0.86);
}
.banner-dots {
  position: absolute;
  right: 14px;
  bottom: 12px;
  display: flex;
  gap: 6px;
}
.banner-dots button {
  width: 7px;
  height: 7px;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: rgba(248, 240, 228, 0.45);
  transition: width 0.2s ease, background 0.2s ease;
}
.banner-dots button.on {
  width: 18px;
  border-radius: 999px;
  background: #f4e6cf;
}
@media (prefers-reduced-motion: reduce) {
  .banner-dots button {
    transition: none;
  }
}
</style>
