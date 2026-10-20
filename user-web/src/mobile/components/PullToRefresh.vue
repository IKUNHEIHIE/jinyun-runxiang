<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";

const props = withDefaults(
  defineProps<{ onRefresh: () => Promise<unknown> | void; disabled?: boolean }>(),
  { disabled: false },
);

const THRESHOLD = 56;
const MAX = 96;
const distance = ref(0);
const refreshing = ref(false);
const pulling = ref(false);
let startY = 0;
let tracking = false;

const atTop = () => (window.scrollY || document.documentElement.scrollTop || 0) <= 0;

function onStart(event: TouchEvent) {
  if (props.disabled || refreshing.value || event.touches.length !== 1 || !atTop()) return;
  tracking = true;
  startY = event.touches[0].clientY;
}

function onMove(event: TouchEvent) {
  if (!tracking) return;
  const delta = event.touches[0].clientY - startY;
  if (delta <= 0) {
    distance.value = 0;
    pulling.value = false;
    return;
  }
  if (!atTop()) {
    tracking = false;
    distance.value = 0;
    pulling.value = false;
    return;
  }
  if (event.cancelable) event.preventDefault();
  pulling.value = true;
  distance.value = Math.min(MAX, delta * 0.5);
}

async function onEnd() {
  if (!tracking) return;
  tracking = false;
  pulling.value = false;
  if (distance.value < THRESHOLD) {
    distance.value = 0;
    return;
  }
  refreshing.value = true;
  distance.value = THRESHOLD;
  try {
    await props.onRefresh();
  } finally {
    refreshing.value = false;
    distance.value = 0;
  }
}

onMounted(() => {
  window.addEventListener("touchstart", onStart, { passive: true });
  window.addEventListener("touchmove", onMove, { passive: false });
  window.addEventListener("touchend", onEnd, { passive: true });
  window.addEventListener("touchcancel", onEnd, { passive: true });
});
onBeforeUnmount(() => {
  window.removeEventListener("touchstart", onStart);
  window.removeEventListener("touchmove", onMove);
  window.removeEventListener("touchend", onEnd);
  window.removeEventListener("touchcancel", onEnd);
});
</script>

<template>
  <div
    class="pull-refresh"
    :class="{ active: distance > 0 || refreshing }"
    :style="{
      transform:
        distance > 0 || refreshing
          ? `translateY(${refreshing ? THRESHOLD : distance}px)`
          : 'translateY(-100%)',
    }"
    aria-hidden="true"
  >
    <span class="pull-ring" :class="{ spin: refreshing }" />
    <span class="pull-copy">
      {{
        refreshing
          ? "正在刷新…"
          : distance >= 56
            ? "松开刷新"
            : "下拉刷新"
      }}
    </span>
  </div>
</template>

<style scoped>
.pull-refresh {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 44px;
  padding-top: var(--safe-top);
  box-sizing: content-box;
  background: linear-gradient(
    180deg,
    rgba(245, 237, 228, 0.98),
    rgba(245, 237, 228, 0.86)
  );
  -webkit-backdrop-filter: blur(10px);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(139, 105, 48, 0.14);
  transform: translateY(-100%);
  transition: transform 0.18s ease;
  pointer-events: none;
  font: 400 11px/1 var(--sans);
  letter-spacing: 1px;
  color: #8a6125;
}
.pull-refresh.active {
  transition: none;
}
.pull-ring {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid rgba(139, 105, 48, 0.25);
  border-top-color: #8b1a1a;
}
.pull-ring.spin {
  animation: pull-spin 0.8s linear infinite;
}
@keyframes pull-spin {
  to {
    transform: rotate(360deg);
  }
}
@media (prefers-reduced-motion: reduce) {
  .pull-refresh {
    transition: none;
  }
  .pull-ring.spin {
    animation-duration: 2s;
  }
}
</style>
