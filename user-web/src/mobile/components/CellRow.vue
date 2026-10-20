<script setup lang="ts">
defineProps<{
  label: string;
  to?: string;
  danger?: boolean;
  disabled?: boolean;
}>();
</script>

<template>
  <RouterLink v-if="to" :to="to" class="ui-cell">
    <i class="ui-cell-mark" aria-hidden="true" />
    <span class="ui-cell-label">{{ label }}</span>
    <span class="ui-cell-arrow" aria-hidden="true">›</span>
    <slot name="value" />
  </RouterLink>
  <button
    v-else
    class="ui-cell"
    :class="{ danger }"
    :disabled="disabled"
  >
    <i v-if="!danger" class="ui-cell-mark" aria-hidden="true" />
    <span class="ui-cell-label">{{ label }}</span>
    <span v-if="!danger" class="ui-cell-arrow" aria-hidden="true">›</span>
    <slot name="value" />
  </button>
</template>

<style scoped>
.ui-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-height: 48px;
  padding: 0 16px;
  background: none;
  border: 0;
  text-align: left;
  font: 400 14px/1.4 var(--sans);
  color: #2d1810;
}
.ui-cell + .ui-cell {
  border-top: 1px solid rgba(200, 169, 110, 0.16);
}
.ui-cell:active {
  background: rgba(200, 169, 110, 0.08);
}
.ui-cell-mark {
  width: 4px;
  height: 14px;
  border-radius: 2px;
  background: rgba(139, 26, 26, 0.55);
  flex-shrink: 0;
}
.ui-cell-label {
  flex: 1;
  min-width: 0;
}
.ui-cell-arrow {
  color: #b9a48c;
  font-size: 16px;
}
.ui-cell.danger {
  justify-content: center;
  color: #8b1a1a;
}
.ui-cell:disabled {
  opacity: 0.6;
}
</style>
