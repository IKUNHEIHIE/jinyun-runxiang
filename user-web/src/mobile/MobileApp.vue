<script setup lang="ts">
import { computed, watch, onMounted, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Capacitor, SystemBars, SystemBarsStyle } from "@capacitor/core";
import { App } from "@capacitor/app";
import { session, loadProfile, notify } from "./api";
import { syncProgress } from "./progress";
import { designIcon } from "./design";
import AuthSheet from "./components/AuthSheet.vue";
const route = useRoute(),
  router = useRouter();
const tabs = [
  { label: "首页", path: "/", icon: "5:02265", tab: "home" },
  { label: "小课堂", path: "/courses", icon: "5:02254", tab: "courses" },
  { label: "AI工坊", path: "/ai-workshop", icon: "5:02243", tab: "workshop" },
  { label: "社区", path: "/community", icon: "5:02229", tab: "community" },
  { label: "我的", path: "/profile", icon: "5:02215", tab: "profile" },
];
const showTabs = computed(() => !route.meta.hideTabs);
const walkingNav = computed(() => route.meta.navTheme === "walking");
const walkingIcons: Record<string, string> = {
  home: "40:12019",
  courses: "40:12052",
  workshop: "40:12042",
  community: "40:12010",
  profile: "40:12024",
};
const pageTransition = computed(() => {
  const depth = (path: string) => path.split("/").filter(Boolean).length;
  const back = String(window.history.state?.back || "").replace(/^#/, "");
  const current = depth(route.path);
  const previous = depth(back);
  if (!previous || previous === current) return "page-fade";
  return current > previous ? "page-push" : "page-pop";
});
const surface = computed(() =>
  route.params.tool === "bronze"
    ? "#f5f0e6"
    : route.params.tool === "shadow"
      ? "#faf6ee"
      : route.params.tool === "lacquer"
        ? "#f0ebe0"
        : typeof route.meta.surface === "string"
          ? route.meta.surface
          : undefined,
);
watch(
  () => [session.profile?.id, session.profile?.role_code],
  () => {
    void syncProgress();
    if (
      route.meta.teacher &&
      session.profile?.role_code &&
      !["TEACHER", "ADMIN"].includes(session.profile.role_code)
    )
      router.replace("/profile");
  },
);
watch(
  () => session.token,
  (token) => {
    if (!token && (route.meta.requiresAuth || route.meta.teacher))
      router.replace("/profile");
    else if (token) void refreshAndSync();
  },
);
let timer: ReturnType<typeof setInterval>;
const removers: Array<() => Promise<void>> = [];
let mounted = true;
let profileRequest: { token: string; promise: Promise<void> } | undefined;
async function refreshAndSync(silent = true) {
  if (!mounted) return;
  const token = session.token;
  try {
    if (token) {
      if (profileRequest?.token === token) await profileRequest.promise;
      else {
        const request = { token, promise: loadProfile() };
        profileRequest = request;
        try {
          await request.promise;
        } finally {
          if (profileRequest === request) profileRequest = undefined;
        }
      }
    }
    if (mounted && token === session.token) await syncProgress();
  } catch (e) {
    if (mounted && !silent && token === session.token)
      notify((e as Error).message);
  }
}
function reconnect() {
  void refreshAndSync();
}
watch(() => route.path, reconnect);
onMounted(async () => {
  window.addEventListener("online", reconnect);
  timer = setInterval(() => {
    if (session.token && !session.profile) reconnect();
    else void syncProgress();
  }, 30000);
  void refreshAndSync(false);
  if (Capacitor.isNativePlatform()) {
    await SystemBars.setStyle({ style: SystemBarsStyle.Light });
    const back = await App.addListener("backButton", async () => {
      if (session.authVisible) session.authVisible = false;
      else if (
        document.querySelector<HTMLElement>(
          '[role="dialog"][aria-modal="true"] .sheet-close',
        )
      )
        document
          .querySelector<HTMLElement>(
            '[role="dialog"][aria-modal="true"] .sheet-close',
          )!
          .click();
      else if (window.history.state.back) router.back();
      else if (route.path !== "/") router.replace("/");
      else await App.minimizeApp();
    });
    if (!mounted) {
      await back.remove();
      return;
    }
    removers.push(() => back.remove());
    const active = await App.addListener("appStateChange", (state) => {
      if (state.isActive) reconnect();
    });
    if (!mounted) {
      await active.remove();
      return;
    }
    removers.push(() => active.remove());
  }
});
onUnmounted(() => {
  mounted = false;
  clearInterval(timer);
  window.removeEventListener("online", reconnect);
  removers.forEach((remove) => remove());
});
</script>
<template>
  <div
    class="mobile-app"
    :class="{ 'no-tabs': !showTabs }"
    :style="{
      background: surface,
    }"
  >
    <div
      class="system-top-inset"
      :style="{ background: surface || 'var(--paper)' }"
      aria-hidden="true"
    />
    <RouterView v-slot="{ Component, route: viewRoute }">
      <Transition :name="pageTransition" mode="out-in">
        <component :is="Component" :key="viewRoute.path" />
      </Transition>
    </RouterView>
    <nav
      v-if="showTabs"
      class="bottom-nav"
      :class="{ 'walking-nav': walkingNav }"
      aria-label="主导航"
    >
      <RouterLink
        v-for="tab in tabs"
        :key="tab.path"
        :to="
          tab.tab === 'profile' &&
          ['TEACHER', 'ADMIN'].includes(session.profile?.role_code || '')
            ? '/teacher'
            : tab.path
        "
        :class="{ active: route.meta.tab === tab.tab }"
        :aria-current="route.meta.tab === tab.tab ? 'page' : undefined"
        ><img
          :src="
            walkingNav
              ? designIcon('layer-40-07198', walkingIcons[tab.tab])
              : designIcon('home', tab.icon)
          "
          alt=""
        /><span>{{ tab.label }}</span></RouterLink
      >
    </nav>
    <AuthSheet /><Teleport to="body"
      ><div
        v-if="session.notice"
        class="toast"
        role="status"
        aria-live="polite"
      >
        {{ session.notice }}
      </div></Teleport
    >
  </div>
