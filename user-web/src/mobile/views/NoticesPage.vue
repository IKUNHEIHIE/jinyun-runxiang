<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { api, post, notify, session } from "../api";
import PageHeader from "../components/PageHeader.vue";
import AsyncState from "../components/AsyncState.vue";
import { formatDate } from "../dates";
const classes = ref<any[]>([]),
  classId = ref<number>(Number(useRoute().query.class_id) || undefined),
  notices = ref<any[]>([]),
  title = ref(""),
  content = ref(""),
  loading = ref(true),
  error = ref(""),
  busy = ref(false);
const teacher = computed(() =>
  ["TEACHER", "ADMIN"].includes(session.profile?.role_code || ""),
);
async function load() {
  loading.value = true;
  error.value = "";
  try {
    classes.value = await api(
      teacher.value ? "/teacher/classes" : "/mobile/me/classes",
    );
    if (!classes.value.some((c) => c.id === classId.value))
      classId.value = undefined;
    if (!classId.value && classes.value.length)
      classId.value = classes.value[0].id;
    notices.value = classId.value
      ? await api("/mobile/classes/" + classId.value + "/notices")
      : [];
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
}
async function publish() {
  if (!classId.value) return;
  busy.value = true;
  try {
    await post("/mobile/teacher/classes/" + classId.value + "/notices", {
      title: title.value,
      content: content.value,
    });
    title.value = "";
    content.value = "";
    await load();
    notify("通知已发布，班级学生可以查看");
  } catch (e) {
    notify((e as Error).message);
  } finally {
    busy.value = false;
  }
}
onMounted(load);
</script>
<template>
  <div>
    <PageHeader title="班级通知" />
    <div class="page-padding">
      <label
        >选择班级<select v-model="classId" @change="load">
          <option v-for="c in classes" :key="c.id" :value="c.id">
            {{ c.name }}
          </option>
        </select></label
      >
      <form v-if="teacher" class="notice-form" @submit.prevent="publish">
        <label
          >通知标题<input
            v-model.trim="title"
            required
            maxlength="128" /></label
        ><label
          >通知内容<textarea
            v-model.trim="content"
            required
            maxlength="10000"
          /></label
        ><button class="primary-button" :disabled="busy || !classId">
          发布通知
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
