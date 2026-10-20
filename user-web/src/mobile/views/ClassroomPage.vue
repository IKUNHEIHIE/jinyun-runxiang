<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api, post, session, notify } from "../api";
import PageHeader from "../components/PageHeader.vue";
import SectionCard from "../components/SectionCard.vue";
import CellGroup from "../components/CellGroup.vue";
import CellRow from "../components/CellRow.vue";
import { formatTime } from "../dates";
const route = useRoute(),
  router = useRouter(),
  room = ref<any>(),
  messages = ref<any[]>([]),
  text = ref(""),
  error = ref(""),
  sending = ref(false);
const isHost = computed(
  () =>
    room.value?.host_id === session.profile?.id ||
    session.profile?.role_code === "ADMIN",
);
let timer: ReturnType<typeof setTimeout>,
  alive = true,
  loadingId: string | undefined;
async function load() {
  const id = String(route.params.id);
  if (loadingId === id) return;
  loadingId = id;
  clearTimeout(timer);
  try {
    const after = messages.value[messages.value.length - 1]?.id || 0;
    const data = await api("/mobile/classroom/" + id + "?after_id=" + after);
    if (!alive || id !== String(route.params.id)) return;
    room.value = data;
    const known = new Set(messages.value.map((m) => m.id));
    messages.value.push(...data.messages.filter((m: any) => !known.has(m.id)));
    error.value = "";
  } catch (e) {
    if (alive) error.value = (e as Error).message;
  } finally {
    if (loadingId === id) loadingId = undefined;
  }
  if (alive && session.token && id === String(route.params.id) && room.value?.status !== "ENDED") timer = setTimeout(load, 3000);
}
async function send(type = "CHAT") {
  if (sending.value || (type === "CHAT" && !text.value.trim())) return;
  sending.value = true;
  try {
    await post("/mobile/classroom/" + route.params.id + "/messages", {
      type,
      content: type === "HAND" ? "我想提问" : text.value.trim(),
    });
    if (type === "CHAT") text.value = "";
    else notify("已举手，老师可以看到你的提问请求");
    await load();
  } catch (e) {
    notify((e as Error).message);
  } finally {
    sending.value = false;
  }
}
async function end() {
  try {
    await post("/mobile/classroom/" + route.params.id + "/end");
    await load();
    notify("课堂已结束，讨论记录已保存");
  } catch (e) {
    notify((e as Error).message);
  }
}
watch(
  () => route.params.id,
  () => {
    messages.value = [];
    room.value = undefined;
    load();
  },
  { immediate: true },
);
onUnmounted(() => {
  alive = false;
  clearTimeout(timer);
});
</script>
<template>
  <div class="classroom-page">
    <PageHeader :title="room?.title || '在线课堂'" />
    <div class="classroom-body">
      <div class="classroom-stage">
        <video
          v-if="room?.stream_url"
          class="classroom-video"
          :src="room.stream_url"
          controls
          playsinline
          @error="notify('课堂视频暂时无法播放，请联系授课老师')"
        />
        <div v-else class="classroom-video-empty">
          <h2>{{ room?.status === "ENDED" ? "课堂已结束" : "课堂讨论" }}</h2>
          <p>课堂视频待教师配置，讨论和举手可正常使用</p>
        </div>
      </div>
      <p v-if="error" class="form-error classroom-error" role="alert">
        {{ error }} <button class="text-button" @click="load">重试连接</button>
      </p>
      <SectionCard
        title="师生互动"
        :meta="room?.status === 'ENDED' ? '已结束' : '实时讨论'"
      >
        <div class="class-messages" aria-live="polite">
          <article
            v-for="message in messages"
            :key="message.id"
            :class="{
              mine: message.user_id === session.profile?.id,
              hand: message.type === 'HAND',
            }"
          >
            <span>{{ message.nickname }}</span>
            <p>{{ message.type === "HAND" ? "✋ " : "" }}{{ message.content }}</p>
            <small>{{ formatTime(message.created_at) }}</small>
          </article>
          <p v-if="!messages.length" class="subtle class-messages-empty">
            课堂已经就绪，向老师和同学问声好吧
          </p>
        </div>
        <form
          v-if="room?.status === 'LIVE'"
          class="class-message-form"
          @submit.prevent="send()"
        >
          <label
            >课堂发言<textarea
              v-model.trim="text"
              required
              maxlength="1000"
              placeholder="分享你的观察，或提出问题…"
            />
          </label>
          <div class="class-message-actions">
            <button
              type="button"
              class="outline-button"
              :disabled="sending"
              @click="send('HAND')"
            >
              举手提问</button
            ><button class="primary-button" :disabled="sending">发送</button>
          </div>
        </form>
      </SectionCard>
      <CellGroup label="课堂操作">
        <CellRow
          v-if="isHost && room?.status === 'LIVE'"
          label="结束课堂并保存记录"
          danger
          @click="end"
        />
        <CellRow label="返回课堂列表" @click="router.back()" />
      </CellGroup>
    </div>
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
.classroom-stage {
  margin-bottom: 14px;
  border-radius: 14px;
  overflow: hidden;
  background: #201a15;
  box-shadow: 0 8px 24px rgba(70, 42, 26, 0.14);
}
.classroom-video {
  width: 100%;
  aspect-ratio: 16/10;
  background: #201a15;
  display: block;
}
.classroom-video-empty {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 12px;
  padding: 24px;
  background: linear-gradient(130deg, #3d2314, #6c2e11);
  color: #f6ead9;
  text-align: center;
}
.classroom-video-empty h2 {
  font: 500 16px/1.4 var(--serif);
  letter-spacing: 1.5px;
}
.classroom-video-empty p {
  font: 400 11px/1.8 var(--sans);
  letter-spacing: 0.5px;
  color: #e8d9a8;
}
.classroom-error {
  margin: 0 2px 12px;
  color: #8b1a1a;
  font-size: 12px;
  line-height: 1.8;
}
.classroom-error .text-button {
  padding: 4px 6px;
  color: #8b1a1a;
  font-size: 11px;
}
.class-messages {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 180px;
}
.class-messages article {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}
.class-messages span,
.class-messages small {
  font: 400 10px/1.5 var(--sans);
  color: #8a7a70;
}
.class-messages p {
  max-width: 88%;
  padding: 10px 12px;
  border: 1px solid rgba(200, 169, 110, 0.4);
  border-radius: 2px 12px 12px 12px;
  background: #fffdf8;
  color: #2d1810;
  font: 400 13px/1.75 var(--sans);
  white-space: pre-line;
  overflow-wrap: anywhere;
}
.class-messages .mine {
  align-items: flex-end;
}
.class-messages .mine p {
  background: rgba(139, 26, 26, 0.06);
  border-color: rgba(139, 26, 26, 0.18);
  border-radius: 12px 2px 12px 12px;
}
.class-messages .hand p {
  border-color: rgba(200, 169, 110, 0.7);
  color: #8a6125;
}
.class-messages-empty {
  padding: 18px 0;
  text-align: center;
  font-size: 11px;
  line-height: 1.8;
  color: #8a7a70;
}
.class-message-form {
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid rgba(200, 169, 110, 0.28);
  gap: 12px;
}
.class-message-form label {
  font: 500 12px/1.4 var(--sans);
  color: #5a3e36;
  gap: 8px;
}
.class-message-form textarea {
  min-height: 84px;
  border-color: rgba(200, 169, 110, 0.42);
  border-radius: 10px;
  background: #fffdf8;
  color: #2d1810;
}
.class-message-actions {
  display: flex;
  gap: 10px;
}
.class-message-actions > * {
  flex: 1;
}
.class-message-actions .primary-button {
  min-height: 42px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: #8b1a1a;
  color: #f6ead9;
  font-size: 13px;
}
.class-message-actions .outline-button {
  min-height: 42px;
  border: 1px solid rgba(200, 169, 110, 0.55);
  border-radius: 10px;
  background: #fffdf8;
  color: #8a6125;
  font-size: 13px;
}
</style>
