<script setup lang="ts">
defineProps<{ title?: string; meta?: string }>();
</script>

<template>
  <section class="ui-card corner-card">
    <div v-if="title || $slots.meta" class="ui-card-head">
      <h2 v-if="title">{{ title }}</h2>
      <span v-if="meta" class="ui-card-meta">{{ meta }}</span>
      <slot name="meta" />
    </div>
    <slot />
  </section>
</template>

<style scoped>
.ui-card {
  margin-bottom: 14px;
  padding: 16px 14px;
}
.ui-card-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  min-height: 22px;
}
.ui-card-head h2 {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font: 500 16px/1.3 var(--serif);
  letter-spacing: 1.6px;
  color: #2d1810;
  white-space: nowrap;
}
.ui-card-head h2::before {
  content: "";
  width: 3px;
  height: 15px;
  border-radius: 2px;
  background: #8b1a1a;
  flex-shrink: 0;
}
.ui-card-head h2::after {
  content: "";
  flex: 1;
  height: 1px;
  margin-left: 4px;
  background: rgba(200, 169, 110, 0.42);
}
.ui-card-meta {
  font: 400 10px/1.4 var(--sans);
  letter-spacing: 1px;
  color: #8a7a70;
  white-space: nowrap;
}
</style>
