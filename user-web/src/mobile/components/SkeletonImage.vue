<script setup lang="ts">
import { computed, ref } from "vue";
import { mediaUrl } from "../api";

const props = withDefaults(
  defineProps<{
    src?: string | null;
    alt?: string;
    eager?: boolean;
    ratio?: string;
  }>(),
  { src: "", alt: "", eager: false, ratio: "" },
);

const loaded = ref(false);
const failed = ref(false);
const url = computed(() => (props.src ? mediaUrl(props.src) : ""));
</script>

<template>
  <span
    class="skeleton-media"
    :class="{ loaded, failed }"
    :style="ratio ? { aspectRatio: ratio } : undefined"
  >
    <span v-if="!loaded && !failed" class="skeleton-shimmer" aria-hidden="true" />
    <img
      v-if="url && !failed"
      :src="url"
      :alt="alt"
      :loading="eager ? 'eager' : 'lazy'"
      :fetchpriority="eager ? 'high' : 'low'"
      decoding="async"
      @load="loaded = true"
      @error="failed = true"
    />
    <span v-else-if="failed" class="skeleton-fallback" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <rect x="3" y="4" width="18" height="16" rx="2.5" />
        <circle cx="9" cy="10" r="1.6" />
        <path d="M4.5 18l4.2-4.4 3 2.8 3.1-3.6 4.7 5.2" />
      </svg>
    </span>
  </span>
</template>

<style scoped>
.skeleton-media {
  position: relative;
  display: block;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: linear-gradient(160deg, #f3e9db, #ece0cd);
}
.skeleton-media img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
  transition: opacity 0.3s ease;
}
.skeleton-media.loaded img {
  opacity: 1;
}
.skeleton-shimmer {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    100deg,
    rgba(255, 255, 255, 0) 20%,
    rgba(255, 255, 255, 0.55) 48%,
    rgba(255, 255, 255, 0) 76%
  );
  background-size: 220% 100%;
  animation: skeleton-sweep 1.35s ease-in-out infinite;
}
@keyframes skeleton-sweep {
  from {
    background-position: 140% 0;
  }
  to {
    background-position: -60% 0;
  }
}
.skeleton-fallback {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: rgba(139, 105, 48, 0.45);
  background: rgba(250, 245, 240, 0.85);
}
.skeleton-fallback svg {
  width: 34px;
  height: 34px;
  stroke-width: 1.4;
}
@media (prefers-reduced-motion: reduce) {
  .skeleton-shimmer {
    animation: none;
    background: rgba(255, 255, 255, 0.28);
  }
  .skeleton-media img {
    transition: none;
  }
}
</style>
