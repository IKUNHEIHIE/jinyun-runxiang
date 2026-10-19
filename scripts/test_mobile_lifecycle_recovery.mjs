import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";
const requireApp = createRequire(new URL("../user-web/package.json",import.meta.url));
const ts = requireApp("typescript");
const source = readFileSync(new URL("../user-web/src/mobile/MobileApp.vue",import.meta.url),"utf8").match(/<script setup lang="ts">([\s\S]*?)<\/script>/)[1];
const defer = () => {let resolve,reject; const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};};
const flush = () => new Promise(resolve=>setImmediate(resolve));
const session = {token:"A",profile:null}, route={path:"/",params:{},meta:{}};
const watches=[],mount=[],unmount=[],dom={},native={},notices=[],exports={},navigations=[];
let interval, calls=0, work, clears=0;
const mocks = {
  "vue":{ref:value=>({value}),computed:fn=>({get value(){return fn();}}),watch:(_,fn)=>watches.push(fn),onMounted:fn=>mount.push(fn),onUnmounted:fn=>unmount.push(fn)},
  "vue-router":{useRoute:()=>route,useRouter:()=>({replace:path=>navigations.push(path),back(){}})},
  "@capacitor/core":{Capacitor:{isNativePlatform:()=>true},SystemBars:{setStyle:async()=>{}},SystemBarsStyle:{Light:"LIGHT"}},
  "@capacitor/app":{App:{addListener:async(name,fn)=>{native[name]=fn;return {remove:async()=>{delete native[name];}};}}},
  "./api":{session,notify:value=>notices.push(value),loadProfile:async()=>{calls++;const token=session.token;const data=await work();if(token===session.token)session.profile=data;}},
  "./progress":{syncProgress:async()=>{}},"./design":{designIcon:()=>""}
};
vm.runInNewContext(ts.transpileModule(source+"\nexport {refreshAndSync,updatePageTransition,pageTransition};",{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{
  exports,window:{addEventListener:(name,fn)=>{dom[name]=fn;},removeEventListener:(name,fn)=>{if(dom[name]===fn)delete dom[name];}},
  setInterval:fn=>{interval=fn;return 1;},clearInterval:()=>clears++,
  require(name){if(name.endsWith('.vue'))return {};if(name in mocks)return mocks[name];throw new Error(name);}
});
const offline = defer(); work=()=>offline.promise;
await mount[0]();
assert.equal(calls,1); assert.ok(native.backButton); assert.ok(native.appStateChange); assert.ok(dom.online);
offline.reject(new Error("offline")); await flush();
assert.equal(session.token,"A"); assert.equal(notices[0],"offline");
work=async()=>({id:1,energy_value:260});dom.online();await flush();
assert.equal(session.profile.energy_value,260);
work=async()=>({id:1,energy_value:240});native.appStateChange({isActive:true});await flush();
assert.equal(session.profile.energy_value,240);
work=async()=>({id:1,energy_value:280});route.path='/profile';watches[2]();await flush();
assert.equal(session.profile.energy_value,280);
const shared=defer(); work=()=>shared.promise;const before=calls;
const first=exports.refreshAndSync(),second=exports.refreshAndSync();
assert.equal(calls,before+1);shared.resolve({id:1,energy_value:260});await Promise.all([first,second]);
const a=defer(),b=defer();work=()=>a.promise;const old=exports.refreshAndSync();
session.token="B";work=()=>b.promise;const current=exports.refreshAndSync();
b.resolve({id:2,energy_value:100});await current;
a.resolve({id:1,energy_value:999});await old;
assert.equal(session.profile.id,2); assert.equal(session.profile.energy_value,100);
session.profile=null;work=async()=>({id:2,energy_value:120});interval();await flush();
assert.equal(session.profile.energy_value,120);
route.meta.teacher=true;session.profile.role_code="STUDENT";watches[0]();
assert.equal(navigations.at(-1),"/profile","Restored or changed student role cannot remain on a teacher route");
const previous=navigations.length;session.profile.role_code="TEACHER";watches[0]();assert.equal(navigations.length,previous);
exports.updatePageTransition('/courses','/');assert.equal(exports.pageTransition.value,'page-fade','Main tabs crossfade');
exports.updatePageTransition('/community/1','/community');assert.equal(exports.pageTransition.value,'page-push','Details enter forward');
exports.updatePageTransition('/community','/community/1');assert.equal(exports.pageTransition.value,'page-pop','Returning from details reverses the direction');
unmount[0]();await flush();assert.equal(clears,1);assert.equal(dom.online,undefined);assert.equal(Object.keys(native).length,0);
const ended=calls;await exports.refreshAndSync();assert.equal(calls,ended);
console.log("PASS: root account recovery on online, route/resume and missing-profile timer; same-token coalescing, token isolation and listener cleanup.");
