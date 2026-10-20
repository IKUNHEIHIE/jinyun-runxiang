<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import { api, post, mediaUrl, requireSession, notify, session } from "../api";
import { categoryName, designIcon } from "../design";
import { Capacitor } from "@capacitor/core";
import { saveAsset } from "../files";
import AsyncState from "../components/AsyncState.vue";
import PageHeader from "../components/PageHeader.vue";
import SectionCard from "../components/SectionCard.vue";
import SkeletonImage from "../components/SkeletonImage.vue";
import { formatDate } from "../dates";
const route = useRoute(),
  artwork = ref<any>(),
  loading = ref(true),
  error = ref(""),
  comment = ref(""),
  busy = ref(false);
const collected = ref(false),
  following = ref(false),
  replyTo = ref<number>(),
  replyName = ref(""),
  reportVisible = ref(false),
  reason = ref("侵犯版权或不当内容");
const galleryIndex = ref(0),
  comments = ref<any[]>([]),
  commentPage = ref(1),
  commentTotal = ref(0),
  moreLoading = ref(false),
  related = ref<any[]>([]),
  likingComment = ref<number>(),
  editingComment = ref(false),
  commentField = ref<HTMLTextAreaElement>();
const relatedError = ref("");
const gallery = computed<string[]>(() =>
  artwork.value?.gallery?.length
    ? artwork.value.gallery
    : artwork.value?.cover_url
      ? [artwork.value.cover_url]
      : [],
);
let loadVersion = 0,
  swipeStart: { x: number; y: number } | undefined;
