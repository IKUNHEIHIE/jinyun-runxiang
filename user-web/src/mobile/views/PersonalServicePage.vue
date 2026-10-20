<script setup lang="ts">
import { computed, ref, watch, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import { api, post, mediaUrl, notify, session } from "../api";
import PageHeader from "../components/PageHeader.vue";
import AsyncState from "../components/AsyncState.vue";
import SectionCard from "../components/SectionCard.vue";
import { formatDate } from "../dates";
const route = useRoute(),
  items = ref<any[]>([]),
  loading = ref(false),
  error = ref(""),
  busy = ref(false);
const feedbackBusy = ref(false);
const invite = ref(""),
  content = ref(""),
  contact = ref(""),
  selectedAssignment = ref<number>(),
  submission = ref("");
const classes = ref<any[]>([]);
const section = computed(() => String(route.params.section));
const title = computed(
  () =>
    ({
      collections: "我的收藏",
      follows: route.query.direction === "followers" ? "我的粉丝" : "我的关注",
      posts: "我的作品",
      orders: "我的订单",
      exchanges: "能量兑换记录",
      assignments: "我的班级与作业",
      feedback: "帮助与反馈",
      learning: "修习记录",
      reviews: "我的评价",
    })[section.value] || "我的服务",
);
let loadVersion = 0,
  mounted = true;
let feedbackVersion = 0;
async function load() {
  const version = ++loadVersion,
    token = session.token;
  const current = () =>
    mounted && version === loadVersion && token === session.token;
  loading.value = true;
  error.value = "";
  items.value = [];
  classes.value = [];
  try {
    const endpoint =
      section.value === "orders"
        ? "/mall/orders"
        : "/mobile/me/" +
          section.value +
          (section.value === "follows"
            ? "?direction=" + (route.query.direction || "following")
            : "");
    const loaded = await api(endpoint);
    if (!current()) return;
    items.value = loaded;
    if (section.value === "assignments") {
      const loadedClasses = await api("/mobile/me/classes");
      if (current()) classes.value = loadedClasses;
    }
  } catch (e) {
    if (current()) error.value = (e as Error).message;
  } finally {
    if (current()) loading.value = false;
  }
}
async function join() {
  if (busy.value) return;
  busy.value = true;
  try {
    const result = await post("/mobile/classes/join", {
      invite_code: invite.value,
    });
    notify("已加入 " + result.name);
    invite.value = "";
    await load();
  } catch (e) {
    notify((e as Error).message);
  } finally {
    busy.value = false;
  }
}
async function submitAssignment() {
  if (busy.value || !selectedAssignment.value) return;
  busy.value = true;
  try {
    await post("/mobile/assignments/" + selectedAssignment.value + "/submit", {
      content: submission.value,
    });
    selectedAssignment.value = undefined;
    notify("作业已提交，等待教师批改");
    await load();
  } catch (e) {
    notify((e as Error).message);
  } finally {
    busy.value = false;
  }
}
async function feedback() {
  if (feedbackBusy.value) return;
  const version = ++feedbackVersion,
    token = session.token;
  const current = () =>
    mounted &&
    version === feedbackVersion &&
    token === session.token &&
    section.value === "feedback";
  feedbackBusy.value = true;
  try {
    await post("/mobile/feedback", {
      content: content.value,
      contact: contact.value,
    });
    if (!current()) return;
    content.value = "";
    contact.value = "";
    notify("反馈已提交，感谢你的建议");
    await load();
  } catch (e) {
    if (current()) notify((e as Error).message);
  } finally {
    if (current()) feedbackBusy.value = false;
  }
}
async function cancelOrder(order: any) {
  if (busy.value) return;
  busy.value = true;
  try {
    await post("/mall/orders/" + order.order_no + "/cancel");
    notify("订单已取消");
    await load();
  } catch (e) {
    notify((e as Error).message);
  } finally {
    busy.value = false;
  }
}
function itemUrl(item: any) {
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
  return item.type === "COURSE" || section.value === "learning"
    ? "/courses/" + (item.course_id || item.id)
    : item.type === "HERITAGE"
      ? "/heritage/" + item.id
      : "/community/" + item.id;
}
watch(
  () => [
    route.params.section,
    route.query.direction,
    session.token,
    session.profile?.id,
  ],
  (next, previous) => {
    feedbackVersion++;
    feedbackBusy.value = false;
    if (previous && (next[2] !== previous[2] || next[3] !== previous[3])) {
      content.value = "";
      contact.value = "";
    }
    load();
  },
  {
    immediate: true,
  },
);
onUnmounted(() => {
  mounted = false;
  loadVersion++;
});
</script>
<template>
  <div class="service-page">
    <PageHeader :title="title" />
    <div class="service-body">
      <template v-if="section === 'feedback'">
        <SectionCard title="让非遗之旅更美好">
          <p class="subtle service-intro">
            告诉我们你遇到的问题或建议，反馈会保存在平台中。
          </p>
          <form class="service-form" @submit.prevent="feedback">
            <label
              >反馈内容<textarea
                v-model.trim="content"
                required
                minlength="5"
                maxlength="5000"
                placeholder="请描述问题或建议（至少5个字）"
              /></label
            ><label
              >联系方式（选填）<input
                v-model.trim="contact"
                maxlength="128"
            /></label>
            <button class="primary-button" :disabled="feedbackBusy">
              {{ feedbackBusy ? "正在提交…" : "提交反馈" }}
            </button>
          </form>
        </SectionCard>
        <SectionCard title="我的反馈">
          <template #meta>
            <button class="text-link" :disabled="loading" @click="load">
              刷新
            </button>
          </template>
          <AsyncState
            :loading="loading"
            :error="error"
            :empty="!items.length"
            empty-text="还没有反馈记录"
            @retry="load"
          >
            <div class="feedback-list">
              <article
                v-for="item in items"
                :key="item.id"
                class="feedback-item"
              >
                <div class="feedback-head">
                  <span class="status-chip">
                    {{
                      {
                        PENDING: "待处理",
                        PROCESSING: "处理中",
                        RESOLVED: "已回复",
                      }[item.status] || item.status
                    }}
                  </span>
                  <span class="feedback-date">{{
                    formatDate(item.created_at)
                  }}</span>
                </div>
                <p class="feedback-content">{{ item.content }}</p>
                <div v-if="item.reply_text" class="feedback-reply">
                  <b>平台回复</b>
                  <p class="feedback-content">{{ item.reply_text }}</p>
                  <small>{{ formatDate(item.handled_at) }}</small>
                </div>
              </article>
            </div>
          </AsyncState>
        </SectionCard>
      </template>
      <template v-else>
        <SectionCard v-if="section === 'assignments'">
          <form class="join-form" @submit.prevent="join">
            <label
              >班级邀请码<input
                v-model.trim="invite"
                required
                minlength="4"
                maxlength="16"
                placeholder="向老师获取班级邀请码" /></label
            ><button class="primary-button" :disabled="busy">加入班级</button>
          </form>
        </SectionCard>
        <div
          v-if="section === 'assignments' && classes.length"
          class="class-list"
        >
          <article
            v-for="c in classes"
            :key="c.id"
            class="class-card corner-card"
          >
            <h2>{{ c.name }}</h2>
            <p class="subtle">{{ c.grade }}</p>
            <div class="class-actions">
              <RouterLink
                :to="'/notices?class_id=' + c.id"
                class="outline-button"
                >班级通知</RouterLink
              ><RouterLink to="/classroom" class="outline-button"
                >进入课堂</RouterLink
              >
            </div>
          </article>
        </div>
        <AsyncState
          :loading="loading"
          :error="error"
          :empty="!items.length"
          @retry="load"
          ><div class="service-list">
            <template v-for="item in items" :key="item.order_no || item.id"
              ><article
                v-if="section === 'assignments'"
                class="service-card corner-card"
              >
                <h2>
                  <span v-if="item.type === 'CONTEST'" class="contest-badge"
                    >对抗赛</span
                  >
                  {{ item.title }}
                </h2>
                <p class="subtle">{{ item.description }}</p>
                <p class="service-caption">
                  截止 {{ formatDate(item.deadline) }}
                </p>
                <template v-if="item.submission"
                  ><p class="submission-content">
                    {{ item.submission.content }}
                  </p>
                  <p class="service-caption">
                    {{
                      item.contest && item.contest.status !== "PUBLISHED"
                        ? "已提交，等待成绩公布"
                        : item.submission.status === "REVIEWED"
                          ? "已批改"
                          : "已提交，等待批改"
                    }}
                  </p>
                  <p v-if="item.submission.score != null" class="review-score">
                    {{ item.submission.score }} 分
                  </p>
                  <p v-if="item.submission.comment" class="subtle">
                    教师评语：{{ item.submission.comment }}
                  </p></template
                >
                <div class="service-actions">
                  <RouterLink
                    v-if="item.contest"
                    :to="'/contests/' + item.contest.id"
                    class="outline-button"
                    >进入对抗赛</RouterLink
                  ><button
                    v-if="item.submission?.status !== 'REVIEWED'"
                    class="outline-button"
                    @click="
                      selectedAssignment = item.id;
                      submission = item.submission?.content || '';
                    "
                  >
                    {{ item.submission ? "修改提交" : "提交作业" }}
                  </button>
                </div>
              </article>
              <article
                v-else-if="section === 'exchanges'"
                class="service-card corner-card"
              >
                <h2>{{ item.item_name }}</h2>
                <p class="service-caption">
                  {{ item.energy_cost }} 能量 ·
                  {{
                    {
                      REQUESTED: "待发放",
                      FULFILLED: "已发放",
                      CANCELLED: "已取消并退还能量",
                    }[item.status] || item.status
                  }}
                </p>
                <p v-if="item.tracking_no" class="subtle">
                  发放单号：{{ item.tracking_no }}
                </p>
                <p v-if="item.handling_note" class="feedback-content">
                  处理说明：{{ item.handling_note }}
                </p>
                <p v-if="item.handled_at" class="subtle">
                  处理时间：{{ formatDate(item.handled_at) }}
                </p>
                <p class="service-caption">{{ formatDate(item.created_at) }}</p>
              </article>
              <article
                v-else-if="section === 'orders'"
                class="service-card corner-card"
              >
                <h2>{{ item.order_no }}</h2>
                <p class="service-caption">
                  {{
                    item.status === "CREATED"
                      ? "待支付"
                      : item.status === "CANCELLED"
                        ? "已取消"
                        : item.status
                  }}
                </p>
                <strong class="order-price"
                  >¥{{ Number(item.total_amount_yuan || 0).toFixed(2) }}</strong
                >
                <p class="subtle">{{ formatDate(item.created_at) }}</p>
                <button
                  v-if="item.status === 'CREATED'"
                  class="outline-button"
                  :disabled="busy"
                  @click="cancelOrder(item)"
                >
                  取消订单
                </button>
              </article>
              <article
                v-else-if="section === 'reviews'"
                class="service-card corner-card"
              >
                <RouterLink :to="'/courses/' + item.course_id"
                  ><h2>{{ item.title }}</h2></RouterLink
                >
                <p class="service-caption">我的评分 {{ item.rating }} / 5</p>
                <p v-if="item.comment" class="subtle">{{ item.comment }}</p>
                <p class="subtle">{{ formatDate(item.created_at) }}</p>
              </article>
              <article
                v-else-if="section === 'follows'"
                class="follow-row corner-card"
              >
                <img
                  v-if="item.avatar_url"
                  :src="mediaUrl(item.avatar_url)"
                  alt=""
                /><span v-else class="small-avatar">{{
                  item.nickname.slice(0, 1)
                }}</span>
                <h3>{{ item.nickname }}</h3>
              </article>
              <RouterLink
                v-else
                :to="itemUrl(item)"
                class="saved-item corner-card"
                ><img :src="mediaUrl(item.cover_url)" :alt="item.title" />
                <div class="saved-copy">
                  <h3>{{ item.title }}</h3>
                  <p class="subtle">
                    {{
                      item.status === "PENDING_REVIEW"
                        ? "审核中"
                        : item.status === "REJECTED"
                          ? "未通过审核"
                          : item.completed
                            ? "已完成修习"
                            : ""
                    }}
                  </p>
                </div></RouterLink
              ></template
            >
          </div></AsyncState
        >
      </template>
    </div>
    <Teleport to="body"
      ><div
        v-if="selectedAssignment"
        class="sheet-overlay"
        @click.self="selectedAssignment = undefined"
      >
        <section
          class="auth-sheet corner-card service-sheet"
          role="dialog"
          aria-modal="true"
          aria-labelledby="assignment-title"
        >
          <button
            class="sheet-close"
            aria-label="关闭提交作业"
            @click="selectedAssignment = undefined"
          >
            ×
          </button>
          <h2 id="assignment-title">提交作业</h2>
          <form @submit.prevent="submitAssignment">
            <label
              >创作心得与作业内容<textarea
                v-model.trim="submission"
                required
                maxlength="10000"
            /></label>
            <button class="primary-button" :disabled="busy">
              {{ busy ? "提交中…" : "提交给老师" }}
            </button>
          </form>
        </section>
      </div></Teleport
    >
  </div>
</template>
<style scoped>
.service-page {
  min-height: 100dvh;
  padding-bottom: 12px;
  background: #f5ede4;
  color: #2d1810;
}
.service-body {
  padding: 14px 16px 24px;
}
.service-intro {
  margin-bottom: 14px;
  color: #8a7a70;
  font: 400 11px/1.7 var(--sans);
}
.service-form,
.join-form {
  gap: 12px;
  margin: 0;
}
.service-form label,
.join-form label,
.service-sheet label {
  gap: 6px;
  color: #8a7a70;
  font: 400 11px/1.4 var(--sans);
  letter-spacing: 1px;
}
.service-form input,
.service-form textarea,
.join-form input,
.service-sheet input,
.service-sheet textarea {
  min-height: 42px;
  padding: 10px 12px;
  border: 1px solid rgba(200, 169, 110, 0.45);
  border-radius: 10px;
  background: #fffdf8;
  color: #2d1810;
  font: 400 14px/1.6 var(--sans);
  letter-spacing: 0;
}
.service-form textarea,
.service-sheet textarea {
  min-height: 110px;
}
.service-page .primary-button,
.service-sheet .primary-button {
  min-height: 44px;
  border: 1px solid rgba(232, 217, 168, 0.55);
  border-radius: 10px;
  background: #8b1a1a;
  color: #f6ead9;
  font: 500 13px/1.4 var(--sans);
  letter-spacing: 2px;
  box-shadow: 0 6px 16px rgba(139, 26, 26, 0.16);
}
.text-link {
  padding: 4px 0;
  color: #8a6125;
  font: 400 11px/1.4 var(--sans);
  letter-spacing: 0.5px;
}
.text-link:disabled {
  opacity: 0.5;
}
.status-chip {
  display: inline-block;
  padding: 2px 8px;
  border: 1px solid rgba(139, 26, 26, 0.28);
  border-radius: 999px;
  background: #fff0f0;
  color: #8b1a1a;
  font: 400 10px/1.5 var(--sans);
  letter-spacing: 0.5px;
  white-space: nowrap;
}
.feedback-list {
  display: flex;
  flex-direction: column;
}
.feedback-item {
  padding: 14px 0;
  border-top: 1px solid rgba(200, 169, 110, 0.22);
}
.feedback-item:first-child {
  padding-top: 0;
  border-top: 0;
}
.feedback-item:last-child {
  padding-bottom: 0;
}
.feedback-head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.feedback-date {
  margin-left: auto;
  color: #8a7a70;
  font: 400 10px/1.5 var(--sans);
}
.feedback-content {
  margin-top: 8px;
  color: #4a3228;
  font: 400 13px/1.85 var(--sans);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.feedback-reply {
  margin-top: 10px;
  padding: 10px 12px;
  border-left: 2px solid #c8a96e;
  border-radius: 0 8px 8px 0;
  background: rgba(200, 169, 110, 0.1);
}
.feedback-reply b {
  display: block;
  color: #8a6125;
  font: 500 11px/1.5 var(--sans);
  letter-spacing: 1px;
}
.feedback-reply small {
  display: block;
  margin-top: 4px;
  color: #8a7a70;
  font: 400 10px/1.5 var(--sans);
}
.class-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 14px;
}
.class-card {
  padding: 14px;
}
.class-card h2 {
  color: #2d1810;
  font: 500 14px/1.5 var(--sans);
  overflow-wrap: anywhere;
}
.class-card .subtle {
  margin-top: 4px;
  color: #8a7a70;
  font: 400 10px/1.5 var(--sans);
}
.class-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
.class-actions .outline-button {
  flex: 1;
}
.service-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.service-card {
  padding: 14px;
}
.service-card h2 {
  color: #2d1810;
  font: 500 14px/1.55 var(--sans);
  letter-spacing: 0.3px;
  overflow-wrap: anywhere;
}
.service-card > p {
  margin-top: 8px;
}
.service-card > p.subtle {
  color: #8a7a70;
  font: 400 11px/1.7 var(--sans);
}
.service-caption {
  color: #8a7a70;
  font: 400 10px/1.6 var(--sans);
  letter-spacing: 0.5px;
}
.submission-content {
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(200, 169, 110, 0.12);
  color: #4a3228;
  font: 400 12px/1.85 var(--sans);
  white-space: pre-line;
}
.review-score {
  color: #8b1a1a;
  font: 500 18px/1.4 var(--serif);
}
.order-price {
  display: block;
  margin-top: 10px;
  color: #8b1a1a;
  font: 500 20px/1.3 var(--serif);
  letter-spacing: 0.5px;
}
.service-page .outline-button,
.service-sheet .outline-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 34px;
  padding: 0 14px;
  border: 1px solid rgba(139, 26, 26, 0.24);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.55);
  color: #8b1a1a;
  font: 500 11px/1 var(--sans);
  letter-spacing: 0.5px;
  white-space: nowrap;
}
.service-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
.service-actions .outline-button {
  flex: 1;
  margin: 0;
}
.service-card > .outline-button {
  width: 100%;
  margin-top: 12px;
}
.contest-badge {
  display: inline-block;
  margin-right: 6px;
  padding: 2px 7px;
  border-radius: 4px;
  background: linear-gradient(135deg, #a33a3a, #8b1a1a);
  color: #f6ead9;
  font: 500 10px/1.5 var(--sans);
  vertical-align: middle;
}
.follow-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
}
.follow-row img,
.small-avatar {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  border-radius: 50%;
  object-fit: cover;
}
.small-avatar {
  display: grid;
  place-items: center;
  background: #8b1a1a;
  color: #f6ead9;
  font: 400 16px/1 var(--serif);
}
.follow-row h3 {
  color: #2d1810;
  font: 500 14px/1.5 var(--sans);
}
.saved-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
}
.saved-item:active {
  background: #fbf4ea;
}
.saved-item img {
  width: 68px;
  height: 68px;
  flex-shrink: 0;
  border-radius: 8px;
  object-fit: cover;
  background: #f0e3d6;
}
.saved-copy {
  min-width: 0;
}
.saved-item h3 {
  color: #2d1810;
  font: 500 13px/1.6 var(--sans);
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}
.saved-item p {
  margin-top: 4px;
  color: #8a7a70;
  font: 400 10px/1.5 var(--sans);
}
.service-sheet h2 {
  margin: 4px 0 14px;
  color: #2d1810;
  font: 500 20px/1.3 var(--serif);
  letter-spacing: 2px;
}
.service-sheet form {
  gap: 12px;
  margin-top: 14px;
}
.service-sheet .primary-button {
  width: 100%;
}
</style>

