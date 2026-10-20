<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

export type TheaterStat = { label: string; value: string };

const props = withDefaults(
  defineProps<{
    steps: string[];
    stats?: TheaterStat[];
    title?: string;
    preview?: string;
    stepMs?: number;
    caption?: string;
  }>(),
  {
    stats: () => [],
    title: "生成中",
    preview: "",
    stepMs: 520,
    caption: "本地规则引擎 · 不调用外部生成模型",
  },
);

const emit = defineEmits<{ (event: "done"): void }>();

const current = ref(0);
const finished = ref(false);
const elapsed = ref(0);
let timer = 0;
let ticker = 0;

const progress = computed(() =>
  finished.value ? 100 : Math.round(((current.value + 0.4) / props.steps.length) * 100),
);

function finish() {
  finished.value = true;
  window.setTimeout(() => emit("done"), 900);
}

onMounted(() => {
  const started = performance.now();
  ticker = window.setInterval(() => {
    elapsed.value = (performance.now() - started) / 1000;
  }, 100);
  timer = window.setInterval(() => {
    if (current.value < props.steps.length - 1) current.value += 1;
    else {
      window.clearInterval(timer);
      finish();
    }
  }, props.stepMs);
});

onBeforeUnmount(() => {
  window.clearInterval(timer);
  window.clearInterval(ticker);
});
</script>

