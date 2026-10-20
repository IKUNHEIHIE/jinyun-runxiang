<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api, post, requireSession, notify, mediaUrl, session } from "../api";
import { saveProgress, progressState, syncProgress } from "../progress";
import { designImage, designIcon, categoryName } from "../design";
import AsyncState from "../components/AsyncState.vue";
import PageHeader from "../components/PageHeader.vue";
import SectionCard from "../components/SectionCard.vue";
const route = useRoute(),
  router = useRouter(),
  course = ref<any>(),
  loading = ref(true),
  error = ref(""),
  chapterIndex = ref(0);
const video = ref<HTMLVideoElement>(),
  videoError = ref(""),
  playing = ref(false),
  videoProgress = ref(0),
  quiz = ref<any>(),
  quizIndex = ref(0),
  answers = ref<Record<string, string[]>>({});
const quizResult = ref<any>(),
  saving = ref(false),
  collected = ref(false),
  rating = ref(5);
const currentChapter = computed(
  () => course.value?.chapters?.[chapterIndex.value],
);
const currentQuestion = computed(
  () => quiz.value?.questions?.[quizIndex.value],
);
const currentDetail = computed(() =>
  quizResult.value?.details?.find(
    (detail: any) => detail.question_id === currentQuestion.value?.id,
  ),
);
const teacherTitle = computed(() => "平台课程");
const teacherBio = computed(() => course.value?.subtitle || "课程简介待补充");
const quizImage = computed(
  () =>
    mediaUrl(course.value?.cover_url) ||
    designImage("layer-5-01018", "5:01170"),
);
const durationLabel = computed(() => {
  const seconds = Number(currentChapter.value?.duration_seconds || 0);
  if (!seconds) return "";
  return (
    String(Math.floor(seconds / 60)).padStart(2, "0") +
    ":" +
    String(seconds % 60).padStart(2, "0")
  );
});
let lastSaved = -1,
  playbackUserId: number | undefined,
  playbackToken = "",
  loadedToken = "",
  loadVersion = 0,
  mounted = true;
