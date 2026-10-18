<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import request from "@/api/request";
import { action, errorMessage } from "./shared";

const classes = ref<any[]>([]);
const contests = ref<any[]>([]);
const studentsHome = ref<any[]>([]);
const studentsAway = ref<any[]>([]);
const loading = ref(false);
const busy = ref(false);
const error = ref("");
const creating = ref(false);
const detail = ref<any>(null);
const editingRoster = ref(false);
const roster = ref({
  home_student_ids: [] as number[],
  away_student_ids: [] as number[],
});
const scoring = ref<Record<number, { score: number | null; comment: string }>>({});
const draft = ref({
  title: "",
  description: "",
  tool_type: "BRONZE_PATTERN",
  home_class_id: undefined as number | undefined,
  away_class_id: undefined as number | undefined,
  round_no: 1,
  scoring_mode: "TOTAL",
  deadline_days: 7,
  home_student_ids: [] as number[],
  away_student_ids: [] as number[],
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

async function load() {
  loading.value = true;
  error.value = "";
  try {
    [classes.value, contests.value] = await Promise.all([
      request.get("/teacher/classes"),
      request.get("/teacher/contests"),
    ]);
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    loading.value = false;
  }
}

async function loadStudents(classId: number, side: "home" | "away") {
  if (!classId) return;
  const rows = await request.get(`/mobile/teacher/classes/${classId}/students`);
  if (side === "home") studentsHome.value = rows;
  else studentsAway.value = rows;
}

async function openCreate() {
  if (classes.value.length < 2) {
    ElMessage.warning("至少需要两个班级才能创建对抗赛");
    return;
  }
  draft.value.home_class_id = classes.value[0].id;
  draft.value.away_class_id = classes.value[1].id;
  draft.value.home_student_ids = [];
  draft.value.away_student_ids = [];
  await Promise.all([
    loadStudents(draft.value.home_class_id, "home"),
    loadStudents(draft.value.away_class_id, "away"),
  ]);
  creating.value = true;
}

async function createContest() {
  if (!draft.value.title.trim() || !draft.value.description.trim()) {
    ElMessage.warning("请填写名称和任务要求");
    return;
  }
  if (!draft.value.home_student_ids.length || !draft.value.away_student_ids.length) {
    ElMessage.warning("两个班级都至少选择一名参赛学生");
    return;
  }
  busy.value = true;
  await action(async () => {
    const created = await request.post("/teacher/contests", draft.value);
    creating.value = false;
    ElMessage.success("对抗赛已创建");
    await load();
    await openDetail(created);
  });
  busy.value = false;
}

function prepareScoring(row: any) {
  const next: Record<number, { score: number | null; comment: string }> = {};
  for (const group of row.classes)
    for (const entry of group.entries)
      next[entry.entry_id] = {
        score: entry.score,
        comment: entry.comment || "",
      };
  scoring.value = next;
}

async function openDetail(row: any) {
  busy.value = true;
  await action(async () => {
    const data = await request.get(`/teacher/contests/${row.id}`);
    detail.value = data;
    prepareScoring(data);
  });
  busy.value = false;
}

async function refreshDetail() {
  if (detail.value) await openDetail(detail.value);
}

async function openRosterEditor() {
  if (!detail.value) return;
  editingRoster.value = true;
  await action(async () => {
    await Promise.all([
      loadStudents(detail.value.home_class.id, "home"),
      loadStudents(detail.value.away_class.id, "away"),
    ]);
    const home = detail.value.classes.find(
      (group: any) => group.class_id === detail.value.home_class.id,
    );
    const away = detail.value.classes.find(
      (group: any) => group.class_id === detail.value.away_class.id,
    );
    roster.value.home_student_ids =
      home?.entries.map((entry: any) => entry.student_id) || [];
    roster.value.away_student_ids =
      away?.entries.map((entry: any) => entry.student_id) || [];
  });
}

async function saveRoster() {
  if (!detail.value) return;
  if (
    !roster.value.home_student_ids.length ||
    !roster.value.away_student_ids.length
  ) {
    ElMessage.warning("两个班级都至少保留一名参赛学生");
    return;
  }
  busy.value = true;
  await action(async () => {
    await request.put(`/teacher/contests/${detail.value.id}/entries`, roster.value);
    editingRoster.value = false;
    ElMessage.success("参赛名单已更新");
    await refreshDetail();
    await load();
  });
  busy.value = false;
}

async function saveScore(entry: any) {
  const current = scoring.value[entry.entry_id];
  if (!current || current.score === null) {
    ElMessage.warning("请填写分数");
    return;
  }
  if (!entry.submission_id) {
    ElMessage.warning("该学生尚未提交作品");
    return;
  }
  busy.value = true;
  await action(async () => {
    await request.post(`/teacher/submissions/${entry.submission_id}/review`, {
      score: current.score,
      comment: current.comment,
    });
    ElMessage.success("评分已保存");
    await refreshDetail();
    await load();
  });
  busy.value = false;
}

async function changeStatus(status: "SCORING" | "PUBLISHED") {
  if (status === "PUBLISHED") {
    const confirmed = window.confirm(
      "公布后本轮成绩将锁定，不能再修改评分。确定公布？"
    );
    if (!confirmed) return;
  }
  busy.value = true;
  await action(async () => {
    await request.post(`/teacher/contests/${detail.value.id}/status`, { status });
    ElMessage.success(status === "PUBLISHED" ? "成绩已公布" : "已进入评分阶段");
    await refreshDetail();
    await load();
  });
  busy.value = false;
}

onMounted(load);
</script>

<template>
  <section v-loading="loading">
    <el-alert v-if="error" :title="error" type="error" :closable="false" />
    <div class="toolbar">
      <el-button type="primary" @click="openCreate">新建对抗赛</el-button>
      <el-button @click="load">刷新</el-button>
    </div>
    <el-table :data="contests" empty-text="还没有对抗赛">
      <el-table-column prop="title" label="对抗赛" min-width="180" />
      <el-table-column label="对阵" min-width="220">
        <template #default="{ row }">
          {{ row.home_class.name }} VS {{ row.away_class.name }}
        </template>
      </el-table-column>
      <el-table-column label="轮次" width="80">
        <template #default="{ row }">第 {{ row.round_no }} 轮</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'PUBLISHED' ? 'success' : row.status === 'SCORING' ? 'warning' : 'info'">
            {{ statusText[row.status] || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="submitted_count" label="提交" width="80" />
      <el-table-column label="胜者" min-width="120">
        <template #default="{ row }">
          <template v-if="row.winner_class_id">
            {{
              row.winner_class_id === row.home_class.id
                ? row.home_class.name
                : row.away_class.name
            }}
          </template>
          <span v-else>—</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">名单与评分</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="creating" title="新建班级对抗赛" width="760px">
      <el-form label-position="top" @submit.prevent="createContest">
        <el-form-item label="对抗赛名称">
          <el-input v-model.trim="draft.title" maxlength="128" />
        </el-form-item>
        <el-form-item label="任务要求">
          <el-input v-model.trim="draft.description" type="textarea" :rows="4" maxlength="10000" />
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="主队班级">
            <el-select
              v-model="draft.home_class_id"
              style="width: 100%"
              @change="loadStudents(draft.home_class_id!, 'home')"
            >
              <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="客队班级">
            <el-select
              v-model="draft.away_class_id"
              style="width: 100%"
              @change="loadStudents(draft.away_class_id!, 'away')"
            >
              <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="轮次">
            <el-input-number v-model="draft.round_no" :min="1" :max="99" />
          </el-form-item>
          <el-form-item label="排名方式">
            <el-select v-model="draft.scoring_mode" style="width: 100%">
              <el-option label="班级总分" value="TOTAL" />
              <el-option label="班级平均分" value="AVERAGE" />
            </el-select>
          </el-form-item>
          <el-form-item label="创作工具">
            <el-select v-model="draft.tool_type" style="width: 100%">
              <el-option label="皮影角色" value="SHADOW_PUPPET" />
              <el-option label="青铜纹样" value="BRONZE_PATTERN" />
              <el-option label="漆绣创作" value="LACQUER" />
            </el-select>
          </el-form-item>
          <el-form-item label="截止天数">
            <el-input-number v-model="draft.deadline_days" :min="1" :max="365" />
          </el-form-item>
        </div>
        <div class="form-grid">
          <div>
            <h4>主队参赛名单</h4>
            <el-checkbox-group v-model="draft.home_student_ids">
              <el-checkbox v-for="s in studentsHome" :key="s.id" :value="s.id">
                {{ s.nickname }}
              </el-checkbox>
            </el-checkbox-group>
            <el-empty v-if="!studentsHome.length" description="该班暂无学生" :image-size="60" />
          </div>
          <div>
            <h4>客队参赛名单</h4>
            <el-checkbox-group v-model="draft.away_student_ids">
              <el-checkbox v-for="s in studentsAway" :key="s.id" :value="s.id">
                {{ s.nickname }}
              </el-checkbox>
            </el-checkbox-group>
            <el-empty v-if="!studentsAway.length" description="该班暂无学生" :image-size="60" />
          </div>
        </div>
        <el-button type="primary" native-type="submit" :loading="busy">创建对抗赛</el-button>
      </el-form>
    </el-dialog>

    <el-dialog
      :model-value="!!detail"
      :title="detail?.title || '对抗赛详情'"
      width="980px"
      @close="detail = null"
    >
      <template v-if="detail">
        <el-descriptions :column="4" border>
          <el-descriptions-item label="轮次">第 {{ detail.round_no }} 轮</el-descriptions-item>
          <el-descriptions-item label="工具">
            {{ toolText[detail.tool_type] || detail.tool_type }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            {{ statusText[detail.status] || detail.status }}
          </el-descriptions-item>
          <el-descriptions-item label="截止">
            {{ detail.deadline?.slice(0, 16).replace("T", " ") }}
          </el-descriptions-item>
        </el-descriptions>
        <div class="summary-row">
          <el-card v-for="group in detail.classes" :key="group.class_id" shadow="never">
            <strong>{{ group.name }}</strong>
            <p>参赛 {{ group.participant_count }} · 提交 {{ group.submitted_count }} · 已评 {{ group.scored_count }}</p>
            <p v-if="detail.status === 'PUBLISHED'">
              总分 {{ group.total_score ?? "—" }} · 平均 {{ group.average_score ?? "—" }}
              <span v-if="group.rank"> · 第 {{ group.rank }} 名</span>
            </p>
          </el-card>
        </div>
        <el-alert
          v-if="detail.status === 'PUBLISHED'"
          :title="
            detail.winner_class_id
              ? '本轮胜者：' +
                (detail.winner_class_id === detail.home_class.id
                  ? detail.home_class.name
                  : detail.away_class.name)
              : '本轮未形成完整胜负'
          "
          type="success"
          :closable="false"
          class="winner-alert"
        />
        <div v-if="detail.can_edit_roster" class="roster-toolbar">
          <el-button @click="openRosterEditor">编辑参赛名单</el-button>
        </div>
        <template v-for="group in detail.classes" :key="'table-' + group.class_id">
          <h4 class="group-title">{{ group.name }}</h4>
          <el-table :data="group.entries" empty-text="暂无参赛学生" size="small">
            <el-table-column prop="student_name" label="学生" width="120" />
            <el-table-column label="提交" width="90">
              <template #default="{ row }">
                {{ row.submitted ? (row.score != null ? row.score + " 分" : "待评分") : "未提交" }}
              </template>
            </el-table-column>
            <el-table-column label="排名" width="80">
              <template #default="{ row }">{{ row.rank ? "第 " + row.rank + " 名" : "—" }}</template>
            </el-table-column>
            <el-table-column prop="content" label="作品说明" min-width="180">
              <template #default="{ row }">
                <p class="submission-text">{{ row.content || "—" }}</p>
              </template>
            </el-table-column>
            <el-table-column label="分数" width="120">
              <template #default="{ row }">
                <el-input-number
                  v-if="row.submitted && detail.status !== 'PUBLISHED'"
                  v-model="scoring[row.entry_id].score"
                  :min="0"
                  :max="100"
                  size="small"
                />
                <span v-else>{{ row.score ?? "—" }}</span>
              </template>
            </el-table-column>
            <el-table-column label="评语" min-width="180">
              <template #default="{ row }">
                <el-input
                  v-if="row.submitted && detail.status !== 'PUBLISHED'"
                  v-model="scoring[row.entry_id].comment"
                  size="small"
                  maxlength="5000"
                />
                <span v-else>{{ row.comment || "—" }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button
                  v-if="row.submitted && detail.status !== 'PUBLISHED'"
                  link
                  type="primary"
                  :loading="busy"
                  @click="saveScore(row)"
                >
                  保存评分
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </template>
        <div class="dialog-actions">
          <el-button
            v-if="detail.status === 'OPEN'"
            :loading="busy"
            @click="changeStatus('SCORING')"
          >
            截止提交，进入评分
          </el-button>
          <el-button
            v-if="detail.status !== 'PUBLISHED'"
            type="primary"
            :loading="busy"
            @click="changeStatus('PUBLISHED')"
          >
            公布成绩并锁定
          </el-button>
          <span v-else class="locked-text">成绩已公布，评分已锁定</span>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="editingRoster" title="编辑参赛名单" width="720px">
      <el-alert
        title="已有学生提交作品后不能将其移出名单；截止或公布后名单锁定。"
        type="info"
        :closable="false"
      />
      <div class="form-grid" style="margin-top: 16px">
        <div>
          <h4>{{ detail?.home_class.name }} 参赛名单</h4>
          <el-checkbox-group v-model="roster.home_student_ids">
            <el-checkbox v-for="s in studentsHome" :key="s.id" :value="s.id">
              {{ s.nickname }}
            </el-checkbox>
          </el-checkbox-group>
          <el-empty
            v-if="!studentsHome.length"
            description="该班暂无学生"
            :image-size="60"
          />
        </div>
        <div>
          <h4>{{ detail?.away_class.name }} 参赛名单</h4>
          <el-checkbox-group v-model="roster.away_student_ids">
            <el-checkbox v-for="s in studentsAway" :key="s.id" :value="s.id">
              {{ s.nickname }}
            </el-checkbox>
          </el-checkbox-group>
          <el-empty
            v-if="!studentsAway.length"
            description="该班暂无学生"
            :image-size="60"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="editingRoster = false">取消</el-button>
        <el-button type="primary" :loading="busy" @click="saveRoster"
          >保存名单</el-button
        >
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 20px;
}
.form-grid h4 {
  margin: 8px 0 12px;
}
.summary-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin: 18px 0;
}
.summary-row p {
  margin-top: 8px;
  color: #646c77;
  font-size: 13px;
}
.winner-alert {
  margin-bottom: 16px;
}
.roster-toolbar {
  margin-bottom: 12px;
}
.group-title {
  margin: 18px 0 10px;
  font-size: 15px;
}
.submission-text {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  max-height: 100px;
  overflow: auto;
  margin: 0;
}
.dialog-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-top: 20px;
}
.locked-text {
  color: #72777f;
}
</style>
