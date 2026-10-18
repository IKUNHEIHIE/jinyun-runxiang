import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";

const appRequire = createRequire(new URL("../user-web/package.json", import.meta.url));
const ts = appRequire("typescript");
const file = readFileSync(new URL("../user-web/src/mobile/views/CoursePlayerPage.vue", import.meta.url), "utf8");
const script = file.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)[1];
const compiled = ts.transpileModule(script + "\nexport { load, report, beginPlayback, restorePosition, changeChapter, video, course, collected };", {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
const session = { token: "token-A", profile: { id: 3 } };
const route = { params: { id: "1" } };
const saved = [], unmounts = [];
const data = (title) => ({ id: 1, title, chapters: [
  { id: 1, video_url: "/test.mp4", progress: { position_seconds: 10, completed: true } },
  { id: 2, video_url: "/test2.mp4", progress: { position_seconds: 3, completed: false } },
] });
let request = async (path) => path === "/courses/1" ? data("current course") : [];
const exports = {};
vm.runInNewContext(compiled, {
  exports,
  require: (name) => {
    if (name === "vue") return {
      ref: (value) => ({ value }), computed: (fn) => ({ get value() { return fn(); } }),
      watch: () => {}, onUnmounted: (fn) => unmounts.push(fn),
    };
    if (name === "vue-router") return { useRoute: () => route };
    if (name === "../api") return { session, api: (...args) => request(...args), mediaUrl: (url) => url };
    if (name === "../progress") return {
      progressState: {}, syncProgress: async () => {},
      saveProgress: async (payload) => saved.push({ uid: session.profile.id, payload: JSON.parse(JSON.stringify(payload)) }),
    };
    if (name.endsWith(".vue")) return {};
    throw new Error("Unexpected dependency " + name);
  },
});
await exports.load();
const video = { duration: 10, currentTime: 0, ended: false, pause() {} };
exports.video.value = video;
exports.restorePosition();
assert.equal(video.currentTime, 10);
await exports.report();
await exports.report(true);
assert.equal(saved.length, 0, "Restoring a saved position is not new study activity");

exports.beginPlayback();
video.currentTime = 4;
await exports.report(true);
assert.deepEqual(saved[0], { uid: 3, payload: { course_id: 1, chapter_id: 1, position_seconds: 4, duration_seconds: 10, completed: false } });
video.currentTime = 10;
video.ended = true;
await exports.report(true);
assert.equal(saved[1].payload.completed, true, "Actual playback completion remains reportable");

session.token = "token-B";
session.profile = { id: 4 };
await exports.report(true);
exports.beginPlayback();
await exports.report(true);
assert.equal(saved.length, 2, "Outgoing playback cannot become the new user's progress");
await exports.load();
exports.beginPlayback();
video.currentTime = 2;
video.ended = false;
await exports.report(true);
assert.equal(saved.at(-1).uid, 4);
await exports.changeChapter(1);
const afterChange = saved.length;
exports.restorePosition();
await exports.report(true);
assert.equal(saved.length, afterChange, "Each chapter must actually start playing");

let resolveOld;
session.token = "token-A";
session.profile = { id: 3 };
request = () => new Promise((resolve) => { resolveOld = resolve; });
const oldLoad = exports.load();
session.token = "token-B";
session.profile = { id: 4 };
request = async (path) => path === "/courses/1" ? data("new user's course") : [];
await exports.load();
resolveOld(data("old user's course"));
await oldLoad;
assert.equal(exports.course.value.title, "new user's course");
assert.equal(exports.collected.value, false);
for (const unmount of unmounts) unmount();
assert.equal(saved.length, afterChange);
console.log("PASS: metadata restoration never reports study; actual playback still saves completion; chapter/account changes and stale loads remain isolated.");
