import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import portraits from '../web/staging/board-adapter.js';
import {resolveChampion} from '../proof/staging/collect-champions.mjs';
const root=new URL('../web/staging/',import.meta.url),routes=JSON.parse(readFileSync(new URL('asset-routes.json',root))),library=JSON.parse(readFileSync(new URL('library.json',root)));
const catalog=JSON.parse(readFileSync(new URL('../proof/staging/championship-catalog.json',import.meta.url)));
const supplement=JSON.parse(readFileSync(new URL('../proof/staging/named-portrait-supplement.json',import.meta.url)));
function config(html){return JSON.parse(html.match(/<base[^>]*><script>[\s\S]*?\)\((\{"weeklyResults":[\s\S]*?)\);<\/script>/)[1]);}
test('all ten named portraits retain source labels, verified bytes and complete route mappings',()=>{
 assert.equal(supplement.assets.length,10);
 for(const a of supplement.assets){assert.equal(createHash('sha256').update(readFileSync(new URL(a.path,root))).digest('hex'),a.sha256);assert.match(a.source_page,/^https:\/\/www.thesmackdownhotel.com\/wrestlers\//);assert.ok(a.alpha_crop.length===4);for(const r of a.routes)assert.equal(routes[r],'/shared/'+a.sha256+'.webp');}
 for(const n of ['Kento','SB KENTo','Kento Kobune'])assert.deepEqual(portraits.portraitSlugs(n,routes),['kento']);
 assert.deepEqual(portraits.portraitSlugs('El Hijo del Dr. Wagner Jr.',routes),['el-hijo-de-dr-wagner-jr']);
});
test('AAA champions complete missing and partial artwork while preserving the titleholder and belt',()=>{
 const board=library.records.find(r=>r.id==='championship-aaa');
 for(const [id,n] of [['aaa-latin',1],['aaa-tag',2],['aaa-mixed',2]]){const original=catalog.aaa.find(c=>c.id===id),c=resolveChampion(original,original.name,{catalog,routes,board,show:'aaa',asOf:'2026-11-03'});assert.equal(c.portraits.length,n);assert.equal(c.name,original.name);assert.equal(c.belt,original.belt);for(const p of c.portraits)assert.ok(c.portrait_routes[p]);}
});
test('named pairs show both people and large factions are never expanded from roster reference alone',()=>{
 assert.deepEqual(portraits.portraitSlugs('The Wagner Brothers',routes),['el-hijo-de-dr-wagner-jr','galeno']);
 assert.deepEqual(portraits.portraitSlugs('N Flava',routes),['kiera-hogan','tasha-steelz']);
 assert.deepEqual(portraits.portraitSlugs('The Street Profits',routes),['angelo-dawkins','montez-ford']);
 assert.deepEqual(portraits.portraitSlugs('The Judgment Day',routes),[]);
});
test('TNA preview paints both Fire N Flava members and both announced opponents',()=>{
 const row=library.records.find(r=>r.id==='weekly-upcoming-tna'),source=readFileSync(new URL(row.delivery,root),'utf8');
 const feeds={'snapshot.json':{shows:[{id:'tna',next:{date:'2026-11-05'}}]},'reported.json':{programs:[{show_id:'tna',airdate:'2026-11-05',matches:[{text:'N Flava vs. Allie and Shotzi Blackheart'}],appearances:[]}]}};
 const c=config(portraits.build(source,row,routes,'https://player.example/','active',feeds));
 assert.deepEqual(c.previewTeams.nflava,['kiera-hogan','tasha-steelz']);assert.deepEqual(c.previewTeams.allieandshotziblackheart,['allie','shotzi-blackheart']);
 for(const p of ['kierahogan','tashasteelz','allie','shotziblackheart'])assert.ok(c.previewPortraits[p]);
});
