import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { createRequire } from 'node:module';
const requireApp=createRequire(new URL('../user-web/package.json',import.meta.url));
const ts=requireApp('typescript'),vue=requireApp('vue');
const compile=source=>ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
const source=fs.readFileSync(new URL('../user-web/src/mobile/views/LessonPlanPage.vue',import.meta.url),'utf8');
const compiled=compile(source.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)[1]+'\nexport {grade,topic,duration,mode,result,history,historyTotal,cursor,busy,historyBusy,openingId,exporting,error,historyError,detailError,exportError,settingsVisible,historyVisible,expanded,loadHistory,generate,open,exportPpt,selectTemplate,templates};');
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return{promise,resolve,reject};};
const wait=async()=>{for(let i=0;i<15;i++)await Promise.resolve();};
const plan=id=>({id,source:'本地课程模板',content:{title:'方案'+id,topic:'古琴鉴赏'}});
function environment(){
  const session=vue.reactive({token:'A'}),hooks=[],cleanup=[],stops=[],calls=[],notices=[],exports={};let uuid=0;
  let request=async path=>path.includes('capabilities')?{model_enabled:false}:path.includes('history')?{items:[],total:0,next_cursor:null}:plan(1);
  let save=async()=>true;
  vm.runInNewContext(compiled,{exports,crypto:{randomUUID:()=> 'request-id-'+ ++uuid},window:{history:{state:{}}},require(name){
    if(name==='vue')return{...vue,onMounted:fn=>hooks.push(fn),onUnmounted:fn=>cleanup.push(fn),watch(...args){const stop=vue.watch(...args);stops.push(stop);return stop;}};
    if(name==='vue-router')return{useRouter:()=>({back(){},replace(){}})};
    if(name==='../api')return{session,notify:s=>notices.push(s),api:(path,options)=>{calls.push({path,options});return request(path,options);},post:(path,body)=>{calls.push({path,body});return request(path,{body});}};
    if(name==='../files')return{saveApiFile:(...args)=>save(...args)};
    if(name==='../design')return{};if(name==='../dates')return{};throw Error(name);
  }});
  exports.grade.value='大学';exports.topic.value='古琴鉴赏';
  return{...exports,session,calls,notices,request:fn=>{request=fn;},save:fn=>{save=fn;},mount(){hooks.forEach(fn=>fn());},destroy(){cleanup.forEach(fn=>fn());stops.forEach(fn=>fn());}};
}
{
  const e=environment(),old=deferred();e.request(()=>old.promise);const pending=e.loadHistory();
  e.request(async path=>path.includes('capabilities')?{model_enabled:false}:{items:[{id:2}],total:1,next_cursor:null});e.session.token='B';await wait();
  old.resolve({items:[{id:999}],total:999,next_cursor:10});await pending;
  assert.equal(e.history.value[0].id,2);assert.equal(e.historyTotal.value,1);assert.equal(e.historyBusy.value,false);e.destroy();
}
{
  const e=environment(),old=deferred();e.request(()=>old.promise);const first=e.open(1);
  e.request(async()=>plan(2));await e.open(2);old.resolve(plan(1));await first;
  assert.equal(e.result.value.id,2,'Late history detail cannot overwrite a later selection');e.destroy();
}
{
  const e=environment(),pending=deferred();e.request(()=>pending.promise);const first=e.generate();await e.generate();
  assert.equal(e.calls.length,1,'Double taps create one in-flight request');
  const id=e.calls[0].body.request_id;pending.reject(new Error('response lost'));await first;
  e.request(async path=>path.includes('history')?{items:[],total:0,next_cursor:null}:plan(4));await e.generate();
  assert.equal(e.calls.filter(c=>c.body)[1].body.request_id,id,'Retry reuses the original saved-request identity');
  e.topic.value='陶瓷文化';await e.generate();assert.notEqual(e.calls.filter(c=>c.body)[2].body.request_id,id);e.destroy();
}
{
  const e=environment(),old=deferred();e.request(()=>old.promise);const first=e.open(1);
  e.request(async path=>path.includes('history')?Promise.reject(new Error('history offline')):plan(7));await e.generate();await wait();
  old.resolve(plan(1));await first;assert.equal(e.result.value.id,7);assert.equal(e.error.value,'');assert.equal(e.historyError.value,'history offline');assert.equal(e.notices.length,1);e.destroy();
}
{
  const e=environment(),old=deferred();e.request(()=>old.promise);const first=e.generate();
  e.session.token='B';e.request(async()=>({items:[],total:0,next_cursor:null}));old.resolve(plan(999));await first;await wait();
  assert.equal(e.result.value,undefined);assert.equal(e.notices.length,0);assert.equal(e.grade.value,'');e.destroy();
}
{
  const e=environment();e.result.value=plan(1);const old=deferred();let valid;
  e.save(async(path,file,guard)=>{valid=guard;await old.promise;throw new Error('old export');});
  const pending=e.exportPpt();await e.exportPpt();assert.equal(e.exporting.value,true);
  e.session.token='B';assert.equal(valid(),false);old.resolve();await pending;assert.equal(e.exportError.value,'');e.destroy();
}
{
  const e=environment(),old=deferred();e.request(()=>old.promise);const pending=e.open(1);e.destroy();old.reject(new Error('unmounted'));await pending;assert.equal(e.detailError.value,'');
}
{
  const e=environment(),old=deferred();e.request(()=>old.promise);const first=e.loadHistory();
  e.request(async path=>path.includes('history')?{items:[{id:8}],total:1,next_cursor:null}:plan(8));await e.generate();await wait();
  old.resolve({items:[],total:0,next_cursor:null});await first;
  assert.equal(e.history.value[0].id,8,'Saved generation must refresh past an older in-flight history snapshot');e.destroy();
}
console.log('PASS: lesson account/detail/generation races, UUID retry, duplicate taps, history refresh after save, export invalidation and unmount.');

