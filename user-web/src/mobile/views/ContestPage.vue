<script setup lang="ts">
import { ref } from "vue";
import { useRoute } from "vue-router";
import { api, post, notify } from "../api";
import PageHeader from "../components/PageHeader.vue";
import AsyncState from "../components/AsyncState.vue";

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
  <div>
    <PageHeader title="班级对抗赛" subtitle="与对手班级同题创作" />
    <div class="page-padding">
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
            <p class="subtle">
              {{ item.submitted ? "已提交作品" : "待提交作品" }}
              <template v-if="item.score != null"> · 得分 {{ item.score }}</template>
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
          <p class="subtle">
            第 {{ detail.round_no }} 轮 ·
            {{ statusText[detail.status] || detail.status }} · 截止
            {{ detail.deadline?.slice(0, 16).replace("T", " ") }}
          </p>
          <p class="versus">
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
            <p v-if="detail.published && detail.my_entry.score != null" class="score-line">
              得分 {{ detail.my_entry.score }} 分
              <span v-if="detail.my_entry.rank"> · 班级第 {{ detail.my_entry.rank }} 名</span>
            </p>
            <p v-if="detail.published && detail.my_entry.comment" class="subtle">
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
                {{ busy ? "提交中…" : detail.my_entry.submitted ? "重新提交" : "提交作品" }}
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
.page-padding {
  padding: 0 20px 40px;
}
.contest-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.contest-card {
  display: block;
  width: 100%;
  text-align: left;
  border: 0;
  padding: 20px 18px;
  background: var(--paper, #fffaf4);
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.status-chip {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 999px;
  background: #efe4d4;
  color: #7a5b3c;
}
.status-chip.open {
  background: #e3efe0;
  color: #3f6b3b;
}
.status-chip.scoring {
  background: #f6e8c8;
  color: #8a5b13;
}
.status-chip.published {
  background: #ead7d4;
  color: #8a2b2b;
}
.round {
  font-size: 11px;
  color: var(--clay, #9b7a5c);
}
.contest-card h2 {
  margin: 12px 0 8px;
  font-size: 19px;
}
.versus {
  font-size: 14px;
  margin: 6px 0;
}
.versus b {
  color: var(--cinnabar, #a33);
  margin: 0 6px;
}
.contest-sheet {
  max-height: 88vh;
  overflow-y: auto;
}
.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin: 14px 0;
}
.summary-card {
  padding: 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.6);
}
.summary-card h3 {
  font-size: 14px;
  margin-bottom: 6px;
}
.summary-card p {
  font-size: 12px;
  color: var(--clay, #9b7a5c);
  margin: 3px 0;
}
.published-banner {
  margin: 12px 0;
  padding: 10px 12px;
  border-radius: 8px;
  background: #f3e3df;
  color: #8a2b2b;
  font-size: 13px;
}
.my-work {
  margin-top: 16px;
  padding: 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.6);
}
.my-work h3 {
  font-size: 15px;
  margin-bottom: 8px;
}
.work-content {
  font-size: 13px;
  line-height: 1.9;
  white-space: pre-line;
}
.score-line {
  margin-top: 8px;
  color: #8a2b2b;
  font-size: 14px;
}
.work-input {
  display: block;
  margin-top: 12px;
}
.work-input textarea {
  width: 100%;
  min-height: 110px;
  margin-top: 6px;
  padding: 10px;
  border: 1px solid #d9c7b5;
  border-radius: 8px;
  background: #fff;
  box-sizing: border-box;
}
.my-work .primary-button {
  margin-top: 12px;
  width: 100%;
}
</style>
