import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import {collectChampions,resolveChampion,tnaTitleholders} from '../proof/staging/collect-champions.mjs';
const root=new URL('../web/staging/',import.meta.url);
const catalog=JSON.parse(readFileSync(new URL('../proof/staging/championship-catalog.json',import.meta.url)));
const library=JSON.parse(readFileSync(new URL('library.json',root))),routes=JSON.parse(readFileSync(new URL('asset-routes.json',root)));
const now=new Date('2026-11-03T14:00:00Z');
const board=library.records.find(r=>r.id==='championship-raw');
const options={catalog,routes,board,show:'raw',asOf:'2026-11-03'};
const title=catalog.raw.find(c=>c.id==='raw-ic');
const pad=html=>html+' '.repeat(1100);
function wweRequester(overrides={}){
 const holders=new Map(Object.entries(catalog).filter(([s])=>!['tna','aaa'].includes(s)).flatMap(([,cs])=>cs.map(c=>[c.source,c.name])));
 return async url=>{if(!holders.has(url))throw Error('offline');return new Response(pad('<h3>Championship Holder '+(overrides[url]||holders.get(url))+'</h3><div>Time Held</div><div data-reign-start-date="1793663040"></div>'));};
}
test('WWE title change automatically resolves Ethan Page, reign date and approved cross-show artwork',async()=>{
 const got=await collectChampions({library,routes,now,requester:wweRequester({[title.source]:'Ethan Page'})});
 const raw=got.feed.programs.find(p=>p.show==='raw');assert.equal(raw.champions.length,5);
 const c=raw.champions.find(c=>c.id===title.id);assert.equal(c.name,'ETHAN PAGE');assert.equal(c.since_date,'2026-11-02');assert.deepEqual(c.members,['Ethan Page']);assert.equal(c.belt,title.belt);
 assert.equal(c.portrait_routes['ethan-page.png'],'/boards/RESULTS/RAW/assets/portraits/ethan-page.png');
 const host={};runInNewContext(readFileSync(new URL('board-adapter.js',root),'utf8'),{window:host,URL});
 const source=readFileSync(new URL(board.delivery,root),'utf8');
 const html=host.ISCBoardAdapter.build(source,board,routes,'https://player.example/','active',{'champions.json':got.feed});
 assert.ok(html.includes(JSON.stringify(raw.champions)));
 const config=JSON.parse(html.match(/<base[^>]*><script>[\s\S]*?\)\((\{"weeklyResults":[\s\S]*?)\);<\/script>/)[1]);
 const assetKey=board.href.slice(0,board.href.lastIndexOf('/')+1)+'assets/ethan-page.png';
 assert.equal(config.routes[assetKey],routes[c.portrait_routes['ethan-page.png']]);
 assert.equal(routes[assetKey],undefined,'approved route inventory is never modified');
});
test('changed holder never inherits the previous reign; explicit tag members map individually',()=>{
 const c=resolveChampion(title,'Ethan Page',options);assert.equal(c.since_date,null);assert.equal(c.since,null);
 const tag=resolveChampion(catalog.raw.find(c=>c.id==='raw-tag'),'Penta & Dragon Lee',options);
 assert.deepEqual(tag.members,['Penta','Dragon Lee']);assert.equal(tag.portraits.length,2);assert.equal(tag.kind,'tag');
 assert.throws(()=>resolveChampion(title,'Unpictured Wrestler',options),/Approved portrait unavailable/);
 assert.throws(()=>resolveChampion(title,'Vacant',options),/Current holder unavailable/);
});
test('one unavailable WWE title does not remove other champions and history cannot stand in for current holder',async()=>{
 const original=wweRequester();const got=await collectChampions({library,routes,now,requester:async url=>url===title.source?new Response(pad('<p>Former champion Ethan Page</p>')):original(url)});
 const raw=got.feed.programs.find(p=>p.show==='raw');assert.equal(raw.champions.length,4);assert.ok(!raw.champions.some(c=>c.id===title.id));
});
test('TNA updates by the championship label, never another champion elsewhere in the roster',async()=>{
 const cards=catalog.tna.map(c=>'<a><h5>'+(c.id==='tna-world'?'Ethan Page':c.name)+'</h5><h6>'+c.title.replace(/CHAMPIONSHIP$/,'CHAMPION')+'</h6></a>').join('');
 const html=pad('<section><h1>Meet Our Champions</h1>'+cards+'</section><section><h5>Leon Slater</h5><h6>TNA WORLD CHAMPION</h6></section>');
 assert.equal(tnaTitleholders(html).length,7);
 const got=await collectChampions({library,routes,now,requester:async url=>{if(url==='https://tnawrestling.com/roster')return new Response(html);throw Error('offline');}});
 const tna=got.feed.programs.find(p=>p.show==='tna');assert.equal(tna.champions.length,7);
 const c=tna.champions.find(c=>c.id==='tna-world');assert.equal(c.name,'ETHAN PAGE');assert.equal(c.since_date,null);assert.equal(c.belt,'tna_world.png');
});
test('AAA title changes require both lists to agree and use source date instead of old reign',async()=>{
 const table=(other=false)=>'<table><tr><th>Championship</th><th>Current Champion(s)</th><th>Date Won</th></tr>'+catalog.aaa.map(c=>'<tr><td>'+c.title+'</td><td>'+(c.id==='aaa-mega'?(other?'Penta':'Ethan Page'):c.name+' ('+c.members.join(' & ')+')')+'</td><td>November 2, 2026</td></tr>').join('')+'</table>';
 const cards=(disagree=false)=>'<h2>Current AAA Champions: Full List</h2>'+catalog.aaa.map(c=>'<h3>'+(c.id==='aaa-mega'?(disagree?'Penta':'Ethan Page'):c.members.join(' & '))+'</h3><a>'+c.title.replace('WORLD TAG','TAG').replace('WORLD TRIOS','TRIOS').replace('WORLD MIXED TAG','MIXED TAG').replace(/CHAMPIONSHIP$/,'CHAMPION')+'</a><p>Won: November 2, 2026</p>').join('');
 const request=disagree=>async url=>{if(!/sacnilk|thesmackdownhotel/.test(url))throw Error('offline');return new Response(pad(url.includes('thesmackdownhotel')?cards(disagree):table()));};
 const ok=await collectChampions({library,routes,now,requester:request(false)});const aaa=ok.feed.programs.find(p=>p.show==='aaa');assert.equal(aaa.champions.length,7);
 const c=aaa.champions.find(c=>c.id==='aaa-mega');assert.equal(c.name,'ETHAN PAGE');assert.equal(c.since_date,'2026-11-02');
 const held=await collectChampions({library,routes,now,requester:request(true)});assert.equal(held.feed.programs.find(p=>p.show==='aaa').champions.length,6);assert.ok(held.warnings.some(w=>w.includes('AAA current titleholder disagreement')));
});
