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
test('TNA preview excludes later tapings but keeps one complete episode card and announced initiation',async()=>{
 const url='https://wrestlingcentralnews.com/events/2026-11-05-tna-impact/';
 const wrap=items=>'<link rel="canonical" href="'+url+'"><h1>TNA iMPACT Card &amp; Preview November 5, 2026</h1><h2>Card &amp; preview</h2><section id="card">'+items+'</section>';
 const html=wrap(
  article('TNA Reveals Opening Matches For Calgary Debut','Upcoming TV tapings in Calgary later this month feature Indi Hartwell, Allie, Shotzi Blackheart and Gabby Forza vs. Tasha Steelz, Kiera Hogan, Zoey Serrano and Shayna Baszler.')+
  article('TNA Calgary Impact card','The November 18 TV tapings feature Indi Hartwell vs. Shayna Baszler.')+
  article('Harley Hudson Joins Righteous On 11/5 TNA iMPACT','The November 5 episode of Impact features Harley Hudson. Harley Hudson will undergo her initiation into The Righteous. Eddie Edwards faces Bear Bronson. Ryan and Nic Nemeth will defend the TNA Tag Team titles against Amazing Red and Leon Slater while Fire \'N Flava take on Allie and Shotzi Blackheart.')+
  article('TNA Impact lineup for November 5',"Former Knockouts World Tag Team Champions Fire 'N Flava battle Allie and Shotzi Blackheart."));
 const got=parseDatedEventBrief(html,'tna','2026-11-05',routes);
 assert.deepEqual(got.matches.map(m=>m.text),['Eddie Edwards vs. Bear Bronson','Ryan and Nic Nemeth vs. Amazing Red and Leon Slater',"Fire 'N Flava vs. Allie and Shotzi Blackheart"]);
 assert.deepEqual(got.appearances.map(a=>a.text),['Harley Hudson']);
 assert.ok(!got.matches.some(m=>/Hartwell|Forza|Baszler/.test(m.text)));
 const {collectWcn}=await import('../proof/staging/wcn-collector.mjs');
 const now=new Date('2026-11-03T18:00:00Z');let audit;
 const snapshot={schema_version:1,generated_at:now.toISOString(),shows:['raw','nxt','evolve','tna','smackdown','aaa'].map(id=>({id,schedule_status:id==='tna'?'fresh':'unavailable',next:id==='tna'?{date:'2026-11-05'}:null}))};
 const request=async source=>{
  if(source.endsWith('snapshot.json'))return new Response(JSON.stringify(snapshot));
  if(source.endsWith('/upcoming/'))return new Response('<a href="'+url+'">TNA</a>');
  if(source.endsWith('/feed.xml'))return new Response('<rss></rss>');
  if(source===url)return new Response(html);
  throw Error('Unexpected source '+source);
 };
 await collectWcn({WCN_CACHE:{get:async()=>null,put:async(_,value)=>{audit=JSON.parse(value);}}},now,request,routes);
 assert.deepEqual(audit.programs[0].matches.map(m=>m.text),got.matches.map(m=>m.text));
 assert.deepEqual(audit.programs[0].appearances.map(a=>a.text),['Harley Hudson']);
});
test('explicit eight-person lineup is complete regardless of available portrait routes',()=>{
 const url='https://wrestlingcentralnews.com/events/2026-11-18-tna-impact/';
 const text='Indi Hartwell, Allie, Shotzi Blackheart and Gabby Forza vs. Tasha Steelz, Kiera Hogan, Zoey Serrano and Shayna Baszler';
 const html='<link rel="canonical" href="'+url+'"><h1>TNA iMPACT Card &amp; Preview November 18, 2026</h1><section id="card"><article><h3>TNA Calgary Impact card</h3><p class="hs">The November 18 TV tapings feature '+text+'.</p><time datetime="2026-11-04T15:52:00Z"></time></article></section>';
 const withRoutes=parseDatedEventBrief(html,'tna','2026-11-18',routes);
 const withoutRoutes=parseDatedEventBrief(html,'tna','2026-11-18',{});
 assert.deepEqual(withoutRoutes,withRoutes);assert.equal(withoutRoutes.matches.length,1);assert.equal(withoutRoutes.matches[0].text,text);
});
test('a bounded or unreadable participant list never produces a shortened matchup',()=>{
 for(const text of [
  'Chad Gable vs. Ethan Page and a mystery partner.',
  'Chad Gable vs. Ethan Page, Penta, Dragon Lee, Sami Zayn and John Cena.',
  'Ethan Page, Penta, Dragon Lee, Sami Zayn and John Cena vs. Chad Gable.'
 ])assert.deepEqual(parseDatedEventBrief(page(article('Raw match announcement',text)),'raw','2026-11-02',{}).matches,[],text);
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

test('RAW six-man preview uses three individual portraits on each side and the supplied Cena asset',async()=>{
 const {enrichPreviewParticipants}=await import('../proof/staging/preview-participants.mjs');
 const announced='<title>November 2nd WWE RAW</title><p>Penta, Je’Von Evans, Dragon Lee vs. The Vision (Austin Theory, Bronson Reed, Bron Breakker)</p>';
 const program={show_id:'raw',airdate:'2026-11-02',matches:[{text:'Penta, Je’Von Evans and Dragon Lee vs. The Vision'}],appearances:[{text:'John Cena'}]};
 await enrichPreviewParticipants(program,async()=>new Response(announced));
 assert.deepEqual(program.matches[0].participant_sides[0].members,['Austin Theory','Bronson Reed','Bron Breakker']);
 const next={show_id:'raw',airdate:'2026-11-09',matches:[{text:program.matches[0].text}]};
 await enrichPreviewParticipants(next,async()=>{throw Error('must not reuse dated roster');});assert.equal(next.matches[0].participant_sides,undefined);
 const row=library.records.find(r=>r.id==='weekly-upcoming-raw'),host={};runInNewContext(readFileSync(new URL('board-adapter.js',root),'utf8'),{window:host,URL});
 const source=readFileSync(new URL(row.delivery,root),'utf8');
 const html=host.ISCBoardAdapter.build(source,row,routes,'https://player.example/','active',{'reported.json':{programs:[program]},'snapshot.json':{shows:[{id:'raw',next:{date:'2026-11-02'}}]}});
 const config=JSON.parse(html.match(/<base[^>]*><script>[\s\S]*?\)\((\{"weeklyResults":[\s\S]*?)\);<\/script>/)[1]);
 for(const key of ['penta','jevonevans','dragonlee','austintheory','bronsonreed','bronbreakker','johncena'])assert.ok(config.previewPortraits[key],key);
 assert.deepEqual(config.previewTeams.thevision,['Austin Theory','Bronson Reed','Bron Breakker']);
 assert.match(html,/const USER_CUTOUTS=\{"john cena":/);assert.match(html,/const data=\{"snapshot":/);
 const archive=host.ISCBoardAdapter.build(source,row,routes,'https://player.example/','archive',{});assert.ok(!archive.includes('const USER_CUTOUTS={"john cena":'));
});

test('all five championship designs compile checked current titleholders without changing originals',()=>{
 // Rendering coverage uses the approved catalog, never mutable collector output.
 const catalog=JSON.parse(readFileSync(new URL('../proof/staging/championship-catalog.json',import.meta.url)));
 const programs=Object.entries(catalog).map(([show,champions])=>({show,board_id:'championship-'+show,as_of:'2026-11-02',champions}));
 const data={feeds:{'champions.json':{mode:'SOURCE_CHECKED_CHAMPIONS',programs}}},host={};runInNewContext(readFileSync(new URL('board-adapter.js',root),'utf8'),{window:host,URL});
 const champions=data.feeds['champions.json'];assert.equal(champions.programs.length,5);
 for(const program of champions.programs){const row=library.records.find(r=>r.id===program.board_id),source=readFileSync(new URL(row.delivery,root),'utf8');assert.ok(row.design_approved);const html=host.ISCBoardAdapter.build(source,row,routes,'https://player.example/','active',data.feeds);assert.ok(html.includes(JSON.stringify(program.champions)));assert.ok(playlist.dwellMs({id:row.id,kind:'champions'},data.feeds,45000)>=program.champions.length*11000);}
});
test('WWE champion verification reads the current holder, never names in title history',async()=>{
 const {currentWweHolder}=await import('../proof/staging/collect-champions.mjs');
 assert.equal(currentWweHolder('<h3><span>Championship Holder</span>New Champion</h3><div>Time Held</div><p>Previous Champion</p>'),'New Champion');
 assert.equal(currentWweHolder('<p>Former champion New Champion</p>'),null);
});
test('championship reign timestamps use Eastern dates across UTC midnight',async()=>{
 const {easternDate}=await import('../proof/staging/collect-champions.mjs');
 assert.equal(easternDate(new Date('2026-08-03T01:00:00Z')),'2026-08-02');
});

test('schedule rollover retains last verified results without renewing the source check',async()=>{
 const {retainLastVerifiedResults}=await import('../proof/staging/last-verified-results.mjs');
 const old={id:'weekly-results-raw',show:'raw',kind:'results',airdate:'2026-10-26',checked_at:'2026-11-01T20:00:00Z',verification:'OFFICIAL_VERIFIED',completed:true,content_status:'current',source_url:'https://www.wwe.com/shows/raw/2026-10-26/results'};
 const program={show_id:'raw',airdate:old.airdate,source_url:old.source_url,verification:'OFFICIAL_SOURCE_EXTRACTED',segments:[{headline:'SOURCE VERIFIED WINNER'}]};
 const previous={entries:[old],feeds:{'raw-verified-results.json':{mode:'OFFICIAL_EXTRACTED_RESULTS',programs:[program]}}};
 const entries=[],feeds={},now=new Date('2026-11-02T21:00:00Z');
 assert.deepEqual(retainLastVerifiedResults({previous,entries,feeds,library,now}),[old.id]);assert.equal(entries[0].checked_at,old.checked_at);assert.equal(entries[0].airdate,'2026-10-26');
 const newer=[{...old,airdate:'2026-11-02'}];assert.deepEqual(retainLastVerifiedResults({previous,entries:newer,feeds:{},library,now}),[]);
 assert.deepEqual(retainLastVerifiedResults({previous,entries:[],feeds:{},library,now:new Date('2026-11-04T21:00:00Z')}),[]);
});

test('official NXT episode banner overrides Tuesday despite Monday article URL dates and yields the complete announced card',async()=>{
 const {collectOfficialNxtPreview,nextOfficialNxtDate}=await import('../proof/staging/official-nxt-preview.mjs');
 const prefix='https://www.wwe.com/shows/wwenxt/2026-11-2/';
 const articles={
 'punk-waller':['CM Punk challenges Grayson Waller for the NXT Championship','Waller previously defeated Tony D’Angelo.'],
 'nxt-womens-title':['Kelani Jordan defends the NXT Women’s Championship against a mystery opponent','An opponent has not been named.'],
 'dusty-final':['Romeo Moreno & Noam Dar battle Hank & Tank in Dusty Cup Final','Hank Walker and Tank Ledger face Romeo Moreno and Noam Dar. Cody Rhodes will crown the winner.'],
 'six-man-tag':['Chad Gable, Rey Fenix and Dragon Lee take on The Vanity Project','Jackson Drake, Brad Baylor and Ricky Smokes represent The Vanity Project.'],
 'cena':['John Cena to appear on NXT','John Cena will appear.']};
 const index='<div data-a2a-url="https://www.wwe.com/shows/wwenxt/2026-11-4" data-a2a-title="WWE NXT: Nov. 4, 2026"></div>'+Object.keys(articles).map(k=>'<a href="'+prefix+k+'">Preview</a>').join('');
 const requester=async url=>{if(url==='https://www.wwe.com/shows/wwenxt')return new Response(index);const slug=url.split('/').at(-1),a=articles[slug];if(a)return new Response('<link rel="canonical" href="'+url+'"><title>'+a[0]+' | WWE</title><div class="field--name-body"><p>'+a[1]+'</p><p>WWE NXT airs live on WEDNESDAY at 8 ET/7 CT on the CW Network.</p></div>');return new Response('<h2>Current Card For Next Week’s WWE NXT Show</h2><p>November 4th: Unsanctioned match – Cruz Montana vs. Dion Lennox, with Michael Chandler involved.</p>');};
 const now=new Date('2026-11-02T21:00:00Z');assert.equal(nextOfficialNxtDate(index,now),'2026-11-04');assert.equal(nextOfficialNxtDate(index,new Date('2026-11-05T21:00:00Z')),null);
 const p=await collectOfficialNxtPreview({routes,now,requester});assert.equal(p.airdate,'2026-11-04');assert.equal(p.start_time,'20:00');assert.equal(p.matches.length,5);assert.deepEqual(p.appearances.map(a=>a.text).sort(),['Cody Rhodes','John Cena']);
 assert.ok(p.matches.some(m=>m.text==='CM Punk vs. Grayson Waller'));assert.ok(!p.matches.some(m=>m.text.includes('Tony')));assert.equal(p.matches.find(m=>m.text.includes('Cruz')).note,'Michael Chandler involved');
 const row=library.records.find(r=>r.id==='weekly-upcoming-nxt'),host={};runInNewContext(readFileSync(new URL('board-adapter.js',root),'utf8'),{window:host,URL});
 const source=readFileSync(new URL(row.delivery,root),'utf8'),feeds={'reported.json':{programs:[p]},'snapshot.json':{shows:[{id:'nxt',next:{date:p.airdate,time:p.start_time}}]}};
 const compiled=host.ISCBoardAdapter.build(source,row,routes,'https://player.example/','active',feeds);
 assert.match(compiled,/WEDNESDAY NIGHT NXT/);assert.ok(!compiled.includes('TUESDAY NIGHT NXT'));assert.match(compiled,/const USER_CUTOUTS=\{"john cena":/);
 const config=JSON.parse(compiled.match(/<base[^>]*><script>[\s\S]*?\)\((\{"weeklyResults":[\s\S]*?)\);<\/script>/)[1]);assert.equal(config.previewTeams.thevanityproject.length,3);assert.equal(config.previewTeams.hanktank.length,2);assert.ok(config.previewPortraits.johncena);assert.ok(config.previewNotes.cruzmontanavsdionlennox.includes('MICHAEL CHANDLER'));
 assert.equal(playlist.dwellMs({kind:'upcoming',show:'nxt',airdate:p.airdate},feeds,45000),118500);
});
test('official NXT preview rejects a banner title/date mismatch and an article advertising another weekday',async()=>{
 const {nextOfficialNxtDate,parseOfficialNxtArticle}=await import('../proof/staging/official-nxt-preview.mjs');
 const bad='<div data-a2a-url="https://www.wwe.com/shows/wwenxt/2026-11-4" data-a2a-title="WWE NXT: Nov. 3, 2026">';assert.equal(nextOfficialNxtDate(bad,new Date('2026-11-02T21:00:00Z')),null);
 const url='https://www.wwe.com/shows/wwenxt/2026-11-2/punk-waller';assert.equal(parseOfficialNxtArticle('<link href="'+url+'"><title>CM Punk challenges Grayson Waller</title><div class="field--name-body">WWE NXT airs live on TUESDAY at 8 ET/7 CT</div>',url,'2026-11-04',routes),null);
});

 test('an unmapped champion withholds only its title and never invalidates other verified programs',async()=>{
 const {collectChampions}=await import('../proof/staging/collect-champions.mjs');
 const catalog=JSON.parse(readFileSync(new URL('../proof/staging/championship-catalog.json',import.meta.url)));
 const holders=new Map(Object.entries(catalog).filter(([show])=>!['aaa','tna'].includes(show)).flatMap(([,rows])=>rows.map(c=>[c.source,c.name])));
 const rawSource=catalog.raw[0].source;
 const got=await collectChampions({library,routes,now:new Date('2026-11-03T14:00:00Z'),requester:async url=>{
  if(!holders.has(url))throw Error('source temporarily unavailable');
  return new Response('<h3>Championship Holder '+(url===rawSource?'New Unmapped Champion':holders.get(url))+'</h3><div>Time Held</div>'+' '.repeat(1100));
 }});
 assert.deepEqual(got.feed.programs.map(p=>p.show).sort(),['nxt','raw','smackdown']);
 assert.ok(got.warnings.some(w=>w.includes('Approved portrait unavailable: New Unmapped Champion')));
 assert.equal(got.feed.programs.find(p=>p.show==='raw').champions.length,4);
 assert.ok(!got.feed.programs.find(p=>p.show==='raw').champions.some(c=>c.id==='raw-world'));
 });
