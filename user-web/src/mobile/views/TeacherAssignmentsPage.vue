<script setup lang="ts">
import { ref, watch } from "vue";
import { useRoute } from "vue-router";
import { api, post, notify } from "../api";
import PageHeader from "../components/PageHeader.vue";
import AsyncState from "../components/AsyncState.vue";
const route = useRoute(),
  classes = ref<any[]>([]),
  classId = ref<number>(),
  assignments = ref<any[]>([]),
  submissions = ref<any[]>([]);
const loading = ref(true),
  error = ref(""),
  creating = ref(false),
  busy = ref(false),
  reviewing = ref<any>(),
  score = ref<number | "">(""),
  comment = ref("");
const form = ref({
  title: "",
  description: "",
  deadline_days: 7,
  type: "AI_CREATION",
  tool_type: "SHADOW_PUPPET",
});
async function load() {
  loading.value = true;
  error.value = "";
  try {
    classes.value = await api("/teacher/classes");
    if (!classId.value && classes.value.length)
      classId.value = classes.value[0].id;
    if (route.params.id)
      submissions.value = await api(
        "/teacher/assignments/" + route.params.id + "/submissions",
      );
    else
      assignments.value = classId.value
        ? await api("/teacher/assignments?class_id=" + classId.value)
        : [];
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
}
async function create() {
  if (!classId.value) {
    notify("请先创建班级");
    return;
  }
  busy.value = true;
  try {
    await post("/teacher/assignments", {
      ...form.value,
      class_id: classId.value,
      deadline_days: Number(form.value.deadline_days),
    });
    creating.value = false;
    form.value.title = "";
    form.value.description = "";
    await load();
    notify("作业已发布，班级学生可以提交了");
  } catch (e) {
    notify((e as Error).message);
  } finally {
    busy.value = false;
  }
}
function review(record: any) {
  reviewing.value = record;
  score.value = record.score ?? "";
  comment.value = record.comment || "";
}
async function saveReview() {
  busy.value = true;
  try {
    await post("/teacher/submissions/" + reviewing.value.id + "/review", {
      score: Number(score.value),
      comment: comment.value,
    });
    reviewing.value = null;
    await load();
    notify("批改已保存，学生可以查看结果");
  } catch (e) {
    notify((e as Error).message);
  } finally {
    busy.value = false;
  }
}
watch(
  () => route.params.id,
  () => {
    load();
    if (route.query.create) creating.value = true;
  },
  { immediate: true },
);
</script>
<template>
  <div>
    <PageHeader :title="route.params.id ? '作业批改' : '作业 · 对抗赛'" />
    <div class="page-padding">
      <template v-if="!route.params.id"
        ><label
          >选择班级<select v-model="classId" @change="load">
            <option v-for="c in classes" :key="c.id" :value="c.id">
              {{ c.name }}
            </option>
          </select></label
        >
        <div class="assignment-actions">
          <button class="primary-button" @click="creating = true">
            发布作业</button
          ><RouterLink class="outline-button" to="/teacher/analytics"
            >班级学情排行</RouterLink
          >
        </div></template
      ><AsyncState
        :loading="loading"
        :error="error"
        :empty="route.params.id ? !submissions.length : !assignments.length"
        :empty-text="
          route.params.id
            ? '还没有学生提交作业'
            : '还没有作业，发布第一份非遗创作任务吧'
        "
        @retry="load"
        ><div class="assignment-list">
          <template v-if="!route.params.id"
            ><RouterLink
              v-for="assignment in assignments"
              :key="assignment.id"
              :to="'/teacher/assignments/' + assignment.id"
              class="assignment-card corner-card"
              ><h2>
                <span v-if="assignment.type === 'CONTEST'" class="contest-badge">对抗赛</span>
                {{ assignment.title }}
              </h2>
              <p class="subtle">截止 {{ assignment.deadline }}</p>
              <div>
                <span>已提交 {{ assignment.submit_count }} 份</span
                ><span>查看与批改 ›</span>
              </div></RouterLink
            ></template
          ><template v-else
            ><article
              v-for="submission in submissions"
              :key="submission.id"
              class="assignment-card corner-card"
            >
              <div class="submission-heading">
                <h2>{{ submission.student_name }}</h2>
                <span>{{
                  submission.status === "REVIEWED" ? "已批改" : "待批改"
                }}</span>
              </div>
              <p class="submission-text">{{ submission.content }}</p>
              <p v-if="submission.score != null" class="review-result">
                {{ submission.score }}分 · {{ submission.comment }}
              </p>
              <p class="subtle">{{ submission.submitted_at }}</p>
              <button class="outline-button" @click="review(submission)">
                {{ submission.score != null ? "修改批改" : "批改作业" }}
              </button>
            </article></template
          >
        </div></AsyncState
      >
    </div>
    <Teleport to="body"
      ><div
        v-if="creating"
        class="sheet-overlay"
        @click.self="creating = false"
      >
        <section
          class="auth-sheet corner-card"
          role="dialog"
          aria-modal="true"
          aria-labelledby="create-assignment-title"
        >
          <button
            class="sheet-close"
            aria-label="关闭发布作业"
            @click="creating = false"
          >
            ×
          </button>
          <h2 id="create-assignment-title">发布作业</h2>
          <form @submit.prevent="create">
            <label
              >班级<select v-model="classId" required>
                <option v-for="c in classes" :key="c.id" :value="c.id">
                  {{ c.name }}
                </option>
              </select></label
            ><label
              >作业名称<input
                v-model.trim="form.title"
                required
                maxlength="128" /></label
            ><label
              >作业要求<textarea
                v-model.trim="form.description"
                required
                maxlength="10000"
              /></label
            ><label
              >任务类型<select v-model="form.type">
                <option value="AI_CREATION">常规创作作业</option>
                <option value="CONTEST">班级PK对抗赛</option>
              </select></label
            ><label
              >创作工具<select v-model="form.tool_type">
                <option value="SHADOW_PUPPET">皮影角色</option>
                <option value="BRONZE">青铜纹样</option>
                <option value="EMBROIDERY">漆绣创作</option>
              </select></label
            ><label
              >截止天数<input
                v-model.number="form.deadline_days"
                type="number"
                min="1"
                max="90"
                required /></label
            ><button class="primary-button" :disabled="busy">
              {{ busy ? "发布中…" : "发布给学生" }}
            </button>
          </form>
        </section>
      </div>
      <div
        v-if="reviewing"
        class="sheet-overlay"
        @click.self="reviewing = null"
      >
        <section
          class="auth-sheet corner-card"
          role="dialog"
          aria-modal="true"
          aria-labelledby="review-title"
        >
          <button
            class="sheet-close"
            aria-label="关闭批改"
            @click="reviewing = null"
          >
            ×
          </button>
          <h2 id="review-title">{{ reviewing.student_name }} · 作业批改</h2>
          <form @submit.prevent="saveReview">
            <label
              >成绩（0-100）<input
                v-model.number="score"
                type="number"
                required
                min="0"
                max="100" /></label
            ><label
              >教师评语<textarea
                v-model.trim="comment"
                required
                maxlength="5000"
              /></label
            ><button class="primary-button" :disabled="busy">保存批改</button>
          </form>
        </section>
      </div></Teleport
    >
  </div>
</template>
<style scoped>
.assignment-actions {
  display: flex;
  gap: 12px;
  margin: 20px 0 28px;
}
.assignment-actions > * {
  flex: 1;
}
.assignment-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.assignment-card {
  padding: 22px 18px;
}
.assignment-card > p {
  margin-top: 14px;
}
.assignment-card > div:last-child {
  display: flex;
  justify-content: space-between;
  margin-top: 22px;
  font-size: 11px;
  color: var(--clay);
}
.submission-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}
.submission-heading span {
  font-size: 10px;
  color: var(--clay);
}
.submission-text {
  font-size: 13px;
  line-height: 2;
  white-space: pre-line;
  padding: 14px;
  background: var(--track);
  border-radius: 10px;
}
.review-result {
  font-size: 13px;
  line-height: 1.9;
  color: var(--cinnabar);
}
.assignment-card .outline-button {
  margin-top: 18px;
  width: 100%;
}
.contest-badge {
  display: inline-block;
  background: linear-gradient(135deg, #B85450, #8A2B2B);
  color: #FFF;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 4px;
  margin-right: 6px;
  vertical-align: middle;
}
</style>
