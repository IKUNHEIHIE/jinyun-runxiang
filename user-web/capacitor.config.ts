import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.jinyun.runxiang",
  appName: "津韵润乡",
  webDir: "dist",
  plugins: {
    SystemBars: { insetsHandling: "css", style: "LIGHT" },
  },
  android: {
    allowMixedContent: (process.env.VITE_API_BASE_URL || "").startsWith(
      "http://",
    ),
  },
};

export default config;
