import { reactive } from "vue";
import { Capacitor } from "@capacitor/core";

export interface Profile {
  id: number;
  nickname: string;
  username: string;
  avatar_url?: string;
  role_code: string;
  energy_value: number;
  level_code: string;
  grade?: string;
  bio?: string;
  school_name?: string;
  district?: string;
  badges?: Array<{ id: number; name: string; icon_url: string }>;
}

// Android production builds must supply an HTTPS API origin. Emulator debug uses .env.android.
export const apiBase = (import.meta.env.VITE_API_BASE_URL || "/api").replace(
  /\/$/,
  "",
);
export const apiOrigin = /^https?:/.test(apiBase)
  ? new URL(apiBase).origin
  : window.location.origin;
export function mediaUrl(value?: string) {
  if (!value) return "";
  if (value.startsWith("/design/")) return value;
  if (value.startsWith("/")) {
    const cache = value.startsWith("/static/design/")
      ? (value.includes("?") ? "&" : "?") + "v=hd1"
      : "";
    return apiOrigin + value + cache;
  }
  if (/^https?:\/\//.test(value)) return value;
  return "";
}

export const session = reactive({
  profile: null as Profile | null,
  token: localStorage.getItem("jinyun_user_token") || "",
  authVisible: false,
  authRedirect: "",
  notice: "",
});
let noticeTimer: ReturnType<typeof setTimeout>;
export function notify(message: string) {
  session.notice = message;
  clearTimeout(noticeTimer);
  noticeTimer = setTimeout(() => {
    session.notice = "";
  }, Math.min(10000, Math.max(4000, message.length * 90)));
}
export function requireSession(redirectTo = "") {
  if (session.token) return true;
  session.authRedirect = redirectTo;
  session.authVisible = true;
  return false;
}
export async function api<T = any>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  if (Capacitor.isNativePlatform() && !/^https?:\/\//.test(apiBase)) {
    throw new Error("此安装包未配置服务地址，请使用已配置服务的安装包");
  }
  const headers = new Headers(options.headers);
  const requestToken = session.token;
  if (session.token) headers.set("Authorization", "Bearer " + session.token);
  if (options.body && !(options.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  const controller = new AbortController();
  const cancel = () => controller.abort();
  options.signal?.addEventListener("abort", cancel, { once: true });
  if (options.signal?.aborted) controller.abort();
  const timer = setTimeout(() => controller.abort(), 20000);
  try {
    const response = await fetch(apiBase + path, {
      ...options,
      headers,
      signal: controller.signal,
    });
    if (response.status === 401 && requestToken === session.token) {
      session.token = "";
      session.profile = null;
      localStorage.removeItem("jinyun_user_token");
      localStorage.removeItem("jinyun_user_info");
      session.authVisible = true;
    }
    let result;
    try {
      result = await response.json();
    } catch {
      throw new Error("服务暂时无法响应，请稍后重试");
    }
    if (!result || typeof result !== "object" || (response.ok && !("code" in result)))
      throw new Error("服务返回异常，请稍后重试");
    if (!response.ok || result.code !== 0)
      throw new Error(
        result.message ||
          (typeof result.detail === "string" ? result.detail : "") ||
          (response.status === 429
            ? "操作有些频繁，请稍后再试"
            : response.status === 422
              ? "请检查填写的信息后重试"
              : "操作失败，请稍后重试"),
      );
    return result.data as T;
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError")
      throw new Error("连接超时，请检查网络后重试");
    if (error instanceof TypeError)
      throw new Error("暂时无法连接服务，请检查网络后重试");
    throw error;
  } finally {
    clearTimeout(timer);
    options.signal?.removeEventListener("abort", cancel);
  }
}
export const post = <T = any>(path: string, body: unknown = {}) =>
  api<T>(path, { method: "POST", body: JSON.stringify(body) });
export const put = <T = any>(path: string, body: unknown) =>
  api<T>(path, { method: "PUT", body: JSON.stringify(body) });
export async function loadProfile() {
  const token = session.token;
  if (token) {
    const profile = await api<Profile>("/auth/me");
    if (token === session.token) session.profile = profile;
  }
}
export async function logout() {
  const token = session.token;
  await post("/auth/logout");
  if (token !== session.token) return;
  session.token = "";
  session.profile = null;
  localStorage.removeItem("jinyun_user_token");
  localStorage.removeItem("jinyun_user_info");
}
