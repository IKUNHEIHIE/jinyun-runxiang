import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";
const requireApp = createRequire(new URL("../user-web/package.json", import.meta.url));
const ts = requireApp("typescript");
function component(name, names, mocks) {
  const file = readFileSync(new URL("../user-web/src/mobile/views/" + name + ".vue", import.meta.url), "utf8");
  const source = file.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)[1];
  const compiled = ts.transpileModule(source + "\nexport { " + names.join(",") + " };", {
    compilerOptions:{ module:ts.ModuleKind.CommonJS, target:ts.ScriptTarget.ES2022 },
  }).outputText;
  const exports = {}, unmount = [];
  vm.runInNewContext(compiled, {
    exports, FormData, window:{ history:{ state:{} } }, clearTimeout(){}, setTimeout(){ return 1; },
    require(name) {
      if (name === "vue") return { ref:value=>({value}), computed:fn=>({get value(){return fn();}}), watch(){}, onMounted(){}, onUnmounted:fn=>unmount.push(fn) };
      if (name.endsWith(".vue")) return {};
      if (name in mocks) return mocks[name];
      throw new Error("Unexpected dependency " + name);
    },
  });
  return { ...exports, unmount };
}
const session = { token:"token-A", profile:{id:3} };
const route = { params:{tool:"shadow"}, query:{}, path:"/ai-workshop/shadow" };
const navigations = [], notices = [], saved = [], posts = [];
let request, send;
let profileRefreshes = 0;
const task = (id, type="SHADOW_PUPPET") => ({
  task_id:id, tool_type:type, status:"SUCCESS", collected:false,
  input:{prompt:"当前角色",role_type:"净角",face_style:"FLORAL",color_palette:["#2D5A3D"]},
  result:{title:"当前皮影",line_art_url:"/line-" + id + ".svg",colored_image_url:"/color-" + id + ".svg",print_template_url:"/paper-" + id + ".svg"},
});
const A = "a".repeat(32), B = "b".repeat(32), C = "c".repeat(32);
request = async () => task(A);
send = async () => ({collected:true});
const editor = component("WorkshopEditorPage", ["restore","poll","create","favorite","publish","download","task","prompt","role","color","faceStyle","selectedResult","error","busy","favoriteBusy"], {
  "vue-router":{useRoute:()=>route,useRouter:()=>({push:path=>navigations.push(path),replace:path=>navigations.push(path),back(){}})},
  "../api":{session, api:(...args)=>request(...args),post:(...args)=>{posts.push(args);return send(...args);},mediaUrl:url=>url,requireSession:()=>!!session.token,notify:value=>notices.push(value),loadProfile:async()=>{profileRefreshes++;session.profile.energy_value=220;}},
  "../design":{},
  "../files":{saveAsset:async url=>saved.push(url)},
});
await editor.restore();
assert.equal(editor.role.value,"净");
assert.equal(editor.color.value,"#2D5A3D");
assert.equal(editor.faceStyle.value,"FLORAL");
assert.equal(editor.prompt.value,"当前角色");
await editor.poll();
assert.equal(profileRefreshes,2,"Both restored success and newly polled success refresh the current account");
assert.equal(session.profile.energy_value,220);
for (const [value,prefix] of [["colored_image_url","/color-"],["line_art_url","/line-"],["print_template_url","/paper-"]]) {
  editor.selectedResult.value = value;
  await editor.download();
  assert.equal(saved.at(-1),prefix + A + ".svg");
}

let resolveFavorite;
send = () => new Promise(resolve=>{resolveFavorite=resolve;});
const pendingFavorite = editor.favorite();
session.token = "token-B"; // Same user, new authentication epoch.
request = async () => task(B);
await editor.restore();
resolveFavorite({collected:true});
await pendingFavorite;
assert.equal(editor.task.value.task_id,B);
assert.equal(editor.task.value.collected,false);
assert.equal(editor.favoriteBusy.value,false);
assert.equal(notices.length,0);