function resetPlayback() {
  playbackUserId = undefined;
  playbackToken = "";
  lastSaved = -1;
  playing.value = false;
  videoProgress.value = 0;
}
function beginPlayback() {
  if (loadedToken !== session.token) return;
  playbackUserId = session.profile?.id;
  playbackToken = session.token;
}
async function load() {
  const version = ++loadVersion,
    token = session.token,
    courseId = route.params.id;
  resetPlayback();
  video.value?.pause();
  loading.value = true;
  error.value = "";
  course.value = undefined;
  quiz.value = null;
  quizResult.value = null;
  quizIndex.value = 0;
  answers.value = {};
  collected.value = false;
  try {
    const nextCourse = await api("/courses/" + courseId);
    if (!mounted || version !== loadVersion || token !== session.token) return;
    const [nextQuiz, nextCollections] = await Promise.all([
      nextCourse.quiz_id ? api("/courses/quiz/" + nextCourse.quiz_id) : null,
      token ? api("/mobile/me/collections?kind=COURSE") : [],
    ]);
    if (!mounted || version !== loadVersion || token !== session.token) return;
    course.value = nextCourse;
    chapterIndex.value = 0;
    quiz.value = nextQuiz;
    collected.value = nextCollections.some((c: any) => c.id === nextCourse.id);
    loadedToken = token;
  } catch (e) {
    if (mounted && version === loadVersion && token === session.token)
      error.value = (e as Error).message;
  } finally {
    if (mounted && version === loadVersion) loading.value = false;
  }
}
function restorePosition() {
  if (video.value && currentChapter.value)
    video.value.currentTime =
      currentChapter.value.progress?.position_seconds || 0;
}
async function report(force = false) {
  const v = video.value,
    chapter = currentChapter.value;
  if (
    !v ||
    !chapter ||
    !session.profile ||
    playbackUserId !== session.profile.id ||
    playbackToken !== session.token ||
    !Number.isFinite(v.duration) ||
    v.duration < 1
  )
    return;
  const position = Math.floor(v.currentTime);
  if (!force && Math.abs(position - lastSaved) < 10) return;
  lastSaved = position;
  await saveProgress({
    course_id: course.value.id,
    chapter_id: chapter.id,
    position_seconds: position,
    duration_seconds: Math.max(1, Math.floor(v.duration)),
    completed: v.ended,
  });
}
function onTimeUpdate() {
  const v = video.value;
  if (!v || !Number.isFinite(v.duration) || v.duration < 1) return;
  videoProgress.value = Math.min(100, (v.currentTime / v.duration) * 100);
  void report();
}
function onPlay() {
  playing.value = true;
  beginPlayback();
}
function onPause() {
  playing.value = false;
  void report(true);
}
function playVideo() {
  void video.value?.play().catch(() => {
    videoError.value = "视频暂时无法播放，请检查网络或重新选择章节";
  });
}
async function changeChapter(index: number) {
  await report(true);
  resetPlayback();
  chapterIndex.value = index;
  videoError.value = "";
  lastSaved = -1;
}
function nextChapter() {
  if (chapterIndex.value < (course.value?.chapters?.length || 0) - 1) {
    void changeChapter(chapterIndex.value + 1);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}
function back() {
  window.history.state.back ? router.back() : router.replace("/courses");
}
function scrollToChapters() {
  document
    .getElementById("study-chapters")
    ?.scrollIntoView({ behavior: "smooth", block: "start" });
}
function selectOption(key: string) {
  const question = currentQuestion.value;
  if (!question || quizResult.value) return;
  const current = answers.value[question.id] || [];
  answers.value[question.id] =
    question.type === "MULTIPLE"
      ? current.includes(key)
        ? current.filter((item) => item !== key)
        : [...current, key]
      : [key];
}
function optionState(option: any) {
  const selected = !!answers.value[currentQuestion.value?.id]?.includes(
    option.key,
  );
  if (!currentDetail.value)
    return { selected };
  const correct = currentDetail.value.correct_answers?.includes(option.key);
  return {
    selected,
    correct,
    wrong: !correct && currentDetail.value.user_answers?.includes(option.key),
  };
}
function optionMark(option: any) {
  if (!currentDetail.value) return "";
  if (currentDetail.value.correct_answers?.includes(option.key)) return "✓";
  if (currentDetail.value.user_answers?.includes(option.key)) return "✕";
  return "";
}
async function submitQuiz() {
  if (!requireSession() || saving.value) return;
  if (!quiz.value.questions.every((q: any) => answers.value[q.id]?.length)) {
    notify("请完成所有题目后提交");
    return;
  }
  saving.value = true;
  try {
    quizResult.value = await post(
      "/courses/quiz/" + quiz.value.id + "/submit",
      { answers: answers.value },
    );
    notify("鉴赏结果已保存");
  } catch (e) {
    notify((e as Error).message);
  } finally {
    saving.value = false;
  }
}
async function collect() {
  if (!requireSession()) return;
  try {
    collected.value = (
      await post("/mobile/collections/COURSE/" + course.value.id)
    ).collected;
    notify(collected.value ? "已加入收藏" : "已取消收藏");
  } catch (e) {
    notify((e as Error).message);
  }
}
async function rate() {
  if (!requireSession()) return;
  try {
    await api("/mobile/courses/" + course.value.id + "/rating", {
      method: "PUT",
      body: JSON.stringify({ score: Number(rating.value) }),
    });
    notify("评价已保存");
  } catch (e) {
    notify((e as Error).message);
  }
}
watch(
  [() => route.params.id, () => session.token],
  () => {
    void report(true);
    void load();
  },
  { immediate: true },
);
onUnmounted(() => {
  void report(true);
  mounted = false;
  ++loadVersion;
  resetPlayback();
});
</script>
<template>
  <div class="player-page" data-design-node="5:01018">
    <PageHeader
      :title="course?.title || '非遗研习'"
      :subtitle="
        course
          ? '第 ' + (chapterIndex + 1) + '/' + course.chapters.length + ' 课'
          : undefined
      "
      back-to="/courses"
    >
      <span v-if="course?.rating" class="header-rating">
        <img :src="designIcon('layer-5-01018', '5:01265')" alt="" /><b>{{
          course.rating
        }}</b>
      </span>
    </PageHeader>
    <AsyncState :loading="loading" :error="error" @retry="load">
      <template v-if="course">
        <div class="player-body">
          <div class="video-frame">
            <video
              v-if="currentChapter?.video_url"
              ref="video"
              :key="currentChapter.id"
              :src="mediaUrl(currentChapter.video_url)"
              :poster="mediaUrl(course.cover_url)"
              controls
              playsinline
              preload="metadata"
              @loadedmetadata="restorePosition"
              @play="onPlay"
              @pause="onPause"
              @timeupdate="onTimeUpdate"
              @ended="onPause"
              @error="videoError = '视频暂时无法播放，请检查网络或重新选择章节'"
            />
            <div v-else class="video-unavailable">
              <img
                v-if="course.cover_url"
                :src="mediaUrl(course.cover_url)"
                :alt="course.title"
              />
              <p>该章节暂未上传视频</p>
            </div>
            <span v-if="currentChapter?.video_url" class="video-hd">视频</span>
            <span v-if="durationLabel" class="video-duration">{{
              durationLabel
            }}</span>
            <button
              v-if="currentChapter?.video_url && !playing"
              class="video-play"
              aria-label="播放课程视频"
              @click="playVideo"
            >
              <img
                :src="designIcon('layer-5-01018', '5:01220')"
                alt=""
              />
            </button>
            <span class="video-progress" aria-hidden="true"
              ><i :style="{ width: videoProgress + '%' }"
            /></span>
          </div>
          <p v-if="videoError" class="form-error video-error">
            {{ videoError }}
          </p>
          <p
            v-if="progressState.pending || progressState.error"
            class="progress-sync"
            role="status"
          >
            {{
              progressState.syncing
                ? "正在同步学习进度…"
                : progressState.error ||
                  "有" + progressState.pending + "条学习记录待同步"
            }}
            <button
              v-if="!progressState.syncing"
              class="text-button"
              @click="syncProgress"
            >
              重试同步
            </button>
          </p>
          <SectionCard class="lesson-intro">
            <h1>{{ course.title }}</h1>
            <div class="teacher-row">
              <img
                class="teacher-avatar"
                :src="
                  mediaUrl(course.cover_url) ||
                  designImage('layer-5-01018', '5:01157')
                "
                :alt="course.title"
              />
              <div class="teacher-meta">
                <div class="teacher-line">
                  <b>{{ course.title }}</b>
                  <span class="teacher-badge">{{ teacherTitle }}</span>
                </div>
                <p>{{ teacherBio }}</p>
              </div>
              <span class="chapter-count"
                >{{ chapterIndex + 1 }}/{{ course.chapters.length }}章节</span
              >
            </div>
            <p class="lesson-desc">{{ course.description }}</p>
            <ul
              v-if="currentChapter?.key_points?.length"
              class="key-points"
            >
              <li v-for="(point, i) in currentChapter.key_points" :key="i">
                {{ point }}
              </li>
            </ul>
          </SectionCard>
          <SectionCard
            id="study-chapters"
            class="chapter-list"
            title="继续研习"
            :meta="course.chapters.length + ' 章节'"
          >
            <button
              v-for="(ch, i) in course.chapters"
              :key="ch.id"
              :class="{ active: i === chapterIndex }"
              @click="changeChapter(i)"
            >
              <span class="chapter-seq">{{
                String(Number(i) + 1).padStart(2, "0")
              }}</span>
              <span class="chapter-title">{{ ch.title }}</span>
              <span class="chapter-status">{{
                ch.progress?.completed
                  ? "已完成"
                  : Math.ceil(ch.duration_seconds / 60) + "分钟"
              }}</span>
            </button>
          </SectionCard>
          <SectionCard
            v-if="quiz && quiz.questions?.length"
            class="quiz-card"
            title="随堂 · 鉴宝"
            :meta="
              currentQuestion
                ? '第 ' + (quizIndex + 1) + '/' + quiz.questions.length + ' 题'
                : undefined
            "
          >
            <template v-if="currentQuestion">
              <img class="quiz-image" :src="quizImage" :alt="course.title" />
              <p class="quiz-question">
                {{ quizIndex + 1 }}. {{ currentQuestion.content }}
              </p>
              <div class="quiz-options">
                <button
                  v-for="option in currentQuestion.options"
                  :key="option.key"
                  class="quiz-option"
                  :class="optionState(option)"
                  :aria-pressed="
                    !!answers[currentQuestion.id]?.includes(option.key)
                  "
                  @click="selectOption(option.key)"
                >
                  <b>{{ option.key }}</b>
                  <span class="quiz-option-text">{{ option.text }}</span>
                  <span v-if="optionMark(option)" class="quiz-mark">{{
                    optionMark(option)
                  }}</span>
                </button>
              </div>
              <p v-if="currentDetail" class="quiz-explanation">
                解析：{{ currentDetail.explanation || "知识点已记录。" }}
              </p>
              <div class="quiz-nav">
                <button
                  class="quiz-arrow"
                  :disabled="quizIndex === 0"
                  aria-label="上一题"
                  @click="quizIndex--"
                >
                  ‹
                </button>
                <span class="quiz-dots" aria-hidden="true">
                  <i
                    v-for="(question, i) in quiz.questions"
                    :key="question.id"
                    :class="{
                      active: i === quizIndex,
                      done: !!answers[question.id]?.length,
                    }"
                  />
                </span>
                <button
                  v-if="quizIndex < quiz.questions.length - 1"
                  class="outline-button quiz-next"
                  @click="quizIndex++"
                >
                  下一题
                </button>
                <button
                  v-else
                  class="primary-button quiz-submit"
                  :disabled="saving || !!quizResult"
                  @click="submitQuiz"
                >
                  {{ quizResult ? "已提交" : saving ? "提交中…" : "提交鉴赏" }}
                </button>
              </div>
              <div v-if="quizResult" class="quiz-result" aria-live="polite">
                <h3>
                  {{ quizResult.passed ? "鉴赏通过" : "再接再厉" }} ·
                  {{ quizResult.score }}分
                </h3>
                <p v-if="quizResult.energy_reward">
                  获得 {{ quizResult.energy_reward }} 点成长能量
                </p>
              </div>
              <div v-if="quizResult" class="quiz-after">
                <button
                  class="outline-button"
                  :disabled="chapterIndex >= course.chapters.length - 1"
                  @click="nextChapter"
                >
                  下一件瑰宝
                </button>
                <button class="dark-button" @click="scrollToChapters">
                  继续研习
                </button>
              </div>
            </template>
          </SectionCard>
          <SectionCard class="player-rating">
            <form class="rating-form" @submit.prevent="rate">
              <label
                >课程评价<select v-model="rating">
                  <option v-for="star in 5" :key="star" :value="star">
                    {{ star }} 星
                  </option>
                </select></label
              ><button class="text-button">提交评价</button>
            </form>
          </SectionCard>
        </div>
        <footer class="player-toolbar">
          <span class="toolbar-energy" title="完成课程可获得能量">
            <img
              :src="designIcon('layer-5-01018', '5:01041')"
              alt=""
            />{{ course.energy_reward }}
          </span>
          <button
            class="toolbar-action"
            :class="{ active: collected }"
            :aria-pressed="collected"
            @click="collect"
          >
            <img
              :src="designIcon('layer-5-01018', '5:01059')"
              alt=""
            />{{ collected ? "已保存" : "收藏" }}
          </button>
          <button class="toolbar-action" @click="scrollToChapters">
            <img
              :src="designIcon('layer-5-01018', '5:01071')"
              alt=""
            />继续研习
          </button>
          <RouterLink class="toolbar-ai" to="/ai-workshop"
            >前往AI工坊</RouterLink
          >
        </footer>
      </template>
    </AsyncState>
  </div>
