<script setup lang="ts">
import { computed, ref } from "vue";
import { api, post, put, notify } from "../api";
import PageHeader from "../components/PageHeader.vue";
import AsyncState from "../components/AsyncState.vue";

type Student = { id: number; nickname: string };
type Entry = {
  entry_id: number;
  student_id: number;
  student_name: string;
  class_id: number;
  submission_id: number | null;
  submitted: boolean;
  status: string;
  content: string;
  score: number | null;
  comment: string | null;
  rank: number | null;
};
type ContestClass = {
  class_id: number;
  name: string;
  participant_count: number;
  submitted_count: number;
  scored_count: number;
  total_score: number | null;
  average_score: number | null;
  rank: number | null;
  entries: Entry[];
};
type Contest = {
  id: number;
  title: string;
  description: string;
  tool_type: string;
  round_no: number;
  scoring_mode: string;
  deadline: string;
  status: string;
  published_at: string | null;
  home_class: { id: number; name: string };
  away_class: { id: number; name: string };
  classes: ContestClass[];
  winner_class_id: number | null;
  submitted_count: number;
  scored_count: number;
  can_edit_roster: boolean;
  can_publish: boolean;
};

const classes = ref<any[]>([]);
const contests = ref<Contest[]>([]);
const loading = ref(true);
const busy = ref(false);
const error = ref("");
const creating = ref(false);
const detail = ref<Contest | null>(null);
const homeStudents = ref<Student[]>([]);
const awayStudents = ref<Student[]>([]);
const selectedHome = ref<number[]>([]);
const selectedAway = ref<number[]>([]);
const editingRoster = ref(false);
const rosterHome = ref<Student[]>([]);
const rosterAway = ref<Student[]>([]);
const rosterHomeIds = ref<number[]>([]);
const rosterAwayIds = ref<number[]>([]);
const scoring = ref<Record<number, { score: number | ""; comment: string }>>({});
const form = ref({
  title: "",
  description: "",
  tool_type: "BRONZE_PATTERN",
  home_class_id: 0,
  away_class_id: 0,
  round_no: 1,
  scoring_mode: "TOTAL",
  deadline_days: 7,
});

const statusText: Record<string, string> = {
  OPEN: "进行中",
  SCORING: "评分中",
  PUBLISHED: "已公布",
};
const toolText: Record<string, string> = {
  SHADOW_PUPPET: "皮影角色",
  BRONZE_PATTERN: "青铜纹样",
  LACQUER: "漆绣创作",
};
const classA = computed(() => detail.value?.classes[0]);
const classB = computed(() => detail.value?.classes[1]);
const winnerName = computed(() => {
  if (!detail.value?.winner_class_id) return "";
  return (
    detail.value.classes.find(
      (item) => item.class_id === detail.value?.winner_class_id,
    )?.name || ""
  );
});

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const [classRows, contestRows] = await Promise.all([
      api<any[]>("/teacher/classes"),
      api<Contest[]>("/teacher/contests"),
    ]);
    classes.value = classRows;
    contests.value = contestRows;
    if (!form.value.home_class_id && classRows.length)
      form.value.home_class_id = classRows[0].id;
    if (!form.value.away_class_id && classRows.length > 1)
      form.value.away_class_id = classRows[1].id;
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
}

async function loadStudents(classId: number, side: "home" | "away") {
  if (!classId) return;
  try {
    const rows = await api<Student[]>(
      `/mobile/teacher/classes/${classId}/students`,
    );
    if (side === "home") {
      homeStudents.value = rows;
      selectedHome.value = selectedHome.value.filter((id) =>
        rows.some((row) => row.id === id),
      );
    } else {
      awayStudents.value = rows;
      selectedAway.value = selectedAway.value.filter((id) =>
        rows.some((row) => row.id === id),
      );
    }
  } catch (e) {
    notify((e as Error).message);
  }
}

async function openCreate() {
  if (classes.value.length < 2) {
    notify("至少需要两个班级才能创建对抗赛");
    return;
  }
  if (!form.value.home_class_id) form.value.home_class_id = classes.value[0].id;
  if (
    !form.value.away_class_id ||
    form.value.away_class_id === form.value.home_class_id
  )
    form.value.away_class_id = classes.value[1].id;
  await Promise.all([
    loadStudents(form.value.home_class_id, "home"),
    loadStudents(form.value.away_class_id, "away"),
  ]);
  creating.value = true;
}

