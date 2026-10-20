import { Capacitor } from "@capacitor/core";
import { Filesystem, Directory } from "@capacitor/filesystem";
import { Share } from "@capacitor/share";
import { apiBase, mediaUrl, session } from "./api";

function base64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1]);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}
export async function saveBlob(
  blob: Blob,
  filename: string,
  title = "津韵润乡作品",
  options: { isCurrent?: () => boolean; privateFile?: boolean } = {},
) {
  const valid = options.isCurrent || (() => true);
  const check = () => {
    if (!valid()) throw new Error("账号或页面已变更，请重新导出");
  };
  const name = filename.replace(/[^\p{L}\p{N}._-]/gu, "-");
  const safeName = !name || /^\.+$/.test(name) ? "津韵润乡文件" : name;
  check();
  if (Capacitor.isNativePlatform()) {
    const data = await base64(blob);
    check();
    const path = options.privateFile
      ? "jinyun/private-" + crypto.randomUUID() + "/" + safeName
      : "jinyun/" + safeName;
    const file = await Filesystem.writeFile({
      path,
      data,
      directory: Directory.Cache,
      recursive: true,
    });
    if (!valid()) {
      // This unique export belongs to this request; never remove a shared filename.
      if (options.privateFile)
        await Filesystem.deleteFile({ path, directory: Directory.Cache }).catch(
          () => {},
        );
      check();
    }
    try {
      await Share.share({
        title,
        files: [file.uri],
        dialogTitle: "保存或分享文件",
      });
    } catch (error) {
      if (
        (error as Error).name !== "AbortError" &&
        !/^Share cancel(?:l)?ed$/i.test((error as Error).message)
      )
        throw error;
      return false;
    }
  } else {
    check();
    const url = URL.createObjectURL(blob),
      anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = safeName;
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return true;
}
const KNOWN_CONTAINER = /\.(svg|png|jpe?g|webp|glb|mp4)$/i;
export async function saveAsset(
  url: string,
  filename: string,
  title?: string,
) {
  const response = await fetch(mediaUrl(url), {
    signal: AbortSignal.timeout(20000),
  });
  if (!response.ok) throw new Error("文件暂时无法下载");
  // A capability URL hides its container behind ?exp=&sig=, and callers often guess ".png".
  const container = url.split("?")[0].match(KNOWN_CONTAINER)?.[0];
  const name = container ? filename.replace(KNOWN_CONTAINER, "") + container : filename;
  await saveBlob(await response.blob(), name, title || "津韵润乡作品");
}
export async function saveApiFile(
  path: string,
  filename: string,
  isCurrent = () => true,
) {
  const token = session.token;
  const valid = () => !!token && token === session.token && isCurrent();
  const check = () => {
    if (!valid()) throw new Error("账号或页面已变更，请重新导出");
  };
  check();
  const response = await fetch(apiBase + path, {
    headers: { Authorization: "Bearer " + token },
    signal: AbortSignal.timeout(60000),
  });
  check();
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      error.message ||
        (typeof error.detail === "string" && error.detail) ||
        "文件导出失败",
    );
  }
  const blob = await response.blob();
  check();
  return saveBlob(blob, filename, "津韵润乡备课方案", {
    isCurrent: valid,
    privateFile: true,
  });
}
