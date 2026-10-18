import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";
const requireApp=createRequire(new URL("../user-web/package.json",import.meta.url));
const ts=requireApp("typescript"),vue=requireApp("vue");
const source=readFileSync(new URL("../user-web/src/mobile/views/TeacherAnalyticsPage.vue",import.meta.url),"utf8");
const compiled=ts.transpileModule(source.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)[1]+
  "\nexport {classes,classId,data,loading,error,busy,creating,name,grade,wallVisible,basisVisible,selectedBadge,attendanceDraft,changedAttendance,loadClasses,loadAnalytics,create,saveAttendance,refreshVisible,accuracy,wall};",
  {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
const wait=async()=>{for(let i=0;i<15;i++)await Promise.resolve();};
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return{promise,resolve,reject};};
const stats=(id=1,day="2026-10-17",attendance="UNRECORDED")=>({class:{id},day,students:[{id:3,nickname:"学生",attendance,badges:[],badge_count:0,completion_rate:null,quiz_accuracy_7d:null}],badge_catalog:[]});
function environment(){
  const session=vue.reactive({token:"A"}),hooks=[],cleanup=[],stops=[],events=new Map(),calls=[],notices=[];
  let timer,cleared=false;
  let request=async(path)=>path==="/teacher/classes"?[{id:1},{id:2}]:stats(Number(path.match(/classes\/(\d+)/)?.[1]||1));
  const doc={visibilityState:"visible",addEventListener:(k,fn)=>events.set("doc:"+k,fn),removeEventListener:k=>events.delete("doc:"+k)};
  const exports={};vm.runInNewContext(compiled,{exports,document:doc,window:{history:{state:{}},addEventListener:(k,fn)=>events.set("window:"+k,fn),removeEventListener:k=>events.delete("window:"+k)},
    setInterval:fn=>{timer=fn;return 1;},clearInterval:()=>{timer=undefined;cleared=true;},require(name){
      if(name==="vue")return{...vue,onMounted:fn=>hooks.push(fn),onUnmounted:fn=>cleanup.push(fn),watch(...args){const stop=vue.watch(...args);stops.push(stop);return stop;}};
      if(name==="vue-router")return{useRouter:()=>({back(){},replace(){}})};
      if(name==="../api")return{session,mediaUrl:s=>s||"",notify:s=>notices.push(s),api:(path,options)=>{calls.push({path,options});return request(path,options);}};
      if(name==="../design"||name.endsWith(".vue"))return{};throw new Error(name);
    }});
  return{...exports,session,doc,calls,events,notices,request:fn=>{request=fn;},mount(){hooks.forEach(fn=>fn());},tick(){timer?.();},cleared:()=>cleared,destroy(){cleanup.forEach(fn=>fn());stops.forEach(fn=>fn());}};
}
{
  const e=environment(),old=deferred();e.request(()=>old.promise);const pending=e.loadClasses();
  e.request(async path=>path==="/teacher/classes"?[{id:2}]:stats(2));e.session.token="B";await wait();
  old.resolve([{id:999}]);await pending;
  assert.equal(e.classes.value[0].id,2);assert.equal(e.data.value.class.id,2);e.destroy();
}
{
  const e=environment(),old=deferred();e.request(path=>path.includes("/1/")?old.promise:Promise.resolve(stats(2)));
  e.classId.value=1;const before=e.calls.length;await e.loadAnalytics();assert.equal(e.calls.length,before,"Same-class in-flight refresh is coalesced");
  e.selectedBadge.value="PRIVATE";e.wallVisible.value=true;e.classId.value=2;assert.equal(e.selectedBadge.value,"");assert.equal(e.wallVisible.value,false);await wait();
  old.resolve(stats(1));await wait();assert.equal(e.data.value.class.id,2);e.destroy();
}
{
  const e=environment();e.mount();await wait();e.attendanceDraft.value[3]="PRESENT";
  await e.loadAnalytics();assert.equal(e.attendanceDraft.value[3],"PRESENT","Same-day refresh preserves unsaved attendance edits");
  e.request(async()=>stats(1,"2026-10-18","LEAVE"));await e.loadAnalytics();
  assert.equal(e.attendanceDraft.value[3],"LEAVE","A new Shanghai day does not reuse yesterday's draft");
  assert.equal(e.changedAttendance.value.length,0);assert.equal(e.accuracy.value.length,0,"Unknown scores are never ranked as zero");
  const count=e.calls.length;e.doc.visibilityState="hidden";e.tick();assert.equal(e.calls.length,count);
  e.doc.visibilityState="visible";e.events.get("window:online")();await wait();assert.equal(e.calls.length,count+1);
  e.destroy();assert.equal(e.events.size,0);assert.equal(e.cleared(),true);
}
{
  const e=environment();e.mount();await wait();e.attendanceDraft.value[3]="PRESENT";
  const save=deferred();e.request((path,options)=>options?.method==="PUT"?save.promise:Promise.resolve(stats(1,"2026-10-17","PRESENT")));
  const pending=e.saveAttendance();await e.saveAttendance();
  const calls=e.calls.filter(c=>c.options?.method==="PUT");assert.equal(calls.length,1,"Double taps cannot submit twice");
  assert.equal(JSON.parse(calls[0].options.body).day,"2026-10-17");
  e.session.token="B";await wait();save.resolve({});await pending;
  assert.equal(e.notices.length,0,"An old account's save must not report success in the new account");e.destroy();
}
{
  const e=environment(),late=deferred();e.classId.value=1;await wait();e.request(()=>late.promise);
  const pending=e.loadAnalytics();e.destroy();late.reject(new Error("old class error"));await pending;
  assert.equal(e.error.value,"");
}
console.log("PASS: analytics class/account races, coalescing, attendance day/draft isolation, duplicate saves, unknown ranking, refresh and cleanup.");
