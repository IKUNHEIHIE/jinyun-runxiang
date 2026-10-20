<script setup lang="ts">
import { ref, watch, onUnmounted, onMounted, onBeforeUnmount, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  api,
  session,
  mediaUrl,
  requireSession,
  notify,
  logout,
  put,
  loadProfile,
} from "../api";
import { designIcon, designImage } from "../design";
import { formatDate } from "../dates";
import AsyncState from "../components/AsyncState.vue";
import SectionCard from "../components/SectionCard.vue";
import CellGroup from "../components/CellGroup.vue";
import CellRow from "../components/CellRow.vue";
import SkeletonImage from "../components/SkeletonImage.vue";
const profileRoute = useRoute(),
  profileRouter = useRouter();
const badgeDesigns: Record<
  string,
  { image: string; frame: string; border: string }
> = {
  BADGE_COURSE_SHADOW_PUPPET: {
    image: "5:00945",
    frame: "5:00938",
    border: "2px rgba(200,169,110,.5)",
  },
  BADGE_COURSE_BRONZE: {
    image: "5:00979",
    frame: "5:00975",
    border: "2px rgba(200,169,110,.4)",
  },
  BADGE_COURSE_PAPER_CUTTING: {
    image: "5:00965",
    frame: "5:00958",
    border: "2.5px #c8a96e",
  },
  BADGE_COURSE_EMBROIDERY: {
    image: "5:00921",
    frame: "5:00917",
    border: "2px rgba(200,169,110,.4)",
  },
  BADGE_COURSE_CERAMICS: {
    image: "5:00934",
    frame: "5:00930",
    border: "2px rgba(200,169,110,.4)",
  },
};
const summary = ref<any>({}),
  learning = ref<any[]>([]),
  collections = ref<any[]>([]),
  badges = ref<any[]>([]),
  loading = ref(false),
  loaded = ref(false),
  error = ref("");
const editing = ref(false),
  form = ref({
    nickname: "",
    grade: "",
    bio: "",
    school_name: "",
    district: "",
    avatar_url: "",
  }),
  saving = ref(false),
  signingOut = ref(false);
const AVATAR_TYPES = ["image/png", "image/jpeg", "image/webp"],
  AVATAR_MAX_BYTES = 5 * 1024 * 1024;
const avatarInput = ref<HTMLInputElement | null>(null),
  avatarUploading = ref(false),
  avatarPreview = ref("");
let avatarObjectUrl = "";
const avatarInitial = computed(
  () =>
    (form.value.nickname || session.profile?.nickname || "学").slice(0, 1),
);
const avatarAlt = computed(
  () => (form.value.nickname || session.profile?.nickname || "用户") + "的头像",
);
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
  if (!file || avatarUploading.value || saving.value) return;
  if (!AVATAR_TYPES.includes(file.type)) {
    notify("头像仅支持 PNG、JPEG 或 WebP 格式");
    return;
  }
  if (file.size > AVATAR_MAX_BYTES) {
    notify("头像图片不能超过 5MB");
    return;
  }
  const version = editVersion;
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
    const result = await api<{ file_url: string }>("/ai/assets/upload", {
      method: "POST",
      body,
    });
    if (version !== editVersion || !editing.value) return;
    if (result?.file_url) form.value.avatar_url = result.file_url;
  } catch (e) {
    if (version === editVersion && editing.value) {
      notify((e as Error).message);
      clearAvatarPreview();
    }
  } finally {
    if (version === editVersion) avatarUploading.value = false;
  }
}
const activeBadge = ref<any>();
const todayLearning = computed(() => {
  const day = formatDate(new Date().toISOString(), false);
  return learning.value.filter(
    (item) => formatDate(item.last_learned_at, false) === day,
  );
});
const unlockedBadges = computed(
  () => badges.value.filter((badge) => badge.unlocked).length,
);
const schoolDate = () => formatDate(new Date().toISOString(), false);
const learningPercent = (item: any) =>
  item.completed
    ? 100
    : Math.min(
        100,
        Math.round(
          (item.position_seconds / Math.max(1, item.duration_seconds)) * 100,
        ),
      );
const learningTime = (seconds: number) =>
  seconds < 60
    ? Math.max(0, Math.floor(seconds)) + "秒"
    : Math.floor(seconds / 60) + "分钟";
let loadVersion = 0,
  saveVersion = 0,
  editVersion = 0;
