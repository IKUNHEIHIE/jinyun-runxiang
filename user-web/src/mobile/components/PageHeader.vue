<script setup lang="ts">
import { useRouter } from "vue-router";
defineProps<{ title: string; subtitle?: string }>();
const router = useRouter();
const back = () =>
  window.history.state.back ? router.back() : router.replace("/");
</script>
<template>
  <header class="page-header">
    <button class="back-button" aria-label="返回上一页" @click="back">‹</button>
    <div>
      <h1>{{ title }}</h1>
      <p v-if="subtitle">{{ subtitle }}</p>
    </div>
    <slot />
  </header>
</template>
