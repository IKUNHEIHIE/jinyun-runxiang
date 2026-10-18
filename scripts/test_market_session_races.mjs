import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import { createRequire } from "node:module";
import { randomUUID } from "node:crypto";

const requireApp = createRequire(new URL("../user-web/package.json", import.meta.url));
const ts = requireApp("typescript"), vue = requireApp("vue");
const file = fs.readFileSync(new URL("../user-web/src/mobile/views/MallPage.vue", import.meta.url), "utf8");
const names = ["load", "buy", "redeem", "submit", "closeCheckout", "moreProducts", "explore",
  "products", "summary", "creators", "loading", "error", "category", "filtered", "visibleProducts",
  "visibleCount", "productsSection", "selectedProduct", "selectedReward", "receiver", "requestId", "busy", "checkoutError"];
const compiled = ts.transpileModule(file.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)[1] +
  "\nexport { " + names.join(",") + " };", {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
const fixture = id => ({id, name: "文创" + id, category: "CRAFT", origin_place: "天津",
  skus: [{id:id * 10, stock:0, price_yuan:2}, {id:id * 10 + 1, stock:2, price_yuan:2}]});
const inventory = Array.from({length:10}, (_, i) => fixture(i + 1));
const deferred = () => {
  let resolve, reject;
  const promise = new Promise((a,b) => {resolve=a;reject=b;});
  return {promise, resolve, reject};
};
function environment() {
  const session = vue.reactive({token:"A", profile:{id:1,nickname:"甲"}});
  const route = vue.reactive({query:{}, path:"/mall"});
  const navigation = [], notices = [], submissions = [], stops = [], cleanups = [];
  let request = async path => path === "/mall/products" ? inventory :
    path.includes("/summary") ? {creator_count:1, fund_total_yuan:0} :
    path.includes("/community/") ? {list:[{id:1}]} : [{id:1}];
  let send = async () => ({id:1}), profileRefreshes = 0, profileFailure = false;
  const exports = {};
  vm.runInNewContext(compiled, {exports, crypto:{randomUUID},
    require(name) {
      if (name === "vue") return {...vue, onMounted(){}, onUnmounted: fn=>cleanups.push(fn),
        watch(...args){const stop=vue.watch(...args);stops.push(stop);return stop;}};
      if (name === "vue-router") return {useRoute:()=>route, useRouter:()=>({
        push:path=>navigation.push(path), replace:value=>{navigation.push(value); if(value.query)route.query=value.query;},
      })};
      if (name === "../api") return {session, api:(...args)=>request(...args),
        post:(...args)=>{submissions.push(args);return send(...args);}, mediaUrl:v=>v, notify:v=>notices.push(v),
        requireSession:()=>!!session.token, loadProfile:async()=>{profileRefreshes++;if(profileFailure)throw new Error("profile offline");}};
      if (name === "../design") return {};
      if (name.endsWith(".json")) return {};
      if (name.endsWith(".vue")) return {};
      throw new Error(name);
    },
  });
  return {...exports, session, route, navigation, notices, submissions,
    request:fn=>{request=fn;}, send:fn=>{send=fn;}, refreshes:()=>profileRefreshes, failProfile:()=>{profileFailure=true;},
    destroy(){cleanups.forEach(fn=>fn());stops.forEach(fn=>fn());}};
}

// A real network failure keeps the same idempotency key and draft; double taps do not submit twice.
{
  const app=environment(), pending=deferred();
  app.buy(inventory[0]);
  assert.equal(app.selectedProduct.value.skus.find(s=>s.stock>0).id,11);
  app.receiver.value={receiver_name:"开发测试",receiver_phone:"100000",receiver_address:"Local development test"};
  const key=app.requestId.value;
  app.send(()=>pending.promise);
  const first=app.submit();
  await app.submit();
  app.closeCheckout();
  assert.equal(app.submissions.length,1);
  assert.equal(app.submissions[0][1].items[0].sku_id,11,"Checkout selects an in-stock SKU");
  assert.equal(app.busy.value,true);
  assert.equal(app.selectedProduct.value.id,1,"Pending checkout cannot be dismissed");
  pending.reject(new Error("库存已变化"));
  await first;
  assert.equal(app.checkoutError.value,"库存已变化");
  assert.equal(app.requestId.value,key);
  assert.equal(app.receiver.value.receiver_phone,"100000");
  app.send(async()=>({id:99}));
  await app.submit();
  assert.equal(app.submissions[1][1].request_id,key,"Retry preserves idempotency");
  assert.equal(app.selectedProduct.value,undefined);
  assert.equal(app.receiver.value.receiver_address,"");
  assert.equal(app.navigation.at(-1),"/me/orders");
  app.destroy();
}

// A response from a previous account must not close a new account's checkout or navigate.
{
  const app=environment(), old=deferred(), current=deferred();
  app.buy(inventory[0]); app.receiver.value.receiver_phone="old private phone";
  app.send(()=>old.promise);
  const first=app.submit();
  app.session.token="B"; app.session.profile={id:2,nickname:"乙"};
  assert.equal(app.selectedProduct.value,undefined);
  assert.equal(app.receiver.value.receiver_phone,"","Identity change clears private fields synchronously");
  app.buy(inventory[1]); app.send(()=>current.promise);
  const second=app.submit();
  old.resolve({id:1}); await first;
  assert.equal(app.selectedProduct.value.id,2);
  assert.equal(app.busy.value,true);
  assert.equal(app.notices.length,0);
  assert.equal(app.navigation.length,0);
  current.resolve({id:2}); await second;
  assert.equal(app.notices.length,1);
  app.destroy();
}

// An accepted exchange remains accepted when the follow-up profile request fails.
{
  const app=environment();
  app.redeem({id:5,energy_cost:20});
  app.failProfile();
  await app.submit();
  await vue.nextTick();
  assert.equal(app.submissions[0][0],"/mobile/market/exchanges");
  assert.equal(app.selectedReward.value,undefined);
  assert.equal(app.checkoutError.value,"");
  assert.equal(app.refreshes(),1);
  assert.equal(app.notices.length,1);
  app.destroy();
}

// A newer refresh wins even if the earlier response arrives last.
{
  const app=environment(), old=deferred();
  app.request(path=>path==="/mall/products" ? old.promise : Promise.resolve(path.includes("/community/")?{list:[]} : {}));
  const first=app.load();
  app.request(async path=>path==="/mall/products" ? inventory : path.includes("/community/") ? {list:[{id:4}]} : {});
  await app.load();
  old.resolve([fixture(999)]); await first;
  assert.equal(app.products.value[0].id,1);
  assert.equal(app.creators.value[0].id,4);
  assert.equal(app.loading.value,false);
  assert.equal(app.visibleProducts.value.length,4);
  app.moreProducts(); assert.equal(app.visibleProducts.value.length,8);
  app.moreProducts(); assert.equal(app.visibleProducts.value.length,10);
  app.category.value="青铜复刻"; await vue.nextTick();
  assert.equal(app.visibleCount.value,4,"Changing a filter resets the initial four-card window");
  let scrolled;
  app.productsSection.value={scrollIntoView:options=>{scrolled=options;}};
  app.explore(); assert.equal(scrolled.block,"start");
  assert.equal(app.navigation.length,0,"Explore scrolls without changing hash-router navigation");
  app.destroy();
}

// A deep-linked product beyond the initial window still opens, and unmount drops late errors.
{
  const app=environment();
  app.route.query={product:"10"}; await app.load();
  assert.equal(app.selectedProduct.value.id,10);
  assert.equal(app.navigation[0].query.product,undefined,"Purchase intent is consumed");
  const late=deferred(); app.send(()=>late.promise);
  const pending=app.submit(); app.destroy();
  late.reject(new Error("late failure")); await pending;
  assert.equal(app.checkoutError.value,"");
  assert.equal(app.receiver.value.receiver_name,"");
}
console.log("PASS: market retries, double-submit, account isolation, stale loads, pagination, deep links, scroll routing and unmount cleanup.");
