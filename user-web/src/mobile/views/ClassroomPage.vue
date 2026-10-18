<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api, post, session, notify } from "../api";
import PageHeader from "../components/PageHeader.vue";
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
  <div>
    <PageHeader :title="room?.title || '双师课堂'" /><video
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
    <div class="page-padding">
      <p v-if="error" class="form-error" role="alert">
        {{ error }} <button class="text-button" @click="load">重试连接</button>
      </p>
      <div class="section-heading">
        <h2>师生互动</h2>
        <span>{{ room?.status === "ENDED" ? "已结束" : "实时讨论" }}</span>
      </div>
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
        <p v-if="!messages.length" class="subtle">
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
        <div>
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
      <button
        v-if="isHost && room?.status === 'LIVE'"
        class="text-button end-classroom"
        @click="end"
      >
        结束课堂并保存记录</button
      ><button class="text-button end-classroom" @click="router.back()">
        返回课堂列表
      </button>
    </div>
  </div>
</template>
<style scoped>
.classroom-video {
  width: 100%;
  aspect-ratio: 16/10;
  background: #201a15;
  display: block;
}
.classroom-video-empty {
  min-height: 210px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 18px;
  background: linear-gradient(130deg, #3d2314, #6c2e11);
  color: var(--paper);
  padding: 24px;
  text-align: center;
}
.classroom-video-empty h2 {
  font-size: 25px;
}
.classroom-video-empty p {
  font-size: 11px;
  line-height: 1.9;
  color: var(--gold-light);
}
.class-messages {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-height: 200px;
}
.class-messages article {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}
.class-messages span,
.class-messages small {
  font-size: 10px;
  color: var(--muted);
}
.class-messages p {
  padding: 12px 16px;
  border: 1px solid var(--gold-light);
  border-radius: 0 12px 12px 12px;
  font-size: 12px;
  line-height: 1.8;
  max-width: 90%;
  background: var(--paper);
  white-space: pre-line;
}
.class-messages .mine {
  align-items: flex-end;
}
.class-messages .mine p {
  background: #eedbc5;
  border-radius: 12px 0 12px 12px;
}
.class-messages .hand p {
  border-color: var(--gold);
  color: var(--clay);
}
.class-message-form {
  margin-top: 30px;
}
.class-message-form > div {
  display: flex;
  gap: 12px;
}
.class-message-form > div > * {
  flex: 1;
}
.end-classroom {
  display: block;
  margin: 20px auto 0;
}
</style>
