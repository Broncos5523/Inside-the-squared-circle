const assert=require('node:assert/strict');
const {test}=require('node:test');
const engine=require('../web/staging/playlist-engine.js');
const now=new Date('2026-10-31T00:30:00Z'); // Friday evening in Massachusetts.
function row(id,extra={}){return {id,show:'smackdown',kind:'results',source_available:true,design_approved:true,content_status:'current',source_url:'https://www.wwe.com/shows/smackdown/2026-10-23',source_name:'WWE',checked_at:'2026-10-30T23:30:00Z',airdate:'2026-10-23',verification:'OFFICIAL_VERIFIED',completed:true,...extra};}
test('uses Eastern date across the UTC midnight boundary',()=>assert.equal(engine.etDay(now),'2026-10-30'));
test('archive examples never enter active playback',()=>assert.deepEqual(engine.select([row('archive',{content_status:'archive'})],now),[]));
test('tonight preview precedes the five latest weekly results',()=>{const entries=['raw','smackdown','nxt','aaa','tna'].map(s=>row('result-'+s,{show:s}));entries.push(row('tonight',{kind:'upcoming',airdate:'2026-10-30',verification:'SOURCE_REPORTED',has_content:true,completed:false}));assert.deepEqual(engine.select(entries,now).map(x=>x.id),['tonight','result-raw','result-smackdown','result-nxt','result-aaa','result-tna']);});
test('verified results retire their matching preview',()=>{const entries=[row('preview',{kind:'upcoming',airdate:'2026-10-30',verification:'SOURCE_REPORTED',has_content:true}),row('results',{airdate:'2026-10-30'})];assert.deepEqual(engine.select(entries,now).map(x=>x.id),['results']);});
test('future or incomplete results cannot play',()=>assert.deepEqual(engine.select([row('future',{airdate:'2026-10-31'}),row('unfinished',{completed:false})],now),[]));
test('champions require both current facts and correct belts',()=>{const entries=[row('bad',{kind:'champions',data_verified:true,belts_verified:false}),row('good',{kind:'champions',data_verified:true,belts_verified:true})];assert.deepEqual(engine.select(entries,now).map(x=>x.id),['good']);});
test('stale checks and missing approval hold a board',()=>assert.deepEqual(engine.select([row('old',{checked_at:'2026-10-27T00:00:00Z'}),row('review',{design_approved:false})],now),[]));
test('Evolve cannot play without its exact recovered source',()=>assert.deepEqual(engine.select([row('evolve',{kind:'evolve',show:'evolve',source_available:false})],now),[]));
test('preview may bridge a results delay',()=>assert.deepEqual(engine.select([row('bridge',{kind:'upcoming',verification:'SOURCE_REPORTED',has_content:true,airdate:'2026-10-29'})],now).map(x=>x.id),['bridge']));
test('event previews require sourced dates and content',()=>assert.deepEqual(engine.select([row('event',{kind:'ple-preview',event_date:'2026-11-01',date_confirmed:false,has_content:true})],now),[]));
test('night one and night two remain separate slots',()=>{const entries=[row('night1',{kind:'ple-preview',event_id:'summer-1',event_date:'2026-11-01',date_confirmed:true,has_content:true}),row('night2',{kind:'ple-preview',event_id:'summer-2',event_date:'2026-11-02',date_confirmed:true,has_content:true})];assert.equal(engine.select(entries,now).length,2);});
test('latest episode per show is chosen without favorites',()=>assert.deepEqual(engine.select([row('old'),row('latest',{airdate:'2026-10-30'}),row('raw',{show:'raw'})],now).map(x=>x.id),['raw','latest']));