async function createContest() {
  if (!form.value.title.trim() || !form.value.description.trim()) {
    notify("请填写对抗赛名称和任务要求");
    return;
  }
  if (form.value.home_class_id === form.value.away_class_id) {
    notify("请选择两个不同班级");
    return;
  }
  if (!selectedHome.value.length || !selectedAway.value.length) {
    notify("两个班级都至少选择一名参赛学生");
    return;
  }
  busy.value = true;
  try {
    const created = await post<Contest>("/teacher/contests", {
      ...form.value,
      title: form.value.title.trim(),
      description: form.value.description.trim(),
      round_no: Number(form.value.round_no),
      deadline_days: Number(form.value.deadline_days),
      home_student_ids: selectedHome.value,
      away_student_ids: selectedAway.value,
    });
    creating.value = false;
    form.value.title = "";
    form.value.description = "";
    await load();
    await openDetail(created.id);
    notify("对抗赛已创建，参赛学生可在手机端提交作品");
  } catch (e) {
    notify((e as Error).message);
  } finally {
    busy.value = false;
  }
}

function prepareScoring(contest: Contest) {
  const next: Record<number, { score: number | ""; comment: string }> = {};
  for (const group of contest.classes)
    for (const entry of group.entries)
      next[entry.entry_id] = {
        score: entry.score ?? "",
        comment: entry.comment || "",
      };
  scoring.value = next;
}

async function openDetail(id: number) {
  busy.value = true;
  try {
    const row = await api<Contest>(`/teacher/contests/${id}`);
    detail.value = row;
    prepareScoring(row);
  } catch (e) {
    notify((e as Error).message);
  } finally {
    busy.value = false;
  }
}

async function refreshDetail() {
  if (detail.value) await openDetail(detail.value.id);
}

async function openRosterEditor() {
  if (!detail.value) return;
  const contest = detail.value;
  editingRoster.value = true;
  try {
    const [home, away] = await Promise.all([
      api<Student[]>(
        `/mobile/teacher/classes/${contest.home_class.id}/students`,
      ),
      api<Student[]>(
        `/mobile/teacher/classes/${contest.away_class.id}/students`,
      ),
    ]);
    rosterHome.value = home;
    rosterAway.value = away;
    rosterHomeIds.value =
      contest.classes
        .find((group) => group.class_id === contest.home_class.id)
        ?.entries.map((entry) => entry.student_id) || [];
    rosterAwayIds.value =
      contest.classes
        .find((group) => group.class_id === contest.away_class.id)
        ?.entries.map((entry) => entry.student_id) || [];
  } catch (e) {
    editingRoster.value = false;
    notify((e as Error).message);
  }
}

async function saveRoster() {
  if (!detail.value) return;
  if (!rosterHomeIds.value.length || !rosterAwayIds.value.length) {
    notify("两个班级都至少保留一名参赛学生");
    return;
  }
  busy.value = true;
  try {
    await put(`/teacher/contests/${detail.value.id}/entries`, {
      home_student_ids: rosterHomeIds.value,
      away_student_ids: rosterAwayIds.value,
    });
    editingRoster.value = false;
    await refreshDetail();
    await load();
    notify("参赛名单已更新");
  } catch (e) {
    notify((e as Error).message);
  } finally {
    busy.value = false;
  }
}

async function submitScore(entry: Entry) {
  const draft = scoring.value[entry.entry_id];
  if (!draft || draft.score === "") {
    notify("请填写 0-100 的分数");
    return;
  }
  if (!entry.submission_id) {
    notify("该学生尚未提交作品");
    return;
  }
  busy.value = true;
  try {
    await post(`/teacher/submissions/${entry.submission_id}/review`, {
      score: Number(draft.score),
      comment: draft.comment,
    });
    await refreshDetail();
    notify("评分已保存");
  } catch (e) {
    notify((e as Error).message);
  } finally {
    busy.value = false;
  }
}

async function changeStatus(status: "SCORING" | "PUBLISHED") {
  if (!detail.value) return;
  if (
    status === "PUBLISHED" &&
    !window.confirm("公布后本轮成绩将锁定，不能再修改评分或参赛名单。确定公布？")
  )
    return;
  busy.value = true;
  try {
    await post(`/teacher/contests/${detail.value.id}/status`, { status });
    await refreshDetail();
    await load();
    notify(status === "PUBLISHED" ? "成绩已公布并锁定" : "已进入评分阶段");
  } catch (e) {
    notify((e as Error).message);
  } finally {
    busy.value = false;
  }
}

function join(list: number[], id: number, checked: boolean) {
  return checked ? [...list, id] : list.filter((item) => item !== id);
}

load();
</script>

