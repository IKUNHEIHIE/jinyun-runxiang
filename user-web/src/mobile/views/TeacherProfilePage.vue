<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  api,
  loadProfile,
  logout,
  mediaUrl,
  notify,
  put,
  session,
} from "../api";

const router = useRouter();
const route = useRoute();
const stats = ref<Record<string, any>>({});
const loading = ref(true),
  error = ref("");
const signingOut = ref(false);
const editing = ref(false),
  saving = ref(false);
const form = ref({ nickname: "", bio: "", school_name: "", district: "" });
const avatarInput = ref<HTMLInputElement | null>(null),
  avatarPreview = ref(""),
  avatarUploading = ref(false);
let avatarObjectUrl = "",
  mounted = true,
  loadVersion = 0,
  avatarVersion = 0,
  saveVersion = 0;

const AVATAR_TYPES = ["image/png", "image/jpeg", "image/webp"],
  AVATAR_MAX_BYTES = 5 * 1024 * 1024;

const isAdmin = computed(() => session.profile?.role_code === "ADMIN");
const roleText = computed(() => (isAdmin.value ? "管理员" : "教师"));
const nickname = computed(() => session.profile?.nickname || "教学工坊");
const initial = computed(() => nickname.value.slice(0, 1));
const avatarSource = computed(() =>
  avatarPreview.value
    ? avatarPreview.value
    : session.profile?.avatar_url
      ? mediaUrl(session.profile.avatar_url)
      : "",
);
const achievements = computed(() => stats.value.achievements || []);
const completedAchievements = computed(
  () => achievements.value.filter((item: any) => item.completed).length,
);
const metricRows = computed(() => [
  { label: "任教班级", value: stats.value.class_count, hint: "个班级" },
  { label: "在册学生", value: stats.value.student_count, hint: "名学生" },
  {
    label: "班级作业",
    value: stats.value.assignment_count,
    hint: stats.value.review_pending ? "待批改 " + stats.value.review_pending : "已全部批改",
  },
  { label: "备课教案", value: stats.value.lesson_plan_count, hint: "份方案" },
]);
const entries = [
  { label: "教学工坊", hint: "发布与批改", path: "/teacher/assignments" },
  { label: "智能备课", hint: "教案与课件", path: "/teacher/lesson-plan" },
  { label: "班级对抗赛", hint: "两班擂台", path: "/teacher/contests" },
  { label: "在线课堂", hint: "文字直播", path: "/teacher/classroom" },
  { label: "学生端预览", hint: "核对布置内容", path: "/courses" },
];