let resolveCreate;
editor.prompt.value = "旧账号的花脸";
editor.faceStyle.value = "BOLD";
send = () => new Promise(resolve=>{resolveCreate=resolve;});
const pendingCreate = editor.create();
assert.equal(posts.at(-1)[1].input_payload.face_style,"BOLD");
assert.equal(posts.at(-1)[1].input_payload.role_type,"净角");
session.token = "token-C"; session.profile = {id:4};
request = async () => task(C);
await editor.restore();
resolveCreate({task_id:A,status:"QUEUED"});
await pendingCreate;
assert.equal(editor.task.value.task_id,C);
assert.equal(editor.busy.value,false);

let resolvePoll;
request = () => new Promise(resolve=>{resolvePoll=resolve;});
const pendingPoll = editor.poll();
session.token = "token-D"; // Re-authentication without changing profile ID.
request = async () => task(B);
await editor.restore();
resolvePoll(task(A));
await pendingPoll;
assert.equal(editor.task.value.task_id,B);

let resolvePublish;
send = () => new Promise(resolve=>{resolvePublish=resolve;});
const pendingPublish = editor.publish();
session.token = "token-E"; session.profile = {id:3};
request = async () => task(C);
await editor.restore();
resolvePublish({id:99,status:"APPROVED"});
await pendingPublish;
assert.equal(navigations.length,0);

route.query = {task_id:A};
let requested;
request = async path=>{requested=path;return task(A);};
await editor.restore();
assert.equal(requested,"/ai/tasks/" + A);
request = async () => task(B,"BRONZE");
await editor.restore();
assert.equal(editor.task.value,undefined);
assert.equal(editor.error.value,"作品不属于当前工坊");
route.query = {task_id:"../invalid"};
request = async () => {throw new Error("Invalid task link must not reach the API");};
await editor.restore();
assert.equal(editor.error.value,"创作链接无效");

route.query = {};
request = async () => task(B);
await editor.restore();
request = () => new Promise(resolve=>{resolvePoll=resolve;});
const afterUnmount = editor.poll();
editor.unmount.forEach(fn=>fn());
resolvePoll(task(A)); await afterUnmount;
assert.equal(editor.task.value.task_id,B);

