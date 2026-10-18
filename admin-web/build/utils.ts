import { fileURLToPath } from "node:url";
import { resolve, dirname } from "node:path";
import { readFileSync } from "node:fs";

export const root = fileURLToPath(new URL("../", import.meta.url));
export const alias = { "@": resolve(root, "src"), "@build": resolve(root, "build") };
export const pathResolve = (path: string, base = import.meta.url) =>
  resolve(dirname(fileURLToPath(base)), path);
export function wrapperEnv(env: Record<string, string>) {
  return {
    VITE_PORT: Number(env.VITE_PORT || 5173),
    VITE_PUBLIC_PATH: env.VITE_PUBLIC_PATH || "/",
    VITE_CDN: env.VITE_CDN === "true",
    VITE_COMPRESSION: env.VITE_COMPRESSION || "none"
  };
}
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
export const __APP_INFO__ = { pkg, lastBuildTime: new Date().toISOString() };