function clearAvatarPreview() {
  if (avatarObjectUrl) URL.revokeObjectURL(avatarObjectUrl);
  avatarObjectUrl = "";
  avatarPreview.value = "";
}
function chooseAvatar() {
  if (avatarUploading.value || saving.value) return;
  avatarInput.value?.click();
}
async function uploadAvatar(event: Event) {
  const input = event.target as HTMLInputElement,
    file = input.files?.[0];
  input.value = "";
  if (!file || avatarUploading.value) return;
  if (!AVATAR_TYPES.includes(file.type)) {
    notify("头像仅支持 PNG、JPEG 或 WebP 格式");
    return;
  }
  if (file.size > AVATAR_MAX_BYTES) {
    notify("头像图片不能超过 5MB");
    return;
  }
  const token = session.token,
    serial = ++avatarVersion;
  clearAvatarPreview();
  avatarObjectUrl = URL.createObjectURL(file);
  avatarPreview.value = avatarObjectUrl;
  avatarUploading.value = true;
  try {
    const body = new FormData();
    body.append(
      "file",
      file,
      file.name || "avatar." + (file.type.split("/")[1] || "png"),
    );
    const uploaded = await api<{ file_url: string }>("/ai/assets/upload", {
      method: "POST",
      body,
    });
    if (!uploaded?.file_url) throw new Error("头像上传失败");
    const saved = await save({ ...form.value, avatar_url: uploaded.file_url });
    if (!saved) {
      clearAvatarPreview();
      return;
    }
    if (mounted && serial === avatarVersion && token === session.token)
      notify("头像已更新");
  } catch (e) {
    if (mounted && serial === avatarVersion) {
      notify((e as Error).message);
      clearAvatarPreview();
    }
  } finally {
    if (mounted && serial === avatarVersion) avatarUploading.value = false;
  }
}
async function save(override?: Record<string, string>) {
  if (saving.value || !session.profile) return false;
  const payload = {
    nickname: "",
    grade: session.profile.grade || "",
    bio: "",
    school_name: "",
    district: "",
    avatar_url: "",
    ...(override || form.value),
  };
  if (!payload.nickname.trim()) {
    notify("请先填写昵称");
    return false;
  }
  const token = session.token,
    serial = ++saveVersion;
  saving.value = true;
  try {
    await put("/mobile/me/profile", payload);
    await loadProfile();
    if (mounted && serial === saveVersion && token === session.token) {
      clearAvatarPreview();
      editing.value = false;
      syncForm();
    }
  } catch (e) {
    if (mounted && serial === saveVersion) notify((e as Error).message);
  } finally {
    if (mounted && serial === saveVersion) saving.value = false;
  }
  return true;
}
function syncForm() {
  form.value = {
    nickname: session.profile?.nickname || "",
    bio: session.profile?.bio || "",
    school_name: session.profile?.school_name || "",
    district: session.profile?.district || "",
  };
}
function edit() {
  if (avatarUploading.value) return;
  syncForm();
  editing.value = true;
}
async function signOut() {
  if (signingOut.value) return;
  signingOut.value = true;
  try {
    await logout();
    await router.replace("/profile");
  } catch (e) {
    notify((e as Error).message);
  } finally {
    signingOut.value = false;
  }
}
async function load() {
  const token = session.token,
    serial = ++loadVersion;
  error.value = "";
  loading.value = true;
  try {
    const overview = await api<Record<string, any>>("/mobile/teacher/overview");
    if (!mounted || serial !== loadVersion || token !== session.token) return;
    stats.value = overview;
  } catch (e) {
    if (mounted && serial === loadVersion) error.value = (e as Error).message;
  } finally {
    if (mounted && serial === loadVersion) loading.value = false;
  }
}
onMounted(() => {
  syncForm();
  if (route.query.edit) editing.value = true;
  void load();
});
// 冷启动时 /auth/me 可能晚于本页挂载返回，资料到手后补一次表单。
watch(
  () => session.profile,
  () => {
    if (!editing.value && !saving.value && !avatarUploading.value) syncForm();
  },
);
onUnmounted(() => {
  mounted = false;
  loadVersion++;
  avatarVersion++;
  saveVersion++;
  clearAvatarPreview();
});
</script>
<template>
  <div class="teacher-account-page" data-page-ready>
    <header class="account-hero">
      <button
        class="account-avatar"
        :disabled="avatarUploading"
        aria-label="更换头像"
        @click="chooseAvatar"
      >
        <span>
          <img v-if="avatarSource" :src="avatarSource" alt="我的头像" />
          <b v-else>{{ initial }}</b>
        </span>
        <i>{{ avatarUploading ? "上传中" : "换头像" }}</i>
      </button>
      <input
        ref="avatarInput"
        class="visually-hidden"
        type="file"
        accept="image/png,image/jpeg,image/webp"
        @change="uploadAvatar"
      />
      <h1>{{ nickname }}</h1>
      <p>
        {{ roleText }}<template v-if="session.profile?.school_name">
          · {{ session.profile.school_name }}</template
        ><template v-if="session.profile?.district">
          · {{ session.profile.district }}</template
        >
      </p>
      <p v-if="session.profile?.bio" class="account-bio">
        {{ session.profile.bio }}
      </p>
      <button class="edit-profile" @click="edit">编辑资料</button>
    </header>
    <div class="account-body">
      <p v-if="error" class="account-error" role="alert">
        {{ error }} <button @click="load">重试</button>
      </p>
      <section class="account-panel">
        <h2>教学数据</h2>
        <div class="metric-grid">
          <RouterLink v-for="row in metricRows" :key="row.label" to="/teacher/analytics">
            <strong>{{ loading ? "—" : (row.value ?? "—") }}</strong>
            <span>{{ row.label }}</span>
            <small>{{ row.hint }}</small>
          </RouterLink>
        </div>
      </section>
      <section class="account-panel">
        <h2>教学成就<span>{{ achievements.length ? completedAchievements + " / " + achievements.length : "" }}</span></h2>
        <ul class="achievement-list">
          <li v-for="badge in achievements" :key="badge.code" :class="{ idle: !badge.completed }">
            <span>{{ badge.completed ? "✓" : "○" }}</span>
            <div>
              <strong>{{ badge.name }}</strong>
              <p>{{ badge.description }}</p>
            </div>
            <small>{{ badge.current }} / {{ badge.target }}</small>
          </li>
        </ul>
        <p v-if="!achievements.length" class="panel-empty">
          {{ loading ? "教学数据加载中…" : "教学成就暂未加载" }}
        </p>
      </section>
      <section class="account-panel">
        <h2>常用入口</h2>
        <RouterLink v-for="entry in entries" :key="entry.path" :to="entry.path" class="entry-row">
          <span>{{ entry.label }}</span>
          <small>{{ entry.hint }}</small>
          <b>›</b>
        </RouterLink>
      </section>
      <button class="sign-out" :disabled="signingOut" @click="signOut">
        {{ signingOut ? "退出中…" : "退出登录" }}
      </button>
      <p class="sign-out-note">
        换学生账号登录，就能在学生端核对你布置的作业长什么样。
      </p>
    </div>
    <div v-if="editing" class="sheet-overlay" @click.self="editing = false">
      <section
        class="auth-sheet corner-card account-sheet"
        role="dialog"
        aria-modal="true"
        aria-labelledby="account-edit-title"
      >
        <button class="sheet-close" aria-label="关闭编辑资料" @click="editing = false">×</button>
        <h2 id="account-edit-title">编辑资料</h2>
        <label
          >昵称<input v-model="form.nickname" maxlength="64" required
        /></label>
        <label
          >任教学校<input v-model="form.school_name" maxlength="128"
        /></label>
        <label
          >所在区县<input v-model="form.district" maxlength="64"
        /></label>
        <label
          >个人简介<textarea v-model="form.bio" maxlength="255" rows="3"></textarea
        ></label>
        <p class="sheet-hint">
          年级等学生档案字段请进学生端「我的」修改。
        </p>
        <button
          class="primary-button"
          :disabled="saving || avatarUploading"
          @click="save()"
        >
          {{ saving ? "保存中…" : "保存资料" }}
        </button>
      </section>
    </div>
  </div>