<template>
  <div class="contest-root">
    <PageHeader title="班级对抗赛" subtitle="两班同题创作 · 评分与排名" />
    <div class="page-padding">
      <div class="contest-actions">
        <button class="primary-button" @click="openCreate">新建对抗赛</button>
        <RouterLink class="outline-button link-button" to="/teacher/assignments"
          >普通作业</RouterLink
        >
        <button class="outline-button" @click="load">刷新</button>
      </div>
      <AsyncState
        :loading="loading"
        :error="error"
        :empty="!contests.length"
        empty-text="还没有对抗赛，创建第一轮两班 PK 吧"
        @retry="load"
      >
        <div class="contest-list">
          <button
            v-for="item in contests"
            :key="item.id"
            class="contest-card corner-card"
            @click="openDetail(item.id)"
          >
            <div class="contest-card-head">
              <span class="status-chip" :class="item.status.toLowerCase()">
                {{ statusText[item.status] || item.status }}
              </span>
              <span class="round">第 {{ item.round_no }} 轮</span>
            </div>
            <h2>{{ item.title }}</h2>
            <p class="versus">
              {{ item.home_class.name }} <b>VS</b> {{ item.away_class.name }}
            </p>
            <p class="subtle">
              截止 {{ item.deadline?.slice(0, 16).replace("T", " ") }} ·
              已提交 {{ item.submitted_count }} 份
            </p>
            <p v-if="item.winner_class_id" class="winner">
              胜者：{{
                item.winner_class_id === item.home_class.id
                  ? item.home_class.name
                  : item.away_class.name
              }}
            </p>
            <span class="detail-link">查看名单与评分 ›</span>
          </button>
        </div>
      </AsyncState>
    </div>

    <Teleport to="body">
      <div v-if="creating" class="sheet-overlay" @click.self="creating = false">
        <section
          class="auth-sheet corner-card contest-sheet"
          role="dialog"
          aria-modal="true"
          aria-labelledby="contest-create-title"
        >
          <button
            class="sheet-close"
            aria-label="关闭新建对抗赛"
            @click="creating = false"
          >
            ×
          </button>
          <h2 id="contest-create-title">新建班级对抗赛</h2>
          <form @submit.prevent="createContest">
            <label
              >对抗赛名称<input
                v-model.trim="form.title"
                required
                maxlength="128"
            /></label>
            <label
              >任务要求<textarea
                v-model.trim="form.description"
                required
                maxlength="10000"
            /></label>
            <label
              >创作工具<select v-model="form.tool_type">
                <option value="SHADOW_PUPPET">皮影角色</option>
                <option value="BRONZE_PATTERN">青铜纹样</option>
                <option value="LACQUER">漆绣创作</option>
              </select></label>
            <div class="two-columns">
              <label
                >主队班级<select
                  v-model.number="form.home_class_id"
                  @change="loadStudents(form.home_class_id, 'home')"
                >
                  <option v-for="c in classes" :key="c.id" :value="c.id">
                    {{ c.name }}
                  </option>
                </select></label>
              <label
                >客队班级<select
                  v-model.number="form.away_class_id"
                  @change="loadStudents(form.away_class_id, 'away')"
                >
                  <option v-for="c in classes" :key="c.id" :value="c.id">
                    {{ c.name }}
                  </option>
                </select></label>
            </div>
            <div class="two-columns">
              <label
                >轮次<input
                  v-model.number="form.round_no"
                  type="number"
                  min="1"
                  max="99" /></label>
              <label
                >排名方式<select v-model="form.scoring_mode">
                  <option value="TOTAL">班级总分</option>
                  <option value="AVERAGE">班级平均分</option>
                </select></label>
            </div>
            <label
              >截止天数<input
                v-model.number="form.deadline_days"
                type="number"
                min="1"
                max="365"
            /></label>
            <div class="roster-block">
              <h3>{{ classes.find((c) => c.id === form.home_class_id)?.name }} 参赛名单</h3>
              <p v-if="!homeStudents.length" class="subtle">该班暂无学生</p>
              <label
                v-for="student in homeStudents"
                :key="student.id"
                class="student-check"
              >
                <input
                  type="checkbox"
                  :checked="selectedHome.includes(student.id)"
                  @change="
                    selectedHome = join(
                      selectedHome,
                      student.id,
                      ($event.target as HTMLInputElement).checked,
                    )
                  "
                />
                {{ student.nickname }}
              </label>
            </div>
            <div class="roster-block">
              <h3>{{ classes.find((c) => c.id === form.away_class_id)?.name }} 参赛名单</h3>
              <p v-if="!awayStudents.length" class="subtle">该班暂无学生</p>
              <label
                v-for="student in awayStudents"
                :key="student.id"
                class="student-check"
              >
                <input
                  type="checkbox"
                  :checked="selectedAway.includes(student.id)"
                  @change="
                    selectedAway = join(
                      selectedAway,
                      student.id,
                      ($event.target as HTMLInputElement).checked,
                    )
                  "
                />
                {{ student.nickname }}
              </label>
            </div>
            <button class="primary-button" :disabled="busy">
              {{ busy ? "创建中…" : "创建对抗赛" }}
            </button>
          </form>
        </section>
      </div>

      <div v-if="detail" class="sheet-overlay" @click.self="detail = null">
        <section
          class="auth-sheet corner-card contest-sheet contest-detail-sheet"
          role="dialog"
          aria-modal="true"
          aria-labelledby="contest-detail-title"
        >
          <button
            class="sheet-close"
            aria-label="关闭对抗赛详情"
            @click="detail = null"
          >
            ×
          </button>
          <h2 id="contest-detail-title">{{ detail.title }}</h2>
          <p class="subtle">
            第 {{ detail.round_no }} 轮 ·
            {{ toolText[detail.tool_type] || detail.tool_type }} ·
            {{ statusText[detail.status] }} · 截止
            {{ detail.deadline?.slice(0, 16).replace("T", " ") }}
          </p>
          <div v-if="detail.status === 'PUBLISHED'" class="published-banner">
            {{ winnerName ? `本轮胜者：${winnerName}` : "本轮未形成完整胜负" }}
          </div>
          <div class="summary-grid">
            <article
              v-for="(group, index) in detail.classes"
              :key="group.class_id"
              class="summary-card"
            >
              <h3>
                {{ index === 0 ? "主队" : "客队" }} · {{ group.name }}
                <span v-if="group.rank" class="rank-chip">第 {{ group.rank }} 名</span>
              </h3>
              <p>
                参赛 {{ group.participant_count }} · 提交
                {{ group.submitted_count }} · 已评 {{ group.scored_count }}
              </p>
              <p v-if="detail.status === 'PUBLISHED'">
                总分 {{ group.total_score ?? "—" }} · 平均
                {{ group.average_score ?? "—" }}
              </p>
            </article>
          </div>
          <div v-if="detail.can_edit_roster" class="roster-actions">
            <button
              class="outline-button"
              :disabled="busy"
              @click="openRosterEditor"
            >
              编辑参赛名单
            </button>
          </div>
          <div
            v-for="group in detail.classes"
            :key="'entries-' + group.class_id"
            class="entry-group"
          >
            <h3>{{ group.name }}</h3>
            <article
              v-for="entry in group.entries"
              :key="entry.entry_id"
              class="entry-card"
            >
              <div class="entry-head">
                <b>{{ entry.student_name }}</b>
                <span v-if="entry.rank" class="rank-chip">第 {{ entry.rank }} 名</span>
                <span class="entry-status">{{
                  entry.submitted
                    ? entry.score != null
                      ? entry.score + " 分"
                      : "待评分"
                    : "未提交"
                }}</span>
              </div>
              <p v-if="entry.content" class="entry-content">{{ entry.content }}</p>
              <p v-else-if="entry.submitted" class="subtle">已提交作品</p>
              <div
                v-if="entry.submitted && detail.status !== 'PUBLISHED'"
                class="score-row"
              >
                <input
                  v-model.number="scoring[entry.entry_id].score"
                  type="number"
                  min="0"
                  max="100"
                  placeholder="分数"
                />
                <input
                  v-model.trim="scoring[entry.entry_id].comment"
                  maxlength="5000"
                  placeholder="评语"
                />
                <button
                  class="outline-button"
                  :disabled="busy"
                  @click="submitScore(entry)"
                >
                  保存评分
                </button>
              </div>
              <p v-if="entry.comment" class="entry-comment">{{ entry.comment }}</p>
            </article>
          </div>
          <div class="detail-actions">
            <button
              v-if="detail.status === 'OPEN'"
              class="outline-button"
              :disabled="busy"
              @click="changeStatus('SCORING')"
            >
              截止提交，进入评分
            </button>
            <button
              v-if="detail.status !== 'PUBLISHED'"
              class="primary-button"
              :disabled="busy"
              @click="changeStatus('PUBLISHED')"
            >
              公布成绩并锁定
            </button>
            <span v-else class="subtle">成绩已公布，评分与名单已锁定</span>
          </div>
        </section>
      </div>

      <div
        v-if="editingRoster"
        class="sheet-overlay"
        @click.self="editingRoster = false"
      >
        <section
          class="auth-sheet corner-card contest-sheet"
          role="dialog"
          aria-modal="true"
          aria-labelledby="roster-edit-title"
        >
          <button
            class="sheet-close"
            aria-label="关闭名单编辑"
            @click="editingRoster = false"
          >
            ×
          </button>
          <h2 id="roster-edit-title">编辑参赛名单</h2>
          <p class="subtle">
            已有学生提交作品后不能将其移出名单；截止或公布后名单锁定。
          </p>
          <div class="roster-block">
            <h3>{{ detail?.home_class.name }} 参赛名单</h3>
            <p v-if="!rosterHome.length" class="subtle">该班暂无学生</p>
            <label
              v-for="student in rosterHome"
              :key="'rh-' + student.id"
              class="student-check"
            >
              <input
                type="checkbox"
                :checked="rosterHomeIds.includes(student.id)"
                @change="
                  rosterHomeIds = join(
                    rosterHomeIds,
                    student.id,
                    ($event.target as HTMLInputElement).checked,
                  )
                "
              />
              {{ student.nickname }}
            </label>
          </div>
          <div class="roster-block">
            <h3>{{ detail?.away_class.name }} 参赛名单</h3>
            <p v-if="!rosterAway.length" class="subtle">该班暂无学生</p>
            <label
              v-for="student in rosterAway"
              :key="'ra-' + student.id"
              class="student-check"
            >
              <input
                type="checkbox"
                :checked="rosterAwayIds.includes(student.id)"
                @change="
                  rosterAwayIds = join(
                    rosterAwayIds,
                    student.id,
                    ($event.target as HTMLInputElement).checked,
                  )
                "
              />
              {{ student.nickname }}
            </label>
          </div>
          <button class="primary-button" :disabled="busy" @click="saveRoster">
            {{ busy ? "保存中…" : "保存名单" }}
          </button>
        </section>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.contest-root {
  padding-bottom: calc(88px + var(--safe-bottom));
}
.page-padding {
  padding: 0 20px 40px;
}
.contest-actions {
  display: flex;
  gap: 12px;
  margin: 18px 0 24px;
}
.contest-actions > * {
  flex: 1;
}
.link-button {
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
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
  padding: 20px 18px;
  border: 0;
  background: var(--paper, #fffaf4);
}
.contest-card-head {
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
.winner {
  color: #8a2b2b;
  font-size: 13px;
  margin-top: 8px;
}
.detail-link {
  display: block;
  margin-top: 14px;
  font-size: 12px;
  color: var(--clay, #9b7a5c);
}
.contest-sheet {
  max-height: 88vh;
  overflow-y: auto;
}
.two-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.roster-block {
  margin: 14px 0;
  padding: 12px;
  background: rgba(255, 255, 255, 0.55);
  border-radius: 10px;
}
.roster-block h3 {
  font-size: 14px;
  margin-bottom: 8px;
}
.student-check {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  margin: 8px 0;
  font-size: 13px;
}
.student-check input {
  width: 18px;
  height: 18px;
  min-height: 18px;
  padding: 0;
  border: 0;
  background: transparent;
  flex: 0 0 18px;
  margin: 0;
  accent-color: var(--cinnabar, #a33);
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
.rank-chip {
  display: inline-block;
  font-size: 10px;
  padding: 1px 6px;
  margin-left: 6px;
  border-radius: 999px;
  background: #8a2b2b;
  color: #fff;
  vertical-align: middle;
}
.published-banner {
  margin: 12px 0;
  padding: 10px 12px;
  border-radius: 8px;
  background: #f3e3df;
  color: #8a2b2b;
  font-size: 13px;
}
.entry-group {
  margin-top: 18px;
}
.entry-group > h3 {
  font-size: 15px;
  margin-bottom: 8px;
}
.entry-card {
  padding: 12px;
  margin-bottom: 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.6);
}
.entry-head {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: space-between;
  font-size: 13px;
}
.entry-status {
  color: var(--clay, #9b7a5c);
  font-size: 12px;
}
.entry-content,
.entry-comment {
  margin-top: 8px;
  font-size: 12px;
  line-height: 1.8;
  white-space: pre-line;
  max-height: 120px;
  overflow: auto;
}
.score-row {
  display: grid;
  grid-template-columns: 80px 1fr auto;
  gap: 8px;
  margin-top: 10px;
}
.score-row input {
  min-width: 0;
  padding: 8px;
  border: 1px solid #d9c7b5;
  border-radius: 8px;
  background: #fff;
}
.detail-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  align-items: center;
}
.detail-actions > * {
  flex: 1;
}
.roster-actions {
  margin: 8px 0 4px;
}
.roster-actions .outline-button {
  width: 100%;
}
</style>
