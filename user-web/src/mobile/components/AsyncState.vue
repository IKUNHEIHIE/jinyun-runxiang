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
  <div v-if="loading" class="async-state" role="status" aria-live="polite">
    <span class="spinner" />正在加载…
  </div>
  <div v-else-if="error" class="async-state" role="alert">
    <p>{{ error }}</p>
    <button class="outline-button" @click="$emit('retry')">重新加载</button>
  </div>
  <div v-else-if="empty" class="async-state">
    <p>{{ emptyText || "这里还没有内容，稍后再来看看吧" }}</p>
  </div>
  <slot v-else />
</template>