let pendingToken: string | undefined, pendingUserId: number | undefined;
let mounted = true;
function profileCount(field: string) {
  if (!session.token) return 0;
  return (loading.value && !loaded.value) || !(field in summary.value)
    ? "—"
    : summary.value[field];
}
async function load() {
  const uid = session.profile?.id,
    token = session.token;
  if (loading.value && pendingToken === token && pendingUserId === uid) return;
  const version = ++loadVersion;
  pendingToken = token;
  pendingUserId = uid;
  if (!session.token) {
    summary.value = {};
    learning.value = [];
    collections.value = [];
    badges.value = [];
    loaded.value = false;
    loading.value = false;
    error.value = "";
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    const [s, l, c, b] = await Promise.all([
      api("/mobile/me/summary"),
      api("/mobile/me/learning"),
      api("/mobile/me/collections"),
      api("/mobile/badges"),
    ]);
    if (
      version !== loadVersion ||
      !mounted ||
      token !== session.token ||
      uid !== session.profile?.id ||
      !session.token
    )
      return;
    summary.value = s;
    learning.value = l;
    collections.value = c;
    badges.value = b;
    loaded.value = true;
    if (activeBadge.value)
      activeBadge.value = b.find(
        (badge: any) => badge.id === activeBadge.value.id,
      );
  } catch (e) {
    if (mounted && version === loadVersion && token === session.token)
      error.value = (e as Error).message;
  } finally {
    if (mounted && version === loadVersion && token === session.token)
      loading.value = false;
  }
}
const heroRef = ref<HTMLElement | null>(null);
const compact = ref(false);
const compactLevel = computed(() =>
  !session.token
    ? "入馆开启非遗修习"
    : session.profile?.level_code === "LV1_APPRENTICE"
      ? "典藏学徒"
      : "非遗研习者",
);
let compactFrame = 0;
function syncCompact() {
  compactFrame = 0;
  compact.value = (heroRef.value?.getBoundingClientRect().top ?? 0) < -140;
}
function onPageScroll() {
  if (compactFrame) return;
  compactFrame = requestAnimationFrame(syncCompact);
}
onMounted(() => {
  syncCompact();
  window.addEventListener("scroll", onPageScroll, { passive: true, capture: true });
});
onBeforeUnmount(() => {
  window.removeEventListener("scroll", onPageScroll, { capture: true });
  if (compactFrame) cancelAnimationFrame(compactFrame);
});

