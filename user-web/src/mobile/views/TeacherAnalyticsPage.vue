<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { api, session, mediaUrl, notify } from "../api";
import { designImage, designIcon } from "../design";
import AsyncState from "../components/AsyncState.vue";
const classes = ref<any[]>([]),
  classId = ref<number>(),
  data = ref<any>({});
const loading = ref(false),
  error = ref(""),
  busy = ref(false),
  creating = ref(false);
const name = ref(""),
  grade = ref("小学三年级"),
  wallVisible = ref(false),
  basisVisible = ref(false);
const selectedBadge = ref(""),
  attendanceDraft = ref<Record<number, string>>({});
let mounted = true,
  classVersion = 0,
  dataVersion = 0,
  pendingKey = "";
let timer: ReturnType<typeof setInterval>;
const students = computed<any[]>(() => data.value.students || []);
const catalog = computed<any[]>(() => data.value.badge_catalog || []);
const rank = (field: string) =>
  [...students.value]
    .filter((s) => s[field] != null)
    .sort((a, b) => b[field] - a[field] || a.id - b.id);
const progress = computed(() => rank("completion_rate").slice(0, 5));
const accuracy = computed(() => rank("quiz_accuracy_7d").slice(0, 5));
const energy = computed(() => rank("energy_value").slice(0, 5));
const wall = computed(() => rank("badge_count"));
const badgeGroups = computed(() => {
  const item = (code: string, label: string, art?: string) => ({
    code,
    label,
    art,
    ...catalog.value.find((b) => b.code === code),
  });
  const known = new Set([
    "BADGE_COURSE_SHADOW_PUPPET",
    "BADGE_COURSE_BRONZE",
    "BADGE_COURSE_PAPER_CUTTING",
    "BADGE_COURSE_EMBROIDERY",
    "BADGE_COURSE_CERAMICS",
    "BADGE_CALLIGRAPHY",
    "BADGE_CURATOR",
    "BADGE_INHERITOR",
  ]);
  return [
    {
      label: "匠心工艺",
      items: [
        item("BADGE_COURSE_SHADOW_PUPPET", "皮影", "5:4031"),
        item("BADGE_COURSE_BRONZE", "青铜", "5:4061"),
        item("BADGE_COURSE_PAPER_CUTTING", "剪纸", "5:4039"),
        item("BADGE_COURSE_EMBROIDERY", "苏绣", "5:4082"),
      ],
    },
    {
      label: "学识修养",
      items: [
        item("BADGE_COURSE_CERAMICS", "瓷韵", "5:3981"),
        item("BADGE_CALLIGRAPHY", "书法", "5:3965"),
      ],
    },
    {
      label: "卓越成就",
      items: [
        item("BADGE_CURATOR", "策展", "5:4165"),
        item("BADGE_INHERITOR", "传承", "5:4135"),
        ...catalog.value
          .filter((b) => !known.has(b.code))
          .map((b) => ({ ...b, label: b.name })),
      ],
    },
  ];
});
const activeBadge = computed(() =>
  badgeGroups.value
    .flatMap((g) => g.items)
    .find((b) => b.code === selectedBadge.value),
);
const badgeStudents = computed(() =>
  students.value.filter((s) =>
    s.badges?.some((b: any) => b.code === selectedBadge.value),
  ),
);
const changedAttendance = computed(() =>
  students.value
    .filter(
      (s) =>
        attendanceDraft.value[s.id] &&
        attendanceDraft.value[s.id] !== "UNRECORDED" &&
        attendanceDraft.value[s.id] !== s.attendance,
    )
    .map((s) => ({ student_id: s.id, status: attendanceDraft.value[s.id] })),
);
function percent(n: number | null | undefined) {
  return Math.max(0, Math.min(100, n ?? 0));
}
function value(n: number | null | undefined, suffix = "") {
  return n == null ? "—" : n + suffix;
}
function portrait(s: any) {
  return mediaUrl(s.avatar_url);
}
function close() {
  if (!busy.value) {
    creating.value = false;
    wallVisible.value = false;
    selectedBadge.value = "";
    basisVisible.value = false;
  }
}
async function loadAnalytics() {
  const token = session.token,
    id = classId.value,
    key = token + ":" + id;
  if (!token || !id || !mounted || (loading.value && pendingKey === key))
    return;
  const version = ++dataVersion;
  pendingKey = key;
  loading.value = true;
  error.value = "";
  try {
    const result = await api("/mobile/teacher/classes/" + id + "/analytics");
    if (
      !mounted ||
      token !== session.token ||
      id !== classId.value ||
      version !== dataVersion
    )
      return;
    const previous = data.value,
      drafts: Record<number, string> = {};
    for (const s of result.students) {
      const old = previous.students?.find((v: any) => v.id === s.id);
      drafts[s.id] =
        previous.day === result.day &&
        old &&
        attendanceDraft.value[s.id] !== old.attendance
          ? attendanceDraft.value[s.id] || s.attendance
          : s.attendance;
    }
    data.value = result;
    attendanceDraft.value = drafts;
  } catch (e) {
    if (
      mounted &&
      token === session.token &&
      id === classId.value &&
      version === dataVersion
    )
      error.value = (e as Error).message;
  } finally {
    if (
      mounted &&
      token === session.token &&
      id === classId.value &&
      version === dataVersion
    )
      loading.value = false;
  }
}
async function loadClasses(preferred?: number) {
  const token = session.token,
    version = ++classVersion;
  if (!token || !mounted) return;
  error.value = "";
  try {
    const rows = await api("/teacher/classes");
    if (!mounted || token !== session.token || version !== classVersion) return;
    classes.value = rows;
    const selected = preferred ?? classId.value;
    const next = rows.some((c: any) => c.id === selected)
      ? selected
      : rows[0]?.id;
    if (next !== classId.value) classId.value = next;
    else if (next) await loadAnalytics();
  } catch (e) {
    if (mounted && token === session.token && version === classVersion)
      error.value = (e as Error).message;
  }
}
async function create() {
  if (busy.value || !name.value.trim() || !grade.value.trim()) return;
  const token = session.token,
    version = classVersion;
  busy.value = true;
  try {
    const result = await api("/mobile/teacher/classes", {
      method: "POST",
      body: JSON.stringify({
        name: name.value.trim(),
        grade: grade.value.trim(),
      }),
    });
    if (!mounted || token !== session.token || version !== classVersion) return;
    creating.value = false;
    name.value = "";
    await loadClasses(result.id);
    if (mounted && token === session.token) notify("班级已创建");
  } catch (e) {
    if (mounted && token === session.token) notify((e as Error).message);
  } finally {
    if (mounted && token === session.token) busy.value = false;
  }
}
async function saveAttendance() {
  if (busy.value || !changedAttendance.value.length || !data.value.day) return;
  const token = session.token,
    id = classId.value,
    day = data.value.day;
  busy.value = true;
  try {
    await api("/mobile/teacher/classes/" + id + "/attendance", {
      method: "PUT",
      body: JSON.stringify({ day, records: changedAttendance.value }),
    });
    if (!mounted || token !== session.token || id !== classId.value) return;
    attendanceDraft.value = {};
    ++dataVersion;
    loading.value = false;
    pendingKey = "";
    await loadAnalytics();
    if (mounted && token === session.token && id === classId.value)
      notify("考勤已保存");
  } catch (e) {
    if (mounted && token === session.token && id === classId.value)
      notify((e as Error).message);
  } finally {
    if (mounted && token === session.token) busy.value = false;
  }
}
function refreshVisible() {
  if (document.visibilityState === "visible" && session.token)
    void loadAnalytics();
}
watch(
  classId,
  () => {
    ++dataVersion;
    pendingKey = "";
    loading.value = false;
    data.value = {};
    attendanceDraft.value = {};
    selectedBadge.value = "";
    wallVisible.value = false;
    error.value = "";
    void loadAnalytics();
  },
  { flush: "sync" },
);
watch(
  () => session.token,
  () => {
    ++classVersion;
    ++dataVersion;
    classes.value = [];
    classId.value = undefined;
    data.value = {};
    attendanceDraft.value = {};
    selectedBadge.value = "";
    wallVisible.value = false;
    basisVisible.value = false;
    creating.value = false;
    name.value = "";
    grade.value = "小学三年级";
    busy.value = false;
    loading.value = false;
    pendingKey = "";
    error.value = "";
    if (session.token) void loadClasses();
  },
  { flush: "sync" },
);
onMounted(() => {
  void loadClasses();
  timer = setInterval(refreshVisible, 30000);
  window.addEventListener("online", refreshVisible);
  document.addEventListener("visibilitychange", refreshVisible);
});
onUnmounted(() => {
  mounted = false;
  ++classVersion;
  ++dataVersion;
  clearInterval(timer);
  window.removeEventListener("online", refreshVisible);
  document.removeEventListener("visibilitychange", refreshVisible);
});
</script>
<template>
  <div class="teacher-analytics" data-design-node="5:3855">
    <header class="analytics-header" data-design-node="5:4694">
      <h1>教师端 · 实时数据</h1>
      <RouterLink class="student-mode" to="/courses">学生端 ›</RouterLink>
    </header>
    <main class="analytics-body" :aria-busy="loading">
      <section class="analytics-picker" data-design-node="5:4588">
        <div class="picker-heading">
          <label for="analytics-class">选择班级</label
          ><button :disabled="busy" @click="creating = true">新建班级</button>
        </div>
        <div class="picker-control">
          <select
            id="analytics-class"
            v-model="classId"
            :disabled="busy || !classes.length"
          >
            <option v-if="!classes.length" :value="undefined">
              {{
                error ? "班级加载失败，请重试" : "暂无班级，请先新建班级"
              }}
            </option>
            <option v-for="c in classes" :key="c.id" :value="c.id">
              {{ c.grade }} · {{ c.name }}
            </option></select
          ><img :src="designIcon('layer-5-3855', '5:4608')" alt="" />
        </div>
      </section>
      <AsyncState :error="error" @retry="loadClasses()" />
      <div class="analytics-stats" data-design-node="5:3866">
        <article>
          <strong>{{ value(data.student_count) }}</strong
          ><span>学生总数</span
          ><i><b :style="{ width: data.student_count ? '100%' : '0%' }" /></i>
        </article>
        <article>
          <strong>{{ value(data.mean_completion_rate, "%") }}</strong
          ><span>平均完成度</span
          ><i
            ><b :style="{ width: percent(data.mean_completion_rate) + '%' }"
          /></i>
        </article>
        <article>
          <strong>{{ value(data.badge_total) }}</strong
          ><span>徽章已解锁</span
          ><i
            ><b
              :style="{
                width:
                  data.student_count && data.badge_catalog_count
                    ? percent(
                        (100 * data.badge_total) /
                          (data.student_count * data.badge_catalog_count),
                      ) + '%'
                    : '0%',
              }"
          /></i>
        </article>
      </div>
      <section class="analytics-panel progress-panel" data-design-node="5:4378">
        <div class="panel-heading">
          <h2>
            <span class="heading-icon"
              ><img :src="designIcon('layer-5-3855', '5:4444')" alt="" /></span
            >班级学习进度
          </h2>
          <button
            class="refresh-pill"
            :disabled="loading"
            @click="loadAnalytics"
          >
            {{ loading ? "更新中" : "实时更新" }}
          </button>
        </div>
        <div class="progress-list">
          <article v-for="s in progress" :key="s.id" class="student-progress">
            <span class="student-avatar"
              ><img v-if="portrait(s)" :src="portrait(s)" alt="" /><span
                v-else
                >{{ s.nickname.slice(0, 1) }}</span
              ></span
            >
            <div>
              <p>
                <span>{{ s.nickname }}</span
                ><strong>{{ value(s.completion_rate, "%") }}</strong>
              </p>
              <div
                class="progress-track"
                role="progressbar"
                :aria-label="s.nickname + '学习进度'"
                :aria-valuenow="s.completion_rate"
                aria-valuemin="0"
                aria-valuemax="100"
              >
                <i :style="{ width: percent(s.completion_rate) + '%' }" />
              </div>
            </div>
          </article>
          <p v-if="!progress.length" class="analytics-empty">
            {{
              error && !students.length
                ? "学习记录暂不可用"
                : loading
                  ? "正在读取学习记录…"
                  : "当前学生尚无已发布课程的学习记录"
            }}
          </p>
        </div>
        <button class="progress-summary" @click="basisVisible = true">
          共 {{ value(data.student_count) }} 名学生 · 平均进度
          {{ value(data.mean_completion_rate, "%") }}
        </button>
      </section>
      <section class="analytics-panel accuracy-panel" data-design-node="5:4181">
        <div class="panel-heading">
          <h2>
            <span class="heading-icon gold"
              ><img :src="designIcon('layer-5-3855', '5:4303')" alt="" /></span
            >正确率排行
          </h2>
          <span>近七日数据</span>
        </div>
        <div class="accuracy-list">
          <article
            v-for="(s, i) in accuracy"
            :key="s.id"
            class="accuracy-row"
            :class="'rank-' + i"
          >
            <b class="rank-number">{{ i + 1 }}</b
            ><span class="student-avatar"
              ><img v-if="portrait(s)" :src="portrait(s)" alt="" /><span
                v-else
                >{{ s.nickname.slice(0, 1) }}</span
              ></span
            >
            <div class="accuracy-detail">
              <p>
                <span>{{ s.nickname }}</span
                ><img
                  v-if="i < 3"
                  :src="
                    designIcon(
                      'layer-5-3855',
                      ['5:4357', '5:4265', '5:4237'][i],
                    )
                  "
                  alt=""
                />
              </p>
              <div>
                <span class="progress-track"
                  ><i
                    :style="{
                      width: percent(s.quiz_accuracy_7d) + '%',
                    }" /></span
                ><strong>{{ s.quiz_accuracy_7d }}%</strong>
              </div>
            </div>
          </article>
          <p v-if="!accuracy.length" class="analytics-empty">
            {{
              error && !students.length
                ? "测验数据暂不可用"
                : "近七日暂无可计算的测验记录"
            }}
          </p>
        </div>
      </section>
      <section class="analytics-panel energy-panel" data-design-node="5:4492">
        <div class="panel-heading">
          <h2>
            <span class="heading-icon"
              ><img :src="designIcon('layer-5-3855', '5:4505')" alt="" /></span
            >能量值排行
          </h2>
          <span>实时更新</span>
        </div>
        <div class="energy-chart">
          <article v-for="s in energy" :key="s.id">
            <strong>{{ s.energy_value }}</strong>
            <p>
              <span class="energy-portrait"
                ><img v-if="portrait(s)" :src="portrait(s)" alt="" /><span
                  v-else
                  >{{ s.nickname.slice(0, 1) }}</span
                ></span
              ><span>{{ s.nickname }}</span>
            </p>
          </article>
          <p v-if="!energy.length" class="analytics-empty">
            {{
              error && !students.length ? "能量数据暂不可用" : "暂无班级学生数据"
            }}
          </p>
        </div>
      </section>
      <section class="analytics-panel badge-panel" data-design-node="5:3927">
        <div class="panel-heading">
          <h2>
            <span class="heading-icon gold"
              ><img :src="designIcon('layer-5-3855', '5:4108')" alt="" /></span
            >徽章解锁情况
          </h2>
          <span
            >{{ value(data.unlocked_badge_types) }}/{{
              value(data.badge_catalog_count)
            }}
            类</span
          >
        </div>
        <div
          v-for="group in badgeGroups"
          :key="group.label"
          class="badge-group"
        >
          <h3>{{ group.label }}</h3>
          <div class="analytics-badge-grid">
            <button
              v-for="b in group.items"
              :key="b.code"
              class="analytics-badge"
              :class="{ unconfigured: !b.id }"
              :aria-label="
                b.label +
                '，' +
                (b.id ? b.student_count + '人解锁' : '尚未配置规则')
              "
              @click="selectedBadge = b.code"
            >
              <span
                ><img
                  v-if="b.art || b.icon_url"
                  :src="
                    b.art
                      ? designImage('layer-5-3855', b.art)
                      : mediaUrl(b.icon_url)
                  "
                  alt="" /></span
              ><strong>{{ b.label }}</strong
              ><small>{{
                b.id ? b.student_count + "人" : "未配置"
              }}</small></button
            ><span
              v-for="slot in Math.max(0, 4 - group.items.length)"
              :key="'empty' + slot"
              class="analytics-badge badge-placeholder"
              aria-label="预留徽章位置"
              ><span
                ><img
                  :src="designIcon('layer-5-3855', '5:4013')"
                  alt="" /></span
              ><strong>未解锁</strong></span
            >
          </div>
        </div>
      </section>
      <section class="analytics-panel wall-panel" data-design-node="5:4618">
        <div class="panel-heading">
          <h2>
            <span class="heading-icon"
              ><img :src="designIcon('layer-5-3855', '5:4680')" alt="" /></span
            >学生徽章墙
          </h2>
          <button @click="wallVisible = true">查看全部</button>
        </div>
        <div class="student-badges">
          <button
            v-for="s in wall.slice(0, 3)"
            :key="s.id"
            @click="wallVisible = true"
          >
            <span class="student-avatar"
              ><img v-if="portrait(s)" :src="portrait(s)" alt="" /><span
                v-else
                >{{ s.nickname.slice(0, 1) }}</span
              ></span
            ><strong>{{ s.nickname }}</strong
            ><span class="mini-badges"
              ><img
                v-for="b in s.badges.slice(0, 4)"
                :key="b.id"
                :src="mediaUrl(b.icon_url)"
                :alt="b.name" /></span
            ><small>{{ s.badge_count }} 枚</small>
          </button>
          <p v-if="!wall.length" class="analytics-empty">
            {{
              error && !students.length
                ? "学生数据暂不可用"
                : "暂无学生，将邀请码分享给学生即可加入"
            }}
          </p>
        </div>
      </section>
      <section class="analytics-panel attendance-panel">
        <div class="panel-heading">
          <h2>今日考勤</h2>
          <span>{{ data.day || "—" }}</span>
        </div>
        <p class="attendance-invite">
          班级邀请码：{{ data.class?.invite_code || "—" }}
        </p>
        <label v-for="s in students" :key="s.id" class="attendance-row"
          ><span>{{ s.nickname }}</span
          ><select v-model="attendanceDraft[s.id]" :disabled="busy">
            <option value="UNRECORDED">未记录</option>
            <option value="PRESENT">到课</option>
            <option value="LEAVE">请假</option>
            <option value="ABSENT">缺勤</option>
          </select></label
        >
        <p v-if="!students.length" class="analytics-empty">
          {{ error ? "学生数据暂不可用" : "暂无可记录的学生" }}
        </p>
        <button
          class="primary-button"
          :disabled="busy || !changedAttendance.length"
          @click="saveAttendance"
        >
          {{ busy ? "正在保存…" : "保存考勤" }}
        </button>
      </section>
      <footer class="analytics-footer">
        <span
          >全班解锁 {{ value(data.unlocked_badge_types) }}/{{
            value(data.badge_catalog_count)
          }}
          类徽章 · 累计学习 {{ value(data.learning_days_total) }} 人日</span
        >
        <p>策展人 · 传统工艺研习平台</p>
      </footer>
    </main>
    <Teleport to="body"
      ><div
        v-if="creating || wallVisible || selectedBadge || basisVisible"
        class="sheet-overlay analytics-overlay"
        @click.self="close"
      >
        <section
          class="auth-sheet corner-card analytics-sheet"
          role="dialog"
          aria-modal="true"
          aria-labelledby="analytics-dialog-title"
        >
          <button
            class="sheet-close"
            aria-label="关闭学情面板"
            :disabled="busy"
            @click="close"
          >
            ×
          </button>
          <template v-if="creating"
            ><h2 id="analytics-dialog-title">新建班级</h2>
            <form @submit.prevent="create">
              <label
                >班级名称<input
                  v-model.trim="name"
                  required
                  maxlength="64"
                  :disabled="busy" /></label
              ><label
                >适用年级<input
                  v-model.trim="grade"
                  required
                  maxlength="32"
                  :disabled="busy" /></label
              ><button class="primary-button" :disabled="busy">
                {{ busy ? "正在创建…" : "创建班级" }}
              </button>
            </form></template
          >
          <template v-else-if="basisVisible"
            ><h2 id="analytics-dialog-title">统计口径</h2>
            <p>{{ data.progress_basis }}</p>
            <p>
              当前
              {{
                data.progress_student_count || 0
              }}
              名学生有可计算的学习进度，未开始者显示未知，不作为零分参与平均。
            </p>
            <p>{{ data.quiz_basis }}</p>
            <p>
              能量与徽章来自当前有效班级学生；预留位置和未配置规则不计入真实目录。
            </p></template
          >
          <template v-else-if="activeBadge"
            ><h2 id="analytics-dialog-title">{{ activeBadge.label }}</h2>
            <p>
              {{
                activeBadge.description ||
                "此徽章尚未配置规则与授予记录，当前不计入解锁目录。"
              }}
            </p>
            <p v-if="activeBadge.id">
              班级
              {{ activeBadge.student_count }} 人解锁；查看此页面不会发放奖励。
            </p>
            <ul v-if="badgeStudents.length">
              <li v-for="s in badgeStudents" :key="s.id">{{ s.nickname }}</li>
            </ul></template
          >
          <template v-else
            ><h2 id="analytics-dialog-title">
              学生徽章墙 · {{ students.length }} 人
            </h2>
            <article v-for="s in wall" :key="s.id" class="wall-detail">
              <h3>
                {{ s.nickname }}
                <small
                  >{{ s.badge_count }} 枚 · 学习 {{ s.learning_days }} 天</small
                >
              </h3>
              <p>
                学习进度 {{ value(s.completion_rate, "%") }} · 近七日正确率
                {{ value(s.quiz_accuracy_7d, "%") }}
              </p>
              <div>
                <img
                  v-for="b in s.badges"
                  :key="b.id"
                  :src="mediaUrl(b.icon_url)"
                  :alt="b.name"
                  :title="b.name"
                /><span v-if="!s.badges.length">尚未解锁徽章</span>
              </div>
            </article>
            <p v-if="!wall.length">当前班级暂无学生</p></template
          >
        </section>
      </div></Teleport
    >
  </div>
