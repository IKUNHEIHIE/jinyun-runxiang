import { ref } from "vue";
import { api, loadProfile, mediaUrl, post } from "./api";

export type Evaluation = {
  evaluation_id: string;
  title: string;
  image_url: string;
  total_score: number;
  stars: number;
  dimensions: Record<string, { name: string; score: number; feedback: string }>;
  mentor_comment: string;
  energy_reward: number;
};

/** The vision model only accepts raster images, so SVG works are flattened on a paper ground. */
async function toPng(url: string): Promise<Blob> {
  const response = await fetch(mediaUrl(url), { signal: AbortSignal.timeout(20000) });
  if (!response.ok) throw new Error("作品图片读取失败，请重试");
  const blob = await response.blob();
  if (blob.type !== "image/svg+xml") return blob;
  const objectUrl = URL.createObjectURL(blob);
  try {
    const image = await new Promise<HTMLImageElement>((resolve, reject) => {
      const node = new Image();
      node.onload = () => resolve(node);
      node.onerror = () => reject(new Error("作品图片解析失败"));
      node.src = objectUrl;
    });
    const ratio = (image.naturalHeight || 800) / (image.naturalWidth || 600);
    const canvas = document.createElement("canvas");
    canvas.width = 720;
    canvas.height = Math.round(720 * ratio);
    const context = canvas.getContext("2d");
    if (!context) throw new Error("当前设备不支持图像合成");
    context.fillStyle = "#fbf7ee";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.drawImage(image, 0, 0, canvas.width, canvas.height);
    const png = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/png"));
    if (!png) throw new Error("作品导出失败，请重试");
    return png;
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
}

export function useEvaluation(heritageType = "SHADOW_PUPPET") {
  const busy = ref(false);
  const result = ref<Evaluation | null>(null);
  const error = ref("");

  async function run(imageUrl: string, title: string, notes = "") {
    if (busy.value || !imageUrl) return;
    busy.value = true;
    error.value = "";
    try {
      const form = new FormData();
      form.append(
        "file",
        new File([await toPng(imageUrl)], (title || "work").replace(/[\\/:*?"<>|]/g, "") + ".png", {
          type: "image/png",
        }),
      );
      const upload = await api<{ file_url: string }>("/ai/assets/upload", { method: "POST", body: form });
      result.value = await post<Evaluation>("/ai/evaluate", {
        image_url: upload.file_url,
        heritage_type: heritageType,
        title: (title || "非遗作品").slice(0, 60),
        notes: notes.slice(0, 200),
      });
      if (result.value?.energy_reward) await loadProfile().catch(() => null);
    } catch (e) {
      error.value = e instanceof Error ? e.message : "导师点评暂时不可用，请稍后重试";
    } finally {
      busy.value = false;
    }
  }

  function reset() {
    result.value = null;
    error.value = "";
  }

  return { busy, result, error, run, reset };
}