function edit() {
  if (!requireSession()) return;
  if (!session.profile) {
    notify("账户资料尚未加载，请稍后重试");
    return;
  }
  editVersion++;
  clearAvatarPreview();
  avatarUploading.value = false;
  form.value = {
    nickname: session.profile?.nickname || "",
    grade: session.profile?.grade || "",
    bio: session.profile?.bio || "",
    school_name: session.profile?.school_name || "",
    district: session.profile?.district || "",
    avatar_url: session.profile?.avatar_url?.startsWith("/static/uploads/")
      ? session.profile.avatar_url
      : "",
  };
  editing.value = true;
}
function closeEdit() {
  editVersion++;
  clearAvatarPreview();
  avatarUploading.value = false;
  editing.value = false;
}
async function save() {
  if (
    saving.value ||
    signingOut.value ||
    avatarUploading.value ||
    !editing.value ||
    !requireSession() ||
    !session.profile
  )
    return;
  const version = ++saveVersion,
    editor = editVersion,
    token = session.token,
    uid = session.profile.id,
    payload = { ...form.value };
  const current = () =>
    mounted &&
    version === saveVersion &&
    token === session.token &&
    uid === session.profile?.id;
  const sameEditor = () => current() && editor === editVersion && editing.value;
  saving.value = true;
  try {
    await put("/mobile/me/profile", payload);
    if (!current()) return;
    let refreshFailed = false;
    try {
      await loadProfile();
    } catch {
      refreshFailed = true;
    }
    if (sameEditor()) {
      closeEdit();
      notify(
        refreshFailed
          ? "个人资料已保存，账户显示暂未刷新，请稍后重试"
          : "个人资料已保存",
      );
    }
  } catch (e) {
    if (sameEditor()) notify((e as Error).message);
  } finally {
    if (current()) saving.value = false;
  }
}
async function signout() {
  if (saving.value || signingOut.value || !session.token) return;
  const token = session.token,
    uid = session.profile?.id;
  signingOut.value = true;
  try {
    await logout();
    if (mounted && !session.token) notify("已退出登录");
  } catch (e) {
    if (mounted && token === session.token && uid === session.profile?.id)
      notify((e as Error).message);
  } finally {
    if (mounted && token === session.token) signingOut.value = false;
  }
}
watch(
  [() => session.profile?.id, () => session.token],
  () => {
    loadVersion++;
    saveVersion++;
    editVersion++;
    pendingToken = undefined;
    pendingUserId = undefined;
    summary.value = {};
    learning.value = [];
    collections.value = [];
    badges.value = [];
    activeBadge.value = undefined;
    editing.value =
      saving.value =
      signingOut.value =
      loaded.value =
      loading.value =
        false;
    form.value = {
      nickname: "",
      grade: "",
      bio: "",
      school_name: "",
      district: "",
      avatar_url: "",
    };
    clearAvatarPreview();
    avatarUploading.value = false;
    error.value = "";
    void load();
  },
  { immediate: true, flush: "sync" },
);
onUnmounted(() => {
  mounted = false;
  loadVersion++;
  saveVersion++;
  clearAvatarPreview();
});
watch(
  [() => profileRoute.query.edit, () => session.profile?.id],
  () => {
    if (profileRoute.query.edit === "1" && session.profile) {
      edit();
      profileRouter.replace({
        query: { ...profileRoute.query, edit: undefined },
      });
    }
  },
  { immediate: true },
);
function targetUrl(item: any) {
  if (item.type === "ASSET" && item.task_id) {
    const tool = (
      {
        SHADOW_PUPPET: "shadow",
        BRONZE: "bronze",
        EMBROIDERY: "lacquer",
        LACQUER: "lacquer",
        MESH_3D: "3d",
        SILHOUETTE: "shadow-3d",
      } as Record<string, string>
    )[item.tool_type];
    if (tool)
      return (
        "/ai-workshop/" + tool + "?task_id=" + encodeURIComponent(item.task_id)
      );
  }
  return item.type === "COURSE"
    ? "/courses/" + item.id
    : item.type === "POST"
      ? "/community/" + item.id
      : "/heritage/" + item.id;
}
</script>
<template>
  <div
    class="profile-page"
    data-design-node="5:00420"
    :data-profile-ready="!loading"
    :aria-busy="loading"
  >
    <header class="profile-appbar" :class="{ elevated: compact }">
      <RouterLink to="/" class="appbar-back" aria-label="返回首页"
        ><img :src="designIcon('layer-5-00420', '5:00505')" alt=""
      /></RouterLink>
      <span class="appbar-title">我的</span>
      <button class="appbar-edit" @click="edit">
        {{ session.token ? "编辑资料" : "登录" }}
      </button>
    </header>
    <section ref="heroRef" class="profile-hero">
      <img
        class="profile-hero-art"
        :src="designImage('layer-5-00420', '5:00495')"
        alt=""
      />
      <div class="profile-card">
        <div class="profile-identity">
          <button
            class="profile-avatar"
            aria-label="编辑个人资料或登录"
            @click="edit"
          >
            <img
              v-if="session.profile?.avatar_url"
              :src="mediaUrl(session.profile.avatar_url)"
              alt=""
            /><span v-else>{{
              session.profile?.nickname?.slice(0, 1) || "学"
            }}</span>
          </button>
          <div class="profile-identity-copy">
            <h1 v-if="session.token">
              {{ session.profile?.nickname || "非遗研习者" }}
            </h1>
            <button v-else class="identity-login" @click="requireSession()">
              点击登录
            </button>
            <span class="profile-level">{{ compactLevel }}</span>
          </div>
        </div>
        <p class="profile-caption">美育成长档案 · 研学记录</p>
        <div class="profile-stats">
          <RouterLink to="/me/posts"
            ><strong>{{ profileCount("post_count") }}</strong
            ><span>作品</span></RouterLink
          ><RouterLink to="/me/follows"
            ><strong>{{ profileCount("following_count") }}</strong
            ><span>关注</span></RouterLink
          ><RouterLink to="/me/follows?direction=followers"
            ><strong>{{ profileCount("follower_count") }}</strong
            ><span>粉丝</span></RouterLink
          >
          <div class="stat-energy">
            <strong>{{ profileCount("energy_value") }}</strong><span>能量</span>
          </div>
        </div>
      </div>
    </section>
    <div class="page-padding">
      <div v-if="loaded && error" class="profile-refresh-error" role="alert">
        <p>暂未更新：{{ error }}</p>
        <button class="text-button" :disabled="loading" @click="load">
          重试更新
        </button>
      </div>
      <AsyncState
        :loading="loading && !loaded"
        :error="loaded ? '' : error"
        @retry="load"
        ><SectionCard title="今日修习" :meta="schoolDate()">
          <div class="learning-scroll">
            <RouterLink
              v-for="item in todayLearning.slice(0, 3)"
              :key="item.chapter_id"
              :to="'/courses/' + item.course_id"
              class="learning-row"
              :class="{
                completed: item.completed,
                beginning: !item.position_seconds,
              }"
              ><div class="learning-row-heading">
                <h3>{{ item.title }}</h3>
                <img
                  v-if="item.completed"
                  class="completed-tick"
                  :src="designIcon('layer-5-00420', '5:00695')"
                  alt=""
                /><span v-if="!item.completed" class="learning-state">{{
                  item.position_seconds ? "修习中" : "初学"
                }}</span
                ><strong>{{
                  item.completed ? "已完成" : learningPercent(item) + "%"
                }}</strong>
              </div>
              <template v-if="!item.completed"
                ><div class="progress-track">
                  <i :style="{ width: learningPercent(item) + '%' }" />
                </div>
                <p class="learning-times">
                  <span>已修习 {{ learningTime(item.position_seconds) }}</span
                  ><span>目标 {{ learningTime(item.duration_seconds) }}</span>
                </p></template
              >
              <p v-else class="completed-caption">
                已修习 {{ learningTime(item.position_seconds) }} ·
                {{ item.chapter_title }}
              </p>
            </RouterLink>
            <p v-if="!todayLearning.length" class="subtle empty-inline">
              从一节非遗小课，开始今日的修习
            </p>
          </div>
          <RouterLink to="/me/learning" class="learning-summary"
            >查看全部学习记录 ›</RouterLink
          >
        </SectionCard>
        <SectionCard
          title="所获徽章"
          :meta="unlockedBadges + ' / ' + badges.length"
        >
          <div class="badge-wall">
            <button
              v-for="badge in badges"
              :key="badge.id"
              :class="{ locked: !badge.unlocked }"
              :aria-label="
                badge.name + (badge.unlocked ? '，已解锁' : '，尚未解锁')
              "
              @click="activeBadge = badge"
            >
              <span
                v-if="badgeDesigns[badge.code]"
                class="badge-art"
                :style="{
                  backgroundImage:
                    'url(' +
                    designImage(
                      'layer-5-00420',
                      badgeDesigns[badge.code].frame,
                    ) +
                    ')',
                  boxShadow: 'inset 0 0 0 ' + badgeDesigns[badge.code].border,
                }"
                ><img
                  :src="
                    designImage('layer-5-00420', badgeDesigns[badge.code].image)
                  "
                  :alt="badge.name"
              /></span>
              <img
                v-else
                :src="mediaUrl(badge.icon_url)"
                :alt="badge.name"
              /><span>{{ badge.name }}</span>
            </button>
            <p v-if="!badges.length" class="subtle empty-inline">
              完成学习与创作，解锁属于你的非遗徽章
            </p>
          </div>
        </SectionCard>
        <SectionCard title="我的收藏" class="profile-collections">
          <template #meta>
            <RouterLink to="/me/collections" class="collection-more"
              >共 {{ summary.collection_count || 0 }} 件 ›</RouterLink
            >
          </template>
          <div class="collection-grid">
            <RouterLink
              v-for="(item, index) in collections.slice(0, 4)"
              :key="item.type + item.id"
              :to="targetUrl(item)"
              class="collection-card"
              ><div class="collection-cover">
                <SkeletonImage
                  :src="item.cover_url"
                  :alt="item.title"
                  ratio="4 / 3"
                /><span class="collection-index"
                  >No.{{ String(index + 1).padStart(3, "0") }}</span
                >
              </div>
              <h3>{{ item.title }}</h3>
              <p>
                {{
                  item.type === "COURSE"
                    ? "非遗课程"
                    : item.type === "ASSET"
                      ? "工坊创作"
                      : item.type === "POST"
                        ? "社区作品"
                        : "非遗百科"
                }}
              </p></RouterLink
            >
            <p v-if="!collections.length" class="subtle empty-inline">
              在典藏与课程中遇见心仪之作，点击收藏即可保存
            </p>
          </div>
        </SectionCard>
        <p class="profile-achievements">
          <span
            >已解锁 <strong>{{ unlockedBadges }}</strong> 枚徽章</span
          ><i>·</i
          ><span
            >学习天数 <strong>{{ summary.learning_days || 0 }}</strong> 天</span
          >
        </p>
        <CellGroup label="学习与班级">
          <CellRow
            v-if="
              session.profile?.role_code === 'TEACHER' ||
              session.profile?.role_code === 'ADMIN'
            "
            label="教学工坊"
            to="/teacher"
          />
          <CellRow label="我的班级与作业" to="/me/assignments" />
          <CellRow label="行走的美育地图" to="/landmarks" />
        </CellGroup>
        <CellGroup label="服务与设置">
          <CellRow label="非遗文创共创市集" to="/mall" />
          <CellRow label="我的订单" to="/me/orders" />
          <CellRow label="帮助与反馈" to="/me/feedback" />
          <CellRow
            v-if="session.token"
            danger
            :disabled="saving || signingOut"
            :label="signingOut ? '正在退出…' : '退出登录'"
            @click="signout"
          />
        </CellGroup></AsyncState
      >
    </div>
    <Teleport to="body"
      ><div
        v-if="activeBadge"
        class="sheet-overlay"
        @click.self="activeBadge = undefined"
      >
        <section
          class="auth-sheet corner-card"
          role="dialog"
          aria-modal="true"
          aria-labelledby="badge-detail-title"
        >
          <button
            class="sheet-close"
            aria-label="关闭徽章详情"
            @click="activeBadge = undefined"
          >
            ×
          </button>
          <h2 id="badge-detail-title">{{ activeBadge.name }}</h2>
          <p class="subtle">{{ activeBadge.description }}</p>
          <p class="badge-unlock-state">
            {{
              activeBadge.unlocked
                ? "已解锁 · " + formatDate(activeBadge.unlocked_at)
                : "尚未解锁，完成条件后即可获得"
            }}
          </p>
          <template v-if="activeBadge.course_progress">
            <p class="subtle">
              已完成
              {{ activeBadge.course_progress.completed_courses ?? "—" }} /
              {{ activeBadge.course_progress.required_courses }} 门课程
            </p>
            <RouterLink
              v-if="activeBadge.course_progress.recommended_course_id"
              class="badge-course-action"
              :to="
                '/courses/' + activeBadge.course_progress.recommended_course_id
              "
              >{{ activeBadge.unlocked ? "重温课程" : "去学习" }}</RouterLink
            >
            <p v-else class="subtle">此类课程尚未开放</p>
          </template>
        </section>
      </div></Teleport
    >
    <Teleport to="body"
      ><div v-if="editing" class="sheet-overlay" @click.self="closeEdit">
        <section
          class="auth-sheet corner-card"
          role="dialog"
          aria-modal="true"
          aria-labelledby="edit-profile-title"
        >
          <button
            class="sheet-close"
            aria-label="关闭资料编辑"
            @click="closeEdit"
          >
            ×
          </button>
          <h2 id="edit-profile-title">个人资料</h2>
          <form @submit.prevent="save">
            <div class="avatar-field">
              <span class="avatar-field-figure">
                <img
                  v-if="avatarPreview || form.avatar_url || session.profile?.avatar_url"
                  :src="
                    avatarPreview ||
                    mediaUrl(form.avatar_url || session.profile?.avatar_url)
                  "
                  :alt="avatarAlt"
                />
                <span v-else aria-hidden="true">{{ avatarInitial }}</span>
              </span>
              <span class="avatar-field-copy"
                ><span>头像</span
                ><button
                  type="button"
                  class="avatar-change"
                  :aria-label="avatarUploading ? '头像上传中' : '更换头像'"
                  :disabled="avatarUploading || saving"
                  @click="chooseAvatar"
                >
                  {{ avatarUploading ? "上传中…" : "更换头像" }}
                </button></span
              >
              <input
                ref="avatarInput"
                class="avatar-input"
                type="file"
                accept="image/png,image/jpeg,image/webp"
                aria-label="选择头像图片"
                @change="uploadAvatar"
              />
            </div>
            <label
              >昵称<input
                v-model.trim="form.nickname"
                required
                maxlength="64" /></label
            ><label
              >年级<input v-model.trim="form.grade" maxlength="32" /></label
            ><label
              >学校<input
                v-model.trim="form.school_name"
                maxlength="128" /></label
            ><label
              >所在区县<input
                v-model.trim="form.district"
                maxlength="64" /></label
            ><label
              >个人简介<textarea
                v-model.trim="form.bio"
                maxlength="255"
              /></label
            ><button
              class="primary-button"
              :disabled="saving || avatarUploading"
            >
              {{ saving ? "保存中…" : "保存资料" }}
            </button>
          </form>
        </section>
      </div></Teleport
    >
  </div>
