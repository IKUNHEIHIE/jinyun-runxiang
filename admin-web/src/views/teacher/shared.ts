import { ElMessage } from "element-plus";
import { http } from "@/utils/http";
import { getToken } from "@/utils/auth";
export function errorMessage(error: any) {
  return error.response?.data?.detail || error.message || "操作失败，请重试";
}
export async function action(work: () => Promise<void>) {
  try {
    await work();
  } catch (error) {
    ElMessage.error(String(errorMessage(error)));
  }
}
export function dateText(value?: string) {
  if (!value) return "—";
  const iso = value.replace(" ", "T");
  const date = new Date(/Z$|[+-]\d\d:\d\d$/.test(iso) ? iso : iso + "Z");
  return Number.isNaN(+date)
    ? "—"
    : date.toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" });
}
export async function exportPlan(id: number, isCurrent = () => true) {
  const token = getToken()?.accessToken;
  const valid = () =>
    !!token && token === getToken()?.accessToken && isCurrent();
  if (!valid()) return;
  const blob = await http.request<Blob>(
    "get",
    `/mobile/teacher/lesson-plans/${id}/pptx`,
    { responseType: "blob" }
  );
  if (!valid()) return;
  if (blob.type.includes("json")) {
    const result = JSON.parse(await blob.text());
    if (valid())
      throw new Error(result.message || result.detail || "文件导出失败");
    return;
  }
  const url = URL.createObjectURL(blob),
    link = document.createElement("a");
  link.href = url;
  link.download = "津韵润乡-备课方案.pptx";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 60000);
}