<template>
  <Teleport to="body">
    <div class="theater" role="status" aria-live="polite">
      <div class="theater-card">
        <header class="theater-head">
          <span class="theater-kicker">AI 工坊 · 生成现场</span>
          <h3>{{ finished ? "已交付" : title }}</h3>
          <span class="theater-clock">{{ elapsed.toFixed(1) }}s</span>
        </header>

        <div class="theater-stage" :class="{ done: finished }">
          <img v-if="preview" :src="preview" alt="" class="theater-preview" />
          <div v-else class="theater-orb" aria-hidden="true"><i /><i /><i /></div>
          <span class="theater-scan" aria-hidden="true" />
          <span v-if="finished" class="theater-seal" aria-hidden="true">成</span>
        </div>

        <ol class="theater-steps">
          <li
            v-for="(step, index) in steps"
            :key="step"
            :class="{ on: index === current && !finished, done: index < current || finished }"
          >
            <i aria-hidden="true" />
            <span>{{ step }}</span>
            <b>{{ index < current || finished ? "✓" : index === current ? "…" : "" }}</b>
          </li>
        </ol>

        <div class="theater-bar" aria-hidden="true"><i :style="{ width: progress + '%' }" /></div>

        <div v-if="finished && stats.length" class="theater-stats">
          <div v-for="stat in stats" :key="stat.label">
            <strong>{{ stat.value }}</strong><span>{{ stat.label }}</span>
          </div>
        </div>

        <p class="theater-caption">{{ caption }}</p>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.theater {
  position: fixed;
  inset: 0;
  z-index: 90;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(30, 18, 12, 0.55);
  -webkit-backdrop-filter: blur(6px);
  backdrop-filter: blur(6px);
  animation: theater-in 0.2s ease;
}
@keyframes theater-in {
  from {
    opacity: 0;
  }
}
.theater-card {
  width: min(360px, 100%);
  padding: 16px;
  border-radius: 20px;
  background: #fdf9f2;
  box-shadow: 0 24px 60px rgba(30, 16, 10, 0.35);
  border: 1px solid rgba(200, 169, 110, 0.5);
}
.theater-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 12px;
}
.theater-kicker {
  font: 400 9px/1.4 var(--sans);
  letter-spacing: 1.6px;
  color: #8a6125;
}
.theater-head h3 {
  flex: 1;
  margin: 0;
  font: 500 16px/1.3 var(--serif);
  letter-spacing: 1.6px;
  color: #2d1810;
}
.theater-clock {
  font: 500 11px/1 var(--sans);
  color: #8b1a1a;
  font-variant-numeric: tabular-nums;
}
.theater-stage {
  position: relative;
  height: 190px;
  border-radius: 14px;
  overflow: hidden;
  background: radial-gradient(circle at 50% 38%, #4a1d17, #2a120e 72%);
  display: grid;
  place-items: center;
}
.theater-preview {
  width: 100%;
  height: 100%;
  object-fit: contain;
  opacity: 0.86;
}
.theater-orb {
  position: relative;
  width: 64px;
  height: 64px;
}
.theater-orb i {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1px solid rgba(224, 190, 130, 0.55);
  animation: orb 1.8s ease-out infinite;
}
.theater-orb i:nth-child(2) {
  animation-delay: 0.6s;
}
.theater-orb i:nth-child(3) {
  animation-delay: 1.2s;
}
@keyframes orb {
  from {
    transform: scale(0.35);
    opacity: 0.9;
  }
  to {
    transform: scale(1.35);
    opacity: 0;
  }
}
.theater-scan {
  position: absolute;
  inset: 0 auto 0 0;
  width: 42%;
  background: linear-gradient(90deg, transparent, rgba(244, 230, 207, 0.35), transparent);
  animation: scan 1.3s linear infinite;
}
@keyframes scan {
  from {
    transform: translateX(-120%);
  }
  to {
    transform: translateX(320%);
  }
}
.theater-stage.done .theater-scan {
  display: none;
}
.theater-seal {
  position: absolute;
  right: 14px;
  bottom: 12px;
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  border: 2px solid #b85450;
  color: #b85450;
  font: 500 24px/1 var(--serif);
  background: rgba(253, 249, 242, 0.9);
  transform: rotate(-8deg) scale(0.6);
  animation: seal 0.42s cubic-bezier(0.2, 1.4, 0.4, 1) forwards;
}
@keyframes seal {
  to {
    transform: rotate(-8deg) scale(1);
  }
}
.theater-steps {
  list-style: none;
  margin: 12px 0 8px;
  padding: 0;
  display: grid;
  gap: 6px;
}
.theater-steps li {
  display: flex;
  align-items: center;
  gap: 8px;
  font: 400 12px/1.4 var(--sans);
  color: #9b8478;
  transition: color 0.2s ease;
}
.theater-steps li i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(139, 105, 48, 0.25);
}
.theater-steps li.on {
  color: #2d1810;
}
.theater-steps li.on i {
  background: #b85450;
  box-shadow: 0 0 0 4px rgba(184, 84, 80, 0.18);
}
.theater-steps li.done {
  color: #5c4626;
}
.theater-steps li.done i {
  background: #c8a96e;
}
.theater-steps li b {
  margin-left: auto;
  font-weight: 500;
  color: #8a6125;
}
.theater-bar {
  height: 4px;
  border-radius: 999px;
  background: rgba(200, 169, 110, 0.25);
  overflow: hidden;
}
.theater-bar i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #8b1a1a, #c8a96e);
  transition: width 0.35s ease;
}
.theater-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 12px;
  animation: stats-in 0.3s ease;
}
@keyframes stats-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
}
.theater-stats div {
  padding: 8px 4px;
  border-radius: 10px;
  background: rgba(200, 169, 110, 0.12);
  text-align: center;
}
.theater-stats strong {
  display: block;
  font: 500 15px/1.3 var(--serif);
  color: #8b1a1a;
}
.theater-stats span {
  font: 400 9px/1.4 var(--sans);
  letter-spacing: 0.8px;
  color: #8a7a70;
}
.theater-caption {
  margin: 10px 0 0;
  text-align: center;
  font: 400 9px/1.5 var(--sans);
  letter-spacing: 0.6px;
  color: #9b8478;
}
@media (prefers-reduced-motion: reduce) {
  .theater,
  .theater-orb i,
  .theater-scan,
  .theater-seal,
  .theater-stats {
    animation: none;
  }
  .theater-bar i,
  .theater-steps li {
    transition: none;
  }
}
</style>
