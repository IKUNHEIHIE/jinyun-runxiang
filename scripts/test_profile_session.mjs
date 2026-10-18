import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { createRequire } from 'node:module';
const appRequire=createRequire(new URL('../user-web/package.json',import.meta.url));
const vue=appRequire('vue'), ts=appRequire('typescript');
const source=fs.readFileSync(new URL('../user-web/src/mobile/views/ProfilePage.vue',import.meta.url),'utf8');
const compiled=ts.transpileModule(source.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)[1]+
  '\nexport {summary,learning,collections,badges,loading,loaded,error,editing,form,saving,signingOut,activeBadge,load,edit,closeEdit,save,signout};',
  {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return{promise,resolve,reject};};
const wait=async()=>{for(let i=0;i<15;i++)await Promise.resolve();};
function environment(){
  const session=vue.reactive({token:'A',profile:{id:1,nickname:'甲'}}), route=vue.reactive({query:{}}), exports={};
  const hooks=[],cleanup=[],stops=[],notices=[],calls=[];let refreshes=0;
  let request=async p=>p.endsWith('/summary')?{energy_value:10}:[],
      update=async()=>({}),refresh=async()=>{refreshes++;},out=async()=>{};
  vm.runInNewContext(compiled,{exports,require(name){
    if(name==='vue')return{...vue,onMounted:fn=>hooks.push(fn),onUnmounted:fn=>cleanup.push(fn),watch(...args){const stop=vue.watch(...args);stops.push(stop);return stop;}};
    if(name==='vue-router')return{useRoute:()=>route,useRouter:()=>({replace:async({query})=>{route.query=query;}})};
    if(name==='../api')return{session,api:p=>{calls.push({method:'GET',path:p});return request(p);},put:(p,body)=>{calls.push({method:'PUT',body:JSON.parse(JSON.stringify(body))});return update(p,body);},loadProfile:()=>refresh(),logout:()=>out(),notify:m=>notices.push(m),requireSession:()=>!!session.token,mediaUrl:v=>v};
    if(name==='../design')return{};if(name==='../dates')return{formatDate:v=>v};if(name.endsWith('.vue'))return{};throw Error(name);
  }});
  return{...exports,session,route,calls,notices,request:fn=>{request=fn;},update:fn=>{update=fn;},refresh:fn=>{refresh=fn;},logout:fn=>{out=fn;},refreshes:()=>refreshes,
    mount(){hooks.forEach(fn=>fn());},destroy(){cleanup.forEach(fn=>fn());stops.forEach(fn=>fn());}};
}
{
  const e=environment();e.mount();await wait();e.edit();e.form.value.bio='private A draft';e.activeBadge.value={id:1,name:'private badge'};
  const old=deferred();e.update(()=>old.promise);const save=e.save();
  e.session.profile={id:2,nickname:'乙'};e.session.token='B';
  await wait();e.edit();e.form.value.bio='new B draft';old.resolve({});await save;
  assert.equal(e.refreshes(),0,'Old-account save must not refresh the new account');
  assert.equal(e.editing.value,true,'Old-account save must not close the new editor');
  assert.equal(e.form.value.bio,'new B draft');assert.equal(e.notices.length,0);
  e.destroy();
}
{
  const e=environment();e.mount();await wait();e.edit();const late=deferred();e.update(()=>late.promise);
  const save=e.save();await e.save();assert.equal(e.calls.filter(c=>c.method==='PUT').length,1,'Repeated submit must send one update');
  let exits=0;e.logout(async()=>{exits++;});await e.signout();assert.equal(exits,0,'Do not revoke the session while its save is pending');
  e.destroy();late.reject(Error('old error'));await save;assert.equal(e.notices.length,0);
}
{
  const e=environment();e.mount();await wait();const slow=deferred();let exits=0;e.logout(()=>{exits++;return slow.promise;});const old=e.signout();
  await e.signout();assert.equal(exits,1,'Repeated logout sends one request');
  e.request(async p=>p.endsWith('/summary')?{energy_value:80}:[]);
  e.session.profile={id:2,nickname:'乙'};e.session.token='B';await wait();slow.resolve();await old;
  assert.equal(e.summary.value.energy_value,80,'Stale logout must not clear the new summary');assert.equal(e.notices.length,0);e.destroy();
}
{
  const e=environment();e.mount();await wait();e.edit();e.form.value.nickname='accepted';
  e.refresh(async()=>{throw Error('profile refresh offline');});await e.save();
  assert.equal(e.editing.value,false);assert.equal(e.saving.value,false);
  assert.equal(e.notices.at(-1),'个人资料已保存，账户显示暂未刷新，请稍后重试','Accepted update must not be reported as failed');e.destroy();
}
{
  const e=environment();e.mount();await wait();e.edit();e.form.value.bio='submitted draft';const late=deferred();e.update(()=>late.promise);
  const pending=e.save();e.closeEdit();e.edit();e.form.value.bio='next draft';late.resolve({});await pending;
  assert.equal(e.editing.value,true);assert.equal(e.form.value.bio,'next draft');assert.equal(e.saving.value,false);
  assert.equal(e.calls.find(c=>c.method==='PUT').body.bio,'submitted draft','Update must snapshot the submitted form');assert.equal(e.notices.length,0);e.destroy();
}
{
  const e=environment();e.mount();await wait();const late=deferred();e.refresh(()=>late.promise);e.edit();const pending=e.save();await wait();
  e.session.profile={id:2,nickname:'乙'};e.session.token='B';await wait();e.edit();e.form.value.bio='new B editor';
  late.resolve();await pending;assert.equal(e.editing.value,true);assert.equal(e.form.value.bio,'new B editor');assert.equal(e.notices.length,0);e.destroy();
}
{
  const e=environment();e.mount();await wait();const late=deferred();e.request(()=>late.promise);
  const before=e.calls.length, pending=e.load();await e.load();assert.equal(e.calls.length,before+4,'Same-account in-flight refresh is coalesced');
  assert.equal(e.loaded.value,true);assert.equal(e.summary.value.energy_value,10,'Refreshing retains known data');
  late.reject(Error('refresh failed'));await pending;assert.equal(e.loaded.value,true);assert.equal(e.summary.value.energy_value,10);
  assert.equal(e.error.value,'refresh failed');e.edit();e.form.value.bio='private';e.activeBadge.value={id:8};
  const next=deferred();e.request(()=>next.promise);e.session.token='B';
  assert.equal(e.summary.value.energy_value,undefined);assert.equal(e.collections.value.length,0);
  assert.equal(e.editing.value,false);assert.equal(e.form.value.bio,'');assert.equal(e.activeBadge.value,undefined);assert.equal(e.loaded.value,false);
  e.destroy();next.resolve([]);await wait();
}
{
  const e=environment();e.mount();await wait();e.edit();e.form.value.bio='preserve on failure';e.update(async()=>{throw Error('save offline');});
  await e.save();assert.equal(e.editing.value,true);assert.equal(e.form.value.bio,'preserve on failure');assert.equal(e.saving.value,false);
  e.logout(async()=>{e.session.token='';e.session.profile=null;});await e.signout();
  assert.equal(e.summary.value.energy_value,undefined);assert.equal(e.editing.value,false);assert.equal(e.notices.at(-1),'已退出登录');e.destroy();
}
console.log('PASS: actual personal profile component blocks old-account save/logout and duplicate submission; late errors after unmount are ignored.');
