<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api, notify, post, requireSession, session } from "../api";
import PageHeader from "../components/PageHeader.vue";
import SkeletonImage from "../components/SkeletonImage.vue";

type Work = {
  task_id: string;
  tool_type: string;
  status: string;
  progress: number;
  title: string | null;
  image_url: string | null;
  collected: boolean;
  error_message: string | null;
  created_at: string | null;
};
type Page = { total: number; has_more: boolean; items: Work[] };

const route = useRoute();
const router = useRouter();
const filters = [
  { key: "", label: "全部" },
  { key: "MESH_3D", label: "三维沙盘" },
  { key: "SILHOUETTE", label: "剪影画像" },
  { key: "BRONZE", label: "青铜纹样" },
  { key: "SHADOW_PUPPET", label: "皮影角色" },
  { key: "LACQUER,EMBROIDERY", label: "漆绣智绘" },
];
const TOOL_LABEL: Record<string, string> = {
  MESH_3D: "三维沙盘",
  SILHOUETTE: "剪影画像",
  BRONZE: "青铜纹样",
  SHADOW_PUPPET: "皮影角色",
  LACQUER: "漆绣智绘",
  EMBROIDERY: "漆绣智绘",
  BALLAD: "曲艺谱面",
};
const EDITOR: Record<string, string> = {
  MESH_3D: "3d",
  SILHOUETTE: "shadow-3d",
  BRONZE: "bronze",
  SHADOW_PUPPET: "shadow",
  LACQUER: "lacquer",
  EMBROIDERY: "lacquer",
};

const active = ref("");
const works = ref<Work[]>([]);
const total = ref(0);
const page = ref(1);
const loading = ref(false);
const error = ref("");
const confirmId = ref("");
const busyId = ref("");
let token = 0;

async function load(reset = true) {
  if (!requireSession(route.fullPath)) return;
  const current = ++token;
  loading.value = true;
  error.value = "";
  if (reset) {
    works.value = [];
    page.value = 1;
    confirmId.value = "";
  }
  const query =
    "?page=" + page.value + "&page_size=12" +
    (active.value ? "&tool_type=" + encodeURIComponent(active.value) : "");
  try {
    const data = await api<Page>("/ai/tasks" + query);
    if (current !== token) return;
    works.value = reset ? data.items : works.value.concat(data.items);
    total.value = data.total;
  } catch (e) {
    if (current === token) error.value = (e as Error).message || "作品读取失败，请重试";
  } finally {
    if (current === token) loading.value = false;
  }
}

function choose(key: string) {
  if (active.value === key) return;
  active.value = key;
  void load(true);
}

function more() {
  confirmId.value = "";
  page.value += 1;
  void load(false);
}

function open(item: Work) {
  const tool = EDITOR[item.tool_type];
  if (!tool) {
    notify("这件作品暂时没有可打开的工坊页");
    return;
  }
  router.push("/ai-workshop/" + tool + "?task_id=" + encodeURIComponent(item.task_id));
}

async function toggleCollect(item: Work) {
  if (busyId.value) return;
  const owner = session.token;
  busyId.value = item.task_id;
  try {
    const data = await post<{ collected: boolean }>("/ai/tasks/" + item.task_id + "/favorite", {
      collected: !item.collected,
    });
    if (owner !== session.token) return;
    item.collected = data.collected;
    notify(data.collected ? "已加入我的收藏" : "已取消收藏");
  } catch (e) {
    if (owner === session.token) notify((e as Error).message || "收藏状态未能保存，请重试");
  } finally {
    if (owner === session.token) busyId.value = "";
  }
}

async function remove(item: Work) {
  if (confirmId.value !== item.task_id) {
    confirmId.value = item.task_id;
    notify("再点一次「删除」确认删除这件作品");
    return;
  }
  confirmId.value = "";
  const owner = session.token;
  busyId.value = item.task_id;
  try {
    await api("/ai/tasks/" + item.task_id, { method: "DELETE" });
    if (owner !== session.token) return;
    works.value = works.value.filter((row) => row.task_id !== item.task_id);
    total.value = Math.max(0, total.value - 1);
    notify("作品已删除");
  } catch (e) {
    if (owner === session.token) notify((e as Error).message || "删除失败，请稍后重试");
  } finally {
    if (owner === session.token) busyId.value = "";
  }
}

