import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { createRequire } from 'node:module';
const appRequire=createRequire(new URL('../user-web/package.json',import.meta.url)),ts=appRequire('typescript');
const compiled=ts.transpileModule(fs.readFileSync(new URL('../user-web/src/mobile/profile-scroll.ts',import.meta.url),'utf8'),
  {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
function environment(){
  let ready=false,current=true,callback,guard,timeout,disconnected=false,removed=false,cleared=false;
  const exports={};
  vm.runInNewContext(compiled,{exports,MutationObserver:class{constructor(fn){callback=fn;}observe(){}disconnect(){disconnected=true;}},
    document:{documentElement:{},querySelector:()=>ready?{}:null},
    setTimeout:fn=>{timeout=fn;return 1;},clearTimeout:()=>{cleared=true;}});
  const position={left:0,top:1400};
  return{position,start:()=>exports.restoreProfileScroll(position,()=>current,cancel=>{guard=cancel;return()=>{removed=true;};}),
    ready(){ready=true;callback();},switchAccount(){current=false;callback();},navigate(){guard();},expire(){timeout();},
    clean(){assert.equal(disconnected,true);assert.equal(removed,true);assert.equal(cleared,true);}};
}
{
  const e=environment();let settled=false;const p=e.start().then(value=>{settled=true;return value;});
  await Promise.resolve();assert.equal(settled,false,'Short loading document must not receive the saved scroll position');
  e.ready();assert.equal(await p,e.position);e.clean();
}
{
  const e=environment(),p=e.start();e.navigate();assert.equal(await p,false,'Navigation cancels the older restoration');
  e.ready();e.clean();
}
{
  const e=environment(),p=e.start();e.switchAccount();assert.equal(await p,false,'The former account position must not move the new account view');e.clean();
}
{
  const e=environment(),p=e.start();e.expire();assert.equal(await p,false,'An unmounted/unready view must release the observer');e.clean();
}
console.log('PASS: actual profile scroll waits for content, cancels on navigation/account changes and releases observers/guards/timers.');
