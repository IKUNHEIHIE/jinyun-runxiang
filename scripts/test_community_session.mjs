import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {createRequire} from 'node:module';
const appRequire=createRequire(new URL('../user-web/package.json',import.meta.url)),ts=appRequire('typescript');
function component(name,names,mocks){
  const file=fs.readFileSync(new URL('../user-web/src/mobile/views/'+name+'.vue',import.meta.url),'utf8');
  const source=file.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)[1].replaceAll('import.meta.env','({})');
  const compiled=ts.transpileModule(source+'\nexport { '+names.join(',')+' };',
    {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
  const exports={},watchers=[],unmount=[],leave=[];
  vm.runInNewContext(compiled,{exports,AbortController,FormData,URL,URLSearchParams,window:{confirm:()=>false},
    require(name){
      if(name==='vue')return {ref:value=>({value}),computed:fn=>({get value(){return fn();}}),watch:(_,fn)=>watchers.push(fn),onMounted(){},onUnmounted:fn=>unmount.push(fn)};
      if(name==='vue-router')return {...mocks[name],onBeforeRouteLeave:fn=>leave.push(fn)};
      if(name.endsWith('.vue'))return {};
      if(name==='@capacitor/core')return {Capacitor:{isNativePlatform:()=>false}};
      if(name in mocks)return mocks[name];
      throw Error('Unexpected dependency '+name);
    }});
  return {...exports,watchers,unmount,leave};
}
const session={token:'token-A',profile:{id:1}},route={params:{id:'1'},query:{}},notices=[],navigations=[];
let request,send;
const mocks={
  '../api':{session,api:(...args)=>request(...args),post:(...args)=>send(...args),mediaUrl:v=>v,notify:v=>notices.push(v),requireSession:()=>!!session.token},
  '../design':{categories:[{value:'',label:'全部'},{value:'BRONZE',label:'青铜'}]},
  'vue-router':{useRoute:()=>route,useRouter:()=>({replace:async v=>navigations.push(v),push:async v=>navigations.push(v)})},
  '../files':{},'../dates':{},
};
const list=component('CommunityPage',['load','posts','loading','error','setFilters'],mocks);
let oldResolve,newResolve,oldSignal;
request=(_,options)=>new Promise(resolve=>{oldResolve=resolve;oldSignal=options.signal;});
const oldList=list.load();
route.query={category:'BRONZE',sort:'hot'};
request=()=>new Promise(resolve=>{newResolve=resolve;});
const newList=list.load();
assert.equal(oldSignal.aborted,true);
newResolve({list:[{id:2}]});await newList;
oldResolve({list:[{id:1}]});await oldList;
assert.equal(list.posts.value[0].id,2,'Late old category must not replace the selected category');
assert.equal(list.loading.value,false);
list.setFilters('BRONZE','hot');assert.equal(navigations.at(-1).query.category,'BRONZE');assert.equal(navigations.at(-1).query.sort,'hot');
request=()=>new Promise(resolve=>{oldResolve=resolve;});const oldAccount=list.load();
session.token='token-B';oldResolve({list:[{id:99}]});await oldAccount;
assert.equal(list.posts.value[0].id,2,'Former identity response must not enter the new session');
list.unmount.forEach(fn=>fn());

const detail=component('CommunityDetailPage',['load','collect','like','sendComment','artwork','collected','comment','busy'],mocks);
const record={id:1,status:'APPROVED',comments:[],comment_count:0,is_collected:false,is_following:false,author:{id:9}};
request=async path=>path.endsWith('/related')?[]:{...record};
await detail.load();
send=()=>new Promise(resolve=>{oldResolve=resolve;});const oldFavorite=detail.collect();
session.token='token-C';await detail.load();
oldResolve({collected:true});await oldFavorite;
assert.equal(detail.collected.value,false);assert.equal(notices.length,0);
detail.comment.value='   ';let writes=0;send=async()=>{writes++;};await detail.sendComment();
assert.equal(writes,0,'Whitespace comment must be corrected before submission');
send=()=>new Promise((_,reject)=>{newResolve=reject;});const oldLike=detail.like();
detail.unmount.forEach(fn=>fn());const before=notices.length;newResolve(Error('Late failure'));await oldLike;
assert.equal(notices.length,before,'An abandoned detail must not display a late notification');

const publish=component('PublishPage',['upload','publish','title','content','gallery','busy','error'],mocks);
let input={files:[new File(['png'],'draft.png',{type:'image/png'})],value:'selected'};
request=()=>new Promise(resolve=>{oldResolve=resolve;});const oldUpload=publish.upload({target:input});
session.token='token-D';publish.watchers[0]();oldResolve({file_url:'/static/uploads/old.png'});await oldUpload;
assert.equal(publish.gallery.value.length,0);assert.equal(publish.busy.value,false);
publish.title.value='新作品';publish.content.value='创作故事';publish.gallery.value=['/static/uploads/current.png'];
send=async()=>{throw Error('Try again');};await publish.publish();
assert.equal(publish.title.value,'新作品');assert.equal(publish.gallery.value.length,1);assert.equal(publish.error.value,'Try again');
assert.equal(publish.leave[0](),false,'Cancelling the leave prompt must keep the unfinished form');
send=()=>new Promise(resolve=>{oldResolve=resolve;});const oldPublish=publish.publish();
session.token='token-E';publish.watchers[0]();const count=navigations.length;
oldResolve({id:123,status:'PENDING_REVIEW'});await oldPublish;
assert.equal(navigations.length,count,'A former account publication must not navigate the new account');
publish.unmount.forEach(fn=>fn());
session.profile.role_code='TEACHER';route.query={class_id:'2'};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const noticesPage=component('NoticesPage',['load','publish','classId','notices','title','content'],mocks);
let firstClass,secondClass;
request=async path=>path==='/teacher/classes'?[{id:1},{id:2}]:new Promise(resolve=>{
  if(path.includes('/1/'))firstClass=resolve;else secondClass=resolve;
});
noticesPage.classId.value=1;const firstLoad=noticesPage.load();await tick();
noticesPage.classId.value=2;const secondLoad=noticesPage.load();await tick();
secondClass([{id:22}]);await secondLoad;firstClass([{id:11}]);await firstLoad;
assert.equal(noticesPage.notices.value[0].id,22,'A previous class must not replace the selected class notices');
request=async path=>path==='/teacher/classes'?[{id:1},{id:2}]:[];
noticesPage.watchers[0]();await tick();assert.equal(noticesPage.classId.value,2,'Notice deep links retain their class selection');
noticesPage.title.value='原通知';noticesPage.content.value='原内容';
send=()=>new Promise(resolve=>{oldResolve=resolve;});const oldNotice=noticesPage.publish();
session.token='token-F';noticesPage.watchers[0]();await tick();noticesPage.title.value='新账号草稿';
oldResolve({});await oldNotice;assert.equal(noticesPage.title.value,'新账号草稿');
noticesPage.unmount.forEach(fn=>fn());
const rooms=component('ClassroomHubPage',['load','create','classId','rooms','title'],mocks);
request=async path=>path==='/teacher/classes'?[{id:1},{id:2}]:[];
await rooms.load();rooms.title.value='测试课堂';send=()=>new Promise(resolve=>{oldResolve=resolve;});
const oldRoom=rooms.create();session.token='token-G';rooms.watchers[0]();await tick();
const routeCount=navigations.length;oldResolve({id:88});await oldRoom;
assert.equal(navigations.length,routeCount,'A completed creation for a former account must not navigate the current account');
rooms.unmount.forEach(fn=>fn());
console.log('PASS: community filters, details, comments and uploads ignore old requests; failed publication keeps the form and account changes cannot navigate or attach old files.');
console.log('PASS: notices keep class deep links, reject old-class results and old-account publication; classroom creation cannot navigate a changed session.');