let alive = true;
function context() {
  const version = loadVersion, token = session.token, id = String(route.params.id);
  return () => alive && version === loadVersion && token === session.token && id === String(route.params.id);
}
onUnmounted(() => { alive = false; ++loadVersion; });
function photoSwipe(event: PointerEvent) {
  if (!swipeStart) return;
  const dx = event.clientX - swipeStart.x,
    dy = event.clientY - swipeStart.y;
  swipeStart = undefined;
  if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.3)
    galleryIndex.value = Math.max(
      0,
      Math.min(
        gallery.value.length - 1,
        galleryIndex.value + (dx < 0 ? 1 : -1),
      ),
    );
}
async function loadComments(page = 1) {
  if (moreLoading.value) return;
  const id = String(route.params.id);
  const current = context();
  moreLoading.value = true;
  try {
    const result = await api(
      `/community/posts/${id}/comments?page=${page}&pageSize=20`,
    );
    if (!current()) return;
    comments.value =
      page === 1
        ? result.list
        : [
            ...comments.value,
            ...result.list.filter(
              (c: any) =>
                !comments.value.some((existing) => existing.id === c.id),
            ),
          ];
    commentTotal.value = result.total;
    commentPage.value = page;
    artwork.value.comment_count = result.total;
  } catch (e) {
    if (current()) notify((e as Error).message);
  } finally {
    if (current()) moreLoading.value = false;
  }
}
async function likeComment(record: any) {
  if (!requireSession() || likingComment.value) return;
  const current = context();
  likingComment.value = record.id;
  try {
    const result = await post(`/community/comments/${record.id}/like`);
    if (current()) Object.assign(record, result);
  } catch (e) {
    if (current()) notify((e as Error).message);
  } finally {
    if (current()) likingComment.value = undefined;
  }
}
function reply(record: any) {
  replyTo.value = record.id;
  replyName.value = record.user.nickname;
  commentField.value?.focus();
}
async function loadRelated() {
  const current = context(), id = artwork.value?.id;
  if (!id || artwork.value.status !== "APPROVED") return;
  relatedError.value = "";
  try {
    const rows = await api(`/community/posts/${id}/related`);
    if (current()) related.value = rows;
  } catch (e) {
    if (current()) relatedError.value = (e as Error).message;
  }
}
async function load() {
  ++loadVersion;
  const current = context();
  loading.value = true;
  error.value = "";
  galleryIndex.value = 0;
  collected.value = false;
  following.value = false;
  comments.value = [];
  related.value = [];
  relatedError.value = "";
  replyTo.value = undefined;
  replyName.value = "";
  moreLoading.value = false; likingComment.value = undefined; busy.value = false;
  reportVisible.value = false;
  try {
    const detail = await api("/community/posts/" + route.params.id);
    if (!current()) return;
    artwork.value = detail;
    comments.value = detail.comments;
    commentTotal.value = detail.comment_count;
    commentPage.value = 1;
    collected.value = detail.is_collected;
    following.value = detail.is_following;
    void loadRelated();
  } catch (e) {
    if (current()) error.value = (e as Error).message;
  } finally {
    if (current()) loading.value = false;
  }
}
async function like() {
  if (!requireSession() || busy.value) return;
  const current = context();
  busy.value = true;
  try {
    const r = await post("/community/posts/" + artwork.value.id + "/like");
    if (!current()) return;
    artwork.value.is_liked = r.is_liked;
    artwork.value.like_count = r.like_count;
  } catch (e) {
    if (current()) notify((e as Error).message);
  } finally {
    if (current()) busy.value = false;
  }
}
async function collect() {
  if (!requireSession() || busy.value) return;
  const current = context();
  busy.value = true;
  try {
    const result = await post("/mobile/collections/POST/" + artwork.value.id);
    if (!current()) return;
    collected.value = result.collected;
    notify(collected.value ? "已收藏作品" : "已取消收藏");
  } catch (e) {
    if (current()) notify((e as Error).message);
  } finally {
    if (current()) busy.value = false;
  }
}
async function follow() {
  if (!requireSession() || busy.value) return;
  const current = context();
  busy.value = true;
  try {
    const result = await post("/mobile/users/" + artwork.value.author.id + "/follow");
    if (current()) following.value = result.following;
  } catch (e) {
    if (current()) notify((e as Error).message);
  } finally {
    if (current()) busy.value = false;
  }
}
async function sendComment() {
  if (!requireSession() || busy.value) return;
  if (!comment.value.trim()) { notify("请先写下你的想法"); return; }
  const current = context();
  busy.value = true;
  try {
    await post("/community/posts/" + artwork.value.id + "/comments", {
      content: comment.value.trim(),
      reply_to_id: replyTo.value,
    });
    if (!current()) return;
    comment.value = "";
    replyTo.value = undefined;
    replyName.value = "";
    await loadComments(1);
    if (current()) notify("评论已发布");
  } catch (e) {
    if (current()) notify((e as Error).message);
  } finally {
    if (current()) busy.value = false;
  }
}
function openComments() {
  document
    .getElementById("comments")
    ?.scrollIntoView({ block: "start", behavior: "smooth" });
}
async function share() {
  try {
    if (Capacitor.isNativePlatform() && !import.meta.env.VITE_PUBLIC_SITE_URL) {
      await saveAsset(
        artwork.value.cover_url,
        artwork.value.title +
          (artwork.value.cover_url.endsWith(".svg") ? ".svg" : ".png"),
      );
      return;
    }
    const shareUrl = new URL(
      "/#/community/" + artwork.value.id,
      import.meta.env.VITE_PUBLIC_SITE_URL || window.location.origin,
    ).href;
    if (navigator.share)
      await navigator.share({
        title: artwork.value.title,
        text: artwork.value.content,
        url: shareUrl,
      });
    else {
      await navigator.clipboard.writeText(shareUrl);
      notify("作品链接已复制");
    }
  } catch (e) {
    if ((e as Error).name !== "AbortError") notify("暂时无法分享，请稍后重试");
  }
}
async function report() {
  if (!requireSession() || busy.value) return;
  const current = context();
  busy.value = true;
  try {
    await post("/community/reports", {
      post_id: artwork.value.id,
      reason: reason.value,
    });
    if (!current()) return;
    reportVisible.value = false;
    notify("举报已提交审核");
  } catch (e) {
    if (current()) notify((e as Error).message);
  } finally {
    if (current()) busy.value = false;
  }
}
watch(() => [route.params.id, session.token], () => {
  comment.value = ""; editingComment.value = false;
  void load();
}, { immediate: true });
</script>
<template>
  <div
    class="artwork-detail"
    :class="{ 'comment-editing': editingComment }"
    data-design-node="5:5591"
  >
    <PageHeader title="作品详情" back-to="/community">
      <span v-if="artwork && !loading && !error" class="header-actions">
        <button
          aria-label="收藏作品"
          :aria-pressed="collected"
          :disabled="busy"
          @click="collect"
        >
          <img :src="designIcon('layer-5-5591', '5:6094')" alt="" />
        </button>
        <button aria-label="分享作品" @click="share">
          <img :src="designIcon('layer-5-5591', '5:6098')" alt="" />
        </button>
      </span>
    </PageHeader>
    <AsyncState :loading="loading" :error="error" @retry="load"
      ><template v-if="artwork">
        <div class="artwork-body">
          <p v-if="artwork.status !== 'APPROVED'" class="private-artwork-note">
            {{
              artwork.status === "PENDING_REVIEW"
                ? "作品审核中，当前为本人预览"
                : "当前作品尚未公开"
            }}
          </p>
          <div
            class="artwork-hero corner-card"
            @pointerdown="
              swipeStart = { x: $event.clientX, y: $event.clientY }
            "
            @pointerup="photoSwipe"
            @pointercancel="swipeStart = undefined"
          >
            <SkeletonImage
              :src="gallery[galleryIndex]"
              :alt="artwork.title + ' · ' + (galleryIndex + 1)"
              ratio="343 / 420"
              eager
              class="artwork-cover"
            /><span class="gallery-count"
              >{{ galleryIndex + 1 }}/{{ gallery.length }}</span
            >
            <template v-if="gallery.length > 1"
              ><button
                class="gallery-previous"
                aria-label="上一张作品图片"
                :disabled="galleryIndex === 0"
                @click="galleryIndex--"
              >
                ‹</button
              ><button
                class="gallery-next"
                aria-label="下一张作品图片"
                :disabled="galleryIndex === gallery.length - 1"
                @click="galleryIndex++"
              >
                ›
              </button></template
            >
          </div>
          <SectionCard class="artwork-heading">
            <div class="artwork-title-row">
              <h1>{{ artwork.title }}</h1>
              <span class="artwork-category">{{
                categoryName(artwork.category)
              }}</span>
            </div>
            <div class="artwork-author">
              <img
                v-if="artwork.author.avatar_url"
                :src="mediaUrl(artwork.author.avatar_url)"
                alt=""
              /><span v-else class="author-initial">{{
                artwork.author.nickname.slice(0, 1)
              }}</span>
              <div>
                <h3>{{ artwork.author.nickname }}</h3>
                <p>{{ formatDate(artwork.created_at) }}</p>
              </div>
              <button
                v-if="artwork.author.id !== session.profile?.id"
                class="outline-button"
                :aria-pressed="following"
                @click="follow"
              >
                {{ following ? "已关注" : "关注" }}
              </button>
            </div>
            <div class="artwork-counts">
              <button
                :aria-pressed="artwork.is_liked"
                :disabled="busy || artwork.status !== 'APPROVED'"
                @click="like"
              >
                <img
                  :src="
                    designIcon(
                      'layer-5-5591',
                      artwork.is_liked ? '5:5793' : '5:6128',
                    )
                  "
                  alt="点赞"
                />
                {{ artwork.like_count }}</button
              ><button @click="openComments">
                <img :src="designIcon('layer-5-5591', '5:5806')" alt="评论" />
                {{ artwork.comment_count }}</button
              ><span>浏览 {{ artwork.view_count }}</span>
            </div>
          </SectionCard>
          <SectionCard class="artwork-description" title="作品简介">
            <p class="artwork-description-text">
              {{ artwork.content || "作者尚未填写作品简介" }}
            </p>
            <dl
              v-if="artwork.specifications?.length"
              class="artwork-specifications"
            >
              <div v-for="spec in artwork.specifications" :key="spec.label">
                <dt>{{ spec.label }}</dt>
                <dd>{{ spec.value }}</dd>
              </div>
            </dl>
          </SectionCard>
          <SectionCard
            v-if="artwork.appreciation?.length"
            class="artwork-appreciation"
            title="鉴赏要点"
          >
            <article
              v-for="(point, index) in artwork.appreciation"
              :key="index"
            >
              <span>{{ index + 1 }}</span>
              <p>
                <strong>{{ point.title }}：</strong>{{ point.body }}
              </p>
            </article>
          </SectionCard>
          <SectionCard id="comments" class="artwork-comments" title="评论">
            <template #meta>
              <small class="comment-total">({{ artwork.comment_count }})</small>
              <button
                v-if="comments.length < commentTotal"
                class="text-button comment-more-link"
                :disabled="moreLoading"
                @click="loadComments(commentPage + 1)"
              >
                {{ moreLoading ? "加载中…" : "查看全部" }}</button
              ><span v-else class="comment-latest">最新留言</span>
            </template>
            <article v-for="c in comments" :key="c.id" class="comment-row">
              <img
                v-if="c.user.avatar_url"
                class="comment-avatar"
                :src="mediaUrl(c.user.avatar_url)"
                alt=""
              /><span v-else class="comment-avatar">{{
                c.user.nickname.slice(0, 1)
              }}</span>
              <div>
                <h3>
                  {{ c.user.nickname }}
                  <small v-if="c.user.id === artwork.author.id">作者</small>
                </h3>
                <small>{{ formatDate(c.created_at) }}</small>
                <blockquote v-if="c.reply_to">
                  回复 {{ c.reply_to.nickname }}：{{ c.reply_to.content }}
                </blockquote>
                <p>{{ c.content }}</p>
                <button
                  :disabled="artwork.status !== 'APPROVED'"
                  @click="reply(c)"
                >
                  回复
                </button>
                <button
                  class="comment-like"
                  :aria-pressed="c.is_liked"
                  :disabled="!!likingComment || artwork.status !== 'APPROVED'"
                  @click="likeComment(c)"
                >
                  {{ c.is_liked ? "♥" : "♡" }} {{ c.like_count }}
                </button>
              </div>
            </article>
            <p v-if="!comments.length" class="subtle comment-empty">
              还没有评论，聊聊你的鉴赏感受吧
            </p>
            <button
              v-if="comments.length < commentTotal"
              class="outline-button more-comments"
              :disabled="moreLoading"
              @click="loadComments(commentPage + 1)"
            >
              {{ moreLoading ? "加载中…" : "加载更多评论" }}
            </button>
            <form
              v-if="artwork.status === 'APPROVED'"
              class="comment-form"
              @submit.prevent="sendComment"
            >
              <label
                >{{ replyName ? "回复 " + replyName : "留下你的鉴赏感受"
                }}<textarea
                  v-model.trim="comment"
                  ref="commentField"
                  @focus="editingComment = true"
                  @blur="editingComment = false"
                  required
                  maxlength="1000"
                /></label
              ><button class="primary-button" :disabled="busy">发布评论</button
              ><button
                v-if="replyTo"
                type="button"
                class="text-button"
                @click="
                  replyTo = undefined;
                  replyName = '';
                "
              >
                取消回复
              </button>
            </form>
          </SectionCard>
          <SectionCard
            v-if="related.length || relatedError"
            class="related-artworks"
            title="相关推荐"
          >
            <p v-if="relatedError" class="form-error">
              {{ relatedError }}
              <button class="text-button" @click="loadRelated">重试</button>
            </p>
            <div class="related-scroll">
              <RouterLink
                v-for="item in related"
                :key="item.id"
                :to="'/community/' + item.id"
                ><SkeletonImage
                  :src="item.cover_url"
                  :alt="item.title"
                  class="related-cover"
                />
                <h3>{{ item.title }}</h3>
                <p>{{ item.author }}</p></RouterLink
              >
            </div>
          </SectionCard>
          <button
            v-if="artwork.status === 'APPROVED'"
            class="text-button report-toggle"
            @click="reportVisible = !reportVisible"
          >
            举报不当内容
          </button>
          <form
            v-if="reportVisible"
            class="report-form"
            @submit.prevent="report"
          >
            <label
              >举报原因<textarea
                v-model.trim="reason"
                :disabled="busy"
                required
                maxlength="64"
              /></label
            ><button class="outline-button" :disabled="busy">{{
              busy ? "正在提交…" : "提交举报"
            }}</button>
          </form>
        </div>
        <div class="artwork-actions">
          <button
            :aria-pressed="artwork.is_liked"
            :disabled="busy || artwork.status !== 'APPROVED'"
            @click="like"
          >
            <img
              :src="
                designIcon(
                  'layer-5-5591',
                  artwork.is_liked ? '5:5793' : '5:6128',
                )
              "
              alt="点赞"
            /><span>{{ artwork.like_count }}</span>
          </button>
          <button @click="openComments">
            <img :src="designIcon('layer-5-5591', '5:6116')" alt="" /><span
              >评论</span
            >
          </button>
          <button :aria-pressed="collected" :disabled="busy" @click="collect">
            <img :src="designIcon('layer-5-5591', '5:6120')" alt="" /><span>{{
              collected ? "已收藏" : "收藏"
            }}</span></button
          ><button @click="share">
            <img :src="designIcon('layer-5-5591', '5:6140')" alt="" /><span
              >分享</span
            >
          </button>
        </div></template
      ></AsyncState
    >
  </div>