</template>
<style scoped>
.profile-refresh-error {
  margin-bottom: 16px;
  color: #8b1a1a;
  font-size: 13px;
  line-height: 1.8;
  overflow-wrap: anywhere;
}
.profile-page {
  background: #f5ede4;
  color: #2d1810;
  min-height: 100dvh;
  padding-bottom: 12px;
}
.profile-appbar {
  position: sticky;
  top: 0;
  z-index: 40;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: calc(var(--safe-top) + 6px) 16px 8px;
  background: rgba(245, 237, 228, 0.9);
  -webkit-backdrop-filter: blur(12px);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid transparent;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}
.profile-appbar.elevated {
  border-bottom-color: rgba(139, 105, 48, 0.14);
  box-shadow: 0 6px 18px rgba(60, 38, 24, 0.06);
}
.appbar-back {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(139, 105, 48, 0.18);
}
.appbar-back img {
  width: 18px;
  height: 18px;
}
.appbar-title {
  font: 500 16px/1.2 var(--serif);
  letter-spacing: 3px;
  color: #2d1810;
}
.appbar-edit {
  margin-left: auto;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid rgba(139, 26, 26, 0.22);
  background: rgba(255, 255, 255, 0.66);
  color: #8b1a1a;
  font: 500 11px/1 var(--sans);
  letter-spacing: 1px;
}
.profile-hero {
  position: relative;
  padding: 92px 16px 8px;
  isolation: isolate;
}
.profile-hero-art {
  position: absolute;
  inset: 0 0 auto;
  width: 100%;
  height: 168px;
  object-fit: cover;
  z-index: -1;
  pointer-events: none;
  -webkit-mask-image: linear-gradient(180deg, #000 58%, transparent);
  mask-image: linear-gradient(180deg, #000 58%, transparent);
}
.profile-card {
  position: relative;
  margin-top: 0;
  padding: 16px 16px 6px;
  border-radius: 20px;
  background: #fdf9f2;
  box-shadow: 0 10px 30px rgba(70, 42, 26, 0.12);
}
.profile-identity {
  display: flex;
  align-items: center;
  gap: 14px;
}
.profile-avatar {
  width: 64px;
  height: 64px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  overflow: hidden;
  border-radius: 50%;
  border: 2px solid rgba(200, 169, 110, 0.85);
  background: #8b1a1a;
  color: #f6ead9;
  font: 400 26px/1 var(--serif);
  box-shadow: 0 4px 14px rgba(139, 26, 26, 0.18);
}
.profile-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.avatar-field {
  display: flex;
  align-items: center;
  gap: 14px;
}
.avatar-field-figure {
  width: 56px;
  height: 56px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  overflow: hidden;
  border-radius: 50%;
  border: 2px solid rgba(200, 169, 110, 0.85);
  background: #8b1a1a;
  color: #f6ead9;
  font: 400 22px/1 var(--serif);
}
.avatar-field-figure img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.avatar-field-copy {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  font-size: 13px;
  color: #5a3e36;
}
.avatar-change {
  min-height: 32px;
  padding: 6px 14px;
  border: 1px solid rgba(139, 26, 26, 0.35);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.66);
  color: #8b1a1a;
  font: 500 12px/1 var(--sans);
}
.avatar-change:disabled {
  opacity: 0.6;
}
.avatar-input {
  display: none;
}
.profile-identity-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}
.profile-identity-copy h1,
.identity-login {
  margin: 0;
  padding: 0;
  border: 0;
  background: none;
  text-align: left;
  font: 500 22px/1.25 var(--serif);
  letter-spacing: 2px;
  color: #2d1810;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.identity-login {
  color: #8b1a1a;
}
.profile-level {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font: 400 11px/1.4 var(--sans);
  letter-spacing: 1.4px;
  color: #8a6125;
}
.profile-level::before {
  content: "";
  width: 14px;
  height: 1px;
  background: #c8a96e;
}
.profile-caption {
  margin: 12px 0 0;
  font: 400 10px/1.5 var(--sans);
  letter-spacing: 1.6px;
  color: #9b8478;
}
.profile-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(200, 169, 110, 0.28);
}
.profile-stats > a,
.profile-stats > .stat-energy {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  min-width: 0;
  padding: 2px 0 6px;
}
.profile-stats > a + a,
.profile-stats > .stat-energy {
  border-left: 1px solid rgba(200, 169, 110, 0.18);
}
.profile-stats strong {
  font: 500 19px/1.25 var(--serif);
  color: #8b1a1a;
}
.profile-stats span {
  font: 400 10px/1.4 var(--sans);
  letter-spacing: 1px;
  color: #7c665c;
}
.stat-energy strong {
  color: #8a6125;
}

