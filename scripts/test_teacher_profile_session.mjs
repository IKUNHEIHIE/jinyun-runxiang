import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";
const appRequire=createRequire(new URL("../user-web/package.json",import.meta.url));
const ts=appRequire("typescript"), vue=appRequire("vue");
const file=readFileSync(new URL("../user-web/src/mobile/views/TeacherPage.vue",import.meta.url),"utf8");
const compiled=ts.transpileModule(file.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)[1] +
  "\nexport { load,stats,personal,loading,error,selectedAchievement,activeAchievement,achievements,completedAchievements,refreshVisible };",
  {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
const wait=async()=>{for(let i=0;i<6;i++)await Promise.resolve();};
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return{promise,resolve,reject};};
function environment() {
  const session=vue.reactive({token:"A",profile:{id:1,nickname:"甲"}}), hooks=[], cleanup=[], stops=[], events=new Map();
  let interval,cleared=false,calls=0;
  let request=async path=>path.includes("overview")?{day:"2026-10-17",student_count:2,achievements:[
    {code:"LESSON_PLAN",name:"匠心独运",completed:true,current:1,target:1}]}:{following_count:3};
  const doc={visibilityState:"visible",addEventListener:(e,fn)=>events.set("doc:"+e,fn),removeEventListener:e=>events.delete("doc:"+e)};
  const exports={};
  vm.runInNewContext(compiled,{exports,document:doc,window:{history:{state:{}},
    addEventListener:(e,fn)=>events.set("window:"+e,fn),removeEventListener:e=>events.delete("window:"+e)},
    setInterval:fn=>{interval=fn;return 1;},clearInterval:()=>{cleared=true;interval=undefined;},
    require(name){
      if(name==="vue")return{...vue,onMounted:fn=>hooks.push(fn),onUnmounted:fn=>cleanup.push(fn),watch(...args){const s=vue.watch(...args);stops.push(s);return s;}};
      if(name==="vue-router")return{useRouter:()=>({back(){},replace(){}})};
      if(name==="../api")return{session,api:(path)=>{calls++;return request(path);},mediaUrl:v=>v};
      if(name==="../design"||name.endsWith(".vue"))return{};
      throw new Error(name);
    }});
  return{...exports,session,doc,events,request:fn=>{request=fn;},calls:()=>calls,
    mount(){hooks.forEach(fn=>fn());},tick(){interval?.();},cleared:()=>cleared,
    destroy(){cleanup.forEach(fn=>fn());stops.forEach(fn=>fn());}};
}
{
  const e=environment(),oldStats=deferred(),oldPersonal=deferred();
  e.request(path=>path.includes("overview")?oldStats.promise:oldPersonal.promise);
  const pending=e.load(); await e.load();
  assert.equal(e.calls(),2,"Repeated refresh coalesces the same account's in-flight pair");
  e.request(async path=>path.includes("overview")?{day:"2026-10-17",student_count:8,achievements:[]}:{following_count:9});
  e.selectedAchievement.value="LESSON_PLAN"; e.session.token="B";
  assert.equal(e.selectedAchievement.value,"","Account switch clears the achievement dialog immediately");
  assert.equal(e.stats.value.student_count,undefined);
  await wait();
  oldStats.resolve({student_count:999});oldPersonal.resolve({following_count:999});await pending;
  assert.equal(e.stats.value.student_count,8);
  assert.equal(e.personal.value.following_count,9);
  assert.equal(e.loading.value,false);
  e.destroy();
}
{
  const e=environment();
  e.mount();await wait();
  assert.equal(e.completedAchievements.value,1);
  e.selectedAchievement.value="LESSON_PLAN";
  assert.equal(e.activeAchievement.value.name,"匠心独运");
  assert.equal(e.events.size,2);
  const before=e.calls();
  e.doc.visibilityState="hidden";e.tick();assert.equal(e.calls(),before);
  e.doc.visibilityState="visible";e.events.get("doc:visibilitychange")();await wait();
  assert.equal(e.calls(),before+2);
  e.events.get("window:online")();await wait();
  assert.equal(e.calls(),before+4);
  e.session.token="";
  assert.equal(e.personal.value.following_count,undefined);
  assert.equal(e.achievements.value.length,0);
  const after=e.calls();e.tick();assert.equal(e.calls(),after,"Logged-out timers do not request private data");
  e.destroy();assert.equal(e.events.size,0);assert.equal(e.cleared(),true);
}
{
  const e=environment(),late=deferred();
  e.request(()=>late.promise);
  const pending=e.load();e.destroy();late.reject(new Error("late teacher error"));await pending;
  assert.equal(e.error.value,"");
  assert.equal(e.stats.value.student_count,undefined);
}
console.log("PASS: teacher profile refresh coalescing, account/dialog isolation, visibility/online refresh, logout and unmount cleanup.");