</template>
<style scoped>
.artwork-detail {
  min-height: 100dvh;
  padding-bottom: calc(69px + var(--safe-bottom));
  background: #f5ede4;
  color: #2d1810;
}
.artwork-body {
  padding: 14px 16px 24px;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}
.header-actions button {
  width: 32px;
  height: 32px;
  padding: 6px;
  border: 1px solid rgba(200, 169, 110, 0.45);
  border-radius: 50%;
  background: rgba(255, 253, 248, 0.8);
}
.header-actions img {
  width: 18px;
  height: 18px;
}
.private-artwork-note {
  margin-bottom: 14px;
  padding: 8px 12px;
  border: 1px solid rgba(200, 169, 110, 0.35);
  border-radius: 10px;
  background: rgba(200, 169, 110, 0.14);
  color: #8a6125;
  font: 400 11px/1.7 var(--sans);
}
.artwork-hero {
  position: relative;
  margin-bottom: 14px;
  border-radius: 14px;
  background: #f1e5d6;
  touch-action: pan-y;
}
.artwork-hero > .artwork-cover {
  border-radius: 14px;
}
.artwork-hero > .gallery-count {
  position: absolute;
  right: 12px;
  bottom: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(45, 24, 16, 0.62);
  color: #f6ead9;
  font: 400 10px/1.4 var(--sans);
  letter-spacing: 0.5px;
}
.gallery-previous,
.gallery-next {
  position: absolute;
  top: 45%;
  width: 30px;
  height: 40px;
  padding: 0;
  border-radius: 8px;
  background: rgba(45, 24, 16, 0.45);
  color: #f6ead9;
  font-size: 22px;
  line-height: 1;
}
.gallery-previous {
  left: 10px;
}
.gallery-next {
  right: 10px;
}
.gallery-previous:disabled,
.gallery-next:disabled {
  opacity: 0.3;
}
.artwork-heading {
  padding: 16px 14px 12px;
}
.artwork-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}
.artwork-heading h1 {
  margin: 0;
  color: #2d1810;
  font: 500 16px/1.5 var(--serif);
  letter-spacing: 1px;
  overflow-wrap: anywhere;
}
.artwork-category {
  flex-shrink: 0;
  padding: 2px 8px;
  border: 1px solid rgba(200, 169, 110, 0.42);
  border-radius: 999px;
  background: rgba(200, 169, 110, 0.14);
  color: #8a6125;
  font: 400 10px/1.6 var(--sans);
  white-space: nowrap;
}
.artwork-author {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
}
.artwork-author > img,
.author-initial {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border-radius: 50%;
  object-fit: cover;
}
.author-initial {
  display: grid;
  place-items: center;
  background: #8b1a1a;
  color: #f6ead9;
  font: 400 14px/1 var(--serif);
}
.artwork-author > div {
  flex: 1;
  min-width: 0;
}
.artwork-author h3 {
  color: #2d1810;
  font: 500 13px/1.4 var(--sans);
}
.artwork-author p {
  margin-top: 2px;
  color: #8a7a70;
  font: 400 10px/1.5 var(--sans);
}
.artwork-author > .outline-button {
  min-height: 28px;
  padding: 0 12px;
  border: 0;
  border-radius: 999px;
  background: #8b1a1a;
  color: #f6ead9;
  font: 500 11px/1 var(--sans);
}
.artwork-author > .outline-button[aria-pressed="true"] {
  border: 1px solid rgba(200, 169, 110, 0.5);
  background: rgba(200, 169, 110, 0.14);
  color: #8a6125;
}
.artwork-counts {
  display: flex;
  justify-content: space-around;
  align-items: center;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(200, 169, 110, 0.24);
  color: #8a7a70;
  font: 400 11px/1.5 var(--sans);
}
.artwork-counts button {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 0;
  color: #5a3e36;
  font: 400 11px/1.5 var(--sans);
}
.artwork-counts img {
  width: 15px;
  height: 15px;
}
.artwork-counts button[aria-pressed="true"] {
  color: #8b1a1a;
}
.artwork-description {
  padding: 16px 14px 14px;
}
.artwork-description-text {
  margin: 0;
  color: #5a3e36;
  font: 400 13px/1.9 var(--sans);
  white-space: pre-line;
  overflow-wrap: anywhere;
}
.artwork-specifications {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin: 12px 0 0;
}
.artwork-specifications > div {
  min-height: 56px;
  padding: 9px 10px;
  border: 1px solid rgba(200, 169, 110, 0.22);
  border-radius: 10px;
  background: #fffdf8;
}
.artwork-specifications dt {
  margin-bottom: 3px;
  color: #8a7a70;
  font: 400 10px/1.5 var(--sans);
}
.artwork-specifications dd {
  margin: 0;
  color: #2d1810;
  font: 500 13px/1.5 var(--sans);
  overflow-wrap: anywhere;
}
.artwork-appreciation article {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-top: 10px;
}
.artwork-appreciation article:first-child {
  margin-top: 0;
}
.artwork-appreciation article > span {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: rgba(200, 169, 110, 0.18);
  color: #8a6125;
  font: 500 10px/1 var(--sans);
}
.artwork-appreciation p {
  color: #5a3e36;
  font: 400 13px/1.9 var(--sans);
}
.artwork-appreciation strong {
  color: #8b1a1a;
  font-weight: 500;
}
.artwork-comments {
  scroll-margin-top: 12px;
}
.comment-total {
  flex-shrink: 0;
  color: #8a7a70;
  font: 400 10px/1.4 var(--sans);
}
.comment-more-link {
  flex-shrink: 0;
  padding: 0;
  color: #8b1a1a;
  font-size: 10px;
}
.comment-latest {
  flex-shrink: 0;
  color: #8a7a70;
  font: 400 10px/1.4 var(--sans);
}
.comment-row {
  display: flex;
  gap: 10px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(200, 169, 110, 0.18);
}
.comment-row:last-of-type {
  border-bottom: 0;
}
.comment-avatar {
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: rgba(200, 169, 110, 0.18);
  color: #8a6125;
  font: 400 11px/1 var(--sans);
  object-fit: cover;
}
.comment-row > div {
  flex: 1;
  min-width: 0;
}
.comment-row h3 {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #2d1810;
  font: 500 12px/1.4 var(--sans);
}
.comment-row h3 small {
  padding: 1px 5px;
  border: 1px solid rgba(139, 26, 26, 0.22);
  border-radius: 4px;
  color: #8b1a1a;
  font: 400 9px/1.4 var(--sans);
}
.comment-row small {
  color: #8a7a70;
  font: 400 10px/1.4 var(--sans);
}
.comment-row blockquote {
  margin: 6px 0;
  padding: 6px 10px;
  border-left: 2px solid rgba(200, 169, 110, 0.55);
  border-radius: 0 6px 6px 0;
  background: #f7efe3;
  color: #8a7a70;
  font: 400 11px/1.7 var(--sans);
}
.comment-row p {
  margin-top: 4px;
  color: #5a3e36;
  font: 400 13px/1.85 var(--sans);
  overflow-wrap: anywhere;
}
.comment-row button {
  padding: 6px 0 0;
  color: #8a6125;
  font: 400 10px/1.4 var(--sans);
}
.comment-row .comment-like {
  margin-left: 16px;
}
.comment-like[aria-pressed="true"] {
  color: #8b1a1a;
}
.comment-empty {
  padding: 8px 0 12px;
  text-align: center;
}
.more-comments {
  display: block;
  margin: 12px auto 0;
  min-height: 36px;
  padding: 6px 16px;
  border-color: rgba(200, 169, 110, 0.5);
  border-radius: 999px;
  color: #8a6125;
  font-size: 11px;
}
.comment-form {
  margin-top: 14px;
  gap: 10px;
}
.comment-form label {
  color: #5a3e36;
  font: 400 11px/1.6 var(--sans);
}
.comment-form textarea {
  min-height: 84px;
  border-color: rgba(200, 169, 110, 0.42);
  border-radius: 10px;
  background: #fffdf8;
  font-size: 13px;
}
.comment-form .primary-button {
  min-height: 40px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: #8b1a1a;
  color: #f6ead9;
  font-size: 12px;
}
.comment-form .text-button {
  align-self: center;
  padding: 4px;
  color: #8a7a70;
  font-size: 11px;
}
.related-artworks > p {
  margin-bottom: 8px;
  font-size: 11px;
}
.related-scroll {
  display: flex;
  gap: 10px;
  margin: 0 -14px;
  padding: 0 14px 2px;
  overflow-x: auto;
  scrollbar-width: none;
}
.related-scroll::-webkit-scrollbar {
  display: none;
}
.related-scroll a {
  flex: 0 0 132px;
  overflow: hidden;
  border: 1px solid rgba(200, 169, 110, 0.28);
  border-radius: 10px;
  background: #fffdf8;
}
.related-scroll .related-cover {
  height: 108px;
}
.related-scroll h3 {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  padding: 6px 8px 0;
  color: #2d1810;
  font: 500 11px/1.6 var(--sans);
}
.related-scroll p {
  padding: 2px 8px 8px;
  color: #8a7a70;
  font: 400 10px/1.5 var(--sans);
}
.artwork-actions {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  z-index: 30;
  display: flex;
  justify-content: space-around;
  width: min(100%, 480px);
  padding: 6px 16px calc(6px + var(--safe-bottom));
  background: rgba(250, 245, 240, 0.97);
  border-top: 1px solid rgba(200, 169, 110, 0.35);
  box-shadow: 0 -6px 20px rgba(70, 42, 26, 0.07);
  -webkit-backdrop-filter: blur(10px);
  backdrop-filter: blur(10px);
}
.artwork-actions > * {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  min-width: 44px;
  height: 44px;
  padding: 0;
  font: 400 10px/15px var(--sans);
  color: #8a7a70;
}
.artwork-actions img {
  width: 19px;
  height: 19px;
}
.artwork-actions [aria-pressed="true"],
.header-actions [aria-pressed="true"] {
  color: #8b1a1a;
}
.artwork-actions [aria-pressed="true"] img,
.header-actions [aria-pressed="true"] img {
  filter: sepia(1) saturate(2);
}
.artwork-actions [aria-pressed="true"]:first-child img {
  filter: none;
}
.comment-editing .artwork-actions {
  display: none;
}
.artwork-comments textarea {
  scroll-margin: 24px 0 80px;
}
.report-toggle {
  display: block;
  margin: 0 auto 14px;
  padding: 4px;
  color: #8a7a70;
  font-size: 11px;
}
.report-form {
  margin-bottom: 14px;
  padding: 12px;
  border: 1px solid rgba(200, 169, 110, 0.35);
  border-radius: 12px;
  background: #fffdf8;
  gap: 10px;
}
.report-form label {
  color: #5a3e36;
  font: 400 11px/1.6 var(--sans);
}
.report-form textarea {
  min-height: 72px;
  border-color: rgba(200, 169, 110, 0.4);
  border-radius: 10px;
  background: #fdf9f2;
  font-size: 12px;
}
.report-form .outline-button {
  min-height: 38px;
  border-color: rgba(200, 169, 110, 0.55);
  border-radius: 10px;
  color: #8a6125;
  font-size: 12px;
}
</style>
