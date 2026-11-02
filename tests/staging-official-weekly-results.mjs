import assert from 'node:assert/strict';
import {test} from 'node:test';
import {collectOfficialWeeklyResults} from '../proof/staging/official-weekly-results.mjs';
const now=new Date('2026-10-31T17:21:00Z');
const specs=[
 {show:'raw',day:'2026-10-26',title:'Raw results, Oct. 26, 2026 | WWE',lines:[
  'Sami Zayn def. Je’Von Evans',
  'Bayley def. Lyra Valkyria in No Disqualification Match',
  'IYO SKY def. Raquel Rodriguez',
  'Ethan Page & Big Cass def. Chad Gable & Dragon Lee',
  'Becky Lynch def. Liv Morgan by Disqualification in a Women’s World Title Match']},
 {show:'nxt',day:'2026-10-27',title:'WWE NXT results: Oct. 27, 2026 | WWE',lines:[
  'Romeo Moreno & Noam Dar def. The Vanity Project | Dusty Rhodes Tag Team Classic Semifinals',
  'Chantel Monroe def. Lizzy Rain','Sean Legacy def. Saquon Shugars',
  'Hank & Tank def. El Hijo de Dr. Wagner Jr. & Galeno | Dusty Rhodes Tag Team Classic Semifinals',
  'NXT North American Champion Jackson Drake def. EK Prosper']},
 {show:'smackdown',day:'2026-10-30',title:'SmackDown results: Oct. 30, 2026 | WWE',lines:[
  'Chelsea Green def. Nikki Bella in a WWE Women’s Championship Match',
  'Rey Fenix def. Ricky Saints in an AAA World Cruiserweight Championship Match',
  'Jade Cargill def. Tatum Paxley',
  'Sami Zayn def. Trick Williams in an Undisputed WWE Title Match']},
 {show:'tna',day:'2026-10-29',title:'TNA Thursday Night iMPACT! on AMC Results: October 29, 2026 | TNA Wrestling',lines:[
  'TNA Knockouts TV Champion M by Elegance Def. Jada Stone - TNA Knockouts TV Championship',
  'Zer0 Def. BDE - Singles Match',
  'TNA X-Division Champion Amazing Red Def. Cedric Alexander - TNA X-Division Championship',
  'AJ Francis acc. by Expressions Def. John Skyler acc. by Mila Moore - Singles Match',
  'Elijah Def. TNA World Tag Team Champion Ryan Nemeth - Singles Match']}
];
const lib={records:specs.map(x=>({id:'weekly-results-'+x.show,label:x.show.toUpperCase()+' — Results & Fallout',source_available:true,design_approved:true}))};
const routes={};
for(const s of ['sami-zayn','bayley','iyo-sky','ethan-page','big-cass','becky-lynch','romeo-moreno','noam-dar','sean-legacy','hank-walker','tank-ledger','jackson-drake','chelsea-green','rey-fenix','jade-cargill','m-by-elegance','amazing-red','aj-francis','elijah','chantel-monroe','agent-zero'])
 routes['/boards/UPCOMING/NXT/assets/portraits/'+s+'.png']='/shared/'+s+'.png';
for(const x of ['nxt_north_american','wwe_wwe-womens-championship','cruiserweight','wwe_undisputed-wwe-championship','tna_x_division'])
 routes['/boards/UPCOMING/NXT/assets/belts/'+x+'.png']='/shared/'+x+'.png';
