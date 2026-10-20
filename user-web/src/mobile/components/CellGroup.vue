<script setup lang="ts">
defineProps<{ label?: string }>();
</script>

<template>
  <nav class="ui-cells corner-card" :aria-label="label">
    <slot />
  </nav>
</template>

<style scoped>
.ui-cells {
  margin-bottom: 14px;
  padding: 4px 0;
  overflow: hidden;
}
</style>