function dateText(value: string | null) {
  if (!value) return "";
  const date = new Date(value.endsWith("Z") ? value : value + "Z");
  return Number.isNaN(date.getTime())
    ? ""
    : date.toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

onBeforeUnmount(() => {
  token += 1;
});
watch(
  () => [session.token, session.profile?.id],
  () => {
    // A shared tablet must never keep showing the previous student's works after a switch.
    token += 1;
    works.value = [];
    total.value = 0;
    confirmId.value = "";
    busyId.value = "";
    void load(true);
  },
);
void load(true);
</script>

<template>
  <div class="works-page">
    <PageHeader title="我的工坊作品">
      <em class="works-total">{{ total }} 件</em>
    </PageHeader>

    <div class="page-padding">
      <p class="works-note">工坊里的每一次创作都会留档，可继续查看、收藏或删除。删除后本地作品文件一并清除，已发布到社区的作品会保留。</p>

      <div class="filter-row" role="tablist" aria-label="按工坊筛选">
        <button
          v-for="item in filters"
          :key="item.key"
          role="tab"
          :aria-selected="active === item.key"
          :class="{ on: active === item.key }"
          @click="choose(item.key)"
        >
          {{ item.label }}
        </button>
      </div>

      <p v-if="loading && !works.length" class="works-state">正在翻阅工坊存档…</p>
      <p v-else-if="error" class="works-state error" role="alert">
        {{ error }}
        <button @click="load(true)">重试</button>
      </p>
      <p v-else-if="!works.length" class="works-state">
        这里还没有作品{{ active ? "（当前筛选）" : "" }}，去挑一间工坊开始创作吧。
      </p>

      <ul class="works-list">
        <li v-for="item in works" :key="item.task_id" class="work-row corner-card">
          <button class="work-open" @click="open(item)">
            <span class="work-thumb">
              <SkeletonImage v-if="item.image_url" :src="item.image_url" :alt="item.title || '工坊作品'" />
              <i v-else>{{ (item.title || TOOL_LABEL[item.tool_type] || "作")[0] }}</i>
            </span>
            <span class="work-copy">
              <b>{{ item.title || TOOL_LABEL[item.tool_type] || "未命名作品" }}</b>
              <span>{{ TOOL_LABEL[item.tool_type] || item.tool_type }} · {{ dateText(item.created_at) }}</span>
              <em v-if="item.status !== 'SUCCESS'">{{ item.status === "FAILED" ? (item.error_message || "生成失败") : "创作中 " + item.progress + "%" }}</em>
            </span>
          </button>
          <span class="work-actions">
            <button :class="{ on: item.collected }" :aria-pressed="item.collected" :disabled="busyId === item.task_id" @click="toggleCollect(item)">
              {{ item.collected ? "已收藏" : "收藏" }}
            </button>
            <button
              class="danger"
              :class="{ armed: confirmId === item.task_id }"
              :disabled="busyId === item.task_id"
              @click="remove(item)"
            >
              {{ confirmId === item.task_id ? "确认删除" : "删除" }}
            </button>
          </span>
        </li>
      </ul>

      <button v-if="works.length && total > works.length" class="more" :disabled="loading" @click="more">
        {{ loading ? "正在载入…" : "继续翻阅（还有 " + (total - works.length) + " 件）" }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.works-page {
  min-height: 100dvh;
  background: #f5ede4;
  color: #2d1810;
}
.page-padding {
  padding: 14px 16px 40px;
}
.works-total {
  flex-shrink: 0;
  font: 400 11px/1 var(--sans);
  font-style: normal;
  letter-spacing: 1px;
  color: #8a6125;
  white-space: nowrap;
}
.works-note {
  margin: 0 0 12px;
  font: 400 10px/1.7 var(--sans);
  letter-spacing: 0.3px;
  color: #8a7a70;
}
.filter-row {
  display: flex;
  gap: 8px;
  margin: 0 -16px 14px;
  padding: 0 16px;
  overflow-x: auto;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
}
.filter-row::-webkit-scrollbar {
  display: none;
}
.filter-row button {
  flex: none;
  height: 30px;
  padding: 0 14px;
  border: 1px solid rgba(200, 169, 110, 0.42);
  border-radius: 999px;
  background: #fffdf8;
  color: #5a3e36;
  font: 400 12px/1 var(--sans);
  white-space: nowrap;
}
.filter-row button.on {
  border-color: transparent;
  background: #8b1a1a;
  color: #f6ead9;
  font-weight: 500;
}
.works-state {
  margin: 18px 0 0;
  font: 400 11px/1.8 var(--sans);
  letter-spacing: 0.6px;
  color: #8a7a70;
  text-align: center;
}
.works-state.error {
  color: #8b1a1a;
}
.works-state button {
  margin-left: 6px;
  height: 24px;
  padding: 0 10px;
  border: 1px solid rgba(139, 105, 48, 0.36);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.8);
  color: #8a6125;
  font: 400 10px/1 var(--sans);
}
.works-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.work-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  content-visibility: auto;
  contain-intrinsic-size: auto 98px;
}
.work-open {
  display: flex;
  align-items: center;
  gap: 11px;
  flex: 1;
  min-width: 0;
  text-align: left;
}
.work-thumb {
  width: 54px;
  height: 72px;
  flex: none;
  display: grid;
  place-items: center;
  overflow: hidden;
  border: 1px solid rgba(200, 169, 110, 0.5);
  border-radius: 9px;
  background: #f2e5cf;
  color: #8a6125;
  font: 500 20px/1 var(--serif);
}
.work-thumb i {
  font-style: normal;
}
.work-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.work-copy b {
  font: 500 13px/1.4 var(--sans);
  letter-spacing: 0.4px;
  color: #2d1810;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.work-copy > span {
  font: 400 10px/1.4 var(--sans);
  letter-spacing: 0.6px;
  color: #8a7a70;
}
.work-copy em {
  font-style: normal;
  font: 400 10px/1.4 var(--sans);
  color: #8b1a1a;
}
.work-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: none;
}
.work-actions button {
  width: 58px;
  height: 27px;
  border: 1px solid rgba(139, 105, 48, 0.3);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.7);
  color: #7c665c;
  font: 400 10px/1 var(--sans);
  letter-spacing: 0.8px;
}
.work-actions button.on {
  border-color: rgba(139, 26, 26, 0.5);
  background: #fff0f0;
  color: #8b1a1a;
}
.work-actions .danger {
  border-color: rgba(139, 26, 26, 0.24);
  color: #8b1a1a;
}
.work-actions .danger.armed {
  border-color: rgba(139, 26, 26, 0.9);
  background: #8b1a1a;
  color: #fdf9f2;
}
.work-actions button:disabled {
  opacity: 0.55;
}
.more {
  display: block;
  width: 100%;
  height: 40px;
  margin-top: 14px;
  border: 1px dashed rgba(139, 105, 48, 0.42);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.55);
  color: #8a6125;
  font: 400 12px/1 var(--sans);
  letter-spacing: 1.6px;
}
.more:disabled {
  opacity: 0.6;
}
</style>