const serviceRoute = {params:{section:"collections"},query:{}};
let resolveCollection;
request = () => new Promise(resolve=>{resolveCollection=resolve;});
const service = component("PersonalServicePage", ["load","items","error","loading","itemUrl"], {
  "vue-router":{useRoute:()=>serviceRoute},
  "../api":{session,api:(...args)=>request(...args),post:async()=>({}),mediaUrl:url=>url,notify(){}},
  "../dates":{formatDate:value=>value},
});
const oldCollections = service.load();
session.token = "token-F";
request = async () => [{type:"ASSET",id:9,task_id:C,tool_type:"SHADOW_PUPPET",title:"当前账号创作"}];
await service.load();
resolveCollection([{type:"ASSET",id:8,title:"旧账号创作"}]);
await oldCollections;
assert.equal(service.items.value[0].title,"当前账号创作");
assert.equal(service.itemUrl(service.items.value[0]),"/ai-workshop/shadow?task_id=" + C);
assert.equal(service.error.value,"");
assert.equal(service.loading.value,false);
session.profile.energy_value = 200;
request = async path=>path === "/mobile/me/summary" ? {energy_value:220,post_count:2} : [];
const profile = component("ProfilePage", ["load","profileCount","summary","targetUrl"], {
  "vue-router":{useRoute:()=>({query:{}}),useRouter:()=>({replace(){}})},
  "../api":{session,api:(...args)=>request(...args),mediaUrl:url=>url,requireSession:()=>true,notify(){},logout(){},put(){},loadProfile(){}},
  "../dates":{formatDate:()=> "2026/10/17"}, "../design":{},
});
await profile.load();
assert.equal(profile.profileCount("energy_value"),220,"Profile energy comes from fresh database summary, not cached 200");
assert.equal(profile.targetUrl({type:"ASSET",id:12,task_id:C,tool_type:"SHADOW_PUPPET"}),"/ai-workshop/shadow?task_id=" + C,"Profile favorite card opens the exact saved task instead of a heritage entry");
let resolveSummary;
request = async path=>path === "/mobile/me/summary" ? new Promise(resolve=>{resolveSummary=resolve;}) : [];
const oldSummary = profile.load();
session.token = "token-G";
request = async path=>path === "/mobile/me/summary" ? {energy_value:240} : [];
await profile.load();
resolveSummary({energy_value:220}); await oldSummary;
assert.equal(profile.profileCount("energy_value"),240);
route.params.tool = "lacquer";
route.path = "/ai-workshop/lacquer";
route.query = {};
const lacquerTask = () => ({task_id:C,tool_type:"EMBROIDERY",status:"SUCCESS",input:{prompt:"绿色几何纹样",local_pattern:"GEOMETRIC",color_palette:["#2D5A4A"]},result:{reference_sketch_url:"/static/uploads/current.png",colored_image_url:"/static/current.svg",print_template_url:null}});
request = async () => lacquerTask();
const lacquer = component("WorkshopEditorPage", ["restore","upload","create","prompt","localPattern","color","sketch","busy","uploading","error"], {
  "vue-router":{useRoute:()=>route,useRouter:()=>({push:path=>navigations.push(path),replace:path=>navigations.push(path),back(){}})},
  "../api":{session,api:(...args)=>request(...args),post:(...args)=>send(...args),mediaUrl:url=>url,requireSession:()=>!!session.token,notify:value=>notices.push(value),loadProfile:async()=>{}},
  "../design":{},"../files":{saveAsset:async()=>{}},
});
await lacquer.restore();
assert.equal(lacquer.localPattern.value,"GEOMETRIC");
assert.equal(lacquer.color.value,"#2D5A4A");
assert.equal(lacquer.prompt.value,"绿色几何纹样");
assert.equal(lacquer.sketch.value,"/static/uploads/current.png");
let lacquerPayload;
send = async (path,body)=>{lacquerPayload=body;return {task_id:C,status:"SUCCESS",tool_type:"EMBROIDERY"};};
route.query = {task_id:C};
await lacquer.create();
assert.equal(lacquerPayload.input_payload.local_pattern,"GEOMETRIC");
assert.equal(lacquerPayload.input_payload.sketch_url,"/static/uploads/current.png");
assert.equal(lacquerPayload.input_payload.color_palette[0],"#2D5A4A");
assert.equal(navigations.at(-1).query.task_id,undefined,"New creation leaves the saved-task URL so refresh can restore the new task");
route.query = {};
let resolveUpload;
request = async () => new Promise(resolve=>{resolveUpload=resolve;});
const uploadEvent = () => ({target:{files:[new File([new Uint8Array([1,2,3])],"reference.png",{type:"image/png"})],value:"selected"}});
const oldUpload = lacquer.upload(uploadEvent());
session.token = "token-H";
request = async () => null;
await lacquer.restore();
assert.equal(lacquer.sketch.value,"");
request = async () => ({file_url:"/static/uploads/new.png"});
await lacquer.upload(uploadEvent());
resolveUpload({file_url:"/static/uploads/old-account.png"});
await oldUpload;
assert.equal(lacquer.sketch.value,"/static/uploads/new.png","A delayed old account upload cannot replace the new account reference");
assert.equal(lacquer.busy.value,false);
assert.equal(lacquer.uploading.value,false);
assert.equal(lacquer.error.value,"");
request = async () => ({...lacquerTask(),status:"FAILED",result:null,error_message:"生成失败，请重试"});
await lacquer.restore();
assert.equal(lacquer.error.value,"生成失败，请重试","A restored failed job is visible instead of appearing as an empty example");
console.log("PASS: selected exports, saved controls, task links, and stale restore/poll/create/favorite/publish/collection responses stay with their authentication context.");