</template>
<style scoped>
.teacher-account-page {
  --ta-ink: #2c1810;
  --ta-gold: #b8956a;
  --ta-red: #a84a3b;
  --ta-muted: #8b7355;
  min-height: 100%;
  background: #e5d6d6;
  color: var(--ta-ink);
  font-family: var(--serif);
  padding-bottom: calc(96px + var(--safe-bottom));
}
.account-hero {
  padding: 26px 20px 22px;
  text-align: center;
  background: radial-gradient(
      120% 90% at 50% 0%,
      rgba(184, 149, 106, 0.28),
      rgba(229, 214, 214, 0)
    ),
    linear-gradient(180deg, #f0e4d8, #e5d6d6);
}
.account-avatar {
  position: relative;
  display: grid;
  place-items: center;
  width: 92px;
  height: 92px;
  margin: 0 auto;
  padding: 0;
  border: 3px solid rgba(255, 252, 246, 0.9);
  border-radius: 50%;
  background: transparent;
  box-shadow: 0 10px 24px rgba(44, 24, 16, 0.18);
}
.account-avatar span {
  display: grid;
  place-items: center;
  width: 82px;
  height: 82px;
  border-radius: 50%;
  overflow: hidden;
  background: #ede4da;
  color: var(--ta-red);
}
.account-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.account-avatar b {
  font: 600 32px/1 var(--serif);
}
.account-avatar i {
  position: absolute;
  right: -4px;
  bottom: 2px;
  padding: 3px 8px;
  border-radius: 999px;
  background: var(--ta-red);
  color: #fff9f2;
  font: 500 10px/1.2 var(--sans);
  font-style: normal;
}
.account-avatar:disabled {
  opacity: 0.7;
}
.account-hero h1 {
  margin: 14px 0 4px;
  font: 600 22px/1.3 var(--serif);
  letter-spacing: 0.04em;
}
.account-hero p {
  margin: 0;
  color: var(--ta-muted);
  font: 400 12px/1.6 var(--sans);
  letter-spacing: 0.08em;
}
.account-bio {
  margin: 6px auto 0 !important;
  max-width: 22em;
  color: #5b4436 !important;
}
.edit-profile {
  margin-top: 14px;
  padding: 8px 20px;
  border: 1px solid rgba(168, 74, 59, 0.35);
  border-radius: 999px;
  background: rgba(255, 250, 242, 0.9);
  color: #6c2e11;
  font: 500 12px/1 var(--sans);
  letter-spacing: 0.1em;
}
.account-body {
  margin: -10px 16px 0;
  display: grid;
  gap: 12px;
}
.account-panel {
  padding: 16px;
  border: 1px solid rgba(184, 149, 106, 0.4);
  border-radius: 16px;
  background: rgba(252, 247, 240, 0.94);
  box-shadow: 0 8px 20px rgba(44, 24, 16, 0.08);
}
.account-panel h2 {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin: 0 0 12px;
  font: 600 15px/1 var(--serif);
  letter-spacing: 0.12em;
}
.account-panel h2 span {
  color: var(--ta-gold);
  font: 500 11px/1 var(--sans);
}
.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.metric-grid a {
  padding: 12px;
  border: 1px dashed rgba(184, 149, 106, 0.55);
  border-radius: 12px;
  background: rgba(255, 252, 246, 0.7);
}
.metric-grid strong {
  display: block;
  font: 600 22px/1.1 var(--serif);
  color: var(--ta-red);
}
.metric-grid span {
  display: block;
  margin-top: 4px;
  font: 600 12px/1 var(--sans);
  letter-spacing: 0.08em;
}
.metric-grid small {
  color: var(--ta-muted);
  font: 400 10px/1.4 var(--sans);
}
.achievement-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 10px;
}
.achievement-list li {
  display: flex;
  align-items: center;
  gap: 10px;
}
.achievement-list li > span {
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(107, 142, 107, 0.16);
  color: #4f7050;
  font: 600 12px/1 var(--sans);
}
.achievement-list div {
  flex: 1;
  min-width: 0;
}
.achievement-list strong {
  font: 600 13px/1.3 var(--serif);
}
.achievement-list p {
  margin: 2px 0 0;
  color: var(--ta-muted);
  font: 400 11px/1.4 var(--sans);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.achievement-list small {
  color: var(--ta-gold);
  font: 600 11px/1 var(--sans);
}
.achievement-list li.idle > span {
  background: rgba(139, 115, 85, 0.14);
  color: var(--ta-muted);
}
.entry-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 2px;
  border-top: 1px solid rgba(184, 149, 106, 0.28);
  font: 500 13px/1 var(--sans);
}
.entry-row:first-of-type {
  border-top: 0;
  padding-top: 0;
}
.entry-row span {
  flex: 1;
}
.entry-row small {
  color: var(--ta-muted);
  font: 400 11px/1 var(--sans);
}
.entry-row b {
  color: var(--ta-gold);
  font-size: 16px;
}
.sign-out {
  padding: 13px;
  border: 1px solid rgba(168, 74, 59, 0.5);
  border-radius: 999px;
  background: rgba(168, 74, 59, 0.08);
  color: var(--ta-red);
  font: 600 13px/1 var(--sans);
  letter-spacing: 0.12em;
}
.sign-out:disabled {
  opacity: 0.6;
}
.sign-out-note {
  margin: -2px 0 0;
  color: var(--ta-muted);
  font: 400 11px/1.6 var(--sans);
  text-align: center;
}
.account-error {
  margin: 0;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(168, 74, 59, 0.1);
  color: #7d2f22;
  font: 500 12px/1.5 var(--sans);
}
.account-error button {
  border: 0;
  background: none;
  color: #6c2e11;
  text-decoration: underline;
  font: inherit;
}
.panel-empty {
  margin: 0;
  color: var(--ta-muted);
  font: 400 12px/1.6 var(--sans);
}
.account-sheet {
  display: grid;
  gap: 12px;
}
.account-sheet label {
  display: grid;
  gap: 6px;
  font: 600 12px/1 var(--sans);
  color: #5b4436;
}
.account-sheet input,
.account-sheet textarea {
  padding: 10px 12px;
  border: 1px solid rgba(184, 149, 106, 0.5);
  border-radius: 10px;
  background: #fffaf3;
  color: var(--ta-ink);
  font: 400 14px/1.5 var(--sans);
}
.sheet-hint {
  margin: 0;
  color: var(--ta-muted);
  font: 400 11px/1.5 var(--sans);
}
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  overflow: hidden;
  clip-path: inset(50%);
}
</style>
