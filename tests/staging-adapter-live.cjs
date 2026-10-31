const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');
const vm=require('node:vm');
const crypto=require('node:crypto');
const path=require('node:path');
const root=path.resolve(__dirname,'../web/staging');
const library=JSON.parse(fs.readFileSync(path.join(root,'library.json'),'utf8'));
const routes=JSON.parse(fs.readFileSync(path.join(root,'asset-routes.json'),'utf8'));
const programming=JSON.parse(fs.readFileSync(path.join(root,'data/programming.json'),'utf8'));
const host={};
vm.runInNewContext(fs.readFileSync(path.join(root,'board-adapter.js'),'utf8'),{window:host,URL});
const base='https://raw.githubusercontent.com/Broncos5523/Inside-the-squared-circle/work/all-boards-github-pages/web/staging/';
function prepared(show){
 const row=library.records.find(x=>x.id==='weekly-results-'+show);
 const feed=programming.feeds[show+'-verified-results.json'];
 assert.ok(row?.source_available&&row?.design_approved,row?.id);
 assert.ok(feed?.programs?.length,show+' lacks a source program');
 const original=fs.readFileSync(path.join(root,row.delivery),'utf8');
 const hash=crypto.createHash('sha256').update(original).digest('hex');
 assert.equal(hash,row.delivery_sha256,'Approved source hash changed: '+show);
 const player=host.ISCBoardAdapter.build(original,row,routes,base,'active',programming.feeds);
 return {row,original,player,feed};
}
test('all four officially source-extracted weekly results compile against exact approved HTML',()=>{
 for(const show of ['raw','nxt','smackdown','tna']){
  const p=prepared(show);
  assert.ok(p.player.length>p.original.length,show);
  assert.match(p.player,/OFFICIAL_SOURCE_EXTRACTED/,show+' no source verification acceptance');
  assert.match(p.player,/OFFICIAL_EXTRACTED_RESULTS/,show+' no approved feed mode acceptance');
  assert.match(p.player,/resultPortraits/,show+' no winner headshot fallback');
  assert.match(p.player,/resultBelts/,show+' no title belt fallback');
  assert.match(p.player,/verified-results\.json/,show+' no local results feed proxy');
  assert.match(p.player,/"mode":"active"/,show+' incorrect playback mode');
 }
});
test('the active SmackDown board uses 2026-10-30 official results and never substitutes loser portraits',()=>{
 const {player,feed}=prepared('smackdown');
 const p=feed.programs[0];
 assert.equal(p.airdate,'2026-10-30');
 assert.deepEqual(p.segments.map(x=>x.headline),['CHELSEA GREEN','REY FENIX','JADE CARGILL','SAMI ZAYN']);
 assert.ok(p.segments.every(s=>s.portrait_rule==='winners_only'));
 assert.ok(p.segments.every(s=>!s.portraits.includes('nikki-bella')&&!s.portraits.includes('trick-williams')));
 assert.match(player,/wwe_wwe-womens-championship\.png/);
});
test('archive-mode source remains a standalone original design preview with no live result modification',()=>{
 const row=library.records.find(x=>x.id==='weekly-results-smackdown');
 const original=fs.readFileSync(path.join(root,row.delivery),'utf8');
 const preview=host.ISCBoardAdapter.build(original,row,routes,base,'archive',programming.feeds);
 assert.match(preview,/ARCHIVE|demo=1/i);
 assert.equal(preview.includes('OFFICIAL_EXTRACTED_RESULTS'),false);
 assert.match(preview,/OFFICIAL_RESULTS_REVIEWED/);
});
test('the five-result plus AAA next and two-event lineup is exactly ordered',()=>{
 const engine=require(path.join(root,'playlist-engine.js'));
 const selected=engine.select(programming.entries,new Date(programming.generated_at));
 assert.deepEqual(selected.map(x=>x.id),[
  'weekly-results-aaa','weekly-results-raw','weekly-results-nxt',
  'weekly-results-tna','weekly-results-smackdown',
  'weekly-upcoming-aaa',
  'preview-nxt_halloween_havoc_preview_v4_approved_locked_20261027-night_one',
  'preview-crown_jewel_preview_v1_approved_locked_20261027-night_one'
 ]);
});
test('Evolve active playback uses October 28 data while original source remains October 21',()=>{
 const rowE=library.records.find(x=>x.id==='weekly-results-evolve');
 const original=fs.readFileSync(path.join(root,rowE.delivery),'utf8');
 const episode=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../proof/staging/evolve-oct28-source-payload.json'),'utf8'));episode.verification='EDITORIALLY_VERIFIED';
 const player=host.ISCBoardAdapter.build(original,rowE,routes,base,'active',{'evolve-verified-results.json':{mode:'EDITORIALLY_VERIFIED_EVOLVE_EPISODE',episode}});
 const embedded=text=>JSON.parse(text.match(/<script id="verified-episode" type="application\/json">([\s\S]*?)<\/script>/)[1]);
 assert.equal(embedded(original).episode_date,'2026-10-21');
 assert.equal(embedded(player).episode_date,'2026-10-28');
 assert.equal(embedded(player).segments.length,6);
 assert.match(player,/OCT 28, 2026/);
 assert.doesNotMatch(player,/STARBOY & CAPPUCCINO WIN/);
 const row=library.records.find(x=>x.id==='weekly-results-evolve');
 assert.throws(()=>host.ISCBoardAdapter.build(original,row,routes,base,'active',{}),/Reviewed Evolve/);
 const archive=host.ISCBoardAdapter.build(original,row,routes,base,'archive',programming.feeds);
 assert.equal(embedded(archive).episode_date,'2026-10-21');
});
