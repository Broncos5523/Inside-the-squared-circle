import assert from 'node:assert/strict';
import {test} from 'node:test';
import {mkdtemp,mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {tmpdir} from 'node:os';
import {join,dirname} from 'node:path';
import {pathToFileURL} from 'node:url';
import {collectReviewedArchiveFallback} from '../proof/staging/reviewed-archive-fallback.mjs';
const now=new Date('2026-10-31T16:00:00Z');
const show='aaa',id='weekly-results-aaa';
const program={show_id:show,airdate:'2026-10-24',source_url:'https://www.wwe.com/shows/aaa/aaa-h-roes-inmortales-week-1-results',
 verification:'OFFICIAL_RESULTS_REVIEWED',source_name:'WWE AAA Week 1 results, October 24, 2026',
 segments:[{id:'one',category:'MATCH RESULT',strap:'VERIFIED WINNER',headline:'WINNER',subhead:'def. LOSER',detail:'Source-reviewed result.',ticker:'WINNER PREVAILS',portraits:['winner']}]};
async function fixture(){
 const dir=await mkdtemp(join(tmpdir(),'isc-reviewed-test-'));
 const root=pathToFileURL(join(dir,'web/staging/')+'/');
 const delivery='delivery/boards/RESULTS/AAA/AAA_Results_Fallout_Review.html';
 const html='<html><head><title>approved original</title></head><body><script id="review-verified-results" type="application/json">'+JSON.stringify({mode:'EDITORIALLY_VERIFIED_OFFICIAL_RESULTS',programs:[program]})+'</script></body></html>';
 await mkdir(dirname(join(dir,'web/staging/',delivery)),{recursive:true});
 await writeFile(join(dir,'web/staging/',delivery),html);
 const hash=createHash('sha256').update(html).digest('hex');
 const library={records:[{id,label:'AAA — Results & Fallout',delivery,source_available:true,design_approved:true,delivery_sha256:hash}]};
 const snapshot={shows:[{id:'aaa',previous:{date:'2026-10-31'}}]};
 const requester=async()=>({ok:true,text:async()=>'<html><title>AAA Héroes Inmortales | Week 1 results: Oct. 24, 2026 | WWE</title>'+('z'.repeat(1100))+'</html>'});
 return {library,root,snapshot,requester};
}
test('hash-approved AAA week 1 remains the last verified result while Oct31 show has not yielded reviewed results',async()=>{
 const args=await fixture(),result=await collectReviewedArchiveFallback({...args,now});
 assert.deepEqual(result.entries.map(x=>x.id),[id]);
 assert.equal(result.feeds['aaa-verified-results.json'].programs[0].airdate,'2026-10-24');
 assert.deepEqual(result.warnings,[]);
});
test('tampered original source never becomes current programming',async()=>{
 const args=await fixture();args.library.records[0].delivery_sha256='0'.repeat(64);
 const result=await collectReviewedArchiveFallback({...args,now});
 assert.equal(result.entries.length,0);assert.ok(result.warnings[0].includes('hash mismatch'));
});
test('incorrect official headline date rejects otherwise approved results',async()=>{
 const args=await fixture();args.requester=async()=>({ok:true,text:async()=>'<html><title>Week 2 results: Oct. 31, 2026</title>'+('a'.repeat(1100))+'</html>'});
 const result=await collectReviewedArchiveFallback({...args,now});
 assert.equal(result.entries.length,0);assert.ok(result.warnings[0].includes('date/title'));
});
test('a later schedule date does not erase the last source-verified AAA episode',async()=>{
 const args=await fixture();args.snapshot.shows[0].previous.date='2026-10-31';
 const result=await collectReviewedArchiveFallback({...args,now:new Date('2026-11-01T18:00:00Z')});assert.deepEqual(result.entries.map(x=>x.airdate),['2026-10-24']);
});
test('a source schedule cannot move the verified AAA episode backwards',async()=>{
 const args=await fixture();args.snapshot.shows[0].previous.date='2026-10-17';
 const result=await collectReviewedArchiveFallback({...args,now});assert.deepEqual(result.entries,[]);
});
