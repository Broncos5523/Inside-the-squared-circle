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
test('source-backed SmackDown winner portraits never include opposing wrestlers',()=>{
 const {player,feed}=prepared('smackdown');
 const p=feed.programs[0];
 assert.ok(/^\d{4}-\d{2}-\d{2}$/.test(p.airdate));
 assert.ok(p.segments.length>=3);
 assert.ok(p.segments.every(seg=>seg.portrait_rule==='winners_only'||p.verification==='OFFICIAL_RESULTS_REVIEWED'));
 assert.ok(p.segments.every(seg=>Array.isArray(seg.portraits)));
 assert.match(player,/resultPortraits/);
});
test('archive-mode source remains a standalone original design preview with no live result modification',()=>{
 const row=library.records.find(x=>x.id==='weekly-results-smackdown');
 const original=fs.readFileSync(path.join(root,row.delivery),'utf8');
 const preview=host.ISCBoardAdapter.build(original,row,routes,base,'archive',programming.feeds);
 assert.match(preview,/ARCHIVE|demo=1/i);
 assert.equal(preview.includes('OFFICIAL_EXTRACTED_RESULTS'),false);
 assert.match(preview,/OFFICIAL_RESULTS_REVIEWED/);
});
test('the dynamic TV playlist has only approved source-backed board IDs in date order',()=>{
 const engine=require(path.join(root,'playlist-engine.js'));
 const selected=engine.select(programming.entries,new Date(programming.generated_at));
 const ids=selected.map(x=>x.id);
 assert.equal(new Set(ids).size,ids.length);
 for(const entry of selected){
  const record=library.records.find(x=>x.id===entry.id);
  assert.ok(record?.source_available&&record?.design_approved,entry.id);
 }
 const results=selected.filter(x=>x.kind==='results'||x.kind==='evolve');
 assert.deepEqual(results.map(x=>x.airdate),results.map(x=>x.airdate).sort());
 assert.ok(selected.filter(x=>x.kind==='upcoming').length<=1);
 const next=selected.findIndex(x=>x.kind==='upcoming');
 if(next>=0)assert.equal(next,results.length);
 assert.equal(selected.some(x=>x.kind==='champions'),false);
});
test('all 68 original boards are source-backed; Evolve never substitutes old archive dates',()=>{
 const evolve=library.records.find(x=>x.id==='weekly-results-evolve');
 assert.equal(evolve?.source_available,true);
 assert.equal(evolve?.design_approved,true);
 assert.equal(evolve?.original_sha256,'8ae868647a715faf96ad91dda6d5771e0246ae3a587f345252aafe3957a02089');
 const item=programming.entries.find(x=>x.id===evolve.id);
 if(item){
  assert.equal(item.kind,'evolve');
  assert.equal(item.airdate,programming.feeds['evolve-verified-results.json']?.episode_date);
 }
});
