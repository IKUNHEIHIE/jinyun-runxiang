import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {createRequire} from 'node:module';
const ts=createRequire(new URL('../user-web/package.json',import.meta.url))('typescript');
const compiled=ts.transpileModule(fs.readFileSync(new URL('../user-web/src/mobile/page-scroll.ts',import.meta.url),'utf8'),
  {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
function fixture(restoring=true){
  let path='/old',animation=true,loading=true,observe,guard,timeout,cleaned=false;
  const events=new Map(),exports={};
  const view={getAttribute:name=>name==='data-route-view'?path:null,
    get classList(){return animation?['page-pop-enter-active']:[];},querySelector:()=>loading?{}:null};
  vm.runInNewContext(compiled,{exports,MutationObserver:class{constructor(fn){observe=fn;}observe(){}disconnect(){cleaned=true;}},
    document:{documentElement:{},querySelector:()=>view,addEventListener:(name,fn)=>events.set(name,fn),removeEventListener:name=>events.delete(name)},
    setTimeout:fn=>{timeout=fn;return 1;},clearTimeout(){}});
  const promise=exports.restorePageScroll({left:0,top:1100},'/community',restoring,()=>true,fn=>{guard=fn;return()=>{};});
  return {promise,arrive(){path='/community';observe();},enter(){animation=false;observe();},loaded(){loading=false;observe();},
    interact(){events.get('pointerdown')();},navigate(){guard();},expire(){timeout();},
    clean(){assert.equal(cleaned,true);assert.equal(events.size,0);}};
}
{
  const f=fixture();let result;f.promise.then(value=>{result=value;});
  f.enter();f.loaded();await Promise.resolve();assert.equal(result,undefined,'The leaving page must never receive the new page position');
  f.arrive();assert.equal((await f.promise).top,1100);f.clean();
}
{
  const f=fixture();let result;f.promise.then(value=>{result=value;});
  f.arrive();f.loaded();await Promise.resolve();assert.equal(result,undefined,'Wait for the incoming transition');
  f.enter();assert.equal((await f.promise).behavior,'instant');f.clean();
}
{
  const f=fixture();let result;f.promise.then(value=>{result=value;});
  f.arrive();f.enter();await Promise.resolve();assert.equal(result,undefined,'Do not clamp a list to its short loading state');
  f.loaded();await f.promise;f.clean();
}
{
  const f=fixture(false);f.arrive();f.enter();assert.equal((await f.promise).top,1100,'Forward navigation need not wait for network content');f.clean();
}
for(const action of ['interact','navigate','expire']){
  const f=fixture();f[action]();assert.equal(await f.promise,false,'Interaction/navigation cancels the pending automatic scroll');f.clean();
}
console.log('PASS: incoming route/transition/list readiness controls back restoration; user interaction cancels automatic scrolling and all listeners are released.');
