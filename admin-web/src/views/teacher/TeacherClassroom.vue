<script setup lang="ts">
import { onUnmounted, ref, watch } from "vue";
import { ElMessage, ElMessageBox, type FormInstance } from "element-plus";
import request from "@/api/request";
import { action, dateText, errorMessage } from "./shared";
const props = defineProps<{ classId?: number }>();
const notices = ref<any[]>([]),
  rooms = ref<any[]>([]),
  current = ref<any>(),
  messages = ref<any[]>([]),
  selected = ref<number>();
const error = ref(""),
  sending = ref(false),
  busy = ref(false),
  text = ref(""),
  noticeForm = ref<FormInstance>(),
  roomForm = ref<FormInstance>();
const notice = ref({ title: "", content: "" }),
  room = ref({ title: "", stream_url: "" });
const required = (message: string) => [
  { required: true, whitespace: true, message, trigger: "blur" }
];
const noticeRules = {title: required("请输入通知标题"), content: required("请输入通知内容")};
const roomRules = {title: required("请输入课堂主题")};
let version = 0,
  polling: number | undefined,
  timer: ReturnType<typeof setTimeout> | undefined,
  alive = true;
async function load() {
  const id = props.classId,
    serial = version;
  error.value = "";
  if (!id) return;
  try {
    const [n, r] = await Promise.all([
      request.get(`/mobile/classes/${id}/notices`),
      request.get(`/mobile/classes/${id}/sessions`)
    ]);
    if (serial === version) {
      notices.value = n;
      rooms.value = r;
    }
  } catch (e) {
    if (serial === version) error.value = errorMessage(e);
  }
}
async function publishNotice() {
  if (!(await noticeForm.value?.validate().catch(() => false))) return;
  busy.value = true;
  await action(async () => {
    await request.post(
      `/mobile/teacher/classes/${props.classId}/notices`,
      notice.value
    );
    notice.value = { title: "", content: "" };
    ElMessage.success("通知已发布");
    await load();
  });
  busy.value = false;
}
async function createRoom() {
  if (!(await roomForm.value?.validate().catch(() => false))) return;
  busy.value = true;
  await action(async () => {
    const result = await request.post(
      `/mobile/teacher/classes/${props.classId}/sessions`,
      { title: room.value.title, stream_url: room.value.stream_url || null }
    );
    room.value = { title: "", stream_url: "" };
    await load();
    selected.value = result.id;
    ElMessage.success("课堂已开启");
  });
  busy.value = false;
}
async function poll() {
  const id = selected.value,
    serial = version;
  if (!id || !alive) return;
  if (polling === serial) return;
  polling = serial;
  clearTimeout(timer);
  try {
    const result = await request.get(`/mobile/classroom/${id}`, {
      after_id: messages.value.at(-1)?.id || 0
    });
    if (serial !== version || id !== selected.value) return;
    current.value = result;
    const known = new Set(messages.value.map(m => m.id));
    messages.value.push(
      ...result.messages.filter((m: any) => !known.has(m.id))
    );
    error.value = "";
  } catch (e) {
    if (serial === version) error.value = errorMessage(e);
  } finally {
    if (polling === serial) polling = undefined;
    if (
      alive &&
      serial === version &&
      id === selected.value &&
      current.value?.status !== "ENDED"
    )
      timer = setTimeout(poll, 3000);
  }
}
async function send() {
  if (!text.value.trim() || sending.value) return;
  sending.value = true;
  await action(async () => {
    await request.post(`/mobile/classroom/${selected.value}/messages`, {
      type: "CHAT",
      content: text.value.trim()
    });
    text.value = "";
    clearTimeout(timer);
    await poll();
  });
  sending.value = false;
}
async function end() {
  try {
    await ElMessageBox.confirm(
      "结束后学生将无法继续发送消息，课堂记录仍会保留。",
      "结束课堂",
      { type: "warning" }
    );
  } catch {
    return;
  }
  await action(async () => {
    await request.post(`/mobile/classroom/${selected.value}/end`);
    clearTimeout(timer);
    await poll();
    await load();
    ElMessage.success("课堂已结束");
  });
}
watch(
  () => props.classId,
  () => {
    version++;
    clearTimeout(timer);
    selected.value = undefined;
    current.value = undefined;
    messages.value = [];
    notices.value = [];
    rooms.value = [];
    notice.value = { title: "", content: "" };
    room.value = { title: "", stream_url: "" };
    load();
  },
  { immediate: true }
);
watch(selected, () => {
  version++;
  clearTimeout(timer);
  current.value = undefined;
  messages.value = [];
  text.value = "";
  poll();
});
onUnmounted(() => {
  alive = false;
  version++;
  clearTimeout(timer);
});
</script>
<template>
  <el-empty v-if="!classId" description="请选择班级" />
  <section v-else>
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
      show-icon
    />
    <div class="collaboration-grid">
      <el-card shadow="never"
        ><h3>发布班级通知</h3>
        <el-form
          ref="noticeForm"
          :model="notice"
        :rules="noticeRules"
          label-position="top"
          @submit.prevent="publishNotice"
          ><el-form-item label="通知标题" prop="title"
            ><el-input
              v-model.trim="notice.title"
              maxlength="128" /></el-form-item
          ><el-form-item label="通知内容" prop="content"
            ><el-input
              v-model.trim="notice.content"
              type="textarea"
              :rows="4"
              maxlength="10000" /></el-form-item
          ><el-button type="primary" native-type="submit" :loading="busy"
            >发布通知</el-button
          ></el-form
        >
        <h3>班级通知</h3>
        <el-empty v-if="!notices.length" description="暂无通知" />
        <article v-for="n in notices" :key="n.id" class="notice">
          <b>{{ n.title }}</b>
          <p>{{ n.content }}</p>
          <small>{{ dateText(n.created_at) }}</small>
        </article></el-card
      >
      <el-card shadow="never"
        ><h3>开启互动课堂</h3>
        <el-form
          ref="roomForm"
          :model="room"
        :rules="roomRules"
          label-position="top"
          @submit.prevent="createRoom"
          ><el-form-item label="课堂主题" prop="title"
            ><el-input
              v-model.trim="room.title"
              maxlength="128" /></el-form-item
          ><el-form-item label="课堂视频HTTPS地址（选填）"
            ><el-input
              v-model.trim="room.stream_url"
              placeholder="https://…" /></el-form-item
          ><el-button type="primary" native-type="submit" :loading="busy"
            >开启课堂</el-button
          ></el-form
        >
        <h3>课堂记录</h3>
        <el-select v-model="selected" placeholder="选择课堂" style="width: 100%"
          ><el-option
            v-for="r in rooms"
            :key="r.id"
            :value="r.id"
            :label="
              r.title + (r.status === 'LIVE' ? ' · 进行中' : ' · 已结束')
            "
        /></el-select>
        <template v-if="current"
          ><div class="room-toolbar">
            <b>{{ current.title }}</b
            ><el-tag>{{
              current.status === "LIVE" ? "进行中" : "已结束"
            }}</el-tag
            ><el-button
              v-if="current.status === 'LIVE'"
              type="danger"
              plain
              @click="end"
              >结束课堂</el-button
            >
          </div>
          <video
            v-if="current.stream_url"
            controls
            :src="current.stream_url"
            playsinline
          />
          <p v-else class="muted">
            此课堂未配置视频，可使用文字讨论与举手提问。
          </p>
          <div class="messages" aria-live="polite">
            <p v-if="!messages.length" class="muted">暂无消息</p>
            <article v-for="m in messages" :key="m.id">
              <b
                >{{ m.nickname
                }}<el-tag v-if="m.type === 'HAND'" type="warning" size="small"
                  >举手</el-tag
                ></b
              >
              <p>{{ m.content }}</p>
              <small>{{ dateText(m.created_at) }}</small>
            </article>
          </div>
          <form class="message-form" @submit.prevent="send">
            <el-input
              v-model="text"
              :disabled="current.status !== 'LIVE'"
              maxlength="1000"
              placeholder="回复课堂讨论"
              aria-label="课堂回复"
            /><el-button
              native-type="submit"
              type="primary"
              :loading="sending"
              :disabled="current.status !== 'LIVE' || !text.trim()"
              >发送</el-button
            >
          </form></template
        ></el-card
      >
    </div>
  </section>
</template>
<style scoped>
.collaboration-grid {
  display: grid;
  grid-template-columns: 1fr 1.25fr;
  gap: 20px;
  margin-top: 16px;
}
h3 {
  font-size: 18px;
  margin: 12px 0 20px;
}
.notice {
  border-bottom: 1px solid #eee;
  padding: 16px 0;
}
.notice p,
.messages p {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  line-height: 1.8;
  margin: 8px 0;
}
.notice small,
.messages small,
.muted {
  color: #747b84;
  font-size: 12px;
}
.room-toolbar {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  margin: 22px 0;
}
.messages {
  max-height: 450px;
  overflow: auto;
  background: #f7f8fa;
  border-radius: 8px;
  padding: 18px;
  margin: 20px 0;
}
.messages article {
  margin-bottom: 20px;
}
.messages b {
  display: flex;
  gap: 12px;
  align-items: center;
}
.message-form {
  display: flex;
  gap: 12px;
}
video {
  max-width: 100%;
  max-height: 300px;
  background: #151515;
}
@media (max-width: 1000px) {
  .collaboration-grid {
    grid-template-columns: 1fr;
  }
}
</style>