const fileCode=compile(fs.readFileSync(new URL('../user-web/src/mobile/files.ts',import.meta.url),'utf8'));
function fileEnvironment(){
  const session={token:'A'},calls=[],exports={},reader=deferred(),write=deferred();let request=async()=>({ok:true,blob:async()=>({})}),native=true,cancel=false,id=0;
  class Reader{readAsDataURL(){reader.promise.then(()=>{this.result='data:application/octet-stream;base64,AAAA';this.onload();});}}
  vm.runInNewContext(fileCode,{exports,FileReader:Reader,AbortSignal,crypto:{randomUUID:()=> 'unique-'+ ++id},setTimeout,URL:{createObjectURL:()=> 'blob:test',revokeObjectURL(){}},document:{createElement:()=>({click(){calls.push({type:'download'});}})},fetch:(...args)=>request(...args),require(name){
    if(name==='@capacitor/core')return{Capacitor:{isNativePlatform:()=>native}};
    if(name==='@capacitor/filesystem')return{Directory:{Cache:'CACHE'},Filesystem:{writeFile:async args=>{calls.push({type:'write',...args});await write.promise;return{uri:'cache://'+args.path};},deleteFile:async args=>{calls.push({type:'delete',...args});}}};
    if(name==='@capacitor/share')return{Share:{share:async args=>{calls.push({type:'share',...args});if(cancel)throw Object.assign(new Error('Share canceled'),{name:'AbortError'});}}};
    if(name==='./api')return{session,apiBase:'/api',mediaUrl:s=>s};throw Error(name);
  }});
  return{...exports,session,calls,reader,write,request:fn=>{request=fn;},native:()=>{native=false;},cancel:()=>{cancel=true;}};
}
{
  const e=fileEnvironment(),response=deferred();e.request(()=>response.promise);const pending=e.saveApiFile('/private','lesson.pptx');e.session.token='B';response.resolve({ok:true,blob:async()=>({})});await assert.rejects(pending,/账号/);assert.equal(e.calls.length,0);
}
{
  const e=fileEnvironment(),body=deferred();e.request(async()=>({ok:true,blob:()=>body.promise}));const pending=e.saveApiFile('/private','lesson.pptx');await wait();e.session.token='B';body.resolve({});await assert.rejects(pending,/账号/);assert.equal(e.calls.length,0);
}
{
  const e=fileEnvironment();const pending=e.saveApiFile('/private','lesson.pptx');await wait();e.session.token='B';e.reader.resolve();await assert.rejects(pending,/账号/);assert.equal(e.calls.length,0);
}
{
  const e=fileEnvironment();const pending=e.saveApiFile('/private','lesson.pptx');await wait();e.reader.resolve();await wait();e.session.token='B';e.write.resolve();await assert.rejects(pending,/账号/);
  assert.deepEqual(e.calls.map(c=>c.type),['write','delete']);assert.equal(e.calls[0].path,e.calls[1].path);assert.match(e.calls[1].path,/^jinyun\/private-unique-1\/lesson.pptx$/);
}
{
  const e=fileEnvironment();e.cancel();const pending=e.saveApiFile('/private','lesson.pptx');await wait();e.reader.resolve();e.write.resolve();assert.equal(await pending,false);assert.deepEqual(e.calls.map(c=>c.type),['write','share']);
}
{
  const e=fileEnvironment();e.native();await e.saveApiFile('/private','lesson.pptx');assert.equal(e.calls[0].type,'download');
}
console.log('PASS: actual export helper blocks stale fetch/blob/base64/cache completions, deletes only its own unique cache file, preserves cancel and browser download.');
