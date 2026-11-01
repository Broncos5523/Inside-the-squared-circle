import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import {parseDatedEventBrief} from '../proof/staging/event-preview.mjs';
import {collectOfficialEventResults,HALLOWEEN_RESULTS_ID} from '../proof/staging/official-event-results.mjs';
import playlist from '../web/staging/playlist-engine.js';
import {parseAaaCorroboration} from '../proof/staging/corroborated-aaa-results.mjs';
const root=new URL('../web/staging/',import.meta.url),routes=JSON.parse(readFileSync(new URL('asset-routes.json',root))),library=JSON.parse(readFileSync(new URL('library.json',root)));
const canonical='https://wrestlingcentralnews.com/events/2026-11-02-wwe-raw/';
const article=(head,body)=>'<article><h3>'+head+'</h3><p class="hs">'+body+'</p><time datetime="2026-11-01T14:00:00Z">Nov 1</time></article>';
const page=articles=>'<link rel="canonical" href="'+canonical+'"><h1>WWE Raw Card &amp; Preview November 2, 2026</h1><section id="card">'+articles+'</section>';
test('dated RAW event cards provide matches, appearances, and the special start without importing SmackDown or PLE bouts',()=>{
 const html=page(article('Chad Gable defends IC title vs Ethan Page on Raw','Raw features Chad Gable putting the Intercontinental Championship on the line against Ethan Page. Penta, Je’Von Evans and Dragon Lee face The Vision. John Cena is advertised for a special announcement, while Solo Sikoa faces Royce Keys.')+article('Tomorrow’s Raw lineup','Roman Reigns addressing Sami Zayn on Raw. SmackDown will feature CM Punk vs. Kevin Owens. Roman Reigns vs. Sami Zayn at Crown Jewel.')+article('Raw moves to 6PM ET on November 2','The November 2 show has a special start time at 6 PM ET.'));
 const got=parseDatedEventBrief(html,'raw','2026-11-02',routes);
 assert.equal(got.matches.length,3);assert.equal(got.start_time,'18:00');
 assert.deepEqual(got.appearances.map(x=>x.text).sort(),['John Cena','Roman Reigns']);
 assert.ok(!got.matches.some(x=>/Owens|Sami/.test(x.text)));
 assert.equal(playlist.dwellMs({kind:'upcoming',show:'raw',airdate:'2026-11-02'},{'reported.json':{programs:[{show_id:'raw',airdate:'2026-11-02',...got}]}},45000),90500);
 assert.deepEqual(parseDatedEventBrief(html,'raw','2026-11-09',routes),{matches:[],appearances:[]});
});
test('a conflicting article date or NXT article cannot enter the RAW preview',()=>{
 const html=page(article('Roman Reigns set for Raw','Roman Reigns will appear on the November 4 Raw.')+article('Shawn Michaels promotes NXT on Raw','John Cena vs. Roman Reigns on November 2 NXT.'));
 const got=parseDatedEventBrief(html,'raw','2026-11-02',routes);assert.deepEqual(got.matches,[]);assert.deepEqual(got.appearances,[]);
});
const headings=['Myles Borne def. Tavion Heights | Weapons Wild Match','Izzi Dame def. NXT Women’s North American Champion Zaria | Non-Title Match','Zilla Fatu def. Charlie Dempsey | Very Nice, Very Evil Match','NXT Women’s Champion Kelani Jordan def. Wren Sinclair','Shiloh Hill def. Naraku','NXT Champion Grayson Waller def. Tony D’Angelo'];
const resultHtml=lines=>'<title>Full NXT Halloween Havoc 2026 results | WWE</title><div class="field--name-body">'+lines.map(x=>'<strong>'+x+'</strong>').join('')+' CM Punk who demanded a title opportunity.</div>';
const requester=async url=>new Response(url.includes('full-nxt')?resultHtml(headings):'NXT Halloween Havoc 2026 Saturday, Oct. 31');
test('Halloween Havoc yields all six winners, correct championship belts, and seven-day result eligibility',async()=>{
 const got=await collectOfficialEventResults({library,routes,now:new Date('2026-11-01T18:00:00Z'),requester});
 assert.deepEqual(got.warnings,[]);assert.equal(got.entries[0].id,HALLOWEEN_RESULTS_ID);
 const p=got.feed.programs[0];assert.equal(p.matches.length,6);assert.equal(p.matches.filter(x=>x.belt).length,2);
 assert.equal(p.matches[1].headline,'IZZI DAME');assert.equal(p.matches[1].belt,undefined);
 assert.ok(playlist.dwellMs(got.entries[0],{'official-event-results.json':got.feed},45000)>=62500);
 assert.equal(playlist.select(got.entries,new Date('2026-11-01T18:00:00Z')).length,1);
 const expired=await collectOfficialEventResults({library,routes,now:new Date('2026-11-08T18:00:00Z'),requester});assert.equal(expired.entries.length,0);
 const host={};runInNewContext(readFileSync(new URL('board-adapter.js',root),'utf8'),{window:host,URL});
 const row=library.records.find(r=>r.id===HALLOWEEN_RESULTS_ID),source=readFileSync(new URL(row.delivery,root),'utf8');
 const compiled=host.ISCBoardAdapter.build(source,row,routes,'https://player.example/','active',{'official-event-results.json':got.feed});
 const config=JSON.parse(compiled.match(/<base[^>]*><script>[\s\S]*?\)\((\{"weeklyResults":[\s\S]*?)\);<\/script>/)[1]);
 assert.equal(config.eventResults.matches.length,6);assert.ok(config.eventResults.matches.every(m=>m.portrait_url?.includes('/originals/shared/')));
});
test('incomplete or unapproved event results remain gated',async()=>{
 const notApproved={records:library.records.map(r=>({...r,design_approved:false}))};
 assert.equal((await collectOfficialEventResults({library:notApproved,routes,requester})).entries.length,0);
 const bad=await collectOfficialEventResults({library,routes,now:new Date('2026-11-01T18:00:00Z'),requester:async url=>new Response(url.includes('full-nxt')?resultHtml(headings.slice(0,5)):'NXT Halloween Havoc 2026 Oct 31')});assert.equal(bad.entries.length,0);
});

