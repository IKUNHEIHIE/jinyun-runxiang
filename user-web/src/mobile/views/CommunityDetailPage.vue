<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import { api, post, mediaUrl, requireSession, notify, session } from "../api";
import { categoryName, designIcon } from "../design";
import { Capacitor } from "@capacitor/core";
import { saveAsset } from "../files";
import AsyncState from "../components/AsyncState.vue";
import PageHeader from "../components/PageHeader.vue";
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
const galleryLandscape = ref(false);
function galleryLoaded(event: Event) {
  const image = event.target as HTMLImageElement;
  galleryLandscape.value = image.naturalWidth > image.naturalHeight;
}
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
  galleryLandscape.value = false;
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
    <PageHeader title="作品详情">
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
      </span> </PageHeader
    ><AsyncState :loading="loading" :error="error" @retry="load"
      ><template v-if="artwork"
        ><p v-if="artwork.status !== 'APPROVED'" class="private-artwork-note">
          {{
            artwork.status === "PENDING_REVIEW"
              ? "作品审核中，当前为本人预览"
              : "当前作品尚未公开"
          }}
        </p>
        <div
          class="artwork-hero"
          @pointerdown="swipeStart = { x: $event.clientX, y: $event.clientY }"
          @pointerup="photoSwipe"
          @pointercancel="swipeStart = undefined"
        >
          <img
            :src="mediaUrl(gallery[galleryIndex])"
            :class="{ landscape: galleryLandscape }"
            @load="galleryLoaded"
            :alt="artwork.title + ' · ' + (galleryIndex + 1)"
            draggable="false"
          /><span>{{ galleryIndex + 1 }}/{{ gallery.length }}</span>
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
        <div class="page-padding">
          <header class="artwork-heading">
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
          </header>
          <div class="artwork-information">
            <section class="artwork-description">
              <h2>作品简介</h2>
              <p>{{ artwork.content || "作者尚未填写作品简介" }}</p>
            </section>
            <dl
              v-if="artwork.specifications?.length"
              class="artwork-specifications"
            >
              <div v-for="spec in artwork.specifications" :key="spec.label">
                <dt>{{ spec.label }}</dt>
                <dd>{{ spec.value }}</dd>
              </div>
            </dl>
            <section
              v-if="artwork.appreciation?.length"
              class="artwork-appreciation"
            >
              <h2>鉴赏要点</h2>
              <article
                v-for="(point, index) in artwork.appreciation"
                :key="index"
              >
                <span>{{ index + 1 }}</span>
                <p>
                  <strong>{{ point.title }}：</strong>{{ point.body }}
                </p>
              </article>
            </section>
          </div>
          <section id="comments" class="artwork-comments">
            <div class="section-heading">
              <h2>
                评论 <small>({{ artwork.comment_count }})</small>
              </h2>
              <button
                v-if="comments.length < commentTotal"
                class="text-button"
                :disabled="moreLoading"
                @click="loadComments(commentPage + 1)"
              >
                {{ moreLoading ? "加载中…" : "查看全部" }}</button
              ><span v-else>最新留言</span>
            </div>
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
            <p v-if="!comments.length" class="subtle">
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
          </section>
          <section
            v-if="related.length || relatedError"
            class="related-artworks"
          >
            <h2>相关推荐</h2>
            <p v-if="relatedError" class="form-error">
              {{ relatedError }}
              <button class="text-button" @click="loadRelated">重试</button>
            </p>
            <div>
              <RouterLink
                v-for="item in related"
                :key="item.id"
                :to="'/community/' + item.id"
                ><img :src="mediaUrl(item.cover_url)" :alt="item.title" />
                <h3>{{ item.title }}</h3>
                <p>{{ item.author }}</p></RouterLink
              >
            </div>
          </section>
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
          </div>
          <button
            v-if="artwork.status === 'APPROVED'"
            class="text-button"
            @click="reportVisible = !reportVisible"
          >
            举报不当内容
          </button>
          <form v-if="reportVisible" @submit.prevent="report">
            <label
              >举报原因<textarea
                v-model.trim="reason"
              :disabled="busy"
                required
                maxlength="64"
              /></label
            ><button class="outline-button" :disabled="busy">{{ busy ? '正在提交…' : '提交举报' }}</button>
          </form>
        </div></template
      ></AsyncState
    >
  </div>
