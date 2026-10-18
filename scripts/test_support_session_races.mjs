import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";
const requireApp = createRequire(new URL("../user-web/package.json", import.meta.url));
const ts = requireApp("typescript");
const deferred = () => { let resolve, reject; const promise = new Promise((a,b) => {resolve=a;reject=b;}); return {promise,resolve,reject}; };
const flush = () => new Promise(resolve => setImmediate(resolve));
function component(file, names, mocks) {
  const source = readFileSync(new URL("../" + file, import.meta.url), "utf8").match(/<script setup lang="ts">([\s\S]*?)<\/script>/)[1];
  const compiled = ts.transpileModule(source + "\nexport {" + names.join(",") + "};", {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
  const exports = {}, watches = [], unmount = [];
  vm.runInNewContext(compiled, {exports,require(name) {
    if (name === "vue") return {ref:value=>({value}),computed:fn=>({get value(){return fn();}}),watch:(sources,fn)=>watches.push(fn),onUnmounted:fn=>unmount.push(fn)};
    if (name.endsWith(".vue")) return {};
    if (name in mocks) return mocks[name];
    throw new Error("Unexpected import " + name);
  }});
  return {...exports,watches,unmount};
}

let token = "A", get = async()=>({items:[],total:0}), put = async()=>({});
const messages = [], mutations = [];
const admin = component("admin-web/src/views/support/SupportView.vue", ["load","save","start","open","rows","loading","error","selected","visible","saving","form","draft"], {
  "@/api/request":{default:{get:(...args)=>get(...args),put:(...args)=>{mutations.push(args);return put(...args);}}},
  "@/utils/auth":{getToken:()=>({accessToken:token})},
  "element-plus":{ElMessage:{success:value=>messages.push(value),error:value=>messages.push(value)}}
});
const old = deferred(); get = ()=>old.promise;
const oldLoad = admin.load();
token = "B"; get = async()=>({items:[{id:2,status:"PENDING"}],total:1}); await admin.load();
old.resolve({items:[{id:1,content:"old private feedback"}],total:1}); await oldLoad;
assert.equal(admin.rows.value[0].id,2);
admin.form.value = {validate:async()=>true,clearValidate(){}};
admin.open({id:2,content:"current"},"resolve"); admin.draft.value.reply_text = "reply draft";
put = async()=>{throw new Error("network unavailable");};
await admin.save();
assert.equal(admin.visible.value,true); assert.equal(admin.saving.value,false);
assert.equal(admin.draft.value.reply_text,"reply draft");
assert.equal(messages.at(-1),"network unavailable");
const validation = deferred(), action = deferred();
admin.form.value.validate = ()=>validation.promise; put = ()=>action.promise;
const before = mutations.length, firstSave = admin.save(); await admin.save();
assert.equal(mutations.length,before);
validation.resolve(true); await flush();
assert.equal(mutations.length,before+1);
action.resolve({}); await firstSave;
assert.equal(admin.visible.value,false); assert.equal(admin.saving.value,false);
admin.form.value.validate = async()=>true;
admin.open({id:3},"resolve"); admin.draft.value.reply_text = "A reply";
const staleSave = deferred(); put = ()=>staleSave.promise;
const waitingSave = admin.save(); await flush();
token = "C"; admin.visible.value = true; admin.selected.value = {id:4}; admin.draft.value.reply_text = "C draft";
staleSave.resolve({}); await waitingSave;
assert.equal(admin.visible.value,true); assert.equal(admin.selected.value.id,4); assert.equal(admin.draft.value.reply_text,"C draft");

let sent, failed;
let removed = 0;
const windowMock = {location:{hash:"#/support/index"}}, httpExports = {};
const axiosMock = {create:()=>({interceptors:{request:{use:fn=>{sent=fn;}},response:{use:(_,fn)=>{failed=fn;}}}}),isCancel:()=>false};
const httpSource = readFileSync(new URL("../admin-web/src/utils/http/index.ts",import.meta.url),"utf8");
vm.runInNewContext(ts.transpileModule(httpSource,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText, {
  exports:httpExports,window:windowMock,require(name) {
    if(name==="axios") return {default:axiosMock};
    if(name==="qs") return {stringify:()=>""};
    if(name==="@/utils/auth") return {getToken:()=>({accessToken:token}),formatToken:t=>"Bearer "+t,removeToken:()=>removed++};
    throw new Error("Unexpected http import " + name);
  }
});
token = "A";
const configA = await sent({url:"/mobile/admin/feedback",headers:{}});
token = "B";
await assert.rejects(failed({config:configA,response:{status:401}}));
assert.equal(removed,0); assert.equal(windowMock.location.hash,"#/support/index");
const configB = await sent({url:"/mobile/admin/exchanges",headers:{}});
await assert.rejects(failed({config:configB,response:{status:401}}));
assert.equal(removed,1); assert.equal(windowMock.location.hash,"#/login");
const login = await sent({url:"/auth/login",headers:{}});
await assert.rejects(failed({config:login,response:{status:401}}));
assert.equal(removed,1);

const session = {token:"student-A",profile:{id:3}}, route = {params:{section:"feedback"},query:{}};
const pending = [], notices = [];
let history = [];
const mobile = component("user-web/src/mobile/views/PersonalServicePage.vue", ["feedback","feedbackBusy","content","contact","items","load"], {
  "vue-router":{useRoute:()=>route},
  "../api":{session,api:async()=>history,post:(url,body)=>{const task=deferred();pending.push({url,body,...task});return task.promise;},notify:value=>notices.push(value),mediaUrl:v=>v},
  "../dates":{formatDate:v=>v}
});
mobile.content.value = "A private draft";
const sendA = mobile.feedback();
session.token = "student-B"; session.profile.id = 4;
mobile.watches[0](["feedback",undefined,"student-B",4],["feedback",undefined,"student-A",3]);
assert.equal(mobile.content.value,""); assert.equal(mobile.feedbackBusy.value,false);
mobile.content.value = "B current draft";
const sendB = mobile.feedback();
pending[0].resolve({id:1}); await sendA;
assert.equal(mobile.content.value,"B current draft"); assert.equal(mobile.feedbackBusy.value,true);
assert.equal(notices.length,0);
history = [{id:2,content:"B current draft",status:"PENDING"}];
pending[1].resolve({id:2}); await sendB;
assert.equal(mobile.content.value,""); assert.equal(mobile.feedbackBusy.value,false);
assert.equal(mobile.items.value[0].id,2);
assert.equal(pending[1].url,"/mobile/feedback"); assert.equal(pending[1].body.content,"B current draft");
console.log("PASS: support list/actions, failed drafts, duplicate submits, stale administrator 401 and mobile feedback history stay in their authentication context.");
