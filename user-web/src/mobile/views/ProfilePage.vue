<script setup lang="ts">
import { ref, watch, onUnmounted, computed } from "vue";
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
  }),
  saving = ref(false),
  signingOut = ref(false);
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
function edit() {
  if (!requireSession()) return;
  if (!session.profile) {
    notify("账户资料尚未加载，请稍后重试");
    return;
  }
  editVersion++;
  form.value = {
    nickname: session.profile?.nickname || "",
    grade: session.profile?.grade || "",
    bio: session.profile?.bio || "",
    school_name: session.profile?.school_name || "",
    district: session.profile?.district || "",
  };
  editing.value = true;
}
function closeEdit() {
  editVersion++;
  editing.value = false;
}
async function save() {
  if (
    saving.value ||
    signingOut.value ||
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
    };
    error.value = "";
    void load();
  },
  { immediate: true, flush: "sync" },
);
onUnmounted(() => {
  mounted = false;
  loadVersion++;
  saveVersion++;
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
    <header class="profile-hero">
      <img
        class="profile-hero-art"
        :src="designImage('layer-5-00420', '5:00495')"
        alt=""
      />
      <RouterLink to="/" class="profile-back" aria-label="返回首页"
        ><img :src="designIcon('layer-5-00420', '5:00505')" alt=""
      /></RouterLink>
      <p class="profile-entry-year">美育成长档案 · 研学记录</p>
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
      <div class="profile-avatar-dots" aria-hidden="true"><i /><i /><i /></div>
      <h1>
        <template v-if="session.token">{{
          session.profile?.nickname || "非遗研习者"
        }}</template
        ><button v-else @click="requireSession">点击登录</button>
      </h1>
      <span class="profile-level">{{
        !session.token
          ? "入馆开启非遗修习"
          : session.profile?.level_code === "LV1_APPRENTICE"
            ? "典藏学徒"
            : "非遗研习者"
      }}</span>
      <div class="profile-counters">
        <RouterLink to="/me/posts"
          ><strong>{{ profileCount("post_count") }}</strong
          ><span>作品</span
          ><small>能量 {{ profileCount("energy_value") }}</small></RouterLink
        ><RouterLink to="/me/follows"
          ><strong>{{ profileCount("following_count") }}</strong
          ><span>关注</span><small>师友同道</small></RouterLink
        ><RouterLink to="/me/follows?direction=followers"
          ><strong>{{ profileCount("follower_count") }}</strong
          ><span>粉丝</span><small>知音共赏</small></RouterLink
        >
      </div>
    </header>
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
        ><section class="profile-section">
          <div class="section-heading">
            <h2>今日修习</h2>
            <span>{{ schoolDate() }}</span>
          </div>
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
        </section>
        <section class="profile-section">
          <div class="section-heading">
            <h2>所获徽章</h2>
            <span>{{ unlockedBadges }} / {{ badges.length }}</span>
          </div>
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
        </section>
        <section class="profile-section profile-collections">
          <div class="section-heading">
            <h2>我的收藏</h2>
            <RouterLink to="/me/collections"
              >共 {{ summary.collection_count || 0 }} 件 ›</RouterLink
            >
          </div>
          <div class="collection-grid">
            <RouterLink
              v-for="(item, index) in collections.slice(0, 4)"
              :key="item.type + item.id"
              :to="targetUrl(item)"
              class="collection-card"
              ><div class="collection-cover">
                <img :src="mediaUrl(item.cover_url)" :alt="item.title" /><span
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
        </section>
        <p class="profile-achievements">
          <span
            >已解锁 <strong>{{ unlockedBadges }}</strong> 枚徽章</span
          ><i>·</i
          ><span
            >学习天数 <strong>{{ summary.learning_days || 0 }}</strong> 天</span
          >
        </p>
        <nav class="profile-services">
          <RouterLink
            v-if="
              session.profile?.role_code === 'TEACHER' ||
              session.profile?.role_code === 'ADMIN'
            "
            to="/teacher"
            >教学工坊 <span>›</span></RouterLink
          ><RouterLink to="/me/assignments"
            >我的班级与作业 <span>›</span></RouterLink
          ><RouterLink to="/landmarks">行走的美育地图 <span>›</span></RouterLink
          ><RouterLink to="/mall">非遗文创共创市集 <span>›</span></RouterLink
          ><RouterLink to="/me/orders">我的订单 <span>›</span></RouterLink
          ><RouterLink to="/me/feedback">帮助与反馈 <span>›</span></RouterLink
          ><button
            v-if="session.token"
            :disabled="saving || signingOut"
            @click="signout"
          >
            {{ signingOut ? "正在退出…" : "退出登录" }}
          </button>
        </nav></AsyncState
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
            ><button class="primary-button" :disabled="saving">
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
}
.profile-hero {
  position: relative;
  height: 353px;
  text-align: center;
  isolation: isolate;
}
.profile-hero::before {
  content: "";
  position: absolute;
  inset: 0 0 auto;
  height: 305px;
  background: #c5aaa1;
  z-index: -2;
}
.profile-hero-art {
  position: absolute;
  inset: 0 0 auto;
  width: 100%;
  height: 305px;
  object-fit: cover;
  z-index: -1;
  pointer-events: none;
}
.profile-back {
  position: absolute;
  left: 10px;
  top: 16px;
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  background: rgba(240, 230, 208, 0.8);
  border-radius: 50%;
  z-index: 1;
}
.profile-back img {
  width: 20px;
  height: 20px;
}
.profile-entry-year {
  position: absolute;
  top: 137px;
  left: 42.46%;
  height: 30px;
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
  padding: 6px 16px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 30px;
  color: #5a3e36;
  font: 400 12px/16px var(--serif);
  letter-spacing: 1.53px;
}
.profile-entry-year::before,
.profile-entry-year::after {
  content: "";
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(139, 26, 26, 0.6);
  flex-shrink: 0;
}
.profile-avatar {
  position: absolute;
  top: 24px;
  left: calc(26.84% - 55px);
  display: grid;
  place-items: center;
  width: 110px;
  height: 110px;
  border: 1px solid rgba(200, 169, 110, 0.6);
  border-radius: 50%;
  overflow: hidden;
  margin: 0;
  padding: 0;
  background: #b85450;
  color: #fff0f0;
  font: 400 32px/1 var(--serif);
  box-shadow:
    0 0 0 4px rgba(200, 169, 110, 0.2),
    0 0 0 8px rgba(200, 169, 110, 0.1);
}
.profile-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.profile-avatar-dots {
  position: absolute;
  top: 132px;
  left: calc(26.84% - 15px);
  display: flex;
  gap: 6px;
}
.profile-avatar-dots i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(200, 169, 110, 0.6);
}
.profile-avatar-dots i:nth-child(2) {
  background: rgba(139, 26, 26, 0.4);
}
.profile-hero h1 {
  position: absolute;
  top: 167px;
  left: 30px;
  right: 18px;
  height: 42px;
  font: 400 28px/42px var(--serif);
  letter-spacing: 5.6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.profile-hero h1 button {
  font: inherit;
  letter-spacing: inherit;
  padding: 0;
}
.profile-level {
  position: absolute;
  top: 201px;
  left: 30px;
  right: 18px;
  color: #b85450;
  font: 400 12px/16px var(--serif);
  letter-spacing: 3.6px;
}
.profile-counters {
  position: absolute;
  top: 237px;
  left: 22px;
  right: 18px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}
.profile-counters > a {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-width: 0;
  height: 104px;
  padding: 8px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.7);
}
.profile-counters > a:nth-child(2) {
  background: rgba(255, 255, 255, 0.9);
}
.profile-counters > a::before,
.profile-counters > a::after {
  content: "";
  position: absolute;
  width: 16px;
  height: 16px;
  border-color: #c8a96e;
  border-style: solid;
  pointer-events: none;
}
.profile-counters > a::before {
  left: 8px;
  top: 8px;
  border-width: 1px 0 0 1px;
}
.profile-counters > a::after {
  right: 8px;
  bottom: 10px;
  border-width: 0 1px 1px 0;
}
.profile-counters strong {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  font: 400 22px/33px var(--serif);
  color: #8b1a1a;
}
.profile-counters span {
  font: 500 11px/16px var(--sans);
  color: #5a3e36;
}
.profile-counters small {
  font: 400 10px/15px var(--sans);
  color: #8b7a72;
  white-space: nowrap;
}
.page-padding {
  padding: 24px 20px 30px;
}
.profile-section {
  margin-bottom: 32px;
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
.profile-collections .section-heading {
  margin-bottom: 28px;
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
}
.collection-cover {
  position: relative;
}
.collection-cover img {
  width: 100%;
  height: auto;
  aspect-ratio: 4/3;
  object-fit: cover;
}
.collection-cover span {
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
  margin: 0 0 24px;
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
.profile-services {
  border-top: 1px solid rgba(200, 169, 110, 0.3);
  padding-top: 8px;
}
.profile-services > a,
.profile-services > button {
  display: flex;
  justify-content: space-between;
  width: 100%;
  padding: 16px 2px;
  border-bottom: 1px solid rgba(200, 169, 110, 0.3);
  font-size: 13px;
  color: #5a3e36;
}
.profile-services span {
  color: #8b1a1a;
  font-size: 18px;
}
@media (max-width: 350px) {
  .profile-entry-year {
    left: auto;
    right: 12px;
    padding: 6px 10px;
    letter-spacing: 0.7px;
  }
  .profile-counters {
    gap: 8px;
  }
  .section-heading {
    gap: 8px;
  }
  .profile-achievements {
    font-size: 11px;
    gap: 6px;
  }
}
</style>
