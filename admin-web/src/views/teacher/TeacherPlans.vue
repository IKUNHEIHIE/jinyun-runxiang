<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from "vue";
import { ElMessage, type FormInstance } from "element-plus";
import request from "@/api/request";
import { getToken } from "@/utils/auth";
import { useUserStoreHook } from "@/store/modules/user";
import { dateText, errorMessage, exportPlan } from "./shared";
const user = useUserStoreHook();
const plans = ref<any[]>([]),
  selected = ref<any>(),
  busy = ref(false),
  loading = ref(false),
  exporting = ref(false);
const form = ref<FormInstance>(),
  draft = ref({
    grade: "小学三年级",
    topic: "杨柳青木版年画",
    duration_minutes: 45,
    mode: "LOCAL"
  });
const modelEnabled = ref(false),
  opening = ref(false),
  historyError = ref(""),
  detailError = ref(""),
  createError = ref(""),
  nextCursor = ref<number | null>(null),
  total = ref(0);
const rules = {
  grade: [
    { required: true, whitespace: true, message: "请输入学段", trigger: "blur" }
  ],
  topic: [
    { required: true, whitespace: true, message: "请输入主题", trigger: "blur" }
  ]
};
let mounted = true,
  epoch = 0,
  historyVersion = 0,
  detailVersion = 0;
let retryIdentity: { body: string; id: string } | undefined;
const token = () => getToken()?.accessToken || "";
const current = (savedToken: string, version: number) =>
  mounted && !!savedToken && token() === savedToken && version === epoch;
const values = (value: unknown): string[] =>
  value == null
    ? []
    : (typeof value === "object" ? Object.values(value) : [value])
        .filter(v => v != null)
        .map(v => (typeof v === "object" ? JSON.stringify(v) : String(v)));
