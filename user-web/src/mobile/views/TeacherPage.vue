<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { api, session, mediaUrl } from "../api";
import { designImage, designIcon } from "../design";
import AsyncState from "../components/AsyncState.vue";

const stats = ref<any>({}),
  personal = ref<any>({}),
  loading = ref(false),
  error = ref("");
const selectedAchievement = ref("");
let mounted = true,
  version = 0,
  pendingToken: string | undefined;
let timer: ReturnType<typeof setInterval>;
const achievementArt: Record<string, { ring: string; image: string }> = {
  LESSON_PLAN: { ring: "40:01066", image: "40:01081" },
  ACTIVE_STUDENT: { ring: "40:01129", image: "40:01141" },
  REVIEW: { ring: "40:01190", image: "40:01201" },
  COURSE: { ring: "40:01249", image: "40:01265" },
};
const achievements = computed(() =>
  (stats.value.achievements || []).map((item: any) => ({
    ...item,
    ...achievementArt[item.code],
  })),
);
const completedAchievements = computed(
  () => achievements.value.filter((item: any) => item.completed).length,
);
const activeAchievement = computed(() =>
  achievements.value.find(
    (item: any) => item.code === selectedAchievement.value,
  ),
);
const yearLabel = computed(() => "教学档案 · 乡土美育");
const metricRows = computed(() => [
  {
    label: "今日到课率",
    value: stats.value.attendance_rate,
    unit: "%",
    icon: "40:5074",
    key: "attendance",
    description:
      stats.value.attendance_expected == null
        ? "考勤数据加载后显示"
        : "应到 " +
          stats.value.attendance_expected +
          " 人次 · 实到 " +
          stats.value.attendance_present +
          " · 请假 " +
          stats.value.attendance_leave +
          " · 缺勤 " +
          stats.value.attendance_absent +
          (stats.value.attendance_unrecorded
            ? " · 待记录 " + stats.value.attendance_unrecorded
            : ""),
  },
  {
    label: "作业提交率",
    value: stats.value.submission_rate,
    unit: "%",
    icon: "40:5081",
    key: "submission",
    description:
      stats.value.submission_count == null
        ? "作业数据加载后显示"
        : "已提交 " +
          stats.value.submission_count +
          " 份 · 待提交 " +
          stats.value.submission_pending +
          " 份" +
          (stats.value.next_assignment_deadline
            ? " · 截止 " + deadline(stats.value.next_assignment_deadline)
            : ""),
  },
  {
    label: "课堂活跃度",
    value: stats.value.activity_score,
    unit: "分",
    icon: "40:5091",
    key: "activity",
    description: activityDescription(),
  },
]);
function activityDescription() {
  if (stats.value.interaction_count == null) return "课堂数据加载后显示";
  if (!stats.value.session_count)
    return "还没有课堂记录 · 开启在线课堂后自动统计举手与互动";
  return (
    "今日互动 " +
    stats.value.interaction_count +
    " 次 · 举手 " +
    stats.value.hand_raiser_count +
    " 人 · 参与 " +
    stats.value.activity_participant_count +
    " 人"
  );
}
// 待办只在真实数据上出现：没有待批改就显示 0 行，而不是造一条空任务。
const todos = computed(() => {
  const rows: { label: string; action: string; path: string }[] = [];
  if (stats.value.review_pending)
    rows.push({
      label: "待批改 " + stats.value.review_pending + " 份作业",
      action: "去批改",
      path: "/teacher/assignments",
    });
  if (stats.value.attendance_unrecorded)
    rows.push({
      label: "今日考勤还有 " + stats.value.attendance_unrecorded + " 人未记录",
      action: "记考勤",
      path: "/teacher/analytics",
    });
  if (stats.value.active_contest_count)
    rows.push({
      label: stats.value.active_contest_count + " 场对抗赛进行中",
      action: "看排名",
      path: "/teacher/contests",
    });
  if (stats.value.submission_pending)
    rows.push({
      label: "还有 " + stats.value.submission_pending + " 份作业待学生提交",
      action: "催交",
      path: "/teacher/notices",
    });
  return rows;
});
const assignmentSummary = computed(() => {
  const total = stats.value.assignment_count;
  if (total == null) return "作业 —";
  return (
    "作业 " +
    total +
    " 份" +
    (stats.value.review_pending ? " · 待批改 " + stats.value.review_pending : "")
  );
});
const shortcuts = [
  {
    label: "发布作业",
    path: "/teacher/assignments?create=1",
    icon: "40:00505",
  },
  { label: "班级通知", path: "/teacher/notices", icon: "40:00513" },
  { label: "学生成绩", path: "/teacher/analytics", icon: "40:5081" },
  { label: "在线课堂", path: "/teacher/classroom", icon: "40:00489" },
];
function deadline(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(value));
}
function percent(value: number | null | undefined) {
  return value == null ? 0 : Math.max(0, Math.min(100, value));
}
async function load() {
  const token = session.token;
  if (loading.value && pendingToken === token) return;
  const request = ++version;
  pendingToken = token;
  loading.value = true;
  error.value = "";
  try {
    const [overview, me] = await Promise.all([
      api("/mobile/teacher/overview"),
      api("/mobile/me/summary"),
    ]);
    if (!mounted || request !== version || token !== session.token) return;
    stats.value = overview;
    personal.value = me;
  } catch (e) {
    if (mounted && request === version && token === session.token)
      error.value = (e as Error).message;
  } finally {
    if (mounted && request === version && token === session.token)
      loading.value = false;
  }
}
function refreshVisible() {
  if (document.visibilityState === "visible" && session.token) void load();
}
onMounted(() => {
  void load();
  timer = setInterval(refreshVisible, 30000);
  window.addEventListener("online", refreshVisible);
  document.addEventListener("visibilitychange", refreshVisible);
});
onUnmounted(() => {
  mounted = false;
  version++;
  clearInterval(timer);
  window.removeEventListener("online", refreshVisible);
  document.removeEventListener("visibilitychange", refreshVisible);
});
watch(
  () => session.token,
  () => {
    stats.value = {};
    personal.value = {};
    selectedAchievement.value = "";
    if (session.token) void load();
    else {
      version++;
      loading.value = false;
      pendingToken = undefined;
    }
  },
  { flush: "sync" },
);
</script>
<template>
  <div class="teacher-profile" data-design-node="40:8834" :data-page-ready="!loading">
    <header class="teacher-profile-hero">
      <div
        class="teacher-hero-background"
        :style="{
          backgroundImage:
            'linear-gradient(180deg,rgba(0,0,0,0),rgba(0,0,0,.04)),url(/design/images/fd2936b89e6516c3c5218314d553e049.webp),url(' +
            designImage('layer-40-8834', '40:8836') +
            ')',
        }"
        aria-hidden="true"
      />
      <img
        class="hero-rule"
        :src="designImage('layer-40-8834', '40:8847')"
        alt=""
      />
      <RouterLink
        to="/profile?edit=1"
        class="teacher-avatar"
        aria-label="编辑个人资料"
        :style="{
          backgroundImage:
            'url(' + designImage('layer-40-8834', '40:8868') + ')',
        }"
      >
        <span class="avatar-photo"
          ><img
            v-if="session.profile?.avatar_url"
            :src="mediaUrl(session.profile.avatar_url)"
            alt="我的头像"
          /><span v-else>{{
            session.profile?.nickname?.slice(0, 1) || "师"
          }}</span></span
        ><i aria-hidden="true" />
      </RouterLink>
      <p class="teacher-year"><i />{{ yearLabel }}<i /></p>
      <h1>{{ session.profile?.nickname || "教学工坊" }}</h1>
      <div class="teacher-counters">
        <RouterLink to="/teacher/classroom"
          ><strong>{{ stats.session_count ?? "—" }}</strong
          ><span>授课</span
          ><small>{{
            stats.session_count == null
              ? "—"
              : "累计 " + stats.session_count + " 场"
          }}</small></RouterLink
        >
        <RouterLink to="/me/follows"
          ><strong>{{ personal.following_count ?? "—" }}</strong
          ><span>关注</span><small>师友同道</small></RouterLink
        >
        <RouterLink to="/teacher/analytics"
          ><strong>{{ stats.student_count ?? "—" }}</strong
          ><span>学生</span><small>桃李满园</small></RouterLink
        >
      </div>
    </header>
    <div class="teacher-body">
      <section class="teacher-block" aria-labelledby="teacher-metrics-title">
        <div class="teacher-heading">
          <h2 id="teacher-metrics-title">班级实时数据</h2>
          <button class="refresh-metrics" :disabled="loading" @click="load">
            <i />{{ loading ? "更新中…" : "实时更新" }}
          </button>
        </div>
        <AsyncState :error="error" @retry="load">
          <div
            class="teacher-metrics"
            data-design-node="40:9607"
            :aria-busy="loading"
          >
            <article
              v-for="metric in metricRows"
              :key="metric.key"
              :class="'metric-' + metric.key"
            >
              <div class="metric-heading">
                <span class="metric-icon"
                  ><img :src="designIcon('layer-40-8834', metric.icon)" alt=""
                /></span>
                <h3>{{ metric.label }}</h3>
                <strong
                  >{{ metric.value ?? "—"
                  }}<small v-if="metric.value != null">{{
                    metric.unit
                  }}</small></strong
                >
              </div>
              <div
                class="metric-track"
                role="progressbar"
                :aria-label="metric.label"
                :aria-valuenow="
                  metric.value == null ? undefined : percent(metric.value)
                "
                aria-valuemin="0"
                aria-valuemax="100"
              >
                <i :style="{ width: percent(metric.value) + '%' }" />
              </div>
              <p>{{ metric.description }}</p>
            </article>
          </div>
        </AsyncState>
      </section>
      <section
        v-if="todos.length"
        class="teacher-block teacher-todo"
        aria-labelledby="teacher-todo-title"
      >
        <div class="teacher-heading">
          <h2 id="teacher-todo-title">今日待办</h2>
          <span>{{ todos.length }} 项</span>
        </div>
        <RouterLink
          v-for="item in todos"
          :key="item.label"
          :to="item.path"
          class="todo-row"
          ><i aria-hidden="true" /><span>{{ item.label }}</span
          ><em>{{ item.action }} ›</em></RouterLink
        >
      </section>
      <section
        class="teacher-block teaching-workshop"
        aria-labelledby="teaching-tools-title"
      >
        <div class="teacher-heading">
          <h2 id="teaching-tools-title">教学工坊</h2>
        </div>
        <div class="teaching-tools" data-design-node="40:00306">
          <RouterLink
            to="/teacher/lesson-plan"
            class="teaching-tool lesson-tool"
            ><span
              class="tool-icon"
              :style="{
                backgroundImage:
                  'url(' + designImage('layer-40-8834', '40:00325') + ')',
              }"
              ><img :src="designIcon('layer-40-8834', '40:5092')" alt=""
            /></span>
            <h3>智能备课</h3>
            <p>教案与课件生成</p>
            <small
              >今日 {{ stats.lesson_plan_today_count ?? "—" }} 份</small
            ></RouterLink
          >
          <RouterLink
            to="/teacher/contests"
            class="teaching-tool assignment-tool"
            ><img
              class="tool-corner-art"
              :src="designImage('layer-40-8834', '40:00477')"
              alt=""
            /><img
              class="tool-watermark"
              :src="designIcon('layer-40-8834', '40:00483')"
              alt=""
            /><span class="tool-icon"
              ><img :src="designIcon('layer-40-8834', '40:00484')" alt=""
            /></span>
            <h3>作业·对抗赛</h3>
            <p>发布作业 · 批改与班级任务</p>
            <small>{{ assignmentSummary }}</small
            ><i
              v-if="stats.review_pending"
              class="tool-alert"
              aria-hidden="true"
              >{{ stats.review_pending }}</i
            ></RouterLink
          >
          <RouterLink to="/teacher/classroom" class="classroom-tool"
            ><span
              class="classroom-icon"
              :style="{
                backgroundImage:
                  'url(' + designImage('layer-40-8834', '40:00747') + ')',
              }"
              ><img :src="designIcon('layer-40-8834', '40:00489')" alt=""
            /></span>
            <div>
              <h3>
                在线课堂<small>{{
                  stats.day
                    ? stats.active_session_count
                      ? "进行中"
                      : "暂无进行中课堂"
                    : "状态未知"
                }}</small>
              </h3>
              <p>文字课堂 · 举手互动与实时讨论</p>
            </div>
            <span class="classroom-enter"
              >进入<img
                :src="designIcon('layer-40-8834', '40:00499')"
                alt="" /></span
          ></RouterLink>
        </div>
      </section>
      <section class="teacher-block student-preview" aria-labelledby="student-preview-title">
        <div class="teacher-heading">
          <h2 id="student-preview-title">学生端内容</h2>
        </div>
        <div class="student-preview-links">
          <RouterLink to="/courses">小课堂</RouterLink>
          <RouterLink to="/ai-workshop">AI 工坊</RouterLink>
          <RouterLink to="/community">社区</RouterLink>
          <RouterLink to="/heritage">非遗百科</RouterLink>
        </div>
        <p class="student-preview-note">
          进学生端核对你布置的内容长什么样，回到教师端点底部「教学」。
        </p>
      </section>
      <section
        class="teacher-block teacher-achievements"
        aria-labelledby="teacher-achievements-title"
      >
        <div class="teacher-heading">
          <h2 id="teacher-achievements-title">教学成就</h2>
          <span>{{
            stats.achievements
              ? completedAchievements + " / " + achievements.length
              : "—"
          }}</span>
        </div>
        <div class="teacher-badges" data-design-node="40:01020">
          <button
            v-for="badge in achievements"
            :key="badge.code"
            :class="{ locked: !badge.completed }"
            :aria-label="
              badge.name + (badge.completed ? '，已达成' : '，未达成')
            "
            @click="selectedAchievement = badge.code"
          >
            <span
              class="badge-ring"
              :style="{
                backgroundImage:
                  'url(' + designImage('layer-40-8834', badge.ring) + ')',
              }"
              ><img
                :src="designImage('layer-40-8834', badge.image)"
                alt="" /></span
            ><span>{{ badge.name }}</span>
          </button>
          <p v-if="!achievements.length">
            {{
              loading
                ? "教学成就加载中…"
                : error
                  ? "教学成就暂未加载"
                  : "积累教学与创作，点亮传承成就"
            }}
          </p>
        </div>
      </section>
      <section
        class="teacher-block teacher-shortcuts"
        aria-labelledby="teacher-shortcuts-title"
      >
        <div class="teacher-heading">
          <h2 id="teacher-shortcuts-title">快捷操作</h2>
        </div>
        <div class="shortcut-links">
          <RouterLink
            v-for="(item, index) in shortcuts"
            :key="item.path"
            :to="item.path"
            :class="'shortcut-' + index"
            ><span
              ><img
                :src="designIcon('layer-40-8834', item.icon)"
                alt="" /></span
            >{{ item.label }}</RouterLink
          >
        </div>
      </section>
    </div>
    <Teleport to="body"
      ><div
        v-if="activeAchievement"
        class="sheet-overlay"
        @click.self="selectedAchievement = ''"
      >
        <section
          class="auth-sheet corner-card teacher-achievement-dialog"
          role="dialog"
          aria-modal="true"
          aria-labelledby="teacher-achievement-name"
        >
          <button
            class="sheet-close"
            aria-label="关闭教学成就"
            @click="selectedAchievement = ''"
          >
            ×</button
          ><img
            :src="designImage('layer-40-8834', activeAchievement.image)"
            alt=""
          />
          <h2 id="teacher-achievement-name">{{ activeAchievement.name }}</h2>
          <p>
            {{ activeAchievement.completed ? "已达成" : "未达成" }} ·
            {{ activeAchievement.description }}
          </p>
          <p>
            当前进度：{{ activeAchievement.current }} /
            {{ activeAchievement.target }}。根据当前教学与学习记录计算。
          </p>
          <RouterLink
            class="primary-button"
            :to="activeAchievement.path"
            @click="selectedAchievement = ''"
            >{{
              activeAchievement.completed ? "查看相关记录" : "前往完成"
            }}</RouterLink
          >
        </section>
      </div></Teleport
    >
  </div>
