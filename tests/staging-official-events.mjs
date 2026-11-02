import assert from 'node:assert/strict';
import {test} from 'node:test';
import {collectOfficialEvents} from '../proof/staging/official-events.mjs';
const now=new Date('2026-10-31T16:30:00Z');
const halloweenId='preview-nxt_halloween_havoc_preview_v4_approved_locked_20261027-night_one';
const jewelId='preview-crown_jewel_preview_v1_approved_locked_20261027-night_one';
const lib={records:[{id:halloweenId,label:'NXT Halloween Havoc — Preview',source_available:true,design_approved:true},
{id:jewelId,label:'Crown Jewel — Preview',source_available:true,design_approved:true}]};
const halloween='<html>2026 NXT Halloween Havoc Saturday, Oct. 31 <h3>Grayson Waller defends the NXT Championship against Tony D&#039;Angelo</h3><h3>Kelani Jordan defends the NXT Women’s Championship against Wren Sinclair</h3><h3>NXT Women’s North American Champion Zaria vs. Izzi Dame | Non-Title Match</h3>'+('a'.repeat(1100))+'</html>';
const jewel='<html>2026 WWE Crown Jewel Saturday, Nov. 7 <h3>World Heavyweight Champion Roman Reigns vs. Undisputed WWE Champion Sami Zayn</h3><h3>WWE Women&#039;s Champion Chelsea Green vs. Women&#039;s World Champion Liv Morgan</h3><h3>Cody Rhodes to battle Randy Orton in a Last Man Standing Match</h3>'+('a'.repeat(1100))+'</html>';
function requester(url){return Promise.resolve({ok:true,text:()=>Promise.resolve(url.includes('halloween')?halloween:jewel)});}
test('official date and all 3 source-confirmed match headings admit both event previews',async()=>{
 const got=await collectOfficialEvents({library:lib,now,requester});
 assert.deepEqual(got.entries.map(x=>x.event_id),['nxt-halloween-havoc-2026','wwe-crown-jewel-2026']);
 assert.equal(got.feed.programs[0].cards[0].left,'Tony D’Angelo');
 assert.ok(got.feed.programs.every(x=>x.render_ready));
 assert.deepEqual(got.errors,[]);
});
test('wrong date or unverified match card is never shown',async()=>{
 const got=await collectOfficialEvents({library:lib,now,requester:(url)=>Promise.resolve({ok:true,text:()=>Promise.resolve(url.includes('halloween')?halloween.replace('Oct. 31','Oct. 29'):jewel.replace('Sami Zayn','Somebody Else'))})});
 assert.equal(got.entries.length,0);assert.equal(got.errors.length,2);
});
test('source not visually locked cannot broadcast',async()=>{
 const got=await collectOfficialEvents({library:{records:lib.records.map(x=>({...x,design_approved:false}))},now,requester});
 assert.equal(got.entries.length,0);
});
test('special-event preview is removed the day after its event',async()=>{
 const got=await collectOfficialEvents({library:lib,now:new Date('2026-11-01T16:30:00Z'),requester});
 assert.deepEqual(got.entries.map(x=>x.event_id),['wwe-crown-jewel-2026']);
});
test('event more than 14 days ahead is not selected',async()=>{
 const got=await collectOfficialEvents({library:lib,now:new Date('2026-10-20T16:30:00Z'),requester});
 assert.deepEqual(got.entries.map(x=>x.event_id),['nxt-halloween-havoc-2026']);
});
