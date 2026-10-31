const assert=require('node:assert/strict');
const {test}=require('node:test');
const engine=require('../web/staging/playlist-engine.js');
const now=new Date('2026-10-31T16:00:00Z'); // Saturday noon, Eastern.
const checked_at='2026-10-31T15:58:00Z';
function row(id,extra={}){
 return {id,show:'smackdown',kind:'results',source_available:true,design_approved:true,
  content_status:'current',source_url:'https://example.org/checked-fixture',source_name:'Approved QA fixture',
  checked_at,airdate:'2026-10-30',verification:'OFFICIAL_VERIFIED',completed:true,
  has_content:true,schedule_confirmed:true,date_confirmed:true,...extra};
}
function preview(id,show,airdate){return row(id,{show,kind:'upcoming',airdate,completed:false,verification:'SOURCE_REPORTED'});}
function special(id,kind,event_date,event_id){return row(id,{kind,event_date,event_id,completed:kind.endsWith('results'),verification:kind.endsWith('preview')?'SOURCE_REPORTED':'OFFICIAL_VERIFIED'});}
test('Eastern calendar is used across UTC midnight',()=>assert.equal(engine.etDay(new Date('2026-10-31T00:30:00Z')),'2026-10-30'));
test('Oct 31 example: 6 latest show results in date order, 1 next show, 2 upcoming events',()=>{
 const entries=[
 row('weekly-results-aaa',{show:'aaa',airdate:'2026-10-24'}),
 row('weekly-results-raw',{show:'raw',airdate:'2026-10-26'}),
 row('weekly-results-nxt',{show:'nxt',airdate:'2026-10-27'}),
 row('weekly-results-evolve',{show:'evolve',kind:'evolve',airdate:'2026-10-28'}),
 row('weekly-results-tna',{show:'tna',airdate:'2026-10-29'}),
 row('weekly-results-smackdown',{show:'smackdown',airdate:'2026-10-30'}),
 preview('weekly-upcoming-aaa','aaa','2026-10-31'),
 preview('weekly-upcoming-raw','raw','2026-11-02'),
 special('halloween','ple-preview','2026-10-31','nxt-halloween-havoc'),
 special('crown-jewel','ple-preview','2026-11-07','wwe-crown-jewel')
 ];
 assert.deepEqual(engine.select(entries,now).map(x=>x.id),[
  'weekly-results-aaa','weekly-results-raw','weekly-results-nxt',
  'weekly-results-evolve','weekly-results-tna','weekly-results-smackdown',
  'weekly-upcoming-aaa','halloween','crown-jewel'
 ]);
});
test('only the latest verified episode of each show plays, oldest to newest',()=>{
 const entries=[row('aaa-old',{show:'aaa',airdate:'2026-10-17'}),row('aaa-new',{show:'aaa',airdate:'2026-10-24'}),row('raw',{show:'raw',airdate:'2026-10-26'})];
 assert.deepEqual(engine.select(entries,now).map(x=>x.id),['aaa-new','raw']);
});
test('last episode stays until a new verified episode replaces it; no artificial 14-day cutoff',()=>{
 assert.deepEqual(engine.select([row('last-week-show',{airdate:'2026-10-01'})],now).map(x=>x.id),['last-week-show']);
});
test('the next weekly show is exactly one, even when several are advertised',()=>{
 assert.deepEqual(engine.select([preview('raw','raw','2026-11-02'),preview('aaa','aaa','2026-10-31'),preview('nxt','nxt','2026-11-03')],now).map(x=>x.id),['aaa']);
});
test('a scheduled show may have no matches, but needs schedule confirmation',()=>{
 const p=preview('schedule-only','aaa','2026-10-31');p.has_content=false;
 assert.deepEqual(engine.select([p],now).map(x=>x.id),['schedule-only']);
 p.schedule_confirmed=false;assert.deepEqual(engine.select([p],now),[]);
});
test('a verified result replaces a same-show same-day preview',()=>{
 assert.deepEqual(engine.select([preview('up','aaa','2026-10-31'),row('finished',{show:'aaa',airdate:'2026-10-31'})],now).map(x=>x.id),['finished']);
});
test('events are displayed when today or within 14 days, not 15 days',()=>{
 const entries=[special('today','ple-preview','2026-10-31','today'),special('14d','special-preview','2026-11-14','14d'),special('15d','special-preview','2026-11-15','15d')];
 assert.deepEqual(engine.select(entries,now).map(x=>x.id),['today','14d']);
});
test('only PLE/special results from today through seven days ago',()=>{
 const entries=[special('seven','ple-results','2026-10-24','a'),special('eight','special-results','2026-10-23','b'),special('today','special-results','2026-10-31','c')];
 assert.deepEqual(engine.select(entries,now).map(x=>x.id),['today','seven']);
});
test('verified event results retire the event preview',()=>{
 const entries=[special('preview','ple-preview','2026-10-31','x'),special('result','ple-results','2026-10-31','x')];
 assert.deepEqual(engine.select(entries,now).map(x=>x.id),['result']);
});
test('two-night events are independent slots',()=>{
 const entries=[special('one','ple-preview','2026-11-01','summer-night-1'),special('two','ple-preview','2026-11-02','summer-night-2')];
 assert.deepEqual(engine.select(entries,now).map(x=>x.id),['one','two']);
});
test('championship and unrelated archive designs never enter current TV rotation',()=>{
 const entries=[row('champ',{kind:'champions',data_verified:true,belts_verified:true}),
  row('archive',{content_status:'archive'}),row('other',{kind:'random'})];
 assert.deepEqual(engine.select(entries,now),[]);
});
test('source unavailable or unapproved Evolve cannot play',()=>{
 const entries=[row('missing',{show:'evolve',kind:'evolve',source_available:false}),
  row('unapproved',{show:'evolve',kind:'evolve',design_approved:false})];
 assert.deepEqual(engine.select(entries,now),[]);
});
test('unverified, incomplete, future, stale, unsourced and expired programming never plays',()=>{
 const entries=[row('bad-result',{verification:'SOURCE_REPORTED'}),
 row('incomplete',{completed:false}),row('future',{airdate:'2026-11-01'}),
 row('stale',{checked_at:'2026-10-28T00:00:00Z'}),
 row('unsourced',{source_url:''}),preview('yesterday','aaa','2026-10-30')];
 assert.deepEqual(engine.select(entries,now),[]);
});

