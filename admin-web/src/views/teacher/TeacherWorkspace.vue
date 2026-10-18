<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { ElMessage, type FormInstance } from "element-plus";
import request from "@/api/request";
import { errorMessage, action } from "./shared";
import TeacherAssignments from "./TeacherAssignments.vue";
import TeacherContests from "./TeacherContests.vue";
import TeacherPlans from "./TeacherPlans.vue";
import TeacherClassroom from "./TeacherClassroom.vue";
const classes = ref<any[]>([]),
  selected = ref<number>(),
  students = ref<any[]>([]),
  overview = ref<any>({});
const loading = ref(false),
  error = ref(""),
  creating = ref(false),
  saving = ref(false),
  newClass = ref(false);
const attendanceDay = ref("");
const classForm = ref<FormInstance>(),
  draft = ref({ name: "", grade: "小学三年级" });
const classRules = {
  name: [
    {
      required: true,
      whitespace: true,
      message: "请输入班级名称",
      trigger: "blur"
    }
  ],
  grade: [{ required: true, message: "请输入学段", trigger: "blur" }]
};
let studentRequest = 0;
async function loadStudents() {
  const id = selected.value,
    serial = ++studentRequest;
  students.value = [];
  attendanceDay.value = "";
  if (!id) return;
  await action(async () => {
    const result = await request.get(`/mobile/teacher/classes/${id}/analytics`);
    if (serial === studentRequest && id === selected.value) {
      students.value = result.students;
      attendanceDay.value = result.day;
    }
  });
}
async function load() {
  loading.value = true;
  error.value = "";
  try {
    [classes.value, overview.value] = await Promise.all([
      request.get("/teacher/classes"),
      request.get("/mobile/teacher/overview")
    ]);
    if (!classes.value.some(c => c.id === selected.value))
      selected.value = classes.value[0]?.id;
    else await loadStudents();
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    loading.value = false;
  }
}
async function createClass() {
  if (!(await classForm.value?.validate().catch(() => false))) return;
  creating.value = true;
  await action(async () => {
    const created = await request.post("/mobile/teacher/classes", draft.value);
    newClass.value = false;
    await load();
    selected.value = created.id;
    ElMessage.success("班级已创建，可将邀请码发给学生");
  });
  creating.value = false;
}
async function saveAttendance() {
  saving.value = true;
  await action(async () => {
    const records = students.value
      .filter(s => s.attendance !== "UNRECORDED")
      .map(s => ({ student_id: s.id, status: s.attendance }));
    if (!records.length) {
      ElMessage.info("请先选择学生的考勤状态");
      return;
    }
    await request.put(`/mobile/teacher/classes/${selected.value}/attendance`, {
      records,
      day: attendanceDay.value
    });
    ElMessage.success("今日考勤已保存");
    await load();
  });
  saving.value = false;
}
watch(selected, loadStudents);
onMounted(load);
</script>
<template>
  <main class="teacher-workspace" v-loading="loading">
    <header>
      <div>
        <h1>津韵润乡 · 教师工作台</h1>
        <p>班级学情、教学活动与学生端实时协同</p>
      </div>
      <el-button @click="load">刷新数据</el-button>
    </header>
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      :closable="false"
    />
    <section class="overview-grid">
      <el-card
        v-for="metric in [
          ['班级', overview.class_count],
          ['学生', overview.student_count],
          ['作业', overview.assignment_count],
          ['提交', overview.submission_count],
          ['备课', overview.lesson_plan_count]
        ]"
        :key="String(metric[0])"
        shadow="never"
        ><span>{{ metric[0] }}</span
        ><strong>{{ metric[1] ?? "—" }}</strong></el-card
      >
    </section>
    <div class="class-selector">
      <label for="teacher-class">当前班级</label
      ><el-select
        id="teacher-class"
        v-model="selected"
        placeholder="请选择班级"
        style="width: 280px"
        ><el-option
          v-for="c in classes"
          :key="c.id"
          :value="c.id"
          :label="c.name + ' · ' + c.grade" /></el-select
      ><span v-if="selected"
        >邀请码：<b>{{
          classes.find(c => c.id === selected)?.invite_code
        }}</b></span
      ><el-button type="primary" @click="newClass = true">创建班级</el-button>
    </div>
    <el-tabs
      ><el-tab-pane label="班级学情与考勤">
        <el-empty v-if="!selected" description="创建第一个班级，邀请学生加入" />
        <template v-else
          ><el-table
            :data="students"
            empty-text="学生使用邀请码加入后会出现在这里"
            stripe
          >
            <el-table-column prop="nickname" label="学生" min-width="130" />
            <el-table-column label="课程完成率" min-width="120"
              ><template #default="{ row }">{{
                row.completion_rate == null
                  ? "暂无学习记录"
                  : row.completion_rate + "%"
              }}</template></el-table-column
            >
            <el-table-column label="答题正确率" min-width="120"
              ><template #default="{ row }">{{
                row.quiz_accuracy == null
                  ? "暂无答题记录"
                  : row.quiz_accuracy + "%"
              }}</template></el-table-column
            >
            <el-table-column
              prop="energy_value"
              label="能量"
              width="90"
            /><el-table-column prop="badge_count" label="徽章" width="90" />
            <el-table-column label="今日考勤" width="180"
              ><template #default="{ row }"
                ><el-select
                  v-model="row.attendance"
                  :aria-label="row.nickname + '的考勤'"
                  ><el-option label="未记录" value="UNRECORDED" /><el-option
                    label="出勤"
                    value="PRESENT" /><el-option
                    label="请假"
                    value="LEAVE" /><el-option
                    label="缺勤"
                    value="ABSENT" /></el-select></template
            ></el-table-column> </el-table
          ><el-button
            class="save-attendance"
            type="primary"
            :loading="saving"
            :disabled="!students.length"
            @click="saveAttendance"
            >保存今日考勤</el-button
          ></template
        > </el-tab-pane
      ><el-tab-pane label="作业与批改" lazy
        ><TeacherAssignments
          :class-id="selected"
          @changed="load" /></el-tab-pane
      ><el-tab-pane label="班级对抗赛" lazy
        ><TeacherContests /></el-tab-pane
      ><el-tab-pane label="备课与课件" lazy><TeacherPlans /></el-tab-pane
      ><el-tab-pane label="通知与课堂互动" lazy
        ><TeacherClassroom :class-id="selected" /></el-tab-pane
    ></el-tabs>
    <el-dialog v-model="newClass" title="创建班级" width="480px"
      ><el-form
        ref="classForm"
        :model="draft"
        :rules="classRules"
        label-position="top"
        @submit.prevent="createClass"
        ><el-form-item label="班级名称" prop="name"
          ><el-input v-model.trim="draft.name" maxlength="64" /></el-form-item
        ><el-form-item label="学段" prop="grade"
          ><el-input v-model.trim="draft.grade" maxlength="32" /></el-form-item
        ><el-button type="primary" native-type="submit" :loading="creating"
          >创建班级</el-button
        ></el-form
      ></el-dialog
    >
  </main>
</template>
<style scoped>
.teacher-workspace {
  padding: 24px;
  max-width: 1600px;
  margin: auto;
}
.teacher-workspace header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.teacher-workspace h1 {
  font-size: 25px;
  font-weight: 600;
}
.teacher-workspace header p {
  color: #72777f;
  margin-top: 8px;
}
.overview-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin: 20px 0;
}
.overview-grid strong {
  display: block;
  font-size: 28px;
  margin-top: 12px;
}
.overview-grid span {
  color: #646c77;
}
.class-selector {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
  margin: 28px 0;
}
.save-attendance {
  margin-top: 20px;
}
@media (max-width: 900px) {
  .overview-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .teacher-workspace {
    padding: 12px;
  }
}
</style>