const snapshot={shows:specs.map(x=>({id:x.show,previous:{date:x.day}}))};
function html(x){return '<html><head><title>'+x.title+'</title></head><body><div class="'+(x.show==='tna'?'article-body':'field--name-body')+'">'+x.lines.map(s=>'<p><strong>'+s.replaceAll('&','&amp;').replaceAll('’','&#039;')+'</strong></p>').join('')+'</div>'+('z'.repeat(3100))+'</body></html>';}
const requester=async url=>{
 const x=specs.find(s=>url.includes('tna')?s.show==='tna':url.includes(s.show==='nxt'?'/wwenxt/':('/'+s.show+'/'))&&s.show!=='tna');
 return {ok:!!x,status:x?200:404,text:async()=>x?html(x):''};
};
test('all four current official dated results pass deterministic source checks',async()=>{
 const got=await collectOfficialWeeklyResults({library:lib,routes,snapshot,now,requester});
 assert.deepEqual(got.entries.map(e=>e.show),['raw','nxt','smackdown','tna']);
 assert.deepEqual(got.entries.map(e=>e.airdate),['2026-10-26','2026-10-27','2026-10-30','2026-10-29']);
 assert.deepEqual(got.entries.map(e=>got.feeds[e.show+'-verified-results.json'].programs[0].segments.length),[5,5,4,5]);
 assert.deepEqual(got.warnings,[]);
 assert.ok(got.entries.every(e=>e.verification==='OFFICIAL_VERIFIED'));
 assert.ok(got.entries.every(e=>got.feeds[e.show+'-verified-results.json'].mode==='OFFICIAL_EXTRACTED_RESULTS'));
 assert.ok(got.feeds['raw-verified-results.json'].programs[0].verification==='OFFICIAL_SOURCE_EXTRACTED');
});
test('winners-only portraits, no losers and no invented headshots or belts',async()=>{
 const got=await collectOfficialWeeklyResults({library:lib,routes,snapshot,now,requester});
 const raw=got.feeds['raw-verified-results.json'].programs[0].segments;
 assert.deepEqual(raw[3].portraits,['ethan-page','big-cass']);
 assert.equal(raw[4].headline,'BECKY LYNCH');
 assert.equal(raw[4].subhead,'def. Liv Morgan');
 assert.equal(raw[4].belt,undefined);
 const nxt=got.feeds['nxt-verified-results.json'].programs[0].segments;
 assert.deepEqual(nxt[1].portraits,['chantel-monroe']);
 assert.deepEqual(nxt[3].portraits,['hank-walker','tank-ledger']);
 assert.equal(nxt[4].belt,'nxt_north_american.png');
 const tna=got.feeds['tna-verified-results.json'].programs[0].segments;
 assert.equal(tna[0].headline,'M BY ELEGANCE');
 assert.deepEqual(tna[1].portraits,['agent-zero']);
 assert.equal(tna[2].belt,'tna_x_division.png');
});
test('Zero, Zer0 and Agent Zero use one approved portrait and preserve the source name',async()=>{
 for(const name of ['Zero','Zer0','Agent Zero']){
  const got=await collectOfficialWeeklyResults({library:lib,routes,snapshot,now,requester:async url=>{
   const response=await requester(url);
   const text=await response.text();
   return {...response,text:async()=>text.replace('Zer0 Def.',name+' Def.')};
  }});
  const segment=got.feeds['tna-verified-results.json'].programs[0].segments[1];
  assert.equal(segment.headline,name.toUpperCase());
  assert.deepEqual(segment.portraits,['agent-zero']);
 }
 const missing={...routes};delete missing['/boards/UPCOMING/NXT/assets/portraits/agent-zero.png'];
 const got=await collectOfficialWeeklyResults({library:lib,routes:missing,snapshot,now,requester});
 assert.deepEqual(got.feeds['tna-verified-results.json'].programs[0].segments[1].portraits,[]);
});
test('wrong official date or only two match finishes never enters rotation',async()=>{
 const bad=await collectOfficialWeeklyResults({library:lib,routes,snapshot,now,requester:async url=>{
 const x=specs.find(s=>url.includes('tna')?s.show==='tna':url.includes('/'+(s.show==='nxt'?'wwenxt':s.show)+'/')&&s.show!=='tna');
 if(!x)return{ok:false,status:404,text:async()=>''};
 const wrong=x.show==='raw'?html({...x,title:'Raw results, Oct. 19, 2026 | WWE'}):x.show==='nxt'?html({...x,lines:x.lines.slice(0,2)}):html(x);
 return {ok:true,status:200,text:async()=>wrong};
 }});
 assert.deepEqual(bad.entries.map(e=>e.show),['smackdown','tna']);
 assert.equal(bad.warnings.length,2);
});
test('a result cannot be admitted until original board source is approved and published',async()=>{
 const notReady={records:lib.records.map(x=>({...x,source_available:false}))};
 const got=await collectOfficialWeeklyResults({library:notReady,routes,snapshot,now,requester});
 assert.deepEqual(got.entries,[]);
});
test('future episode date cannot be misreported as completed result',async()=>{
 const future={shows:snapshot.shows.map(s=>({...s,previous:{date:'2026-11-01'}}))};
 const got=await collectOfficialWeeklyResults({library:lib,routes,snapshot:future,now,requester});
 assert.deepEqual(got.entries,[]);
});
