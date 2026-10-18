import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { randomUUID } from "node:crypto";
import vm from "node:vm";

const appRequire = createRequire(new URL("../user-web/package.json", import.meta.url));
const ts = appRequire("typescript");
const storage = new Map();
const api = {
  session: { profile: { id: 3 }, token: "test-session" },
  post: async () => { throw new Error("offline"); },
};
class Clock extends Date {
  static current = "2026-10-14T15:50:00Z";
  constructor(...args) { super(...(args.length ? args : [Clock.current])); }
}
function load(name, dependencies) {
  const source = readFileSync(new URL(`../user-web/src/mobile/${name}.ts`, import.meta.url), "utf8");
  const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } });
  const module = { exports: {} };
  vm.runInNewContext(compiled.outputText, {
    module, exports: module.exports,
    require: (id) => id in dependencies ? dependencies[id] : appRequire(id),
    Date: Clock, crypto: { randomUUID },
    localStorage: { getItem: (key) => storage.get(key) ?? null, setItem: (key, value) => storage.set(key, value) },
  }, { filename: `${name}.ts` });
  return module.exports;
}
const dates = load("dates", {});
const progress = load("progress", { "./api": api, "./dates": dates });
const payload = { course_id: 1, chapter_id: 1, position_seconds: 3, duration_seconds: 60, completed: false };
const pending = () => JSON.parse(storage.get("jinyun-progress-3"));
await progress.saveProgress(payload);
Clock.current = "2026-10-14T15:55:00Z";
await progress.saveProgress({ ...payload, position_seconds: 10 });
assert.equal(pending().length, 1);
assert.equal(pending()[0].payload.position_seconds, 10);
Clock.current = "2026-10-14T16:01:00Z";
await progress.saveProgress({ ...payload, position_seconds: 60, completed: true });
assert.equal(pending().length, 2);
assert.equal(pending()[0].payload.position_seconds, 10);
Clock.current = "2026-10-14T16:02:00Z";
await progress.saveProgress({ ...payload, position_seconds: 1 });
assert.equal(pending().length, 2);
assert.equal(pending()[1].payload.completed, true);
assert.notEqual(pending()[0].event_id, pending()[1].event_id);
api.post = async (_path, { events }) => ({ success_event_ids: [events[0].event_id], conflict_event_ids: [events[1].event_id] });
await progress.syncProgress();
assert.equal(pending().length, 1);
assert.equal(pending()[0].event_time, "2026-10-14T16:02:00.000Z");
api.post = async (_path, { events }) => ({ success_event_ids: events.map((event) => event.event_id) });
await progress.syncProgress();
assert.equal(pending().length, 0);
assert.equal(progress.progressState.pending, 0);
storage.set("jinyun-progress-3", JSON.stringify(Array.from({ length: 101 }, (_, index) => ({
  event_id: "switch-" + index, event_type: "PROGRESS_UPDATE", event_time: Clock.current, payload,
}))));
let requests = 0;
api.post = async (_path, { events }) => {
  requests++;
  api.session.token = "new-login-token"; // Profile loading can lag the new credential.
  return { success_event_ids: events.map((event) => event.event_id) };
};
await progress.syncProgress();
assert.equal(requests, 1, "Do not send the next old-user batch with a new login token");
assert.equal(pending().length, 1);
api.session.token = "test-session";
api.post = async (_path, { events }) => ({ success_event_ids: events.map((event) => event.event_id) });
await progress.syncProgress();
assert.equal(pending().length, 0);
console.log("PASS: same-day coalescing, Shanghai midnight, completion persistence, partial acknowledgment, retry and token changes between batches");
