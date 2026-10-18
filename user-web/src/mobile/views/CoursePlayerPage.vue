<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api, post, requireSession, notify, mediaUrl, session } from "../api";
import { saveProgress, progressState, syncProgress } from "../progress";
import { designImage, designIcon, categoryName } from "../design";
import AsyncState from "../components/AsyncState.vue";
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
const teacherTitle = computed(() =>
  course.value?.category
    ? categoryName(course.value.category) + "技艺传承人"
    : "非遗技艺传承人",
);
const teacherBio = computed(
  () => course.value?.subtitle || "传承非遗技艺，守护匠心文脉",
);
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
    <AsyncState :loading="loading" :error="error" @retry="load">
      <template v-if="course">
        <header class="player-top">
          <button class="player-back" aria-label="返回上一页" @click="back">
            ‹
          </button>
          <div class="lesson-pill">
            <span
              >第 {{ chapterIndex + 1 }}/{{ course.chapters.length }} 课</span
            >
            <template v-if="course.rating"
              ><img
                :src="designIcon('layer-5-01018', '5:01265')"
                alt="" /><b>{{ course.rating }}</b></template
            >
          </div>
          <span aria-hidden="true"></span>
        </header>
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
            <span class="video-hd">高清</span>
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
          <section class="lesson-intro corner-card">
            <h1>{{ course.title }}</h1>
            <div class="teacher-row">
              <img
                class="teacher-avatar"
                :src="designImage('layer-5-01018', '5:01157')"
                alt=""
              />
              <div class="teacher-meta">
                <div class="teacher-line">
                  <b>润乡非遗课堂</b>
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
              <li
                v-for="(point, i) in currentChapter.key_points"
                :key="i"
              >
                {{ point }}
              </li>
            </ul>
          </section>
          <section id="study-chapters" class="chapter-list">
            <div class="section-heading">
              <h2>继续研习</h2>
              <span>{{ course.chapters.length }} 章节</span>
            </div>
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
          </section>
          <section v-if="quiz && quiz.questions?.length" class="quiz-card corner-card">
            <div class="quiz-heading">
              <h2>随堂 · 鉴宝</h2>
              <span v-if="currentQuestion"
                >第 {{ quizIndex + 1 }}/{{ quiz.questions.length }} 题</span
              >
            </div>
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
          </section>
          <form class="rating-form player-rating" @submit.prevent="rate">
            <label
              >课程评价<select v-model="rating">
                <option v-for="star in 5" :key="star" :value="star">
                  {{ star }} 星
                </option>
              </select></label
            ><button class="text-button">提交评价</button>
          </form>
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
  padding-bottom: calc(86px + var(--safe-bottom));
  background:
    radial-gradient(120% 70% at 50% 0%, rgba(255, 252, 244, 0.9), transparent 60%),
    linear-gradient(#f7efe0, #f4e7d2);
  color: #2a2620;
}
.player-top {
  position: sticky;
  top: 0;
  z-index: 8;
  display: grid;
  grid-template-columns: 40px 1fr 40px;
  align-items: center;
  padding: calc(8px + var(--safe-top)) 14px 8px;
  background: rgba(249, 244, 232, 0.92);
  backdrop-filter: blur(10px);
}
.player-back {
  width: 36px;
  height: 36px;
  border: 1px solid rgba(201, 168, 76, 0.45);
  border-radius: 50%;
  background: rgba(253, 251, 245, 0.85);
  color: #5e5448;
  font-size: 24px;
  line-height: 1;
  padding: 0 0 3px;
}
.lesson-pill {
  justify-self: center;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 14px;
  border-radius: 999px;
  background: #fdfbf5;
  border: 1px solid rgba(201, 168, 76, 0.35);
  box-shadow: 0 2px 10px rgba(212, 140, 88, 0.08);
  font-size: 12px;
  color: #6b5b45;
  white-space: nowrap;
}
.lesson-pill img {
  width: 13px;
  height: 13px;
}
.lesson-pill b {
  color: #c47040;
  font-weight: 600;
}
.player-body {
  padding: 2px 20px 0;
}
.video-frame {
  position: relative;
  margin: 6px 0 0;
  border-radius: 16px;
  overflow: hidden;
  border: 2px solid rgba(245, 232, 184, 0.6);
  background: #201a15;
  box-shadow: 0 8px 32px rgba(212, 140, 88, 0.12);
}
.video-frame video {
  display: block;
  width: 100%;
  aspect-ratio: 16/10;
  object-fit: contain;
  background: #201a15;
}
.video-unavailable {
  min-height: 208px;
}
.video-hd {
  position: absolute;
  left: 14px;
  top: 14px;
  padding: 3px 11px;
  border-radius: 999px;
  background: linear-gradient(90deg, #c47040, #b86040);
  color: #fdfbf5;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.6px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}
.video-duration {
  position: absolute;
  right: 14px;
  top: 14px;
  padding: 3px 9px;
  border-radius: 6px;
  background: rgba(26, 24, 20, 0.7);
  color: #f9f4e8;
  font-size: 11px;
  backdrop-filter: blur(4px);
}
.video-play {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 62px;
  height: 62px;
  margin: -31px 0 0 -31px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 2px solid #d48c58;
  background: rgba(249, 244, 232, 0.9);
  box-shadow: 0 4px 20px rgba(212, 140, 88, 0.25);
  backdrop-filter: blur(4px);
}
.video-play img {
  width: 26px;
  height: 26px;
}
.video-progress {
  position: absolute;
  left: 2px;
  right: 2px;
  bottom: 0;
  height: 4px;
  background: rgba(42, 38, 32, 0.3);
}
.video-progress i {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #d48c58, #e0c05c 50%, #e0a878);
}
.video-error {
  margin: 8px 4px 0;
}
.progress-sync {
  margin: 12px 2px 0;
}
.lesson-intro {
  margin-top: 16px;
  padding: 20px 18px 16px;
  background: linear-gradient(127deg, #f9f4e8 4%, #fdfbf5 100%);
  border: 1px solid rgba(245, 232, 184, 0.5);
  box-shadow: 0 4px 20px rgba(212, 140, 88, 0.06);
}
.lesson-intro h1 {
  margin: 0 0 14px;
  font-family: var(--serif);
  font-size: 21px;
  line-height: 1.5;
  letter-spacing: 0.5px;
  color: #2a2620;
}
.teacher-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}
.teacher-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #e0a878;
  flex: 0 0 42px;
}
.teacher-meta {
  min-width: 0;
  padding-top: 1px;
}
.teacher-line {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.teacher-line b {
  font-size: 13px;
  font-weight: 600;
  color: #3a342c;
}
.teacher-badge {
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid #ebc4a8;
  background: #fbf0e8;
  color: #9c4828;
  font-size: 9px;
  line-height: 14px;
  white-space: nowrap;
}
.teacher-meta p {
  margin: 5px 0 0;
  color: #7a6e5e;
  font-size: 11px;
  line-height: 1.6;
}
.chapter-count {
  margin-left: auto;
  padding-top: 3px;
  color: #c47040;
  font-size: 11px;
  white-space: nowrap;
}
.lesson-desc {
  margin: 14px 0 0;
  color: #5e5448;
  font-size: 13px;
  line-height: 1.85;
}
.key-points {
  list-style: none;
  margin: 14px 0 0;
  padding: 0;
}
.key-points li {
  position: relative;
  padding-left: 14px;
  color: #7a6e5e;
  font-size: 12px;
  line-height: 1.9;
}
.key-points li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 9px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #e0a878;
}
.chapter-list {
  margin: 24px 0 0;
}
.section-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 10px;
}
.section-heading h2 {
  margin: 0;
  font-family: var(--serif);
  font-size: 17px;
  color: #2a2620;
}
.section-heading span {
  color: #a08b74;
  font-size: 11px;
}
.chapter-list button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  margin-bottom: 8px;
  border: 1px solid rgba(201, 168, 76, 0.25);
  border-radius: 12px;
  background: rgba(253, 251, 245, 0.72);
  text-align: left;
  color: #5e5448;
  font-size: 12px;
}
.chapter-list button.active {
  background: #f4e7d4;
  border-color: rgba(196, 112, 64, 0.35);
  color: #a0522d;
}
.chapter-seq {
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #f3e9d8;
  color: #b07a4a;
  font-size: 10px;
  flex: 0 0 24px;
}
.chapter-title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.chapter-status {
  margin-left: auto;
  color: #a08b74;
  font-size: 10px;
  white-space: nowrap;
}
.quiz-card {
  margin-top: 22px;
  padding: 18px 16px 16px;
  background: linear-gradient(160deg, #f9f4e8 0%, #fdfbf5 55%, #f8eddd 100%);
  border: 1px solid rgba(201, 168, 76, 0.3);
  box-shadow: 0 6px 24px rgba(212, 140, 88, 0.08);
}
.quiz-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 8px;
}
.quiz-heading h2 {
  margin: 0;
  font-family: var(--serif);
  font-size: 18px;
  color: #2a2620;
}
.quiz-heading span {
  color: #c47040;
  font-size: 11px;
}
.quiz-image {
  display: block;
  width: 100%;
  max-height: 158px;
  object-fit: cover;
  border-radius: 10px;
  border: 1px solid rgba(201, 168, 76, 0.3);
  margin: 4px 0 12px;
}
.quiz-question {
  margin: 0 0 10px;
  color: #3a342c;
  font-size: 13px;
  line-height: 1.8;
}
.quiz-options {
  display: grid;
  gap: 8px;
}
.quiz-option {
  width: 100%;
  min-height: 48px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid #e8d9c0;
  border-radius: 12px;
  background: #fffdf8;
  color: #3a342c;
  text-align: left;
  font-size: 12px;
  line-height: 1.5;
}
.quiz-option b {
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  flex: 0 0 24px;
  border-radius: 50%;
  background: #f5eee0;
  color: #9a7b55;
  font-size: 11px;
  font-weight: 600;
}
.quiz-option-text {
  min-width: 0;
}
.quiz-mark {
  margin-left: auto;
  font-size: 15px;
  font-weight: 700;
}
.quiz-option.selected {
  border-color: #d48c58;
  background: #f8eee3;
}
.quiz-option.selected b {
  background: #e8cbb2;
  color: #8a4a2a;
}
.quiz-option.correct {
  border-color: #5a7d4a;
  background: #eff4e9;
}
.quiz-option.correct b,
.quiz-option.correct .quiz-mark {
  background: #dfead5;
  color: #4e7240;
}
.quiz-option.wrong {
  border-color: #b85450;
  background: #f8e9e4;
}
.quiz-option.wrong b,
.quiz-option.wrong .quiz-mark {
  background: #f0d7d2;
  color: #a33f3a;
}
.quiz-explanation {
  margin: 10px 0 0;
  color: #7a6e5e;
  font-size: 11px;
  line-height: 1.75;
}
.quiz-nav {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 14px;
}
.quiz-arrow {
  width: 32px;
  height: 32px;
  padding: 0 0 3px;
  border-radius: 50%;
  border: 1px solid rgba(201, 168, 76, 0.35);
  background: #fffdf8;
  color: #8a6a4a;
  font-size: 19px;
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
  background: #d8ab80;
}
.quiz-dots i.active {
  width: 16px;
  border-radius: 999px;
  background: #c47040;
}
.quiz-next,
.quiz-submit {
  min-height: 40px;
  padding: 0 18px;
  font-size: 12px;
  border-radius: 12px;
}
.quiz-submit {
  background: linear-gradient(90deg, #c06a52, #a94a46);
  border-color: transparent;
  color: #fdfbf5;
}
.quiz-result {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(244, 231, 212, 0.7);
  color: #6b5b45;
  font-size: 12px;
  line-height: 1.7;
}
.quiz-result h3 {
  margin: 0;
  font-family: var(--serif);
  font-size: 14px;
  color: #a0522d;
}
.quiz-result p {
  margin: 4px 0 0;
  font-size: 11px;
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
  min-height: 44px;
  border-radius: 12px;
  font-size: 12px;
}
.dark-button {
  border: 1px solid #2b2620;
  background: #2b2620;
  color: #f9f4e8;
}
.player-rating {
  margin: 18px 0 4px;
  padding-top: 14px;
  border-top: 1px dashed rgba(201, 168, 76, 0.4);
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
  gap: 12px;
  padding: 9px 16px calc(9px + var(--safe-bottom));
  background: rgba(250, 246, 238, 0.97);
  border-top: 1px solid rgba(201, 168, 76, 0.45);
  box-shadow: 0 -4px 20px rgba(61, 35, 20, 0.08);
  backdrop-filter: blur(10px);
}
.toolbar-energy {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #8b7355;
  font-size: 12px;
  font-weight: 600;
}
.toolbar-energy img {
  width: 18px;
  height: 18px;
}
.toolbar-action {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 2px;
  border: 0;
  background: none;
  color: #8b7355;
  font-size: 11px;
  white-space: nowrap;
}
.toolbar-action img {
  width: 14px;
  height: 14px;
}
.toolbar-action.active {
  color: #a0522d;
}
.toolbar-ai {
  justify-self: end;
  padding: 9px 14px;
  border-radius: 999px;
  background: linear-gradient(90deg, #c47040, #b86040);
  color: #fdfbf5;
  font-size: 11px;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(184, 96, 64, 0.25);
}
</style>
