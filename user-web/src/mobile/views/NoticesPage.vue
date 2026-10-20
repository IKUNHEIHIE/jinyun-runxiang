<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import { api, post, notify, session } from "../api";
import PageHeader from "../components/PageHeader.vue";
import AsyncState from "../components/AsyncState.vue";
import SectionCard from "../components/SectionCard.vue";
import { formatDate } from "../dates";
const route = useRoute();
const classes = ref<any[]>([]),
  classId = ref<number>(Number(route.query.class_id) || undefined),
  notices = ref<any[]>([]),
  title = ref(""),
  content = ref(""),
  loading = ref(true),
  error = ref(""),
  busy = ref(false);
const teacher = computed(() =>
  ["TEACHER", "ADMIN"].includes(session.profile?.role_code || ""),
);
let version = 0, alive = true;
onUnmounted(() => { alive = false; ++version; });
async function load() {
  const request = ++version, token = session.token;
  const current = () => alive && request === version && token === session.token;
  loading.value = true;
  error.value = "";
  try {
    const rows = await api(
      teacher.value ? "/teacher/classes" : "/mobile/me/classes",
    );
    if (!current()) return;
    classes.value = rows;
    if (!classes.value.some((c) => c.id === classId.value))
      classId.value = undefined;
    if (!classId.value && classes.value.length)
      classId.value = classes.value[0].id;
    const result = classId.value
      ? await api("/mobile/classes/" + classId.value + "/notices")
      : [];
    if (current()) notices.value = result;
  } catch (e) {
    if (current()) error.value = (e as Error).message;
  } finally {
    if (current()) loading.value = false;
  }
}
async function publish() {
  if (!classId.value || busy.value) return;
  if (!title.value.trim() || !content.value.trim()) { notify("请填写通知标题和内容"); return; }
  const token = session.token, id = classId.value;
  const current = () => alive && token === session.token && id === classId.value;
  busy.value = true;
  try {
    await post("/mobile/teacher/classes/" + classId.value + "/notices", {
      title: title.value,
      content: content.value,
    });
    if (!current()) return;
    title.value = "";
    content.value = "";
    await load();
    if (current()) notify("通知已发布，班级学生可以查看");
  } catch (e) {
    if (current()) notify((e as Error).message);
  } finally {
    if (current()) busy.value = false;
  }
}
watch(() => [session.token, teacher.value, route.query.class_id], () => {
  ++version; classId.value = Number(route.query.class_id) || undefined; classes.value = []; notices.value = [];
  title.value = ""; content.value = ""; busy.value = false;
  void load();
}, { immediate: true });
</script>
<template>
  <div class="notices-page">
    <PageHeader title="班级通知" />
    <div class="notices-body">
      <SectionCard title="班级">
        <label class="notices-class"
          ><span>选择班级</span
          ><select v-model="classId" :disabled="busy" @change="load">
            <option v-for="c in classes" :key="c.id" :value="c.id">
              {{ c.name }}
            </option>
          </select></label
        >
      </SectionCard>
      <SectionCard v-if="teacher" title="发布通知">
        <form class="notices-form" @submit.prevent="publish">
          <label
            >通知标题<input
              v-model.trim="title"
              :disabled="busy"
              required
              maxlength="128" /></label
          ><label
            >通知内容<textarea
              v-model.trim="content"
              :disabled="busy"
              required
              maxlength="10000"
            /></label
          ><button class="notices-publish" :disabled="busy || !classId">
            {{ busy ? '正在发布…' : '发布通知' }}
          </button>
        </form>
      </SectionCard>
      <SectionCard title="通知">
        <AsyncState :loading="loading" :error="error" @retry="load"
          ><div class="notice-list">
            <article
              v-for="notice in notices"
              :key="notice.id"
              class="notice-item"
            >
              <div class="notice-head">
                <h3>{{ notice.title }}</h3>
                <small class="notice-time">{{
                  formatDate(notice.created_at)
                }}</small>
              </div>
              <p class="notice-content">{{ notice.content }}</p>
            </article>
          </div>
          <p v-if="!notices.length" class="notice-empty">暂无已发布通知</p></AsyncState
        >
      </SectionCard>
    </div>
  </div>
</template>
<style scoped>
.notices-page {
  min-height: 100dvh;
  padding-bottom: 12px;
  background: #f5ede4;
  color: #2d1810;
}
.notices-body {
  padding: 14px 16px 24px;
}
.notices-class {
  gap: 6px;
  margin: 0;
}
.notices-class > span {
  color: #8a7a70;
  font: 400 10px/1.4 var(--sans);
  letter-spacing: 1px;
}
.notices-class select {
  min-height: 42px;
  border-color: rgba(200, 169, 110, 0.45);
  border-radius: 10px;
  background: #fffdf8;
  color: #2d1810;
  font: 400 14px/1.4 var(--sans);
  letter-spacing: 0;
}
.notices-form {
  gap: 14px;
  margin: 0;
}
.notices-form label {
  gap: 6px;
  color: #8a7a70;
  font: 400 10px/1.4 var(--sans);
  letter-spacing: 1px;
}
.notices-form input,
.notices-form textarea {
  border-color: rgba(200, 169, 110, 0.45);
  border-radius: 10px;
  background: #fffdf8;
  color: #2d1810;
  font: 400 14px/1.6 var(--sans);
  letter-spacing: 0;
}
.notices-form textarea {
  min-height: 96px;
}
.notices-publish {
  display: grid;
  place-items: center;
  min-height: 42px;
  padding: 0 14px;
  border: 1px solid #8b1a1a;
  border-radius: 10px;
  background: #8b1a1a;
  color: #fdf6ec;
  font: 500 13px/1.4 var(--sans);
  letter-spacing: 1px;
}
.notice-list {
  display: flex;
  flex-direction: column;
}
.notice-item {
  padding: 14px 0;
  border-top: 1px solid rgba(200, 169, 110, 0.22);
}
.notice-item:first-child {
  padding-top: 0;
  border-top: 0;
}
.notice-item:last-child {
  padding-bottom: 0;
}
.notice-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.notice-head h3 {
  flex: 1;
  min-width: 0;
  color: #2d1810;
  font: 500 14px/1.5 var(--sans);
  overflow-wrap: anywhere;
}
.notice-time {
  flex-shrink: 0;
  color: #8a7a70;
  font: 400 10px/1.5 var(--sans);
  letter-spacing: 0.5px;
}
.notice-content {
  margin-top: 6px;
  color: #4a3228;
  font: 400 13px/1.9 var(--sans);
  white-space: pre-line;
  overflow-wrap: anywhere;
}
.notice-empty {
  padding: 18px 0;
  text-align: center;
  color: #8a7a70;
  font: 400 11px/1.6 var(--sans);
}
</style>