test('segment-aware duration shows every verified result card once before switching boards',()=>{
 const entry=row('weekly-results-aaa',{show:'aaa',airdate:'2026-10-24'});
 const feeds={'aaa-verified-results.json':{programs:[{show_id:'aaa',airdate:'2026-10-24',segments:Array(7).fill({id:'result'})}]}};
 assert.equal(engine.dwellMs(entry,feeds,45000),104500);
 assert.equal(engine.dwellMs(entry,feeds,120000),120000);
});
test('shorter result boards do not get prematurely cut off at 45 seconds',()=>{
 const entry=row('weekly-results-smackdown',{show:'smackdown',airdate:'2026-10-30'});
 const feeds={'smackdown-verified-results.json':{programs:[{show_id:'smackdown',airdate:'2026-10-30',segments:Array(4).fill({id:'result'})}]}};
 assert.equal(engine.dwellMs(entry,feeds,45000),62500);
});
test('special-event preview and unverified feed do not invent additional dwell or segments',()=>{
 const preview=row('halloween',{show:'nxt',kind:'ple-preview',event_date:'2026-10-31'});
 assert.equal(engine.dwellMs(preview,{},45000),45000);
 const result=row('raw',{show:'raw',airdate:'2026-10-26'});
 assert.equal(engine.dwellMs(result,{},45000),45000);
});