</template>
<style scoped>
.student-preview-links {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}
.student-preview-links a {
  padding: 8px 14px;
  border: 1px solid rgba(139, 26, 26, 0.28);
  border-radius: 999px;
  background: rgba(255, 250, 242, 0.86);
  color: #6c2e11;
  font: 500 12px/1 var(--sans);
  letter-spacing: 0.08em;
}
.student-preview-note {
  margin: 10px 0 0;
  color: var(--muted);
  font: 400 11px/1.6 var(--sans);
}
.teacher-todo {
  padding: 14px 16px 6px;
  border-radius: 16px;
  border: 1px solid rgba(168, 74, 59, 0.22);
  background: linear-gradient(180deg, rgba(255, 250, 242, 0.94), rgba(250, 240, 230, 0.86));
}
.todo-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 2px;
  border-top: 1px solid rgba(139, 115, 85, 0.16);
  margin-top: 10px;
  font: 500 13px/1.4 var(--serif);
  color: #2c1810;
}
.todo-row i {
  width: 7px;
  height: 7px;
  flex: none;
  border-radius: 50%;
  background: var(--teacher-red);
  box-shadow: 0 0 0 4px rgba(168, 74, 59, 0.14);
}
.todo-row span {
  min-width: 0;
  flex: 1;
}
.todo-row em {
  flex: none;
  font: 600 11px/1 var(--sans);
  letter-spacing: 0.04em;
  color: var(--teacher-red);
}
.tool-alert {
  position: absolute;
  right: 12px;
  top: 12px;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: var(--teacher-red);
  color: #fff9f2;
  font: 700 12px/1 var(--sans);
}
.teacher-profile {
  --teacher-red: #a84a3b;
  --teacher-gold: #b8956a;
  --teacher-green: #6b8e6b;
  --teacher-muted: #8b7355;
  background: #e5d6d6;
  color: #2c1810;
  font-family: var(--serif);
  padding-bottom: calc(88px + var(--safe-bottom));
}
.teacher-profile-hero {
  position: relative;
  min-height: 354px;
  text-align: center;
}
.teacher-hero-background {
  position: absolute;
  inset: 0 0 auto;
  height: 295px;
  background-size: cover;
  background-position: center;
}
.hero-rule {
  position: absolute;
  width: 80px;
  height: 2px;
  left: calc(50% - 40px);
  top: 12px;
}
.teacher-avatar {
  position: absolute;
  top: 40px;
  left: calc(50% - 44px);
  width: 88px;
  height: 88px;
  padding: 3px;
  border-radius: 50%;
  background-size: cover;
}
.avatar-photo {
  display: grid;
  place-items: center;
  width: 82px;
  height: 82px;
  background: #ede4da;
  color: var(--teacher-red);
  border-radius: 50%;
  overflow: hidden;
  font-size: 30px;
}
.avatar-photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.teacher-avatar > i {
  position: absolute;
  right: 4px;
  bottom: 4px;
  width: 20px;
  height: 20px;
  border: 4px solid #f7f2ed;
  border-radius: 50%;
  background: var(--teacher-green);
}
.teacher-year {
  position: absolute;
  top: 144px;
  left: 50%;
  transform: translateX(-50%);
  min-width: 162px;
  height: 28px;
  padding: 6px 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 9999px;
  background: #ffffffb3;
  backdrop-filter: blur(4px);
  font-size: 12px;
  line-height: 16px;
  letter-spacing: 0.93px;
  color: var(--teacher-muted);
  white-space: nowrap;
}
.teacher-year i {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #a84a3b99;
  flex-shrink: 0;
}
.teacher-profile-hero h1 {
  position: absolute;
  left: 20px;
  right: 20px;
  top: 184px;
  font-size: 24px;
  line-height: 32px;
  letter-spacing: 7.2px;
  font-weight: 700;
}
.teacher-counters {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 260px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}
.teacher-counters a {
  position: relative;
  min-height: 94px;
  padding: 16px 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  border: 1px solid #a84a3b4d;
  border-radius: 16px;
  background: #fffc;
}
.teacher-counters a::before,
.teacher-counters a::after {
  content: "";
  position: absolute;
  width: 12px;
  height: 12px;
  border-color: #a84a3b4d;
}
.teacher-counters a::before {
  top: 7px;
  left: 7px;
  border-top: 1px solid #a84a3b4d;
  border-left: 1px solid #a84a3b4d;
  border-top-left-radius: 6px;
}
.teacher-counters a::after {
  bottom: 7px;
  right: 7px;
  border-bottom: 1px solid #a84a3b4d;
  border-right: 1px solid #a84a3b4d;
  border-bottom-right-radius: 6px;
}
.teacher-counters a:nth-child(2) {
  border-color: #b8956a4d;
}
.teacher-counters a:nth-child(3) {
  border-color: #6b8e6b4d;
}
.teacher-counters a:nth-child(2)::before,
.teacher-counters a:nth-child(2)::after {
  border-color: #b8956a4d;
}
.teacher-counters a:nth-child(3)::before,
.teacher-counters a:nth-child(3)::after {
  border-color: #6b8e6b4d;
}
.teacher-counters strong {
  color: var(--teacher-red);
  font-size: 20px;
  line-height: 25px;
  font-weight: 700;
}
.teacher-counters a:nth-child(2) strong {
  color: var(--teacher-gold);
}
.teacher-counters a:nth-child(3) strong {
  color: var(--teacher-green);
}
.teacher-counters a > span {
  font-size: 11px;
  line-height: 16.5px;
  margin-top: 4px;
}
.teacher-counters small {
  color: var(--teacher-muted);
  font-size: 10px;
  line-height: 15px;
  margin-top: 2px;
}
.teacher-body {
  padding: 28px 20px 0;
}
.teacher-block + .teacher-block {
  margin-top: 20px;
}
.teacher-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  height: 24px;
}
.teacher-heading h2 {
  position: relative;
  padding-left: 11px;
  font-size: 16px;
  line-height: 24px;
  letter-spacing: 0.8px;
  font-weight: 700;
}
.teacher-heading h2::before {
  content: "";
  position: absolute;
  left: 0;
  top: 4px;
  height: 16px;
  width: 3px;
  background: var(--teacher-red);
  border-radius: 9999px;
}
.teacher-heading > span {
  color: var(--teacher-muted);
  font-size: 11px;
  line-height: 16.5px;
}
.refresh-metrics {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
  color: var(--teacher-red);
  font-size: 11px;
  line-height: 16.5px;
}
.refresh-metrics i {
  width: 6px;
  height: 6px;
  background: var(--teacher-red);
  border-radius: 50%;
}
.teacher-metrics {
  margin-top: 12px;
  padding: 20px;
  min-height: 304px;
  border: 1px solid #8b735526;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 4px 20px #2c18100f;
}
.teacher-metrics article + article {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #8b73551a;
}
.metric-heading {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 28px;
}
.metric-icon {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: #f5e6e0;
}
.metric-icon img {
  width: 14px;
  height: 14px;
  object-fit: contain;
}
.metric-heading h3 {
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
  flex: 1;
}
.metric-heading strong {
  display: flex;
  align-items: baseline;
  font-size: 18px;
  line-height: 28px;
  font-weight: 700;
  color: var(--teacher-red);
}
.metric-heading small {
  font-size: 14px;
  line-height: 20px;
}
.metric-track {
  margin-top: 8px;
  height: 8px;
  border-radius: 9999px;
  background: #ede4da;
  overflow: hidden;
}
.metric-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #c46a5a, #a84a3b);
}
.teacher-metrics article > p {
  margin-top: 6px;
  color: #3d3d3d;
  font-size: 11px;
  line-height: 16.5px;
}
.metric-submission .metric-icon {
  background: #f5ebe0;
}
.metric-submission strong {
  color: var(--teacher-gold);
}
.metric-submission .metric-track i {
  background: linear-gradient(90deg, #d4b896, #b8956a);
}
.metric-activity .metric-icon {
  background: #e8f0e8;
}
.metric-activity strong {
  color: var(--teacher-green);
}
.metric-activity .metric-track i {
  background: linear-gradient(90deg, #8fb08f, #6b8e6b);
}
.metric-submission > p,
.metric-activity > p {
  color: var(--teacher-muted) !important;
}
.teaching-workshop .teacher-heading h2::before {
  background: var(--teacher-red);
}
.teaching-tools {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.teaching-tool {
  position: relative;
  min-width: 0;
  height: 152px;
  padding: 16px;
  border-radius: 16px;
  background: #fff;
  border: 1px solid #8b735526;
}
.tool-icon {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background-size: cover;
}
.tool-icon img {
  width: 20px;
  height: 20px;
}
.teaching-tool h3 {
  margin-top: 12px;
  font-size: 14px;
  line-height: 20px;
  color: #3d3d3d;
  font-weight: 700;
}
.teaching-tool p {
  margin-top: 4px;
  color: var(--teacher-muted);
  font-size: 11px;
  line-height: 17.88px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.teaching-tool > small {
  display: table;
  margin-top: 6px;
  padding: 2px 6px;
  border-radius: 9999px;
  background: #f5e6e0;
  color: var(--teacher-red);
  font-size: 10px;
  line-height: 15px;
}
.assignment-tool {
  background: var(--teacher-red);
  border: 0;
  box-shadow: 0 4px 20px #a84a3b40;
}
.assignment-tool h3 {
  color: #fff;
}
.assignment-tool p {
  color: #fffc;
}
.assignment-tool .tool-icon,
.assignment-tool > small {
  background: #fff3;
  color: #fff;
}
.tool-corner-art {
  position: absolute;
  right: 0;
  top: 0;
  width: 64px;
  height: 64px;
  border-radius: 0 16px 0 32px;
}
.tool-watermark {
  position: absolute;
  right: -2px;
  bottom: -4px;
  width: 36px;
  height: 40px;
  opacity: 0.2;
}
.classroom-tool {
  grid-column: 1/-1;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  min-height: 80px;
  background: #fff;
  box-shadow: inset 0 0 0 1px #8b735526;
  border-radius: 16px;
}
.classroom-icon {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background-size: cover;
}
.classroom-icon img {
  width: 24px;
  height: 24px;
}
.classroom-tool > div {
  flex: 1;
  min-width: 0;
}
.classroom-tool h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  line-height: 20px;
  font-weight: 700;
}
.classroom-tool h3 small {
  padding: 2px 6px;
  border-radius: 9999px;
  color: var(--teacher-green);
  background: #e8f0e8;
  font-size: 10px;
  line-height: 15px;
  white-space: nowrap;
  font-weight: 400;
}
.classroom-tool p {
  margin-top: 4px;
  font-size: 11px;
  line-height: 17.88px;
  color: var(--teacher-muted);
}
.classroom-enter {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--teacher-muted);
  font-size: 12px;
  line-height: 16px;
  white-space: nowrap;
}
.classroom-enter img {
  width: 4px;
  height: 8px;
}
.teacher-achievements .teacher-heading h2::before {
  background: var(--teacher-gold);
}
.teacher-badges {
  margin-top: 12px;
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding: 20px;
  min-height: 123px;
  border: 1px solid #8b735526;
  border-radius: 16px;
  background: #fff;
  scrollbar-width: none;
}
.teacher-badges button {
  flex: 0 0 56px;
  padding: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  font-size: 10px;
  line-height: 15px;
  white-space: nowrap;
}
.badge-ring {
  display: grid;
  place-items: center;
  width: 56px;
  height: 56px;
  padding: 2px;
  background-size: cover;
  border-radius: 50%;
}
.badge-ring img {
  width: 52px;
  height: 52px;
  border-radius: 50%;
}
.teacher-badges .locked .badge-ring {
  filter: grayscale(1);
  opacity: 0.45;
}
.teacher-badges .locked {
  color: var(--teacher-muted);
}
.teacher-badges > p {
  align-self: center;
  font-size: 11px;
  line-height: 18px;
  color: var(--teacher-muted);
}
.teacher-shortcuts .teacher-heading h2::before {
  background: var(--teacher-green);
}
.shortcut-links {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.shortcut-links a {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px 0;
  font-size: 11px;
  line-height: 16.5px;
  white-space: nowrap;
}
.shortcut-links a > span {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: #f5e6e0;
}
.shortcut-links img {
  width: 18px;
  height: 18px;
  object-fit: contain;
}
.shortcut-links .shortcut-1 > span {
  background: #f5ebe0;
}
.shortcut-links .shortcut-2 > span {
  background: #e8f0e8;
}
.shortcut-links .shortcut-3 > span {
  background: #f0e8dc;
}
.teacher-achievement-dialog > img {
  width: 80px;
  height: 80px;
  margin: 8px auto 16px;
}
.teacher-achievement-dialog > h2 {
  text-align: center;
}
.teacher-achievement-dialog > p {
  font-size: 13px;
  line-height: 1.8;
  margin-top: 16px;
}
.teacher-achievement-dialog > a {
  display: block;
  text-align: center;
  margin-top: 20px;
}
</style>