</template>
<style scoped>
.artwork-hero {
  position: relative;
  background: #fff;
  margin: 12px 16px;
  border-radius: 12px;
  overflow: hidden;
  touch-action: pan-y;
}
.artwork-detail {
  min-height: calc(100dvh - var(--safe-top));
  padding-bottom: calc(69px + var(--safe-bottom));
  background: #e4d4c3;
  color: #333;
}
.artwork-detail .page-padding {
  padding: 0 16px 24px;
}
.artwork-detail :deep(.page-header) {
  height: 49px;
  padding: 0 16px 0 8px;
  gap: 0;
  background: rgba(245, 240, 235, 0.9);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}
.artwork-detail :deep(.page-header > div) {
  flex: 1;
  text-align: center;
}
.artwork-detail :deep(.page-header h1) {
  font-size: 16px;
  font-weight: 600;
  line-height: 24px;
  letter-spacing: 0.4px;
}
.header-actions {
  display: flex;
  width: 80px;
}
.header-actions button {
  width: 40px;
  height: 40px;
  padding: 10px;
}
.header-actions img {
  width: 20px;
  height: 20px;
}
.artwork-heading,
.artwork-information,
.artwork-comments {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}
.artwork-information {
  padding: 16px;
  margin-top: 12px;
}
.artwork-detail h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  font: 600 14px/20px var(--serif);
}
.artwork-detail h2::before {
  content: "";
  width: 4px;
  height: 16px;
  border-radius: 4px;
  background: #8b4513;
}
.private-artwork-note {
  font-size: 12px;
  line-height: 1.8;
  padding: 12px 16px;
  background: var(--gold-light);
}
.artwork-hero > img {
  aspect-ratio: 343 / 420;
  height: auto;
  width: 100%;
  object-fit: cover;
}
.artwork-hero > img.landscape {
  object-fit: contain;
}
.gallery-previous,
.gallery-next {
  position: absolute;
  top: 45%;
  width: 32px;
  height: 42px;
  border-radius: 8px;
  background: #3d231466;
  color: var(--paper);
  font-size: 27px;
  padding: 0;
}
.gallery-previous {
  left: 10px;
}
.gallery-next {
  right: 10px;
}
.gallery-previous:disabled,
.gallery-next:disabled {
  opacity: 0.25;
}
.artwork-specifications {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin: 16px 0 24px;
}
.artwork-specifications > div {
  min-height: 64px;
  padding: 12px;
  border-radius: 8px;
  background: #f5f0eb;
}
.artwork-specifications dt {
  font-size: 12px;
  color: #999;
  line-height: 16px;
  margin-bottom: 4px;
}
.artwork-specifications dd {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
  overflow-wrap: anywhere;
}
.artwork-appreciation {
  margin: 24px 0 0;
}
.artwork-appreciation article {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-top: 12px;
}
.artwork-appreciation article > span {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  background: #f5f0eb;
  font-size: 12px;
  color: #8b4513;
}
.artwork-appreciation p {
  font-size: 14px;
  line-height: 22px;
}
.artwork-appreciation strong {
  color: #8b4513;
  font-weight: 500;
}
.comment-row blockquote {
  margin: 12px 0;
  padding: 8px 12px;
  background: var(--track);
  border-left: 2px solid var(--gold-light);
  font-size: 11px;
  line-height: 1.7;
}
.comment-row .comment-like {
  margin-left: 20px;
}
.comment-like[aria-pressed="true"] {
  color: var(--cinnabar);
}
.more-comments {
  display: block;
  margin: 16px auto;
}
.related-artworks {
  padding: 18px 0 24px;
}
.related-artworks > div {
  display: flex;
  gap: 12px;
  overflow: auto;
  margin-top: 12px;
}
.related-artworks a {
  flex: 0 0 144px;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
}
.related-artworks img {
  width: 100%;
  height: 128px;
  object-fit: cover;
}
.related-artworks h3 {
  font-size: 12px;
  font-weight: 500;
  line-height: 1.8;
  padding: 10px 8px 0;
}
.related-artworks p {
  padding: 6px 8px 12px;
  font-size: 10px;
  color: var(--muted);
}
.artwork-hero > span {
  position: absolute;
  bottom: 16px;
  right: 20px;
  border-radius: 20px;
  background: rgba(61, 35, 20, 0.6);
  padding: 5px 12px;
  color: var(--paper);
  font-size: 11px;
}
.artwork-category {
  display: inline-block;
  flex-shrink: 0;
  font-size: 12px;
  line-height: 16px;
  color: #8b4513;
  padding: 4px 8px;
  background: #f5f0eb;
  border-radius: 12px;
}
.artwork-heading {
  padding: 16px 16px 0;
}
.artwork-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}
.artwork-heading h1 {
  font-size: 18px;
  font-weight: 700;
  line-height: 25px;
  margin: 0;
  overflow-wrap: anywhere;
}
.artwork-author {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}
.artwork-author > img,
.author-initial {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 50%;
  object-fit: cover;
}
.author-initial {
  display: grid;
  place-items: center;
  background: var(--coral);
  color: var(--paper);
  font-family: var(--serif);
}
.artwork-author > div {
  flex: 1;
}
.artwork-author h3 {
  font: 500 14px/20px var(--sans);
}
.artwork-author p {
  font-size: 12px;
  line-height: 16px;
  color: #999;
  margin-top: 4px;
}
.artwork-author > .outline-button {
  min-height: 34px;
  padding: 6px 16px;
  font-size: 11px;
  background: #8b4513;
  border: 0;
  color: #fff;
}
.artwork-counts {
  display: flex;
  justify-content: space-around;
  align-items: center;
  margin-top: 16px;
  padding: 16px 0;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  font-size: 14px;
  line-height: 20px;
  color: #525252;
}
.artwork-counts button {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  padding: 0;
}
.artwork-counts img {
  width: 16px;
  height: 16px;
}
.artwork-counts button[aria-pressed="true"] {
  color: var(--cinnabar);
}
.artwork-description {
  margin: 0;
}
.artwork-description p {
  margin-top: 12px;
  line-height: 22px;
  font-size: 14px;
  white-space: pre-line;
  overflow-wrap: anywhere;
}
.artwork-comments {
  scroll-margin-top: 24px;
  padding: 16px;
  margin: 12px 0 0;
}
.artwork-comments small {
  font-size: 11px;
  color: var(--muted);
}
.comment-row {
  display: flex;
  gap: 12px;
  padding: 18px 0;
  border-bottom: 1px solid var(--gold-light);
}
.comment-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--gold-light);
  color: var(--clay);
  font-size: 12px;
  flex-shrink: 0;
  object-fit: cover;
}
.comment-row > div {
  flex: 1;
  min-width: 0;
}
.comment-row h3 {
  font-size: 12px;
  margin-bottom: 5px;
}
.comment-row p {
  font-size: 14px;
  line-height: 22px;
  margin-top: 4px;
  overflow-wrap: anywhere;
}
.comment-row button {
  font-size: 10px;
  color: var(--clay);
  padding: 10px 0 0;
}
.artwork-comments form {
  margin-top: 24px;
}
.artwork-actions {
  display: flex;
  justify-content: space-around;
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: min(100%, 480px);
  padding: 6px 16px calc(6px + var(--safe-bottom));
  background: rgba(255, 255, 255, 0.95);
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  z-index: 30;
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
  color: #999;
}
.artwork-actions img {
  width: 20px;
  height: 20px;
}
.artwork-actions [aria-pressed="true"],
.header-actions [aria-pressed="true"] {
  color: #8b4513;
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
</style>
