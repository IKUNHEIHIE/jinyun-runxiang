import { post, session } from "./api";
import { reactive } from "vue";
import { formatDate } from "./dates";
interface Progress {
  course_id: number;
  chapter_id: number;
  position_seconds: number;
  duration_seconds: number;
  completed: boolean;
}
interface OfflineEvent {
  event_id: string;
  event_type: "PROGRESS_UPDATE";
  payload: Progress;
  event_time: string;
}
const key = (uid: number) => "jinyun-progress-" + uid;
function read(uid: number): OfflineEvent[] {
  try {
    const stored = JSON.parse(localStorage.getItem(key(uid)) || "[]");
    return Array.isArray(stored) ? stored : [];
  } catch {
    return [];
  }
}
let syncing = false;
export const progressState = reactive({
  pending: 0,
  syncing: false,
  error: "",
});
function refreshState() {
  progressState.pending = session.profile ? read(session.profile.id).length : 0;
}
export async function saveProgress(payload: Progress) {
  const uid = session.profile?.id;
  if (!uid) return;
  const stored = read(uid);
  const eventTime = new Date().toISOString();
  const sameChapter = stored.filter(
    (e) =>
      e.payload.chapter_id === payload.chapter_id &&
      e.payload.course_id === payload.course_id,
  );
  const sameDay = sameChapter.filter(
    (e) => formatDate(e.event_time, false) === formatDate(eventTime, false),
  );
  const queue = stored.filter((e) => !sameDay.includes(e));
  queue.push({
    event_id: crypto.randomUUID(),
    event_type: "PROGRESS_UPDATE",
    payload: {
      ...payload,
      completed:
        payload.completed || sameChapter.some((e) => e.payload.completed),
    },
    event_time: eventTime,
  });
  try {
    localStorage.setItem(key(uid), JSON.stringify(queue));
  } catch {
    progressState.error = "设备存储不足，学习进度暂未保存，请释放空间后重试";
    return;
  }
  refreshState();
  await syncProgress();
}
export async function syncProgress() {
  const uid = session.profile?.id;
  const token = session.token;
  refreshState();
  if (!uid || syncing) return;
  if (!read(uid).length) {
    progressState.error = "";
    return;
  }
  syncing = true;
  progressState.syncing = true;
  try {
    for (
      let round = 0;
      round < 10 &&
      uid === session.profile?.id &&
      token === session.token &&
      token;
      round++
    ) {
      const batch = read(uid).slice(0, 100);
      if (!batch.length) break;
      const result = await post("/courses/sync-offline", { events: batch });
      const submitted = new Set(batch.map((e) => e.event_id));
      const accepted = new Set<string>(
        (result.success_event_ids || []).filter((id: string) =>
          submitted.has(id),
        ),
      );
      localStorage.setItem(
        key(uid),
        JSON.stringify(read(uid).filter((e) => !accepted.has(e.event_id))),
      );
      refreshState();
      if (result.conflict_event_ids?.length || !accepted.size) {
        progressState.error =
          "部分课程记录暂未同步，请稍后重试；已保存到本机的进度会保留";
        break;
      }
      progressState.error = "";
    }
  } catch (e) {
    progressState.error = (e as Error).message + "，学习进度已保存在本机";
  } finally {
    syncing = false;
    progressState.syncing = false;
    refreshState();
    if (uid !== session.profile?.id && session.profile) void syncProgress();
  }
}
