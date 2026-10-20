<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{ page: number; total: number; pageSize?: number; unit?: string }>(),
  { pageSize: 20, unit: "条" },
);
const emit = defineEmits<{ (event: "change", page: number): void }>();

const pages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)));
const jump = (next: number) => {
  const target = Math.min(pages.value, Math.max(1, next));
  if (target !== props.page) emit("change", target);
};
</script>

<template>
  <nav class="pager" aria-label="分页">
    <button
      type="button"
      class="pager-step"
      :disabled="page <= 1"
      aria-label="上一页"
      @click="jump(page - 1)"
    >
      ‹ 上一页
    </button>
    <span class="pager-state">
      <span class="pager-count">第 <b>{{ page }}</b> / {{ pages }} 页</span>
      <small>共 {{ total }} {{ unit }}</small>
    </span>
    <button
      type="button"
      class="pager-step"
      :disabled="page >= pages"
      aria-label="下一页"
      @click="jump(page + 1)"
    >
      下一页 ›
    </button>
    <slot />
  </nav>
</template>

<style scoped>
.pager {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 2px 2px;
}
.pager-step {
  min-width: 88px;
  height: 36px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid rgba(139, 105, 48, 0.28);
  background: rgba(255, 255, 255, 0.72);
  color: #8a6125;
  font: 400 12px/1 var(--sans);
  letter-spacing: 1px;
}
.pager-step:disabled {
  opacity: 0.4;
}
.pager-state {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  min-width: 0;
  text-align: center;
  font: 400 11px/1.4 var(--sans);
  color: #7c665c;
  white-space: nowrap;
}
.pager-count {
  white-space: nowrap;
}
.pager-count b {
  font-weight: 600;
  color: #8b1a1a;
}
.pager-state small {
  font-size: 10px;
  color: #9b8478;
}
</style>
