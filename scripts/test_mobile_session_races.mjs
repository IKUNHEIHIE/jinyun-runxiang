import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(path.join(root, "user-web/package.json"));
const ts = require("typescript");
const source = fs.readFileSync(path.join(root, "user-web/src/mobile/api.ts"), "utf8")
  .replaceAll("import.meta.env", '({ VITE_API_BASE_URL: "https://test.invalid/api" })');
const compiled = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS },
}).outputText;
const storage = new Map();
const requests = [];
const exports = {};
vm.runInNewContext(compiled, {
  exports,
  require: (name) => {
    if (name === "vue") return { reactive: (value) => value };
    if (name === "@capacitor/core") return { Capacitor: { isNativePlatform: () => false } };
    throw new Error("Unexpected dependency: " + name);
  },
  localStorage: {
    getItem: (key) => storage.get(key) ?? null,
    setItem: (key, value) => storage.set(key, value),
    removeItem: (key) => storage.delete(key),
  },
  window: { location: { origin: "https://test.invalid" } },
  URL, Headers, FormData, AbortController, setTimeout, clearTimeout,
  fetch: (url, options) => new Promise((resolve) => requests.push({ url, options, resolve })),
});
const { session, api, loadProfile, logout } = exports;
const profileA = { id: 1, nickname: "A" }, profileB = { id: 2, nickname: "B" };
function signIn(token, profile) {
  session.token = token;
  session.profile = profile;
  session.authVisible = false;
  storage.set("jinyun_user_token", token);
  storage.set("jinyun_user_info", JSON.stringify(profile));
}
function answer(status, data) {
  const request = requests.shift();
  assert.ok(request, "Request must exist before answering");
  request.resolve({ status, ok: status < 400, json: async () => ({ code: status < 400 ? 0 : 401, message: "expired", data }) });
  return request;
}
function expectB() {
  assert.equal(session.token, "token-B");
  assert.equal(session.profile, profileB);
  assert.equal(storage.get("jinyun_user_token"), "token-B");
  assert.equal(storage.get("jinyun_user_info"), JSON.stringify(profileB));
  assert.equal(session.authVisible, false);
}

signIn("token-A", profileA);
const old401 = api("/private");
signIn("token-B", profileB);
assert.equal(answer(401).options.headers.get("Authorization"), "Bearer token-A");
await assert.rejects(old401, /expired/);
expectB();

signIn("token-A", profileA);
const oldProfile = loadProfile();
signIn("token-B", profileB);
answer(200, profileA);
await oldProfile;
expectB();

signIn("token-A", profileA);
const oldLogout = logout();
signIn("token-B", profileB);
answer(200, {});
await oldLogout;
expectB();

const current401 = api("/private");
answer(401);
await assert.rejects(current401, /expired/);
assert.equal(session.token, "");
assert.equal(session.profile, null);
assert.equal(session.authVisible, true);
assert.equal(storage.has("jinyun_user_token"), false);
assert.equal(storage.has("jinyun_user_info"), false);
assert.equal(requests.length, 0);
const invalidJson = api('/unavailable');
requests.shift().resolve({ status:503,ok:false,json:async()=>{throw new SyntaxError('Unexpected token <');} });
await assert.rejects(invalidJson, /服务暂时无法响应/);
const detailError=api('/validation');
requests.shift().resolve({status:400,ok:false,json:async()=>({detail:'请选择有效图片'})});
await assert.rejects(detailError,/请选择有效图片/);
const validation=api('/validation');
requests.shift().resolve({status:422,ok:false,json:async()=>({detail:[{msg:'Field required'}]})});
await assert.rejects(validation,/请检查填写的信息/);
const malformed=api('/malformed');
requests.shift().resolve({status:200,ok:true,json:async()=>null});
await assert.rejects(malformed,/服务返回异常/);
console.log("PASS: stale 401, profile and logout responses preserve the new identity; current 401 clears private session data.");
