<script setup lang="ts">
import { useRouter } from "vue-router";

const props = withDefaults(
  defineProps<{ title: string; subtitle?: string; back?: boolean; backTo?: string }>(),
  { back: true, backTo: "/" },
);
const router = useRouter();
const goBack = () =>
  window.history.state.back
    ? router.back()
    : router.replace(props.backTo);
</script>

<template>
  <header class="ui-appbar">
    <button v-if="back" class="ui-appbar-back" aria-label="返回上一页" @click="goBack">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M15 18l-6-6 6-6" />
      </svg>
    </button>
    <div class="ui-appbar-copy">
      <h1>{{ title }}</h1>
      <p v-if="subtitle">{{ subtitle }}</p>
    </div>
    <div class="ui-appbar-actions"><slot /></div>
  </header>
</template>

<style scoped>
.ui-appbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: calc(var(--safe-top) + 6px) 16px 10px;
  background: rgba(245, 237, 228, 0.92);
  -webkit-backdrop-filter: blur(12px);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(139, 105, 48, 0.14);
}
.ui-appbar-back {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 1px solid rgba(139, 105, 48, 0.18);
  background: rgba(255, 255, 255, 0.6);
  color: #5c4626;
}
.ui-appbar-back svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.ui-appbar-copy {
  min-width: 0;
}
.ui-appbar-copy h1 {
  margin: 0;
  font: 500 16px/1.25 var(--serif);
  letter-spacing: 2px;
  color: #2d1810;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ui-appbar-copy p {
  margin: 2px 0 0;
  font: 400 10px/1.4 var(--sans);
  letter-spacing: 1px;
  color: #8a6125;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ui-appbar-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
