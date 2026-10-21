<script setup lang="ts">
import { ref, watch, nextTick, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { api, session, notify } from "../api";
const router = useRouter();
const registering = ref(false),
  busy = ref(false),
  error = ref("");
const username = ref(""),
  password = ref(""),
  nickname = ref("");
const dialog = ref<HTMLElement>();
let attempt = 0;
let controller: AbortController | undefined;
let restoreFocus: HTMLElement | null = null;
let previousOverflow: string | undefined;
function close() {
  session.authVisible = false;
}
function releaseDialog() {
  if (previousOverflow !== undefined) {
    document.body.style.overflow = previousOverflow;
    previousOverflow = undefined;
    const target = restoreFocus;
    void nextTick(() => {
      if (!session.authVisible && target?.isConnected) target.focus({ preventScroll: true });
    });
    restoreFocus = null;
  }
}
function trapFocus(event: KeyboardEvent) {
  const controls = Array.from(dialog.value?.querySelectorAll<HTMLElement>(
    'button:not(:disabled), input:not(:disabled), [tabindex="0"]',
  ) || []).filter((element) => element.offsetParent !== null);
  if (!controls.length) return;
  const first = controls[0], last = controls[controls.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault(); last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault(); first.focus();
  }
}
watch(() => session.authVisible, async (visible) => {
  ++attempt;
  controller?.abort();
  busy.value = false;
  error.value = "";
  password.value = "";
  if (visible) {
    restoreFocus = document.activeElement as HTMLElement | null;
    previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const opened = attempt;
    await nextTick();
    if (session.authVisible && opened === attempt)
      dialog.value?.querySelector<HTMLInputElement>('input')?.focus({ preventScroll: true });
  } else {
    session.authRedirect = "";
    releaseDialog();
  }
}, { flush: "sync", immediate: true });
onUnmounted(() => {
  ++attempt;
  controller?.abort();
  releaseDialog();
});
async function submit() {
  if (busy.value || !session.authVisible) return;
  const version = ++attempt, token = session.token;
  const isCurrent = () => version === attempt && session.authVisible && token === session.token;
  const isRegistration = registering.value;
  controller = new AbortController();
  busy.value = true;
  error.value = "";
  try {
    const result = await api(
      "/auth/" + (isRegistration ? "register" : "login"),
      {
        method: "POST",
        signal: controller.signal,
        body: JSON.stringify({
          username: username.value,
          password: password.value,
          nickname: nickname.value,
        }),
      },
    );
    if (!isCurrent()) return;
    const destination = session.authRedirect;
    session.profile = result.user;
    localStorage.removeItem("jinyun_user_info");
    session.token = result.token;
    localStorage.setItem("jinyun_user_token", result.token);
    password.value = "";
    session.authVisible = false;
    window.dispatchEvent(new Event("jinyun-signed-in"));
    notify(isRegistration ? "注册成功，欢迎来到津韵润乡" : "登录成功");
    if (destination) await router.push(destination);
    else if (["TEACHER", "ADMIN"].includes(result.user?.role_code))
      await router.replace("/teacher");
  } catch (e) {
    if (isCurrent()) error.value = (e as Error).message;
  } finally {
    if (version === attempt) busy.value = false;
  }
}
</script>
<template>
  <Teleport to="body"
    ><div
      v-if="session.authVisible"
      class="sheet-overlay"
      @click.self="close"
    >
      <section
        class="auth-sheet corner-card"
        ref="dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-title"
        @keydown.esc.prevent.stop="close"
        @keydown.tab="trapFocus"
      >
        <button
          class="sheet-close"
          aria-label="关闭登录"
          @click="close"
        >
          ×
        </button>
        <p class="eyebrow">INTANGIBLE HERITAGE</p>
        <h2 id="auth-title">{{ registering ? "入馆习艺" : "欢迎归来" }}</h2>
        <p class="subtle">登录后保存学习进度与创作作品</p>
        <form :aria-busy="busy" @submit.prevent="submit">
          <label
            >用户名<input
              v-model.trim="username"
              :disabled="busy"
              required
              minlength="3"
              :maxlength="registering ? 32 : 64"
              autocomplete="username"
              inputmode="text"
              enterkeyhint="next"
              autocapitalize="none"
              autocorrect="off"
              :spellcheck="false"
              placeholder="请输入用户名"
          /></label>
          <label v-if="registering"
            >昵称<input
              v-model.trim="nickname"
              :disabled="busy"
              enterkeyhint="next"
              required
              maxlength="32"
              autocomplete="nickname"
              placeholder="如何称呼你"
          /></label>
          <label
            >密码<input
              v-model="password"
              :disabled="busy"
              enterkeyhint="go"
              required
              :minlength="registering ? 8 : 1"
              type="password"
              maxlength="128"
              :autocomplete="registering ? 'new-password' : 'current-password'"
              placeholder="请输入密码"
          /></label>
          <p v-if="error" class="form-error" role="alert">{{ error }}</p>
          <button class="primary-button" :disabled="busy">
            {{ busy ? "请稍候…" : registering ? "注册学员账号" : "登录" }}
          </button>
        </form>
        <button
          class="text-button"
          :disabled="busy"
          @click="
            registering = !registering;
            error = '';
          "
        >
          {{ registering ? "已有账号，立即登录" : "新学徒？注册账号" }}
        </button>
      </section>
    </div></Teleport
  >
</template>
