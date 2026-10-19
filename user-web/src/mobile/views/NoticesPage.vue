<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import { api, post, notify, session } from "../api";
import PageHeader from "../components/PageHeader.vue";
import AsyncState from "../components/AsyncState.vue";
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
  <div>
    <PageHeader title="班级通知" />
    <div class="page-padding">
      <label
        >选择班级<select v-model="classId" :disabled="busy" @change="load">
          <option v-for="c in classes" :key="c.id" :value="c.id">
            {{ c.name }}
          </option>
        </select></label
      >
      <form v-if="teacher" class="notice-form" @submit.prevent="publish">
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
        ><button class="primary-button" :disabled="busy || !classId">
          {{ busy ? '正在发布…' : '发布通知' }}
        </button>
      </form>
      <AsyncState :loading="loading" :error="error" @retry="load"
        ><article
          v-for="notice in notices"
          :key="notice.id"
          class="notice-card corner-card"
        >
          <h2>{{ notice.title }}</h2>
          <p>{{ notice.content }}</p>
          <small>{{ formatDate(notice.created_at) }}</small>
        </article>
        <p v-if="!notices.length" class="subtle">暂无已发布通知</p></AsyncState
      >
    </div>
  </div>
</template>
<style scoped>
.notice-form {
  margin: 26px 0 36px;
}
.notice-card {
  padding: 22px 18px;
  margin-bottom: 20px;
}
.notice-card p {
  font-size: 13px;
  line-height: 2;
  white-space: pre-line;
  margin: 16px 0;
}
.notice-card small {
  font-size: 10px;
  color: var(--muted);
}
</style>
