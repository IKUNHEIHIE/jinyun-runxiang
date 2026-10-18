import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { createRequire } from 'node:module';
const requireApp = createRequire(new URL('../user-web/package.json', import.meta.url));
const ts = requireApp('typescript'), vue = requireApp('vue');
const source = fs.readFileSync(new URL('../user-web/src/mobile/views/HomePage.vue', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)[1] +
  '\nexport {category,age,courses,heritage,checkedIn,signing,energy,levelLabel,personal,courseLoading,heritageLoading,courseError,heritageError,summaryError,summaryLoading,load,loadSummary,checkin,changeAge,changeCategory};',
  {compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022}}).outputText;
const wait = async () => { for (let i=0; i<15; i++) await Promise.resolve(); };
const deferred = () => { let resolve, reject; const promise=new Promise((a,b)=>{resolve=a;reject=b;}); return {promise,resolve,reject}; };
const day = () => new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Shanghai'}).format(new Date());
function environment(options={}) {
  const session=vue.reactive({token:'A',profile:{id:1,energy_value:10}}), route=vue.reactive({query: options.query ?? {}});
  const calls=[], notices=[], hooks=[], cleanup=[], stops=[], events=new Map(), exports={};
  let tick, cleared=false;
  let request=options.request ?? (async path => path.includes('/summary') ? {energy_value:10,checked_in:false} : {list:[{id:1}]});
  let send=async () => ({energy_value:20,already_checked_in:false,date:day()});
  const doc={visibilityState:'visible',addEventListener:(n,f)=>events.set('doc:'+n,f),removeEventListener:n=>events.delete('doc:'+n)};
  vm.runInNewContext(compiled,{exports,URLSearchParams,Intl,Date,document:doc,
    window:{addEventListener:(n,f)=>events.set('win:'+n,f),removeEventListener:n=>events.delete('win:'+n)},
    setInterval:fn=>{tick=fn;return 1;},clearInterval:()=>{cleared=true;tick=undefined;},
    require(name) {
      if(name==='vue') return {...vue,onMounted:fn=>hooks.push(fn),onUnmounted:fn=>cleanup.push(fn),watch(...args){const s=vue.watch(...args);stops.push(s);return s;}};
      if(name==='vue-router') return {useRoute:()=>route,useRouter:()=>({replace:async ({query})=>{route.query=query;},push(){}})};
      if(name==='../api') return {session,api:path=>{calls.push(path);return request(path);},post:(path,body)=>{calls.push(path);return send(path,body);},requireSession:()=>!!session.token,notify:m=>notices.push(m)};
      if(name==='../design') return {categories:[{value:''},{value:'CLAY_FIGURINE'},{value:'KITE'},{value:'NEW_YEAR_PAINTING'}]};
      if(name.endsWith('.vue')) return {};
      throw Error(name);
    }});
  return {...exports,session,route,calls,notices,events,doc,request:fn=>{request=fn;},send:fn=>{send=fn;},
    mount(){hooks.forEach(fn=>fn());},tick(){tick?.();},cleared:()=>cleared,
    destroy(){cleanup.forEach(fn=>fn());stops.forEach(fn=>fn());}};
}
{
  const e=environment(); await wait(); const slow=deferred(); e.request(()=>slow.promise);
  const old=e.load(); e.request(async()=>({list:[{id:2}]})); await e.changeCategory('KITE'); await wait();
  slow.resolve({list:[{id:999}]}); await old;
  assert.equal(e.courses.value[0].id,2); assert.equal(e.heritage.value[0].id,2);
  assert.equal(e.courseLoading.value,false); assert.equal(e.heritageLoading.value,false);
  await e.changeAge('PRIMARY_HIGH'); await wait();
  assert.equal(e.route.query.category,'KITE'); assert.equal(e.route.query.age,'PRIMARY_HIGH'); e.destroy();
  const restored=environment({query:{category:'KITE',age:'PRIMARY_HIGH'}}); await wait();
  assert.equal(restored.category.value,'KITE'); assert.equal(restored.age.value,'PRIMARY_HIGH');
  assert.ok(restored.calls.some(p=>p.includes('category=KITE') && p.includes('age_group=PRIMARY_HIGH'))); restored.destroy();
}
{
  const e=environment({request:async p=>{if(p.includes('/summary')) throw Error('summary offline');return {list:[{id:4}]};}}); await wait();
  assert.equal(e.courses.value[0].id,4); assert.equal(e.heritage.value[0].id,4);
  assert.equal(e.courseError.value,''); assert.equal(e.summaryError.value,'summary offline'); assert.equal(e.energy.value,null);
  assert.equal(e.levelLabel.value,'等级未知');
  e.request(async p=>{if(p.includes('/courses'))throw Error('courses offline'); return p.includes('/summary')?{energy_value:30,checked_in:true}:{list:[{id:5}]};});
  await e.load(); await e.loadSummary();
  assert.equal(e.heritage.value[0].id,5); assert.equal(e.heritageError.value,'');
  assert.equal(e.courseError.value,'courses offline'); assert.equal(e.checkedIn.value,true); e.destroy();
}
{
  const e=environment(); await wait(); const slow=deferred(); e.send(()=>slow.promise);
  const first=e.checkin(); await e.checkin();
  assert.equal(e.calls.filter(p=>p.endsWith('/checkin')).length,1,'Double tap must not send another check-in');
  e.request(async p=>p.includes('/summary')?{energy_value:80,checked_in:false}:{list:[{id:8}]});
  e.session.profile={id:2,energy_value:80}; e.session.token='B';
  assert.equal(e.checkedIn.value,null); assert.equal(e.energy.value,null); assert.equal(e.signing.value,false);
  await wait(); slow.resolve({energy_value:999,already_checked_in:false,date:day()}); await first;
  assert.equal(e.energy.value,80); assert.equal(e.session.profile.energy_value,80); assert.equal(e.checkedIn.value,false);
  assert.equal(e.notices.length,0,'Old-account success must not appear in the new account'); e.destroy();
}
{
  const e=environment(); await wait(); const slow=deferred(); e.request(()=>slow.promise);
  const old=e.loadSummary(true); await e.checkin();
  assert.equal(e.checkedIn.value,true); assert.equal(e.energy.value,20);
  slow.resolve({checked_in:false,energy_value:0}); await old;
  assert.equal(e.checkedIn.value,true); assert.equal(e.energy.value,20,'Earlier summary must not undo a successful check-in'); e.destroy();
}
{
  const e=environment(); await wait(); const slow=deferred();e.send(()=>slow.promise);
  const old=e.checkin();e.destroy();slow.reject(Error('late check-in error'));await old;
  assert.equal(e.notices.length,0);assert.equal(e.session.profile.energy_value,10);
  const other=environment();await wait();const late=deferred();other.request(()=>late.promise);
  const catalog=other.load();other.destroy();late.reject(Error('late catalog error'));await catalog;
  assert.equal(other.courseError.value,'');assert.equal(other.heritageError.value,'');
}
{
  const e=environment();await wait();e.mount();assert.equal(e.events.size,2);
  const before=e.calls.length;e.doc.visibilityState='hidden';e.tick();assert.equal(e.calls.length,before);
  e.doc.visibilityState='visible';e.request(async p=>p.includes('/summary')?{energy_value:10,checked_in:true}:{list:[]});
  e.events.get('doc:visibilitychange')();await wait();assert.equal(e.checkedIn.value,true);
  e.session.token='';assert.equal(e.checkedIn.value,null);assert.equal(e.energy.value,0);assert.equal(e.levelLabel.value,'LV.1');await wait();
  const loggedOut=e.calls.length;e.tick();assert.equal(e.calls.length,loggedOut,'Guest timers must not request private summary');
  e.destroy();assert.equal(e.events.size,0);assert.equal(e.cleared(),true);
}
console.log('PASS: actual home component filters, late requests, independent catalog/account failures, duplicate check-in, account isolation, earlier summary, visibility and unmount cleanup.');