</template>
<style scoped>
/* MasterGo 5:3855: paint_5:3868,3957,3894,3884,3878,3881; font Noto Serif SC. */
.teacher-analytics {
  --a-ink: #5c3d3d;
  --a-clay: #c85050;
  --a-gold: #c8a882;
  --a-muted: #8b6b6b;
  --a-card: #fffbf9;
  --a-track: #fce8e8;
  min-height: 100vh;
  padding-bottom: calc(88px + var(--safe-bottom));
  color: var(--a-ink);
  font-family: var(--serif);
  background: linear-gradient(
      rgba(255, 130, 130, 0.94),
      rgba(255, 130, 130, 0.94)
    ),
    url("/design/images/cce9457aabb953dc482bc8d13628edf9.webp") center
      top/100% 2614px no-repeat,
    #ff8282;
}
.analytics-header {
  height: 77px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  background: rgba(255, 240, 240, 0.92);
  border-bottom: 1px solid rgba(200, 168, 130, 0.2);
  backdrop-filter: blur(12px);
}
.analytics-header h1 {
  font-size: 16px;
  line-height: 24px;
  font-weight: 600;
  white-space: nowrap;
  flex: 1;
  color: #5d4040;
}
.student-mode {
  flex: none;
  padding: 7px 12px;
  border: 1px solid rgba(184, 149, 106, 0.55);
  border-radius: 999px;
  background: rgba(255, 251, 249, 0.9);
  font: 12px/1 var(--serif);
  letter-spacing: 1px;
  color: #6c2e11;
  white-space: nowrap;
}
.analytics-body {
  padding: 24px 20px 40px;
}
.picker-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 20px;
  margin-bottom: 16px;
}
.picker-heading label {
  background: var(--a-card);
  border-radius: 0 4px 4px 0;
  padding-right: 8px;
  border-left: 4px solid var(--a-clay);
  padding-left: 12px;
  font: 500 14px/20px var(--serif);
  color: var(--a-muted);
}
.picker-heading button {
  background: rgba(255, 251, 249, 0.94);
  border-radius: 4px;
  padding: 0 8px;
  font: 12px/20px var(--serif);
  color: var(--a-muted);
}
.picker-control {
  position: relative;
}
.picker-control select {
  appearance: none;
  width: 100%;
  height: 60px;
  border: 2px solid var(--a-gold);
  border-radius: 16px;
  background: var(--a-card);
  padding: 16px 40px 16px 18px;
  font: 16px/24px var(--serif);
  color: var(--a-ink);
  box-shadow: 0 2px 8px rgba(200, 168, 130, 0.15);
}
.picker-control > img {
  position: absolute;
  right: 20px;
  top: 27px;
  width: 8px;
  height: 4px;
  pointer-events: none;
}
.analytics-stats {
  display: flex;
  gap: 12px;
  margin: 24px 0;
}
.analytics-stats article {
  height: 102px;
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  border: 1px solid rgba(200, 168, 130, 0.2);
  border-radius: 16px;
  background: var(--a-card);
  padding: 14px 16px;
}
.analytics-stats strong {
  font: 700 24px/35px var(--serif);
  color: var(--a-clay);
  white-space: nowrap;
}
.analytics-stats article:nth-child(2) strong {
  color: var(--a-gold);
}
.analytics-stats span {
  font-size: 12px;
  line-height: 17px;
  color: var(--a-muted);
  white-space: nowrap;
  margin-top: 2px;
}
.analytics-stats i {
  height: 4px;
  border-radius: 4px;
  display: block;
  align-self: stretch;
  background: var(--a-track);
  margin-top: 12px;
  overflow: hidden;
}
.analytics-stats b {
  height: 100%;
  display: block;
  background: var(--a-clay);
}
.analytics-stats article:nth-child(2) b {
  background: var(--a-gold);
}
.analytics-panel {
  border: 1px solid rgba(200, 168, 130, 0.2);
  border-radius: 16px;
  background: var(--a-card);
  box-shadow: 0 4px 20px rgba(92, 61, 61, 0.06);
  padding: 20px;
  margin-bottom: 24px;
}
.panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: 32px;
}
.panel-heading h2 {
  display: flex;
  align-items: center;
  gap: 12px;
  font: 700 16px/24px var(--serif);
  white-space: nowrap;
  min-width: 0;
}
.heading-icon {
  width: 32px;
  height: 32px;
  flex: none;
  border-radius: 8px;
  background: #e8b0b0;
  display: grid;
  place-items: center;
}
.heading-icon.gold {
  background: #f0e0d0;
}
.heading-icon img {
  width: 16px;
  height: 16px;
}
.panel-heading > span,
.panel-heading > button {
  font: 12px/16px var(--serif);
  color: var(--a-muted);
  white-space: nowrap;
}
.refresh-pill {
  background: var(--a-track);
  border-radius: 24px;
  padding: 4px 6px;
  min-width: 72px;
}
.progress-panel {
  min-height: 415px;
  display: flex;
  flex-direction: column;
}
.progress-list {
  flex: 1;
  padding-top: 20px;
}
.student-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  height: 40px;
}
.student-avatar {
  width: 40px;
  height: 40px;
  flex: none;
  padding: 3px;
  border: 2px solid #d4af37;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: var(--a-clay);
  background: #f0e0d0;
  font-size: 18px;
}
.student-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}
.student-progress > div {
  flex: 1;
  min-width: 0;
}
.student-progress p {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 14px;
  line-height: 20px;
  margin-bottom: 6px;
}
.student-progress p span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.student-progress strong {
  font-size: 14px;
  color: var(--a-clay);
  font-weight: 600;
}
.progress-track {
  height: 10px;
  background: var(--a-track);
  border-radius: 6px;
  display: block;
  overflow: hidden;
}
.progress-track i {
  display: block;
  height: 100%;
  background: var(--a-clay);
  border-radius: inherit;
}
.progress-summary {
  min-height: 41px;
  border-top: 1px solid #e8d5c4;
  padding-top: 16px;
  font: 12px/20px var(--serif);
  color: var(--a-muted);
  text-align: center;
  width: 100%;
}
.analytics-empty {
  font: 12px/20px var(--serif);
  color: var(--a-muted);
  padding: 24px 0;
  text-align: center;
}
.accuracy-panel {
  min-height: 496px;
}
.accuracy-list {
  padding-top: 20px;
}
.accuracy-row {
  height: 70px;
  padding: 12px;
  display: flex;
  gap: 12px;
  align-items: center;
  border: 1px solid rgba(200, 168, 130, 0.2);
  border-radius: 12px;
  margin-bottom: 12px;
  background: rgba(240, 224, 208, 0.15);
}
.accuracy-row:last-child {
  margin-bottom: 0;
}
.accuracy-row.rank-0 {
  border-color: rgba(212, 175, 55, 0.2);
  background: rgba(245, 230, 200, 0.3);
}
.rank-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1.5px solid var(--a-gold);
  background: #f0e0d0;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 700;
  flex: none;
  color: #b8956a;
}
.rank-0 .rank-number {
  border-color: #d4af37;
  background: #f5e6c8;
}
.accuracy-detail {
  flex: 1;
  min-width: 0;
}
.accuracy-detail > p {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  line-height: 20px;
  margin-bottom: 4px;
}
.accuracy-detail > p > span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.accuracy-detail > p img {
  width: 14px;
  height: 14px;
}
.accuracy-detail > div {
  display: flex;
  gap: 8px;
  align-items: center;
}
.accuracy-detail .progress-track {
  flex: 1;
  height: 8px;
}
.accuracy-detail .progress-track i {
  background: var(--a-gold);
}
.rank-0 .progress-track i {
  background: #d4af37;
}
.accuracy-detail strong {
  font: 600 12px/20px var(--serif);
  color: #b8956a;
  min-width: 36px;
  text-align: right;
}
.energy-panel {
  min-height: 214px;
}
.energy-chart {
  display: flex;
  gap: 8px;
  height: 120px;
  margin-top: 20px;
  padding: 14px 8px 8px;
}
.energy-chart article {
  width: calc((100% - 32px) / 5);
  flex: none;
  text-align: center;
  min-width: 0;
  font: 12px/16px var(--serif);
}
.energy-chart strong {
  display: block;
  color: var(--a-clay);
  font-size: 12px;
  line-height: 16px;
  margin-bottom: 24px;
}
.energy-chart article > p {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
.energy-chart article > p > span:last-child {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.energy-portrait {
  width: 32px;
  height: 32px;
  border: 1.5px solid #d4af37;
  border-radius: 50%;
  padding: 2.5px;
  display: grid;
  place-items: center;
  background: #f0e0d0;
}
.energy-portrait img {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
}
.badge-panel {
  min-height: 569px;
}
.badge-group {
  margin-top: 20px;
}
.badge-group h3 {
  font: 12px/16px var(--serif);
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.badge-group h3:before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--a-gold);
}
.analytics-badge-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}
.analytics-badge {
  height: 117px;
  min-width: 0;
  border: 1.5px solid #e8d5c4;
  border-radius: 12px;
  background: var(--a-card);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 13.5px 2px 10px;
  gap: 8px;
  font: 12px/16px var(--serif);
}
.analytics-badge > span {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #f0e0d0;
  flex: none;
}
.analytics-badge img {
  width: 40px;
  height: 40px;
  object-fit: contain;
  border-radius: 50%;
}
.analytics-badge strong {
  font-weight: 400;
  max-width: 100%;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}
