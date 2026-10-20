<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { api, post, notify, session } from "../api";
import PageHeader from "../components/PageHeader.vue";
import AsyncState from "../components/AsyncState.vue";
import SectionCard from "../components/SectionCard.vue";
import CellGroup from "../components/CellGroup.vue";
import CellRow from "../components/CellRow.vue";
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
  <div class="classroom-page">
    <PageHeader title="在线课堂" subtitle="课堂讨论 · 举手互动答疑" />
    <div class="classroom-body">
      <SectionCard title="班级">
        <label class="classroom-class"
          ><span>选择班级</span
          ><select v-model="classId" :disabled="busy" @change="load">
            <option v-for="c in classes" :key="c.id" :value="c.id">
              {{ c.name }}
            </option>
          </select></label
        >
      </SectionCard>
      <CellGroup v-if="teacher" label="课堂操作">
        <CellRow
          label="开启课堂"
          :disabled="loading || busy || !classId"
          @click="creating = true"
        />
      </CellGroup>
      <SectionCard title="课堂房间">
        <AsyncState
          :loading="loading"
          :error="error"
          :empty="!rooms.length"
          empty-text="暂时没有课堂，等待老师开启吧"
          @retry="load"
          ><div class="classroom-rooms">
            <RouterLink
              v-for="room in rooms"
              :key="room.id"
              :to="'/classroom/' + room.id"
              class="classroom-room"
            >
              <div class="classroom-room-head">
                <span
                  class="classroom-state"
                  :class="{ live: room.status === 'LIVE' }"
                  >{{
                    room.status === "LIVE" ? "进行中" : "已结束"
                  }}</span
                >
                <h3>{{ room.title }}</h3>
              </div>
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
              >
            </RouterLink>
          </div></AsyncState
        >
      </SectionCard>
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
.classroom-page {
  min-height: 100dvh;
  padding-bottom: 12px;
  background: #f5ede4;
  color: #2d1810;
}
.classroom-body {
  padding: 14px 16px 24px;
}
.classroom-class {
  gap: 6px;
  margin: 0;
}
.classroom-class > span {
  color: #8a7a70;
  font: 400 10px/1.4 var(--sans);
  letter-spacing: 1px;
}
.classroom-class select {
  min-height: 42px;
  border-color: rgba(200, 169, 110, 0.45);
  border-radius: 10px;
  background: #fffdf8;
  color: #2d1810;
  font: 400 14px/1.4 var(--sans);
  letter-spacing: 0;
}
.classroom-rooms {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.classroom-room {
  display: block;
  padding: 14px;
  border: 1px solid rgba(200, 169, 110, 0.28);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.55);
}
.classroom-room:active {
  background: rgba(200, 169, 110, 0.12);
}
.classroom-room-head {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.classroom-state {
  flex-shrink: 0;
  padding: 2px 8px;
  border: 1px solid rgba(200, 169, 110, 0.55);
  border-radius: 999px;
  color: #8a6125;
  font: 400 10px/1.5 var(--sans);
  letter-spacing: 0.5px;
}
.classroom-state.live {
  border-color: rgba(139, 26, 26, 0.35);
  background: #fff0f0;
  color: #8b1a1a;
}
.classroom-room h3 {
  display: -webkit-box;
  min-width: 0;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  color: #2d1810;
  font: 500 14px/1.5 var(--sans);
}
.classroom-room p {
  margin-top: 6px;
  color: #8a7a70;
  font: 400 11px/1.6 var(--sans);
}
.classroom-room strong {
  display: block;
  margin-top: 10px;
  color: #8b1a1a;
  font: 500 12px/1.5 var(--serif);
  letter-spacing: 0.5px;
}
</style>