</template>
<style scoped>
.player-page {
  min-height: 100dvh;
  padding-bottom: calc(96px + var(--safe-bottom));
  background: #f5ede4;
  color: #2d1810;
}
.header-rating {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 26px;
  padding: 0 10px;
  border: 1px solid rgba(200, 169, 110, 0.45);
  border-radius: 999px;
  background: rgba(255, 253, 248, 0.8);
  color: #8b1a1a;
  font: 500 11px/1 var(--sans);
  white-space: nowrap;
}
.header-rating img {
  width: 12px;
  height: 12px;
}
.header-rating b {
  font-weight: 600;
}
.player-body {
  padding: 14px 16px 0;
}
.video-frame {
  position: relative;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(200, 169, 110, 0.55);
  background: #201a15;
  box-shadow: 0 8px 24px rgba(70, 42, 26, 0.12);
}
.video-frame video {
  display: block;
  width: 100%;
  aspect-ratio: 16/10;
  object-fit: contain;
  background: #201a15;
}
.video-unavailable {
  position: relative;
  min-height: 208px;
  display: grid;
  place-items: center;
}
.video-unavailable img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.45;
}
.video-unavailable p {
  position: relative;
  color: #f6ead9;
  font: 400 12px/1.6 var(--sans);
  letter-spacing: 0.6px;
}
.video-hd {
  position: absolute;
  left: 12px;
  top: 12px;
  padding: 3px 9px;
  border-radius: 999px;
  background: rgba(139, 26, 26, 0.9);
  color: #f6ead9;
  font: 500 10px/1.4 var(--sans);
  letter-spacing: 0.6px;
}
.video-duration {
  position: absolute;
  right: 12px;
  top: 12px;
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(26, 20, 16, 0.72);
  color: #f6ead9;
  font: 400 10px/1.4 var(--sans);
  -webkit-backdrop-filter: blur(4px);
  backdrop-filter: blur(4px);
}
.video-play {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 58px;
  height: 58px;
  margin: -29px 0 0 -29px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 1px solid #c8a96e;
  background: rgba(253, 249, 242, 0.92);
  box-shadow: 0 4px 18px rgba(70, 42, 26, 0.28);
  -webkit-backdrop-filter: blur(4px);
  backdrop-filter: blur(4px);
}
.video-play img {
  width: 24px;
  height: 24px;
}
.video-progress {
  position: absolute;
  left: 2px;
  right: 2px;
  bottom: 0;
  height: 3px;
  background: rgba(42, 32, 26, 0.35);
}
.video-progress i {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: #8b1a1a;
}
.video-error {
  margin: 8px 2px 0;
  font-size: 11px;
  line-height: 1.8;
  color: #8b1a1a;
}
.progress-sync {
  margin: 8px 2px 0;
  color: #8a7a70;
  font-size: 11px;
  line-height: 1.8;
}
.progress-sync .text-button {
  padding: 2px 4px;
  color: #8b1a1a;
  font-size: 11px;
}
.lesson-intro {
  margin-top: 14px;
  padding: 16px 14px;
  border-radius: 14px;
  background: #fdf9f2;
}
.lesson-intro h1 {
  margin: 0 0 12px;
  font: 500 16px/1.45 var(--serif);
  letter-spacing: 1.5px;
  color: #2d1810;
}
.teacher-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.teacher-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid rgba(200, 169, 110, 0.7);
  flex: 0 0 40px;
}
.teacher-meta {
  min-width: 0;
}
.teacher-line {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.teacher-line b {
  font: 500 13px/1.4 var(--sans);
  color: #2d1810;
}
.teacher-badge {
  padding: 1px 7px;
  border-radius: 999px;
  border: 1px solid rgba(200, 169, 110, 0.5);
  background: rgba(200, 169, 110, 0.12);
  color: #8a6125;
  font: 400 10px/1.5 var(--sans);
  white-space: nowrap;
}
.teacher-meta p {
  margin: 3px 0 0;
  color: #8a7a70;
  font: 400 11px/1.6 var(--sans);
}
.chapter-count {
  margin-left: auto;
  flex-shrink: 0;
  color: #8b1a1a;
  font: 400 10px/1.5 var(--sans);
  white-space: nowrap;
}
.lesson-desc {
  margin: 12px 0 0;
  color: #5a3e36;
  font: 400 13px/1.85 var(--sans);
}
.key-points {
  list-style: none;
  margin: 10px 0 0;
  padding: 0;
}
.key-points li {
  position: relative;
  padding-left: 14px;
  color: #8a7a70;
  font: 400 13px/1.9 var(--sans);
}
.key-points li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 9px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #c8a96e;
}
.chapter-list {
  scroll-margin-top: 12px;
}
.chapter-list button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  margin-bottom: 8px;
  border: 1px solid rgba(200, 169, 110, 0.3);
  border-radius: 10px;
  background: #fffdf8;
  text-align: left;
  color: #5a3e36;
  font: 400 13px/1.4 var(--sans);
}
.chapter-list button:last-child {
  margin-bottom: 0;
}
.chapter-list button.active {
  background: rgba(139, 26, 26, 0.06);
  border-color: rgba(139, 26, 26, 0.28);
  color: #8b1a1a;
}
.chapter-seq {
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #f3e9d8;
  color: #8a6125;
  font: 400 10px/1 var(--sans);
  flex: 0 0 22px;
}
.chapter-title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.chapter-status {
  margin-left: auto;
  color: #8a7a70;
  font: 400 10px/1.4 var(--sans);
  white-space: nowrap;
}
.quiz-card {
  background: linear-gradient(160deg, #fdf9f2 0%, #f7efe0 100%);
}
.quiz-image {
  display: block;
  width: 100%;
  max-height: 150px;
  object-fit: cover;
  border-radius: 10px;
  border: 1px solid rgba(200, 169, 110, 0.35);
  margin: 0 0 12px;
}
.quiz-question {
  margin: 0 0 10px;
  color: #2d1810;
  font: 400 13px/1.8 var(--sans);
}
.quiz-options {
  display: grid;
  gap: 8px;
}
.quiz-option {
  width: 100%;
  min-height: 46px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid rgba(200, 169, 110, 0.35);
  border-radius: 10px;
  background: #fffdf8;
  color: #2d1810;
  text-align: left;
  font: 400 13px/1.5 var(--sans);
}
.quiz-option b {
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  flex: 0 0 22px;
  border-radius: 50%;
  background: #f5ede4;
  color: #8a6125;
  font: 500 10px/1 var(--sans);
}
.quiz-option-text {
  min-width: 0;
}
.quiz-mark {
  margin-left: auto;
  font-size: 14px;
  font-weight: 700;
}
.quiz-option.selected {
  border-color: #8a6125;
  background: rgba(200, 169, 110, 0.14);
}
.quiz-option.selected b {
  background: rgba(200, 169, 110, 0.32);
  color: #6b4a1c;
}
.quiz-option.correct {
  border-color: #5a7d4a;
  background: #eef4e8;
}
.quiz-option.correct b,
.quiz-option.correct .quiz-mark {
  background: #dfead5;
  color: #4e7240;
}
.quiz-option.wrong {
  border-color: #8b1a1a;
  background: #f8e9e6;
}
.quiz-option.wrong b,
.quiz-option.wrong .quiz-mark {
  background: #f0d7d2;
  color: #8b1a1a;
}
.quiz-explanation {
  margin: 10px 0 0;
  color: #8a7a70;
  font: 400 11px/1.75 var(--sans);
}
.quiz-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
}
.quiz-arrow {
  width: 30px;
  height: 30px;
  padding: 0 0 3px;
  border-radius: 50%;
  border: 1px solid rgba(200, 169, 110, 0.45);
  background: #fffdf8;
  color: #8a6125;
  font-size: 18px;
  line-height: 1;
}
.quiz-arrow:disabled {
  opacity: 0.35;
}
.quiz-dots {
  flex: 1;
  display: flex;
  justify-content: center;
  gap: 6px;
}
.quiz-dots i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #e3d5c1;
}
.quiz-dots i.done {
  background: #c8a96e;
}
.quiz-dots i.active {
  width: 16px;
  border-radius: 999px;
  background: #8b1a1a;
}
.quiz-next,
.quiz-submit {
  min-height: 40px;
  padding: 0 16px;
  font-size: 12px;
  border-radius: 10px;
}
.quiz-submit {
  border: 1px solid transparent;
  background: #8b1a1a;
  color: #f6ead9;
}
.quiz-next {
  border-color: rgba(200, 169, 110, 0.55);
  color: #8a6125;
}
.quiz-result {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(200, 169, 110, 0.14);
  color: #5a3e36;
  font-size: 12px;
  line-height: 1.7;
}
.quiz-result h3 {
  margin: 0;
  font: 500 14px/1.5 var(--serif);
  color: #8b1a1a;
}
.quiz-result p {
  margin: 4px 0 0;
  font-size: 11px;
  color: #8a7a70;
}
.quiz-after {
  display: flex;
  gap: 10px;
  margin-top: 14px;
}
.quiz-after > * {
  flex: 1;
}
.quiz-after .outline-button,
.dark-button {
  min-height: 42px;
  border-radius: 10px;
  font-size: 12px;
}
.quiz-after .outline-button {
  border-color: rgba(200, 169, 110, 0.55);
  color: #8a6125;
}
.dark-button {
  border: 1px solid #2d1810;
  background: #2d1810;
  color: #f6ead9;
}
.player-rating {
  padding: 14px;
}
.player-rating .rating-form {
  gap: 12px;
}
.player-rating label {
  font: 400 12px/1.5 var(--sans);
  color: #5a3e36;
}
.player-rating select {
  border-color: rgba(200, 169, 110, 0.45);
  border-radius: 10px;
  background: #fffdf8;
  color: #2d1810;
}
.player-rating .text-button {
  align-self: flex-end;
  padding: 4px 8px;
  color: #8b1a1a;
  font-size: 12px;
}
.player-toolbar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  display: grid;
  grid-template-columns: auto auto auto 1fr;
  align-items: center;
  gap: 10px;
  padding: 9px 14px calc(9px + var(--safe-bottom));
  background: rgba(245, 237, 228, 0.97);
  border-top: 1px solid rgba(200, 169, 110, 0.42);
  box-shadow: 0 -6px 20px rgba(70, 42, 26, 0.08);
  -webkit-backdrop-filter: blur(10px);
  backdrop-filter: blur(10px);
}
.toolbar-energy {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #8a6125;
  font: 500 11px/1 var(--sans);
}
.toolbar-energy img {
  width: 17px;
  height: 17px;
}
.toolbar-action {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 2px;
  border: 0;
  background: none;
  color: #5a3e36;
  font: 400 11px/1 var(--sans);
  white-space: nowrap;
}
.toolbar-action img {
  width: 14px;
  height: 14px;
}
.toolbar-action.active {
  color: #8b1a1a;
}
.toolbar-ai {
  justify-self: end;
  padding: 8px 13px;
  border-radius: 999px;
  background: #8b1a1a;
  color: #f6ead9;
  font: 500 11px/1.2 var(--sans);
  letter-spacing: 0.5px;
  white-space: nowrap;
}
</style>