</template>
<style scoped>
.system-top-inset {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: var(--safe-top);
  background: var(--paper);
  z-index: 60;
  pointer-events: none;
}
.walking-nav {
  background: #f4f7f2;
  border-color: #e3ebde;
}
.walking-nav:before {
  background: #e3ebde;
}
.walking-nav a {
  color: #b8ad9e;
  font-family: var(--serif);
}
.walking-nav a.active {
  color: #6b8e6b;
  font-weight: 400;
}
.page-fade-enter-active,
.page-fade-leave-active,
.page-push-enter-active,
.page-push-leave-active,
.page-pop-enter-active,
.page-pop-leave-active {
  transition:
    opacity 0.16s ease,
    transform 0.2s cubic-bezier(0.22, 0.61, 0.36, 1);
  will-change: opacity, transform;
}
.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
  transform: translate3d(0, 4px, 0);
}
.page-push-enter-from {
  opacity: 0;
  transform: translate3d(16px, 0, 0);
}
.page-push-leave-to {
  opacity: 0;
  transform: translate3d(-10px, 0, 0);
}
.page-pop-enter-from {
  opacity: 0;
  transform: translate3d(-14px, 0, 0);
}
.page-pop-leave-to {
  opacity: 0;
  transform: translate3d(10px, 0, 0);
}
@media (prefers-reduced-motion: reduce) {
  .page-fade-enter-active,
  .page-fade-leave-active,
  .page-push-enter-active,
  .page-push-leave-active,
  .page-pop-enter-active,
  .page-pop-leave-active {
    transition: none;
  }
}
</style>