.page-padding {
  padding: 14px 16px 24px;
}
.profile-section {
  margin-bottom: 14px;
  padding: 16px 14px;
}
.section-heading {
  display: flex;
  gap: 12px;
  align-items: center;
  margin: 0 0 16px;
  min-height: 24px;
}
.section-heading::after {
  content: "";
  order: 1;
  height: 1px;
  background: rgba(200, 169, 110, 0.3);
  flex: 1;
}
.section-heading h2 {
  order: 0;
  display: flex;
  gap: 12px;
  align-items: center;
  flex-shrink: 0;
  font: 400 16px/24px var(--serif);
  letter-spacing: 1.6px;
}
.section-heading h2::before {
  content: "";
  width: 3px;
  height: 16px;
  border-radius: 2px;
  background: #b85450;
}
.section-heading > span,
.section-heading > a {
  order: 2;
  flex-shrink: 0;
  color: #8b7a72;
  font: 400 10px/15px var(--sans);
}
.learning-scroll {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.learning-row {
  display: block;
  min-height: 95px;
  padding: 16px;
  border: 1px solid rgba(200, 169, 110, 0.1);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.6);
}
.learning-row-heading {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 20px;
}
.learning-row-heading h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font: 500 14px/20px var(--sans);
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.learning-row-heading h3::before {
  content: "";
  flex-shrink: 0;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #8b1a1a;
}
.learning-row-heading strong {
  margin-left: auto;
  flex-shrink: 0;
  font: 400 14px/20px var(--serif);
  color: #8b1a1a;
}
.learning-state {
  flex-shrink: 0;
  font-size: 10px;
  line-height: 15px;
  padding: 2px 6px;
  color: #8b1a1a;
  background: #fff0f0;
  border-radius: 4px;
}
.learning-row .progress-track {
  height: 6px;
  margin-top: 12px;
  border: 0;
  background: #ffe8e8;
}
.learning-row .progress-track i {
  background: #8b1a1a;
}
.learning-times {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 10px;
  line-height: 15px;
  color: #8b7a72;
  margin-top: 8px;
}
.beginning .learning-state,
.beginning .learning-row-heading strong {
  color: #c8a96e;
}
.beginning .learning-row-heading h3::before,
.beginning .progress-track i {
  background: #c8a96e;
}
.completed .learning-row-heading h3 {
  color: #5a3e36;
  text-decoration: line-through;
}
.learning-row.completed {
  min-height: 77px;
}
.completed .learning-row-heading h3::before {
  background: #059669;
}
.completed .learning-row-heading strong {
  color: #059669;
  font: 500 10px/15px var(--sans);
}
.completed-tick {
  width: 12px;
  height: 12px;
  flex-shrink: 0;
}
.completed-caption {
  font-size: 10px;
  line-height: 15px;
  color: #8b7a72;
  margin-top: 8px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.learning-summary {
  display: block;
  color: #8b7a72;
  font-size: 10px;
  line-height: 15px;
  text-align: right;
  margin-top: 12px;
}
.badge-wall {
  display: flex;
  gap: 16px;
  overflow: auto;
  padding: 0 2px 8px;
  scrollbar-width: none;
}
.badge-wall::-webkit-scrollbar {
  display: none;
}
.badge-wall button {
  flex: 0 0 56px;
  width: 56px;
  padding: 0;
  text-align: center;
  color: #5a3e36;
}
.badge-wall img {
  width: 56px;
  height: 56px;
  object-fit: contain;
  margin: 0 auto 8px;
}
.badge-wall span {
  display: block;
  font: 500 10px/15px var(--sans);
}
.badge-wall .locked img {
  filter: grayscale(1);
  opacity: 0.45;
}
.badge-wall .badge-art {
  position: relative;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background-size: cover;
  background-position: center;
  margin-bottom: 8px;
}
.badge-wall .badge-art img {
  position: absolute;
  left: 8px;
  top: 8px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  margin: 0;
}
.badge-wall .locked .badge-art {
  filter: grayscale(1);
  opacity: 0.45;
}
.badge-wall .locked .badge-art img {
  opacity: 1;
  filter: none;
}
.badge-wall .locked span {
  color: #8b7a72;
}
.badge-unlock-state {
  margin-top: 20px;
  font-size: 13px;
  line-height: 1.8;
  color: #8b1a1a;
}
.badge-course-action {
  display: block;
  margin-top: 12px;
  padding: 10px 16px;
  border-radius: 12px;
  background: #8b1a1a;
  color: #fff;
  text-align: center;
}
.collection-grid {
  display: flex;
  gap: 15px;
  overflow-x: auto;
  margin-right: -20px;
  padding-right: 20px;
  scroll-snap-type: x proximity;
  scroll-behavior: smooth;
  overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch;
}
.collection-grid::-webkit-scrollbar {
  display: none;
}
.collection-more {
  font: 400 10px/1.5 var(--sans);
  letter-spacing: 1px;
  color: #8a7a70;
  white-space: nowrap;
}
.collection-card {
  flex: 0 0 158px;
  min-width: 0;
  min-height: 185px;
  scroll-snap-align: start;
  overflow: hidden;
  border: 1px solid rgba(200, 169, 110, 0.3);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.8);
  content-visibility: auto;
  contain-intrinsic-size: auto 190px;
}
.collection-cover {
  position: relative;
}
.collection-cover .collection-index {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 3px 7px;
  border-radius: 4px;
  background: rgba(255, 253, 248, 0.9);
  color: #8b1a1a;
  font: 400 9px/13.5px var(--serif);
}
.collection-card h3 {
  margin: 6px 8px 0;
  font: 500 12px/16px var(--sans);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.collection-card p {
  color: #8b7a72;
  font-size: 10px;
  line-height: 15px;
  margin: 4px 8px 12px;
}
.empty-inline {
  flex: 1 0 100%;
  padding: 24px 10px;
  text-align: center;
  grid-column: 1/-1;
  color: #8b7a72;
}
.profile-achievements {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: center;
  min-height: 50px;
  padding: 12px 8px;
  border: 1px solid rgba(200, 169, 110, 0.3);
  border-radius: 12px;
  font: 400 12px/16px var(--serif);
  color: #5a3e36;
  margin: 0 0 14px;
  background: rgba(255, 255, 255, 0.3);
}
.profile-achievements strong {
  font-weight: 600;
  color: #8b1a1a;
}
.profile-achievements i {
  font-style: normal;
  color: rgba(200, 169, 110, 0.4);
}
.profile-cells {
  margin-bottom: 14px;
  padding: 4px 0;
  overflow: hidden;
}
.cell {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-height: 48px;
  padding: 0 16px;
  background: none;
  border: 0;
  text-align: left;
  font: 400 14px/1.4 var(--sans);
  color: #2d1810;
}
.cell + .cell {
  border-top: 1px solid rgba(200, 169, 110, 0.16);
}
.cell:active {
  background: rgba(200, 169, 110, 0.08);
}
.cell-mark {
  width: 4px;
  height: 14px;
  border-radius: 2px;
  background: rgba(139, 26, 26, 0.55);
  flex-shrink: 0;
}
.cell-label {
  flex: 1;
  min-width: 0;
}
.cell-arrow {
  color: #b9a48c;
  font-size: 16px;
}
.cell-danger {
  justify-content: center;
  color: #8b1a1a;
}

@media (max-width: 350px) {
  .section-heading {
    gap: 8px;
  }
  .profile-achievements {
    font-size: 11px;
    gap: 6px;
  }
}
</style>
