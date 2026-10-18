import vue from "@vitejs/plugin-vue";
import vueJsx from "@vitejs/plugin-vue-jsx";
import tailwindcss from "@tailwindcss/vite";
import Icons from "unplugin-icons/vite";
import svgLoader from "vite-svg-loader";
import compression from "vite-plugin-compression";
import type { PluginOption } from "vite";

export function getPluginsList(_cdn: boolean, compress: string): PluginOption[] {
  const plugins: PluginOption[] = [vue(), vueJsx(), tailwindcss(), svgLoader(), Icons({ compiler: "vue3" })];
  if (compress.includes("gzip") || compress.startsWith("both")) {
    plugins.push(compression({ algorithm: "gzip", deleteOriginFile: false }));
  }
  if (compress.includes("brotli") || compress.startsWith("both")) {
    plugins.push(compression({ algorithm: "brotliCompress", deleteOriginFile: false }));
  }
  return plugins;
}