async function load(reset = true, force = false) {
  if ((!force && loading.value) || (!reset && !nextCursor.value)) return;
  const savedToken = token(),
    version = epoch,
    serial = ++historyVersion;
  loading.value = true;
  historyError.value = "";
  try {
    const page = await request.get("/mobile/teacher/lesson-plans/history", {
      limit: 20,
      ...(!reset ? { before_id: nextCursor.value } : {})
    });
    if (!current(savedToken, version) || serial !== historyVersion) return;
    const previous = reset ? [] : plans.value,
      seen = new Set(previous.map(p => p.id));
    plans.value = [...previous, ...page.items.filter(p => !seen.has(p.id))];
    nextCursor.value = page.next_cursor;
    total.value = page.total;
  } catch (e) {
    if (current(savedToken, version) && serial === historyVersion)
      historyError.value = String(errorMessage(e));
  } finally {
    if (current(savedToken, version) && serial === historyVersion)
      loading.value = false;
  }
}
async function capabilities() {
  const savedToken = token(),
    version = epoch;
  try {
    const caps = await request.get("/mobile/teacher/lesson-plans/capabilities");
    if (current(savedToken, version)) modelEnabled.value = !!caps.model_enabled;
  } catch {
    if (current(savedToken, version)) modelEnabled.value = false;
  }
}
async function create() {
  if (busy.value) return;
  const savedToken = token(),
    version = epoch,
    serial = ++detailVersion;
  busy.value = true;
  opening.value = false;
  createError.value = "";
  detailError.value = "";
  try {
    if (
      !(await form.value?.validate().catch(() => false)) ||
      !current(savedToken, version)
    )
      return;
    const body = {
        ...draft.value,
        grade: draft.value.grade.trim(),
        topic: draft.value.topic.trim()
      },
      fingerprint = JSON.stringify(body);
    if (retryIdentity?.body !== fingerprint)
      retryIdentity = { body: fingerprint, id: crypto.randomUUID() };
    const plan = await request.post("/mobile/teacher/lesson-plans", {
      ...body,
      request_id: retryIdentity!.id
    });
    if (!current(savedToken, version) || serial !== detailVersion) return;
    selected.value = plan;
    retryIdentity = undefined;
    ElMessage.success("方案已生成并保存");
    void load(true, true);
  } catch (e) {
    if (current(savedToken, version) && serial === detailVersion)
      createError.value = String(errorMessage(e));
  } finally {
    if (current(savedToken, version) && serial === detailVersion)
      busy.value = false;
  }
}
async function open(id: number) {
  if (busy.value) return;
  const savedToken = token(),
    version = epoch,
    serial = ++detailVersion;
  opening.value = true;
  detailError.value = "";
  try {
    const plan = await request.get("/mobile/teacher/lesson-plans/" + id);
    if (current(savedToken, version) && serial === detailVersion)
      selected.value = plan;
  } catch (e) {
    if (current(savedToken, version) && serial === detailVersion)
      detailError.value = String(errorMessage(e));
  } finally {
    if (current(savedToken, version) && serial === detailVersion)
      opening.value = false;
  }
}
async function download() {
  if (!selected.value || exporting.value || busy.value || opening.value) return;
  const savedToken = token(),
    version = epoch,
    serial = detailVersion,
    id = selected.value.id;
  const valid = () =>
    current(savedToken, version) &&
    serial === detailVersion &&
    selected.value?.id === id;
  exporting.value = true;
  detailError.value = "";
  try {
    await exportPlan(id, valid);
  } catch (e) {
    if (valid()) detailError.value = String(errorMessage(e));
  } finally {
    if (current(savedToken, version)) exporting.value = false;
  }
}
function initialize() {
  void load();
  void capabilities();
}
watch(
  () => [user.username, user.roles.join(",")],
  () => {
    epoch++;
    historyVersion++;
    detailVersion++;
    plans.value = [];
    selected.value = undefined;
    busy.value =
      loading.value =
      exporting.value =
      modelEnabled.value =
      opening.value =
        false;
    historyError.value = detailError.value = createError.value = "";
    nextCursor.value = null;
    total.value = 0;
    retryIdentity = undefined;
    draft.value = {
      grade: "小学三年级",
      topic: "杨柳青木版年画",
      duration_minutes: 45,
      mode: "LOCAL"
    };
    if (token()) initialize();
  },
  { flush: "sync" }
);
onMounted(initialize);
onUnmounted(() => {
  mounted = false;
  epoch++;
  historyVersion++;
  detailVersion++;
});
</script>
<template>
  <section class="plans-layout">
    <el-card shadow="never"
      ><h3>新建备课方案</h3>
      <el-form
        ref="form"
        :model="draft"
        :rules="rules"
        label-position="top"
        @submit.prevent="create"
        ><el-form-item label="学段" prop="grade"
          ><el-input
            v-model.trim="draft.grade"
            maxlength="64"
            :disabled="busy" /></el-form-item
        ><el-form-item label="非遗主题" prop="topic"
          ><el-input
            v-model.trim="draft.topic"
            maxlength="128"
            :disabled="busy" /></el-form-item
        ><el-form-item label="课堂时长（分钟）"
          ><el-input-number
            v-model="draft.duration_minutes"
            :min="10"
            :disabled="busy || opening"
            :max="240" /></el-form-item
        ><el-form-item label="生成方式"
          ><el-select v-model="draft.mode" :disabled="busy"
            ><el-option label="本地课程模板" value="LOCAL" /><el-option
              label="模型辅助"
              value="AUTO"
              :disabled="!modelEnabled" /></el-select></el-form-item
        ><el-button type="primary" native-type="submit" :loading="busy"
          >生成并保存</el-button
        ></el-form
      >
      <p class="hint">
        本地模板提供课堂结构与活动建议，请结合教学材料核对。模型辅助失败时使用本地模板，实际来源会随方案保存。
      </p>
      <el-alert
        v-if="createError"
        :title="createError"
        type="error"
        :closable="false"
      />
      <h3>备课历史（{{ total }}）</h3>
      <el-button :loading="loading" @click="load()">刷新</el-button>
      <el-alert
        v-if="historyError"
        :title="historyError"
        type="error"
        :closable="false"
      />
      <el-empty v-if="!plans.length" description="暂无备课记录" /><button
        v-for="plan in plans"
        :key="plan.id"
        class="history-plan"
        :disabled="busy"
        @click="open(plan.id)"
      >
        <b>{{ plan.title }}</b
        ><small>{{ dateText(plan.created_at) }}</small></button
      ><el-button v-if="nextCursor" :loading="loading" @click="load(false)"
        >加载更多</el-button
      ></el-card
    >
    <el-card shadow="never"
      ><el-alert
        v-if="detailError"
        :title="detailError"
        type="error"
        :closable="false"
      /><el-empty v-if="!selected" description="选择历史记录或生成新方案" />
      <article v-else class="plan-document">
        <header>
          <div>
            <h2>{{ selected.content.title }}</h2>
            <p>
              {{ selected.content.grade }} · {{ selected.content.duration }}
            </p>
            <p>来源：{{ selected.source }}</p>
          </div>
          <el-button
            type="primary"
            :loading="exporting"
            :disabled="busy || opening"
            @click="download"
            >导出PPTX</el-button
          >
        </header>
        <h3>教学目标</h3>
        <p v-for="(value, key) in values(selected.content.targets)" :key="key">
          {{ value }}
        </p>
        <h3>教学重难点</h3>
        <p
          v-for="(value, key) in values(selected.content.key_difficult_points)"
          :key="key"
        >
          {{ value }}
        </p>
        <section
          v-for="(step, index) in selected.content.teaching_process"
          :key="index"
        >
          <h3>{{ step.step }}</h3>
          <p>{{ step.content }}</p>
        </section>
        <h3>课堂讲稿</h3>
        <p>{{ selected.content.teacher_script }}</p>
        <h3>互动问题</h3>
        <p
          v-for="(question, i) in values(
            selected.content.interactive_questions
          )"
          :key="i"
        >
          互动问题 {{ i + 1 }}：{{ question }}
        </p>
        <h3>课后作业</h3>
        <p>{{ selected.content.homework_proposal }}</p>
      </article></el-card
    >
  </section>
</template>
<style scoped>
.plans-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 20px;
}
.plans-layout h3 {
  font-size: 18px;
  margin: 12px 0 20px;
}
.hint {
  color: #747b84;
  font-size: 12px;
  line-height: 1.8;
  margin: 20px 0;
}
.history-plan {
  display: block;
  text-align: left;
  width: 100%;
  padding: 14px 0;
  border-bottom: 1px solid #eee;
  cursor: pointer;
}
.history-plan small {
  display: block;
  color: #747b84;
  margin-top: 8px;
}
.plan-document header {
  display: flex;
  gap: 20px;
  justify-content: space-between;
}
.plan-document h2 {
  font-size: 21px;
}
.plan-document h3 {
  margin: 28px 0 14px;
}
.plan-document p {
  white-space: pre-wrap;
  line-height: 1.9;
  margin: 12px 0;
  overflow-wrap: anywhere;
}
@media (max-width: 1000px) {
  .plans-layout {
    grid-template-columns: 1fr;
  }
}
</style>
