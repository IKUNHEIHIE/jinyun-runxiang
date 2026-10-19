<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { api, post, notify, session } from "../api";
import PageHeader from "../components/PageHeader.vue";
import AsyncState from "../components/AsyncState.vue";
const router = useRouter(),
  classes = ref<any[]>([]),
  classId = ref<number>(),
  rooms = ref<any[]>([]),
  loading = ref(true),
  error = ref("");
const teacher = computed(() =>
  ["TEACHER", "ADMIN"].includes(session.profile?.role_code || ""),
);
const creating = ref(false),
  title = ref(""),
  streamUrl = ref(""),
  busy = ref(false);
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
    if (!classes.value.some((c) => c.id === classId.value)) classId.value = undefined;
    if (!classId.value && classes.value.length)
      classId.value = classes.value[0].id;
    const result = classId.value
      ? await api("/mobile/classes/" + classId.value + "/sessions")
      : [];
    if (current()) rooms.value = result;
  } catch (e) {
    if (current()) error.value = (e as Error).message;
  } finally {
    if (current()) loading.value = false;
  }
}
async function create() {
  if (busy.value) return;
  if (!classId.value) {
    notify("请先选择班级");
    return;
  }
  if (!title.value.trim()) { notify("请填写课堂主题"); return; }
  const token = session.token, id = classId.value;
  const current = () => alive && token === session.token && id === classId.value;
  busy.value = true;
  try {
    const result = await post(
      "/mobile/teacher/classes/" + classId.value + "/sessions",
      { title: title.value, stream_url: streamUrl.value || null },
    );
    if (!current()) return;
    creating.value = false;
    await router.push("/classroom/" + result.id);
  } catch (e) {
    if (current()) notify((e as Error).message);
  } finally {
    if (current()) busy.value = false;
  }
}
watch(() => [session.token, teacher.value], () => {
  ++version; classId.value = undefined; classes.value = []; rooms.value = [];
  title.value = ""; streamUrl.value = ""; creating.value = false; busy.value = false;
  void load();
}, { immediate: true });
</script>
<template>
  <div>
    <PageHeader title="在线课堂" subtitle="课堂讨论 · 举手互动答疑" />
    <div class="page-padding">
      <label
        >选择班级<select v-model="classId" :disabled="busy" @change="load">
          <option v-for="c in classes" :key="c.id" :value="c.id">
            {{ c.name }}
          </option>
        </select></label
      ><button
        v-if="teacher"
        class="primary-button start-classroom"
        :disabled="loading || busy || !classId"
        @click="creating = true"
      >
        开启课堂</button
      ><AsyncState
        :loading="loading"
        :error="error"
        :empty="!rooms.length"
        empty-text="暂时没有课堂，等待老师开启吧"
        @retry="load"
        ><div class="room-list">
          <RouterLink
            v-for="room in rooms"
            :key="room.id"
            :to="'/classroom/' + room.id"
            class="room-card corner-card"
            ><span>{{ room.status === "LIVE" ? "进行中" : "已结束" }}</span>
            <h2>{{ room.title }}</h2>
            <p>
              {{
                room.stream_url ? "课堂视频 · 互动讨论" : "互动讨论 · 举手提问"
              }}
            </p>
            <strong
              >{{
                room.status === "LIVE" ? "进入课堂" : "查看课堂记录"
              }}
              ›</strong
            ></RouterLink
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
          aria-labelledby="start-class-title"
        >
          <button
            class="sheet-close"
            aria-label="关闭开启课堂"
            @click="creating = false"
          >
            ×
          </button>
          <h2 id="start-class-title">开启在线课堂</h2>
          <form @submit.prevent="create">
            <label
              >课堂名称<input
                v-model.trim="title"
                required
                maxlength="128" /></label
            ><label
              >课堂视频地址（选填）<input
                v-model.trim="streamUrl"
                type="url"
                placeholder="https://…"
                maxlength="500"
            /></label>
            <p class="subtle">暂不配置视频时，师生仍可实时讨论和举手提问。</p>
            <button class="primary-button" :disabled="busy">开始课堂</button>
          </form>
        </section>
      </div></Teleport
    >
  </div>
</template>
<style scoped>
.start-classroom {
  width: 100%;
  margin-top: 20px;
}
.room-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 28px;
}
.room-card {
  padding: 24px 20px;
}
.room-card > span {
  font-size: 10px;
  color: var(--clay);
  border: 1px solid var(--gold);
  border-radius: 20px;
  padding: 4px 10px;
}
.room-card > h2 {
  font-size: 20px;
  margin: 20px 0 12px;
}
.room-card > p {
  font-size: 12px;
  color: var(--muted);
}
.room-card > strong {
  display: block;
  font-size: 12px;
  color: var(--clay);
  font-weight: 500;
  margin-top: 22px;
}
</style>
