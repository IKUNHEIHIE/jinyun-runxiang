<script setup lang="ts">
import { useEvaluation } from "../useEvaluation";

const props = defineProps<{
  imageUrl: string;
  title: string;
  heritageType: string;
}>();

const review = useEvaluation(props.heritageType);
</script>

<template>
  <section class="review-block">
    <button class="review-trigger" :disabled="review.busy.value || !props.imageUrl" @click="review.run(props.imageUrl, props.title)">
      <i aria-hidden="true">评</i>
      <span>{{ review.busy.value ? "导师正在看画…" : "请导师点评这件作品" }}</span>
      <em>AI 图像测评</em>
    </button>
    <p v-if="review.error.value" class="review-error" role="alert">{{ review.error.value }}</p>
    <div v-if="review.result.value" class="review-card">
      <div class="review-head">
        <div>
          <span>导师点评 · {{ review.result.value.title }}</span>
          <b>{{ review.result.value.total_score }}<em>/100</em></b>
        </div>
        <span class="stars">{{ "★".repeat(review.result.value.stars) }}{{ "☆".repeat(5 - review.result.value.stars) }}</span>
      </div>
      <p class="review-comment">{{ review.result.value.mentor_comment }}</p>
      <ul class="review-dims">
        <li v-for="item in Object.values(review.result.value.dimensions)" :key="item.name">
          <span>{{ item.name }}</span>
          <b>{{ item.score }}</b>
          <em>{{ item.feedback }}</em>
        </li>
      </ul>
      <p v-if="review.result.value.energy_reward" class="review-reward">
        点评完成，能量 +{{ review.result.value.energy_reward }}
      </p>
    </div>
  </section>
</template>

<style scoped>
.review-block { margin: 14px 16px 0; }
.review-trigger {
  width: 100%; height: 44px; display: flex; align-items: center; gap: 10px; padding: 0 12px;
  border: 1px solid rgba(26, 54, 93, 0.38); border-radius: 9px;
  background: linear-gradient(116deg, rgba(251, 247, 238, 0.95), rgba(240, 232, 216, 0.95));
  color: #1a365d; font-family: var(--serif); font-size: 12px; letter-spacing: 1.6px; text-align: left;
}
.review-trigger:disabled { opacity: 0.6; }
.review-trigger i {
  width: 24px; height: 24px; flex: none; display: grid; place-items: center;
  border: 1px solid rgba(139, 26, 26, 0.6); border-radius: 3px; color: #8b1a1a;
  font-style: normal; font-size: 13px;
}
.review-trigger em { margin-left: auto; font-style: normal; font-size: 8px; letter-spacing: 1.4px; color: #8a6a37; }
.review-error { margin: 8px 0 0; font-size: 10px; color: #a12626; }
.review-card {
  margin-top: 10px; padding: 12px; border: 1px solid rgba(201, 168, 76, 0.42); border-radius: 10px;
  background: linear-gradient(180deg, rgba(252, 248, 239, 0.98), rgba(246, 239, 226, 0.98));
}
.review-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 10px; }
.review-head span { font-size: 9px; letter-spacing: 1.2px; color: #8a6a37; }
.review-head b { display: block; margin-top: 2px; font-family: var(--serif); font-size: 26px; line-height: 1; color: #8b1a1a; }
.review-head b em { font-style: normal; font-size: 11px; color: rgba(44, 36, 27, 0.45); }
.review-head .stars { font-size: 12px; letter-spacing: 2px; color: #b8860b; }
.review-comment { margin: 9px 0 0; font-family: var(--serif); font-size: 11px; line-height: 1.8; color: #4a3a26; }
.review-dims { margin: 10px 0 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 6px; }
.review-dims li { display: grid; grid-template-columns: 70px 28px 1fr; gap: 6px; align-items: baseline; }
.review-dims span { font-size: 9px; letter-spacing: 0.6px; color: #8a6a37; }
.review-dims b { font-family: var(--serif); font-size: 12px; color: #1a365d; }
.review-dims em { font-style: normal; font-size: 9px; line-height: 1.6; color: rgba(44, 36, 27, 0.62); }
.review-reward { margin: 9px 0 0; font-size: 10px; letter-spacing: 0.8px; color: #4a7c6f; }
</style>
