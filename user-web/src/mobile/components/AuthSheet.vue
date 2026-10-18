<script setup lang="ts">
import { ref } from "vue";
import { api, session, notify, loadProfile } from "../api";
const registering = ref(false),
  busy = ref(false),
  error = ref("");
const username = ref(""),
  password = ref(""),
  nickname = ref("");
async function submit() {
  if (busy.value) return;
  busy.value = true;
  error.value = "";
  try {
    const result = await api(
      "/auth/" + (registering.value ? "register" : "login"),
      {
        method: "POST",
        body: JSON.stringify({
          username: username.value,
          password: password.value,
          nickname: nickname.value,
        }),
      },
    );
    session.profile = null;
    localStorage.removeItem("jinyun_user_info");
    session.token = result.token;
    localStorage.setItem("jinyun_user_token", result.token);
    await loadProfile();
    password.value = "";
    session.authVisible = false;
    window.dispatchEvent(new Event("jinyun-signed-in"));
    notify(registering.value ? "注册成功，欢迎来到津韵润乡" : "登录成功");
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    busy.value = false;
  }
}
</script>
<template>
  <Teleport to="body"
    ><div
      v-if="session.authVisible"
      class="sheet-overlay"
      @click.self="session.authVisible = false"
    >
      <section
        class="auth-sheet corner-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-title"
      >
        <button
          class="sheet-close"
          aria-label="关闭登录"
          @click="session.authVisible = false"
        >
          ×
        </button>
        <p class="eyebrow">INTANGIBLE HERITAGE</p>
        <h2 id="auth-title">{{ registering ? "入馆习艺" : "欢迎归来" }}</h2>
        <p class="subtle">登录后保存学习进度与创作作品</p>
        <form @submit.prevent="submit">
          <label
            >用户名<input
              v-model.trim="username"
              required
              minlength="3"
              maxlength="32"
              autocomplete="username"
              inputmode="email"
              autocapitalize="none"
              autocorrect="off"
              :spellcheck="false"
              placeholder="请输入用户名"
          /></label>
          <label v-if="registering"
            >昵称<input
              v-model.trim="nickname"
              required
              maxlength="32"
              autocomplete="nickname"
              placeholder="如何称呼你"
          /></label>
          <label
            >密码<input
              v-model="password"
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
