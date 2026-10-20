<script setup lang="ts">
import { ref } from "vue";
import { useRoute } from "vue-router";
import { api, post, notify } from "../api";
import PageHeader from "../components/PageHeader.vue";
import AsyncState from "../components/AsyncState.vue";
import SectionCard from "../components/SectionCard.vue";

const contests = ref<any[]>([]);
const detail = ref<any>(null);
const loading = ref(true);
const error = ref("");
const busy = ref(false);
const draft = ref("");
const route = useRoute();

const statusText: Record<string, string> = {
  OPEN: "进行中",
  SCORING: "评分中",
  PUBLISHED: "已公布",
};

async function load() {
  loading.value = true;
  error.value = "";
  try {
    contests.value = await api("/mobile/me/contests");
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
}

async function openByRoute() {
  const id = Number(route.params.id);
  if (Number.isFinite(id) && id > 0) await open(id);
}

async function open(id: number) {
  busy.value = true;
  try {
    detail.value = await api(`/mobile/me/contests/${id}`);
    draft.value = detail.value.my_entry?.content || "";
  } catch (e) {
    notify((e as Error).message);
  } finally {
    busy.value = false;
  }
}

async function submit() {
  if (!draft.value.trim()) {
    notify("请填写你的作品说明或创作内容");
    return;
  }
  busy.value = true;
  try {
    await post(`/mobile/assignments/${detail.value.my_entry.assignment_id}/submit`, {
      content: draft.value.trim(),
    });
    await open(detail.value.id);
    await load();
    notify("作品已提交，等待老师评分");
  } catch (e) {
    notify((e as Error).message);
  } finally {
    busy.value = false;
  }
}

async function init() {
  await load();
  await openByRoute();
}

init();
</script>
<template>
  <div class="contest-page">
    <PageHeader title="班级对抗赛" subtitle="与对手班级同题创作" />
    <div class="contest-body">
      <AsyncState
        :loading="loading"
        :error="error"
        :empty="!contests.length"
        empty-text="你还没有参加对抗赛"
        @retry="load"
      >
        <div class="contest-list">
          <button
            v-for="item in contests"
            :key="item.id"
            class="contest-card corner-card"
            @click="open(item.id)"
          >
            <div class="card-head">
              <span class="status-chip" :class="item.status.toLowerCase()">
                {{ statusText[item.status] || item.status }}
              </span>
              <span class="round">第 {{ item.round_no }} 轮</span>
            </div>
            <h2>{{ item.title }}</h2>
            <p class="versus">
              {{ item.my_class.name }} <b>VS</b> {{ item.opponent_class.name }}
            </p>
            <p class="contest-note" :class="{ submitted: item.submitted }">
              <i aria-hidden="true" />
              {{ item.submitted ? "已提交作品" : "待提交作品" }}
              <template v-if="item.score != null">
                · 得分 {{ item.score }}</template
              >
            </p>
          </button>
        </div>
      </AsyncState>
    </div>

    <Teleport to="body">
      <div v-if="detail" class="sheet-overlay" @click.self="detail = null">
        <section
          class="auth-sheet corner-card contest-sheet"
          role="dialog"
          aria-modal="true"
          aria-labelledby="student-contest-title"
        >
          <button
            class="sheet-close"
            aria-label="关闭对抗赛详情"
            @click="detail = null"
          >
            ×
          </button>
          <h2 id="student-contest-title">{{ detail.title }}</h2>
          <p class="subtle contest-meta">
            第 {{ detail.round_no }} 轮 ·
            {{ statusText[detail.status] || detail.status }} · 截止
            {{ detail.deadline?.slice(0, 16).replace("T", " ") }}
          </p>
          <p class="versus versus-sheet">
            {{ detail.my_class.name }} <b>VS</b> {{ detail.opponent_class.name }}
          </p>

          <div class="summary-grid">
            <article class="summary-card">
              <h3>{{ detail.my_class.name }}（我方）</h3>
              <p>
                参赛 {{ detail.my_class_summary.participant_count }} · 提交
                {{ detail.my_class_summary.submitted_count }}
              </p>
              <p v-if="detail.published">
                总分 {{ detail.my_class_summary.total_score ?? "—" }} · 平均
                {{ detail.my_class_summary.average_score ?? "—" }}
              </p>
            </article>
            <article class="summary-card">
              <h3>{{ detail.opponent_class.name }}（对手）</h3>
              <p>
                参赛 {{ detail.opponent_summary.participant_count }} · 提交
                {{ detail.opponent_summary.submitted_count }}
              </p>
              <p v-if="detail.published">
                总分 {{ detail.opponent_summary.total_score ?? "—" }} · 平均
                {{ detail.opponent_summary.average_score ?? "—" }}
              </p>
            </article>
          </div>

          <div v-if="detail.published" class="published-banner">
            <template v-if="detail.winner_class_id">
              本轮胜者：{{
                detail.winner_class_id === detail.my_class.id
                  ? detail.my_class.name
                  : detail.opponent_class.name
              }}
            </template>
            <template v-else>本轮未形成完整胜负</template>
          </div>

          <article class="my-work">
            <h3>我的作品</h3>
            <p v-if="detail.my_entry.submitted" class="work-content">
              {{ detail.my_entry.content || "已提交作品" }}
            </p>
            <p v-else class="subtle">尚未提交</p>
            <p
              v-if="detail.published && detail.my_entry.score != null"
              class="score-line"
            >
              得分 {{ detail.my_entry.score }} 分
              <span v-if="detail.my_entry.rank">
                · 班级第 {{ detail.my_entry.rank }} 名</span
              >
            </p>
            <p
              v-if="detail.published && detail.my_entry.comment"
              class="subtle"
            >
              教师评语：{{ detail.my_entry.comment }}
            </p>
            <template v-if="detail.status === 'OPEN'">
              <label class="work-input"
                >{{ detail.my_entry.submitted ? "修改作品说明" : "提交作品说明" }}
                <textarea
                  v-model.trim="draft"
                  maxlength="10000"
                  placeholder="描述你的创作内容或上传作品的说明"
                />
              </label>
              <button class="primary-button" :disabled="busy" @click="submit">
                {{
                  busy
                    ? "提交中…"
                    : detail.my_entry.submitted
                      ? "重新提交"
                      : "提交作品"
                }}
              </button>
            </template>
            <p v-else-if="!detail.published" class="subtle">
              提交已截止，等待老师评分。
            </p>
          </article>
        </section>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.contest-page {
  min-height: 100dvh;
  padding-bottom: 12px;
  background: #f5ede4;
  color: #2d1810;
}
.contest-body {
  padding: 14px 16px 24px;
}
.contest-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.contest-card {
  display: block;
  width: 100%;
  padding: 16px 14px;
  border: 0;
  background: #fdf9f2;
  color: #2d1810;
  text-align: left;
}
.contest-card:active {
  background: #fbf4ea;
}
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.status-chip {
  padding: 2px 9px;
  border: 1px solid rgba(200, 169, 110, 0.55);
  border-radius: 999px;
  background: rgba(200, 169, 110, 0.12);
  color: #8a6125;
  font: 400 10px/1.6 var(--sans);
  letter-spacing: 0.5px;
}
.status-chip.open {
  border-color: rgba(139, 26, 26, 0.32);
  background: #fff0f0;
  color: #8b1a1a;
}
.status-chip.scoring {
  border-color: rgba(200, 169, 110, 0.65);
  background: #fbf0d9;
  color: #8a6125;
}
.status-chip.published {
  border-color: transparent;
  background: #8b1a1a;
  color: #f6ead9;
}
.round {
  color: #8a7a70;
  font: 400 10px/1.6 var(--sans);
  letter-spacing: 1px;
}
.contest-card h2 {
  margin: 10px 0 8px;
  color: #2d1810;
  font: 500 16px/1.45 var(--serif);
  letter-spacing: 1.2px;
  overflow-wrap: anywhere;
}
.versus {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(200, 169, 110, 0.1);
  color: #5a3e36;
  font: 400 13px/1.5 var(--sans);
}
.versus b {
  flex-shrink: 0;
  color: #8b1a1a;
  font: 500 12px/1 var(--serif);
  letter-spacing: 1px;
}
.contest-note {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  color: #8a7a70;
  font: 400 10px/1.6 var(--sans);
  letter-spacing: 0.5px;
}
.contest-note i {
  width: 6px;
  height: 6px;
  flex-shrink: 0;
  border-radius: 50%;
  background: #c8a96e;
}
.contest-note.submitted {
  color: #8b1a1a;
}
.contest-note.submitted i {
  background: #8b1a1a;
}
.contest-sheet {
  max-height: 88vh;
  overflow-y: auto;
  overscroll-behavior: contain;
}
.contest-sheet h2 {
  margin: 4px 0 6px;
  color: #2d1810;
  font: 500 20px/1.35 var(--serif);
  letter-spacing: 1.5px;
}
.contest-meta {
  color: #8a7a70;
  font: 400 11px/1.7 var(--sans);
}
.contest-sheet .versus {
  margin-top: 10px;
}
.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin: 14px 0;
}
.summary-card {
  padding: 12px;
  border: 1px solid rgba(200, 169, 110, 0.28);
  border-radius: 10px;
  background: #fffdf8;
}
.summary-card h3 {
  margin-bottom: 6px;
  color: #5a3e36;
  font: 500 12px/1.55 var(--sans);
}
.summary-card p {
  margin: 3px 0;
  color: #8a7a70;
  font: 400 10px/1.6 var(--sans);
}
.published-banner {
  margin: 12px 0;
  padding: 10px 12px;
  border-left: 2px solid #8b1a1a;
  border-radius: 0 8px 8px 0;
  background: #fff0f0;
  color: #8b1a1a;
  font: 400 12px/1.7 var(--sans);
}
.my-work {
  margin-top: 14px;
  padding: 14px;
  border: 1px solid rgba(200, 169, 110, 0.28);
  border-radius: 10px;
  background: #fffdf8;
}
.my-work h3 {
  margin-bottom: 8px;
  color: #2d1810;
  font: 500 14px/1.5 var(--serif);
  letter-spacing: 1px;
}
.work-content {
  color: #4a3228;
  font: 400 13px/1.85 var(--sans);
  white-space: pre-line;
  overflow-wrap: anywhere;
}
.score-line {
  margin-top: 8px;
  color: #8b1a1a;
  font: 500 14px/1.5 var(--serif);
}
.score-line span {
  color: #8a6125;
  font: 400 11px/1.5 var(--sans);
}
.work-input {
  display: block;
  margin-top: 12px;
  gap: 6px;
  color: #8a7a70;
  font: 400 11px/1.4 var(--sans);
  letter-spacing: 1px;
}
.work-input textarea {
  width: 100%;
  min-height: 110px;
  margin-top: 6px;
  padding: 10px 12px;
  border: 1px solid rgba(200, 169, 110, 0.45);
  border-radius: 10px;
  background: #fffdf8;
  color: #2d1810;
  font: 400 14px/1.7 var(--sans);
}
.my-work .primary-button {
  width: 100%;
  min-height: 44px;
  margin-top: 12px;
  border: 1px solid rgba(232, 217, 168, 0.55);
  border-radius: 10px;
  background: #8b1a1a;
  color: #f6ead9;
  font: 500 13px/1.4 var(--sans);
  letter-spacing: 2px;
}
</style>

