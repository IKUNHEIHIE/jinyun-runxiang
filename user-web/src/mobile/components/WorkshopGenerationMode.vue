<script setup lang="ts">
defineProps<{ available: boolean; editable: boolean; disabled: boolean }>();
const mode = defineModel<string>({ required: true });
</script>
<template>
  <div class="generation-mode">
    <label>创作方式
      <select v-model="mode" :disabled="disabled" aria-label="创作方式">
        <option value="AI" :disabled="!available">AI 图像生成</option>
        <option value="LOCAL">本地模板</option>
      </select>
    </label>
    <p v-if="mode === 'AI'">{{ editable ? '支持文字生成与参考图重绘。' : '当前支持文字生成，暂未启用参考图编辑。' }}失败后可手动重试。取消会停止保存结果，已发出的模型请求可能仍会执行。</p>
    <p v-else>{{ available ? '使用本地固定造型与配色，可切换为 AI 图像生成。' : 'AI 生图暂未配置，可先使用本地模板。' }}</p>
  </div>
</template>
<style scoped>
.generation-mode { margin: 16px 0; color: inherit; }
label { display: flex; align-items: center; justify-content: space-between; gap: 12px; font-size: 14px; }
select { max-width: 65%; padding: 9px 12px; background: #fffaf3; color: #493b31; border: 1px solid #cdbb9f; border-radius: 8px; font: inherit; }
p { margin: 8px 0 0; font-size: 12px; line-height: 1.6; opacity: .8; }
</style>
