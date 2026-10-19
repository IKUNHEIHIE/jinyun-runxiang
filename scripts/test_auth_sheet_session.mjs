import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {createRequire} from 'node:module';
const requireApp=createRequire(new URL('../user-web/package.json',import.meta.url));
const ts=requireApp('typescript'),vue=requireApp('vue');
const file=fs.readFileSync(new URL('../user-web/src/mobile/components/AuthSheet.vue',import.meta.url),'utf8');
const source=file.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)[1];
const compiled=ts.transpileModule(source+'\nexport {submit,close,username,password,busy,error};',
  {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
const session=vue.reactive({token:'',profile:null,authVisible:false,authRedirect:''});
const pending=[],notices=[],navigations=[],storage=new Map(),unmount=[];
const exports={};
vm.runInNewContext(compiled,{
  exports,AbortController,Event,
  document:{body:{style:{overflow:'auto'}},activeElement:null},
  window:{dispatchEvent(){}},
  localStorage:{setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},
  require(name){
    if(name==='vue')return {...vue,onUnmounted:fn=>unmount.push(fn)};
    if(name==='vue-router')return {useRouter:()=>({push:async path=>navigations.push(path)})};
    if(name==='../api')return {session,notify:value=>notices.push(value),api:(path,options)=>new Promise((resolve,reject)=>pending.push({path,options,resolve,reject}))};
    throw Error('Unexpected dependency '+name);
  },
});
const sheet=exports;
session.authVisible=true;sheet.username.value='first';sheet.password.value='password1';
const old=sheet.submit(),oldRequest=pending.shift();
sheet.close();assert.equal(oldRequest.options.signal.aborted,true);assert.equal(sheet.password.value,'');
session.authVisible=true;sheet.username.value='second';sheet.password.value='password2';
const current=sheet.submit(),currentRequest=pending.shift();
oldRequest.resolve({token:'old-token',user:{id:1}});await old;
assert.equal(session.token,'');assert.equal(sheet.busy.value,true,'A dismissed login must not finish a newer login');
session.authRedirect='/community/publish';
currentRequest.resolve({token:'new-token',user:{id:2,nickname:'New'}});await current;
assert.equal(session.token,'new-token');assert.equal(session.profile.id,2);assert.equal(session.authVisible,false);
assert.equal(sheet.password.value,'');assert.deepEqual(navigations,['/community/publish']);
assert.equal(notices.length,1,'A stale result must not display a second login notice');
assert.equal(storage.get('jinyun_user_token'),'new-token');
session.authVisible=true;sheet.password.value='password3';const rejected=sheet.submit(),rejectedRequest=pending.shift();
sheet.close();rejectedRequest.reject(Error('Late network failure'));await rejected;
assert.equal(sheet.error.value,'','A dismissed request must not leave an error in the next dialog');
session.authVisible=true;sheet.password.value='password4';const switched=sheet.submit(),switchedRequest=pending.shift();
session.token='another-token';session.profile={id:3};
switchedRequest.resolve({token:'wrong-token',user:{id:4}});await switched;
assert.equal(session.token,'another-token');assert.equal(session.profile.id,3);
unmount.forEach(fn=>fn());
console.log('PASS: dismissed and stale logins cannot replace a newer identity, clear new loading state, or expose late errors; successful login resumes the intended page.');