.analytics-badge small {
  font-size: 12px;
  line-height: 16px;
  color: var(--a-gold);
  margin-top: -6px;
}
.analytics-badge.unconfigured {
  background: rgba(255, 251, 249, 0.6);
  color: var(--a-muted);
}
.unconfigured img {
  filter: grayscale(1);
  opacity: 0.55;
}
.badge-placeholder {
  opacity: 0.4;
}
.badge-placeholder > span {
  background: var(--a-track);
}
.analytics-badge.badge-placeholder img {
  width: 18px;
  height: 18px;
  border: 1.5px solid var(--a-muted);
  border-radius: 2px;
  padding: 3.5px;
}
.wall-panel {
  min-height: 253px;
}
.student-badges {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  padding-top: 20px;
}
.student-badges > button {
  min-width: 0;
  height: 159px;
  border: 1.5px solid #e8d5c4;
  border-radius: 12px;
  background: var(--a-card);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 6px;
  gap: 10px;
}
.student-badges .student-avatar {
  width: 48px;
  height: 48px;
  padding: 3px;
}
.student-badges strong {
  font: 12px/17px var(--serif);
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.mini-badges {
  display: flex;
  height: 20px;
  gap: 4px;
}
.mini-badges img {
  width: 13px;
  height: 20px;
  object-fit: contain;
}
.student-badges small {
  font: 12px/16px var(--serif);
  color: var(--a-gold);
}
.student-badges .analytics-empty {
  grid-column: 1/-1;
}
.attendance-panel h2 {
  font: 700 16px/24px var(--serif);
}
.attendance-invite {
  font-size: 12px;
  line-height: 20px;
  color: var(--a-muted);
  padding-top: 14px;
  overflow-wrap: anywhere;
}
.attendance-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  font-size: 14px;
  margin-top: 16px;
}
.attendance-row > span {
  overflow-wrap: anywhere;
}
.attendance-row select {
  width: 120px;
  min-height: 40px;
  flex: none;
  font: 14px var(--serif);
  border: 1px solid #e8d5c4;
  background: var(--a-card);
  padding: 8px;
  border-radius: 8px;
}
.attendance-panel > .primary-button {
  width: 100%;
  margin-top: 20px;
}
.analytics-footer {
  text-align: center;
  color: var(--a-muted);
  font-size: 12px;
  line-height: 20px;
  padding-top: 16px;
}
.analytics-footer > span:before {
  content: "";
  display: block;
  width: 96px;
  height: 1px;
  background: #e8d5c4;
  margin: 0 auto 12px;
}
.analytics-footer p {
  margin-top: 8px;
}
.analytics-overlay {
  --ink: #5c3d3d;
  --muted: #8b6b6b;
  --clay: #c85050;
  --gold-light: #e8d5c4;
}
.analytics-sheet {
  background: #fffbf9;
}
.analytics-sheet > p {
  font: 14px/24px var(--serif);
  margin-top: 16px;
}
.analytics-sheet ul {
  padding-left: 20px;
  margin-top: 16px;
}
.wall-detail {
  padding: 16px 0;
  border-bottom: 1px solid #e8d5c4;
}
.wall-detail h3 {
  font: 600 16px/24px var(--serif);
}
.wall-detail small {
  font: 12px/20px var(--serif);
  color: #8b6b6b;
}
.wall-detail p {
  font: 12px/20px var(--serif);
  margin: 8px 0;
  color: #8b6b6b;
}
.wall-detail > div {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.wall-detail img {
  width: 36px;
  height: 36px;
  object-fit: contain;
}
.wall-detail > div > span {
  font-size: 12px;
  color: #8b6b6b;
}
@media (max-width: 374px) {
  .analytics-header {
    padding: 0 16px;
  }
  .analytics-header h1 {
    font-size: 14px;
  }
  .student-mode {
    gap: 6px;
  }
  .student-mode > span {
    width: 44px;
  }
  .analytics-body {
    padding-left: 16px;
    padding-right: 16px;
  }
  .analytics-panel {
    padding: 18px;
  }
  .panel-heading h2 {
    gap: 8px;
    font-size: 15px;
  }
  .analytics-badge-grid {
    gap: 8px;
  }
  .analytics-badge > span {
    width: 44px;
    height: 44px;
  }
  .analytics-badge img {
    width: 36px;
    height: 36px;
  }
  .student-badges {
    gap: 8px;
  }
  .accuracy-row {
    gap: 8px;
    padding: 10px;
  }
  .analytics-stats {
    gap: 10px;
  }
  .analytics-stats article {
    padding-left: 12px;
    padding-right: 12px;
  }
}
</style>
