<script setup lang="ts">
import { computed, ref, watch, onUnmounted } from "vue";
import { ElMessage, type FormInstance } from "element-plus";
import request from "@/api/request";
import { getToken } from "@/utils/auth";

interface ServiceRow {
  id: number;
  user_id: number;
  status: string;
  created_at: string;
  item_name?: string;
  energy_cost?: number;
  receiver_name?: string;
  receiver_phone?: string;
  receiver_address?: string;
  tracking_no?: string;
  handling_note?: string;
  handled_by?: number;
  handled_at?: string;
  content?: string;
  contact?: string;
  reply_text?: string;
}
const tab = ref("exchanges"),
  filter = ref("ALL"),
  page = ref(1),
  total = ref(0);
const rows = ref<ServiceRow[]>([]),
  loading = ref(false),
  error = ref("");
const selected = ref<ServiceRow>(),
  operation = ref<"fulfill" | "cancel" | "resolve">("fulfill");
const visible = ref(false),
  saving = ref(false),
  starting = ref(false),
  form = ref<FormInstance>();
const draft = ref({ tracking_no: "", handling_note: "", reply_text: "" });
let loadVersion = 0,
  alive = true;
const titles = {
  fulfill: "确认发放",
  cancel: "取消并退还",
  resolve: "回复并完成"
};
const states = computed(() =>
  tab.value === "exchanges"
    ? [
        { value: "REQUESTED", label: "待发放" },
        { value: "FULFILLED", label: "已发放" },
        { value: "CANCELLED", label: "已取消" }
      ]
    : [
        { value: "PENDING", label: "待处理" },
        { value: "PROCESSING", label: "处理中" },
        { value: "RESOLVED", label: "已回复" }
      ]
);
const labels: Record<string, string> = {
  REQUESTED: "待发放",
  FULFILLED: "已发放",
  CANCELLED: "已取消",
  PENDING: "待处理",
  PROCESSING: "处理中",
  RESOLVED: "已回复"
};
const rules = computed(() => ({
  tracking_no: [
    {
      required: operation.value === "fulfill",
      whitespace: true,
      message: "请输入发放凭据或物流单号",
      trigger: "blur"
    }
  ],
  handling_note: [
    {
      required: operation.value === "cancel",
      whitespace: true,
      message: "请说明取消原因，用户可以查看",
      trigger: "blur"
    }
  ],
  reply_text: [
    {
      required: operation.value === "resolve",
      whitespace: true,
      message: "请填写给用户的回复",
      trigger: "blur"
    }
  ]
}));
function dateText(value?: string) {
  if (!value) return "—";
  const iso = value.replace(" ", "T");
  const date = new Date(/Z$|[+-]\d\d:\d\d$/.test(iso) ? iso : iso + "Z");
  return Number.isNaN(+date)
    ? "—"
    : date.toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" });
}
function message(e: any) {
  return String(e.response?.data?.detail || e.message || "操作失败，请重试");
}
function context() {
  const token = getToken()?.accessToken;
  return () => alive && token === getToken()?.accessToken;
}
async function load() {
  const current = context(),
    version = ++loadVersion;
  loading.value = true;
  error.value = "";
  rows.value = [];
  try {
    const result = await request.get<{ items: ServiceRow[]; total: number }>(
      `/mobile/admin/${tab.value}`,
      {
        status: filter.value === "ALL" ? undefined : filter.value,
        page: page.value,
        page_size: 20
      }
    );
    if (current() && version === loadVersion) {
      rows.value = result.items;
      total.value = result.total;
    }
  } catch (e) {
    if (current() && version === loadVersion) error.value = message(e);
  } finally {
    if (current() && version === loadVersion) loading.value = false;
  }
}
function changeTab() {
  filter.value = "ALL";
  page.value = 1;
  visible.value = false;
  selected.value = undefined;
}
function changeFilter() {
  page.value = 1;
}
function open(row: ServiceRow, kind: typeof operation.value) {
  selected.value = row;
  operation.value = kind;
  draft.value = { tracking_no: "", handling_note: "", reply_text: "" };
  visible.value = true;
  form.value?.clearValidate();
}
async function start(row: ServiceRow) {
  if (starting.value || saving.value) return;
  const current = context();
  starting.value = true;
  try {
    await request.put(`/mobile/admin/feedback/${row.id}`, {
      status: "PROCESSING"
    });
    if (current()) {
      ElMessage.success("已标记为处理中");
      await load();
    }
  } catch (e) {
    if (current()) ElMessage.error(message(e));
  } finally {
    if (current()) starting.value = false;
  }
}
async function save() {
  if (saving.value || !selected.value) return;
  const current = context(),
    id = selected.value.id,
    kind = operation.value;
  saving.value = true;
  try {
    if (!(await form.value?.validate().catch(() => false)) || !current())
      return;
    if (kind === "resolve") {
      await request.put(`/mobile/admin/feedback/${id}`, {
        status: "RESOLVED",
        reply_text: draft.value.reply_text
      });
    } else {
      await request.put(`/mobile/admin/exchanges/${id}`, {
        status: kind === "fulfill" ? "FULFILLED" : "CANCELLED",
        tracking_no: kind === "fulfill" ? draft.value.tracking_no : "",
        handling_note: draft.value.handling_note
      });
    }
    if (current()) {
      visible.value = false;
      selected.value = undefined;
      ElMessage.success("处理结果已保存");
      await load();
    }
  } catch (e) {
    if (current()) ElMessage.error(message(e));
  } finally {
    if (current()) saving.value = false;
  }
}
watch([tab, filter, page], load, { immediate: true });
onUnmounted(() => {
  alive = false;
  loadVersion++;
});
</script>
<template>
  <section class="support-page">
    <header>
      <div>
        <h2>兑换与反馈</h2>
        <p>处理手机端提交的兑换申请与建议，结果同步到用户的个人中心。</p>
      </div>
      <el-button :loading="loading" :disabled="saving || starting" @click="load"
        >刷新列表</el-button
      >
    </header>
    <el-card shadow="never">
      <el-tabs v-model="tab" @tab-change="changeTab"
        ><el-tab-pane
          label="能量兑换"
          name="exchanges"
          :disabled="saving || starting" /><el-tab-pane
          label="用户反馈"
          name="feedback"
          :disabled="saving || starting"
      /></el-tabs>
      <div class="filter-row">
        <label for="support-status">处理状态</label
        ><el-select
          id="support-status"
          v-model="filter"
          aria-label="处理状态"
          :disabled="saving || starting"
          @change="changeFilter"
          ><el-option label="全部" value="ALL" /><el-option
            v-for="state in states"
            :key="state.value"
            :label="state.label"
            :value="state.value" /></el-select
        ><span>共 {{ total }} 条</span>
      </div>
      <el-alert
        v-if="error"
        :title="error"
        type="error"
        :closable="false"
        show-icon
      />
      <el-table
        v-else
        :key="tab"
        v-loading="loading"
        :data="rows"
        empty-text="暂无相关记录"
        stripe
        row-key="id"
      >
        <el-table-column prop="id" label="编号" width="80" />
        <el-table-column prop="user_id" label="用户ID" width="90" />
        <el-table-column
          v-if="tab === 'exchanges'"
          label="兑换商品"
          min-width="160"
          ><template #default="{ row }"
            ><b>{{ row.item_name }}</b>
            <p>{{ row.energy_cost }} 能量</p></template
          ></el-table-column
        >
        <el-table-column
          v-if="tab === 'exchanges'"
          label="收件信息"
          min-width="220"
          ><template #default="{ row }"
            ><p>{{ row.receiver_name }} · {{ row.receiver_phone }}</p>
            <p class="long-text">{{ row.receiver_address }}</p></template
          ></el-table-column
        >
        <el-table-column
          v-if="tab === 'feedback'"
          label="反馈内容"
          min-width="260"
          ><template #default="{ row }"
            ><p class="long-text">{{ row.content }}</p>
            <small>联系方式：{{ row.contact || "未填写" }}</small></template
          ></el-table-column
        >
        <el-table-column label="状态" width="100"
          ><template #default="{ row }"
            ><el-tag
              :type="
                row.status === 'RESOLVED' || row.status === 'FULFILLED'
                  ? 'success'
                  : row.status === 'CANCELLED'
                    ? 'info'
                    : 'warning'
              "
              >{{ labels[row.status] || row.status }}</el-tag
            ></template
          ></el-table-column
        >
        <el-table-column label="处理记录" min-width="230"
          ><template #default="{ row }"
            ><p v-if="row.tracking_no">发放凭据：{{ row.tracking_no }}</p>
            <p class="long-text">
              {{ row.reply_text || row.handling_note || "—" }}
            </p>
            <small v-if="row.handled_at"
              >操作人 #{{ row.handled_by }} ·
              {{ dateText(row.handled_at) }}</small
            ></template
          ></el-table-column
        >
        <el-table-column label="提交时间" width="180"
          ><template #default="{ row }">{{
            dateText(row.created_at)
          }}</template></el-table-column
        >
        <el-table-column label="操作" width="200" fixed="right"
          ><template #default="{ row }"
            ><template v-if="row.status === 'REQUESTED'"
              ><el-button
                link
                type="primary"
                :disabled="saving || starting"
                @click="open(row, 'fulfill')"
                >确认发放</el-button
              ><el-button
                link
                type="danger"
                :disabled="saving || starting"
                @click="open(row, 'cancel')"
                >取消并退还</el-button
              ></template
            ><template
              v-else-if="
                row.status === 'PENDING' || row.status === 'PROCESSING'
              "
              ><el-button
                v-if="row.status === 'PENDING'"
                link
                type="primary"
                :disabled="saving || starting"
                @click="start(row)"
                >开始处理</el-button
              ><el-button
                link
                type="success"
                :disabled="saving || starting"
                @click="open(row, 'resolve')"
                >回复并完成</el-button
              ></template
            ><span v-else>处理完毕</span></template
          ></el-table-column
        >
      </el-table>
      <el-pagination
        v-model:current-page="page"
        :page-size="20"
        :total="total"
        layout="prev, pager, next, total"
        :disabled="loading || saving || starting"
      />
    </el-card>
    <el-dialog
      v-model="visible"
      :title="titles[operation]"
      width="560px"
      :close-on-click-modal="!saving"
      :close-on-press-escape="!saving"
      :show-close="!saving"
      destroy-on-close
    >
      <template v-if="selected"
        ><p v-if="operation === 'resolve'" class="long-text">
          {{ selected.content }}
        </p>
        <p v-else>
          {{ selected.item_name }} · {{ selected.energy_cost }} 能量 · 申请 #{{
            selected.id
          }}
        </p>
        <el-alert
          v-if="operation === 'cancel'"
          title="确认后会退还本次扣除的能量并恢复一份库存；已发放的申请无法取消。"
          type="warning"
          :closable="false" />
        <el-form
          ref="form"
          :model="draft"
          :rules="rules"
          label-position="top"
          @submit.prevent="save"
        >
          <el-form-item
            v-if="operation === 'fulfill'"
            label="发放凭据或物流单号"
            prop="tracking_no"
            ><el-input
              v-model.trim="draft.tracking_no"
              maxlength="128"
              :disabled="saving"
          /></el-form-item>
          <el-form-item
            v-if="operation !== 'resolve'"
            :label="
              operation === 'cancel'
                ? '取消原因（用户可见）'
                : '处理说明（用户可见，可选）'
            "
            prop="handling_note"
            ><el-input
              v-model.trim="draft.handling_note"
              type="textarea"
              :rows="3"
              maxlength="500"
              show-word-limit
              :disabled="saving"
          /></el-form-item>
          <el-form-item v-else label="平台回复（用户可见）" prop="reply_text"
            ><el-input
              v-model.trim="draft.reply_text"
              type="textarea"
              :rows="6"
              maxlength="5000"
              show-word-limit
              :disabled="saving"
          /></el-form-item> </el-form
      ></template>
      <template #footer
        ><el-button :disabled="saving" @click="visible = false">返回</el-button
        ><el-button
          :type="operation === 'cancel' ? 'danger' : 'primary'"
          :loading="saving"
          @click="save"
          >{{ titles[operation] }}</el-button
        ></template
      >
    </el-dialog>
  </section>
</template>
<style scoped>
.support-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}
header h2 {
  margin: 0 0 8px;
  font-size: 24px;
}
header p,
small {
  color: var(--el-text-color-secondary);
}
.filter-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 0 0 18px;
}
.filter-row .el-select {
  width: 180px;
}
.filter-row span {
  margin-left: auto;
  color: var(--el-text-color-secondary);
}
.long-text {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  line-height: 1.8;
}
.el-pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
.el-form {
  margin-top: 20px;
}
</style>
