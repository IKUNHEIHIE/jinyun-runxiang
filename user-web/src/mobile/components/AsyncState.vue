<script setup lang="ts">
defineProps<{
  loading?: boolean;
  error?: string;
  empty?: boolean;
  emptyText?: string;
}>();
defineEmits<{ retry: [] }>();
</script>
<template>
  <div v-if="loading" class="async-state" role="status" aria-live="polite" aria-busy="true">
    <span class="spinner" aria-hidden="true" />正在加载…
  </div>
  <div v-else-if="error" class="async-state" role="alert">
    <p>{{ error }}</p>
    <button type="button" class="outline-button" @click="$emit('retry')">重新加载</button>
  </div>
  <div v-else-if="empty" class="async-state">
    <p>{{ emptyText || "这里还没有内容，稍后再来看看吧" }}</p>
  </div>
  <slot v-else />
</template>
<style scoped>
.async-state { overflow-wrap: anywhere; }
.async-state p { max-width: 100%; }
</style>