test('latest AAA match results require matching dated reports and ignore related-story lists',()=>{
 const f='<title>AAA Heroes Inmortales Week Two Results (10/31)</title><meta property="article:published_time" content="2026-11-01T03:06:28Z"><div class="entry-content"><div>ad</div><ul><li>AAA World Tag Team Championships: The Wagner Brothers (c) def. Los Vipers to retain the titles.</li><li>El Carnicero &amp; Pagano def. Los Psycho Circus</li><li>AAA World Cruiserweight Championship: Rey Fenix (c) def. Jack Cartwheel, Takuma, and Laredo Kid to retain the title.</li></ul></div><li>Grayson Waller def. Tony D’Angelo</li>';
 const t='<title>AAA Heroes Inmortales 2026 Week 2 Results – Oct. 31, 2026</title><p>Winner: The Wagner Brothers via Pinfall.</p><p>Winner: Pagano &amp; El Carnicero via Pinfall.</p><p>Winner: Rey Fenix via Pinfall.</p>';
 const matches=parseAaaCorroboration(f,t,'2026-10-31',routes);assert.equal(matches.length,3);assert.equal(matches[0].belt,'world_tag.png');assert.equal(matches[2].headline,'REY FENIX');
 assert.deepEqual(parseAaaCorroboration(f,t.replace('Winner: Rey Fenix','Winner: Jack Cartwheel'),'2026-10-31',routes),[]);
 assert.deepEqual(parseAaaCorroboration(f,t,'2026-10-24',routes),[]);
 const entry={id:'weekly-results-aaa',show:'aaa',kind:'results',airdate:'2026-10-31',source_available:true,design_approved:true,content_status:'current',verification:'SOURCE_CORROBORATED',completed:true,checked_at:'2026-11-01T18:00:00Z',source_url:'https://www.fightful.com/wrestling/result/',source_urls:['https://www.fightful.com/wrestling/result/','https://www.tpww.net/result/']};
 assert.equal(playlist.select([entry],new Date('2026-11-01T18:00:00Z')).length,1);
 assert.equal(playlist.select([{...entry,source_urls:[entry.source_url]}],new Date('2026-11-01T18:00:00Z')).length,0);
});
