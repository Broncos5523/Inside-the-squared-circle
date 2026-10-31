const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const vm=require('node:vm');
const root=path.join(__dirname,'../web/staging');
const proof=path.join(__dirname,'../proof/staging');
const library=JSON.parse(fs.readFileSync(path.join(root,'library.json'),'utf8'));
const routes=JSON.parse(fs.readFileSync(path.join(root,'asset-routes.json'),'utf8'));
const payload=JSON.parse(fs.readFileSync(path.join(proof,'evolve-oct28-source-payload.json'),'utf8'));
const row=library.records.find(x=>x.id==='weekly-results-evolve');
const original=fs.readFileSync(path.join(root,row.delivery),'utf8');
const base='https://raw.githubusercontent.com/Broncos5523/Inside-the-squared-circle/work/all-boards-github-pages/web/staging/';
const adapterWindow={};
vm.runInNewContext(fs.readFileSync(path.join(root,'board-adapter.js'),'utf8'),{window:adapterWindow,URL});
const required=['Harley Riggins','Milosh Jovic','Jax Presley','Jasper Troy',
 'Elijah Holyfield','Braxton Cole','Marcus Mathers','Nikkita Lyons',
 'Anya Rune','Skylar Raye','Wendy Choo','Thea Hail','Kale Dixon',
 'Alix Brooks','Aaron Rourke','Laynie Luck'];
function sourceResponse(){return {ok:true,text:async()=>'<html><title>WWE EVOLVE Results (10/28)</title><p>October 28, 2026</p>'+required.join(' • ')+' '+('e'.repeat(1500))+'</html>'};}
async function collect(args={}){const m=await import('../proof/staging/collect-evolve.mjs');return m.collectEvolve({library,routes,payload,now:new Date('2026-10-31T19:00:00Z'),requester:async()=>sourceResponse(),...args});}
test('68 original approved sources and all fourteen exact Evolve asset routes are accounted for',()=>{
 assert.equal(library.slots,68);
 assert.equal(library.source_slots,68);
 assert.equal(library.records.filter(x=>x.source_available).length,68);
 assert.equal(row.design_approved,true);
 assert.equal(row.source_available,true);
 assert.equal(row.delivery_sha256,'8ae868647a715faf96ad91dda6d5771e0246ae3a587f345252aafe3957a02089');
 assert.equal(crypto.createHash('sha256').update(original).digest('hex'),row.delivery_sha256);
 assert.ok(original.includes('Cappuccino'));
 assert.ok(original.includes('user-evolve-three-wrestler-transparent-display.png'));
 const assets=Object.keys(routes).filter(k=>k.startsWith('/boards/RESULTS/Evolve/assets/'));
 assert.equal(assets.length,14);
 for(const asset of assets)assert.match(routes[asset],/^\/shared\/[a-f0-9]{64}\.(?:png|jpeg)$/);
});
test('source-verified six-segment Oct28 Evolve recap enters current programming',async()=>{
 const r=await collect();
 assert.equal(r.warnings.length,0);
 assert.equal(r.entries.length,1);
 assert.deepEqual(r.entries.map(x=>[x.id,x.airdate]),[['weekly-results-evolve','2026-10-28']]);
 assert.equal(r.feeds['evolve-verified-results.json'].episode.episode_date,'2026-10-28');
 assert.equal(r.feeds['evolve-verified-results.json'].episode.segments.length,6);
 assert.equal(r.feeds['evolve-verified-results.json'].episode.segments.filter(s=>s.kind==='result').length,3);
 assert.equal(r.feeds['evolve-verified-results.json'].episode.segments.filter(s=>s.kind==='fallout').length,3);
});
test('official Evolve source/date/participants are mandatory; unavailable source is rejected',async()=>{
 const r=await collect({requester:async()=>({ok:true,text:async()=>'<html><title>WWE EVOLVE Results (10/21)</title>'+('a'.repeat(1500))+'</html>'})});
 assert.equal(r.entries.length,0);assert.ok(r.warnings.length);
});
test('previous episode is withheld after the next Wednesday 10 PM Eastern boundary',async()=>{
 const m=await import('../proof/staging/collect-evolve.mjs');
 assert.equal(m.latestCompletedWednesday(new Date('2026-10-31T19:00:00Z')),'2026-10-28');
 assert.equal(m.latestCompletedWednesday(new Date('2026-11-05T03:30:00Z')),'2026-11-04');
 const r=await collect({now:new Date('2026-11-05T03:30:00Z')});
 assert.equal(r.entries.length,0);
});
test('current Evolve preview injects only Oct28 data and ticker; archive retains original Oct21 source',async()=>{
 const feed=await collect();
 const html=adapterWindow.ISCBoardAdapter.build(original,row,routes,base,'active',feed.feeds);
 assert.match(html,/"episode_date":"2026-10-28"/);
 assert.match(html,/evolveTicker.*OCT 28, 2026/);
 assert.match(html,/assets\/user-evolve-three-wrestler-transparent-display\.png/);
 assert.match(html,/EvolveReview=/);
 const archive=adapterWindow.ISCBoardAdapter.build(original,row,routes,base,'archive',feed.feeds);
 assert.match(archive,/"episode_date":"2026-10-21"/);
 assert.equal(archive.includes('"episode_date":"2026-10-28"'),false);
});
test('current Evolve data never uses opponent photos for winner-only result cards',()=>{
 for(const s of payload.segments.filter(s=>s.kind==='result')){
  assert.ok(!s.portraits.includes('milosh-jovic'));
  assert.ok(!s.portraits.includes('jasper-troy'));
  assert.ok(!s.portraits.includes('braxton-cole'));
  assert.ok(!s.portraits.includes('marcus-mathers'));
  for(const slug of s.portraits)assert.ok(routes['/boards/RESULTS/Evolve/assets/portraits/'+slug+'.png']);
 }
});
