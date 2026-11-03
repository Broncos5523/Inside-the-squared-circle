import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import portraits from '../web/staging/board-adapter.js';
import {segment} from '../proof/staging/official-weekly-results.mjs';
const root=new URL('../web/staging/',import.meta.url),routes=JSON.parse(readFileSync(new URL('asset-routes.json',root))),library=JSON.parse(readFileSync(new URL('library.json',root)));
test('canonical portraits ignore punctuation, accents, title prefixes and approved aliases',()=>{
 for(const [name,expected] of [["Je’Von Evans",'je-von-evans'],["Tony D’Angelo",'tony-d-angelo'],['WWE Women’s Champion Chelsea Green','chelsea-green'],['TNA X-Division Champion Amazing Red','amazing-red'],['Zer0','agent-zero'],['Zero','agent-zero'],['Agent Zero','agent-zero'],['Rey Fénix','rey-fenix'],['All Ego Ethan Page','ethan-page']])assert.deepEqual(portraits.portraitSlugs(name,routes),[expected],name);
 assert.deepEqual(portraits.portraitSlugs('Sami Zayn & World Champion Roman Reigns',routes),['sami-zayn','roman-reigns']);
 assert.deepEqual(portraits.portraitSlugs('Ryan and Nic Nemeth',routes),['the-nemeths']);
 assert.deepEqual(portraits.portraitSlugs('Unpictured Wrestler',routes),[]);
});
test('all winners in explicit tag and triple-threat lists resolve without opponent portraits',()=>{
 const c=segment('Je’Von Evans, Tony D’Angelo & Rey Fénix def. Roman Reigns & Sami Zayn','raw',0,routes,'2026-11-02');
 assert.deepEqual(c.portraits,['je-von-evans','tony-d-angelo','rey-fenix']);assert.equal(c.portrait_rule,'winners_only');
});
test('preview champion prefixes and compound teams populate existing portrait slots',()=>{
 const row=library.records.find(r=>r.id==='weekly-upcoming-raw');
 const feeds={'snapshot.json':{shows:[{id:'raw',next:{date:'2026-11-09'}}]},'reported.json':{programs:[{show_id:'raw',airdate:'2026-11-09',matches:[{text:'WWE Women’s Champion Chelsea Green vs. Je’Von Evans & Tony D’Angelo'},{text:'Ryan and Nic Nemeth vs. Amazing Red'}],appearances:[]}]}};
 const html=portraits.build(readFileSync(new URL(row.delivery,root),'utf8'),row,routes,'https://player.example/','active',feeds);
 const config=JSON.parse(html.match(/<base[^>]*><script>[\s\S]*?\)\((\{"weeklyResults":[\s\S]*?)\);<\/script>/)[1]);
 assert.ok(config.previewPortraits.wwewomenschampionchelseagreen);
 assert.deepEqual(config.previewTeams.jevonevanstonydangelo,['je-von-evans','tony-d-angelo']);
 assert.ok(config.previewPortraits.ryanandnicnemeth);
});
