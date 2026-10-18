<script setup lang="ts">
import { ref, watch } from "vue";
import { ElMessage, type FormInstance } from "element-plus";
import request from "@/api/request";
import { action, dateText, errorMessage } from "./shared";
const props = defineProps<{ classId?: number }>(),
  emit = defineEmits<{ changed: [] }>();
const assignments = ref<any[]>([]),
  submissions = ref<any[]>([]),
  selected = ref<any>(),
  review = ref<any>();
const loading = ref(false),
  busy = ref(false),
  error = ref(""),
  creating = ref(false),
  form = ref<FormInstance>();
const draft = ref({
  title: "",
  description: "",
  type: "OFFLINE_HANDMADE",
  tool_type: "SHADOW_PUPPET",
  deadline_days: 7
});
const rules = {
  title: [
    {
      required: true,
      whitespace: true,
      message: "请输入作业标题",
      trigger: "blur"
    }
  ],
  description: [
    {
      required: true,
      whitespace: true,
      message: "请输入作业要求",
      trigger: "blur"
    }
  ]
};
let generation = 0;
async function load() {
  const serial = ++generation;
  assignments.value = [];
  submissions.value = [];
  selected.value = undefined;
  error.value = "";
  if (!props.classId) return;
  loading.value = true;
  try {
    const rows = await request.get("/teacher/assignments", {
      class_id: props.classId
    });
    if (serial === generation) assignments.value = rows;
  } catch (e) {
    if (serial === generation) error.value = errorMessage(e);
  } finally {
    if (serial === generation) loading.value = false;
  }
}
async function create() {
  if (!(await form.value?.validate().catch(() => false))) return;
  busy.value = true;
  await action(async () => {
    await request.post("/teacher/assignments", {
      ...draft.value,
      class_id: props.classId
    });
    creating.value = false;
    draft.value.title = "";
    draft.value.description = "";
    ElMessage.success("作业已发布，学生可在手机端查看");
    await load();
    emit("changed");
  });
  busy.value = false;
}
async function openSubmissions(item: any) {
  selected.value = item;
  submissions.value = [];
  const id = props.classId;
  await action(async () => {
    const rows = await request.get(
      `/teacher/assignments/${item.id}/submissions`
    );
    if (selected.value?.id === item.id && props.classId === id)
      submissions.value = rows;
  });
}
async function saveReview() {
  busy.value = true;
  await action(async () => {
    await request.post(`/teacher/submissions/${review.value.id}/review`, {
      score: review.value.score,
      comment: review.value.comment
    });
    review.value = undefined;
    ElMessage.success("批改已保存");
    await openSubmissions(selected.value);
    emit("changed");
  });
  busy.value = false;
}
watch(() => props.classId, load, { immediate: true });
</script>
<template>
  <section v-loading="loading">
    <el-alert v-if="error" :title="error" type="error" :closable="false" />
    <el-empty v-if="!classId" description="请选择班级" /><template v-else>
      <div class="toolbar">
        <el-button type="primary" @click="creating = true">发布作业</el-button
        ><el-button @click="load">刷新作业</el-button>
      </div>
      <el-table :data="assignments" empty-text="尚未发布作业"
        ><el-table-column
          prop="title"
          label="作业"
          min-width="200"
        /><el-table-column label="截止时间" min-width="180"
          ><template #default="{ row }">{{
            dateText(row.deadline)
          }}</template></el-table-column
        ><el-table-column
          prop="submit_count"
          label="提交人数"
          width="100"
        /><el-table-column label="操作" width="120"
          ><template #default="{ row }"
            ><el-button link type="primary" @click="openSubmissions(row)"
              >查看与批改</el-button
            ></template
          ></el-table-column
        ></el-table
      >
      <template v-if="selected"
        ><h3 class="section-title">{{ selected.title }} · 学生提交</h3>
        <el-table :data="submissions" empty-text="暂时没有学生提交"
          ><el-table-column
            prop="student_name"
            label="学生"
            width="130"
          /><el-table-column prop="content" label="作业内容" min-width="250"
            ><template #default="{ row }"
              ><p class="submission-text">{{ row.content }}</p></template
            ></el-table-column
          ><el-table-column label="得分" width="100"
            ><template #default="{ row }">{{
              row.score ?? "待批改"
            }}</template></el-table-column
          ><el-table-column
            prop="comment"
            label="教师评语"
            min-width="180"
          /><el-table-column label="操作" width="100"
            ><template #default="{ row }"
              ><el-button
                link
                type="primary"
                @click="
                  review = {
                    ...row,
                    score: row.score ?? 80,
                    comment: row.comment || ''
                  }
                "
                >{{
                  row.status === "REVIEWED" ? "修改批改" : "批改"
                }}</el-button
              ></template
            ></el-table-column
          ></el-table
        ></template
      >
    </template>
    <el-dialog v-model="creating" title="发布作业" width="600px"
      ><el-form
        ref="form"
        :model="draft"
        :rules="rules"
        label-position="top"
        @submit.prevent="create"
        ><el-form-item label="作业标题" prop="title"
          ><el-input v-model.trim="draft.title" maxlength="128" /></el-form-item
        ><el-form-item label="作业要求" prop="description"
          ><el-input
            v-model.trim="draft.description"
            type="textarea"
            :rows="5"
            maxlength="10000" /></el-form-item
        ><el-form-item label="创作方式"
          ><el-radio-group v-model="draft.type"
            ><el-radio value="OFFLINE_HANDMADE">手工作品</el-radio
            ><el-radio value="AI_CREATION">工坊创作</el-radio></el-radio-group
          ></el-form-item
        ><el-form-item v-if="draft.type === 'AI_CREATION'" label="工坊"
          ><el-select v-model="draft.tool_type"
            ><el-option label="皮影工坊" value="SHADOW_PUPPET" /><el-option
              label="青铜工坊"
              value="BRONZE_PATTERN" /><el-option
              label="漆艺工坊"
              value="LACQUER" /></el-select></el-form-item
        ><el-form-item label="几天后截止"
          ><el-input-number
            v-model="draft.deadline_days"
            :min="1"
            :max="365" /></el-form-item
        ><el-button native-type="submit" type="primary" :loading="busy"
          >发布作业</el-button
        ></el-form
      ></el-dialog
    >
    <el-dialog
      :model-value="!!review"
      title="批改作业"
      width="600px"
      @close="review = undefined"
      ><el-form v-if="review" label-position="top" @submit.prevent="saveReview"
        ><p class="submission-text">{{ review.content }}</p>
        <el-form-item label="分数"
          ><el-input-number
            v-model="review.score"
            :min="0"
            :max="100" /></el-form-item
        ><el-form-item label="评语"
          ><el-input
            v-model="review.comment"
            type="textarea"
            :rows="4"
            maxlength="5000" /></el-form-item
        ><el-button native-type="submit" type="primary" :loading="busy"
          >保存批改</el-button
        ></el-form
      ></el-dialog
    >
  </section>
</template>
<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.section-title {
  font-size: 18px;
  margin: 28px 0 18px;
}
.submission-text {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  max-height: 280px;
  overflow: auto;
  line-height: 1.8;
  margin: 12px 0;
}
</style>
