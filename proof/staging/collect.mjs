import {writeFile,readFile} from 'node:fs/promises';
import {collectWcn} from './wcn-collector.mjs';
import {collectOfficialEvents} from './official-events.mjs';
import {collectReviewedArchiveFallback} from './reviewed-archive-fallback.mjs';
import {collectOfficialWeeklyResults} from './official-weekly-results.mjs';
const now=new Date();
const root=new URL('../../web/staging/',import.meta.url);
try{
 const prior=JSON.parse(await readFile(new URL('data/programming.json',root),'utf8'));
 const age=now.getTime()-Date.parse(prior.generated_at);
 if(prior.mode==='SOURCE_GATED_STAGING'&&Number.isFinite(age)&&age>=0&&age<15*60000&&prior.collection?.snapshot_fresh){
  console.log('Reusing current checked staging facts within the 15-minute collection window.');
  process.exit(0);
 }
}catch{}
const library=JSON.parse(await readFile(new URL('library.json',root),'utf8'));
const assetRoutes=JSON.parse(await readFile(new URL('asset-routes.json',root),'utf8'));
const sourceRoot='https://broncos5523.github.io/Inside-the-squared-circle/data/';
const responses=new Map();
async function requester(url,options={}){
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),18000);
 try{
  const response=await fetch(url,{...options,signal:controller.signal});
  if(response.ok&&url===sourceRoot+'snapshot.json')responses.set('snapshot.json',await response.clone().json());
  return response;
 }finally{clearTimeout(timer);}
}
let collected=null;
const cache={async get(){return null;},async put(key,value){collected=JSON.parse(value);}};
const stats=await collectWcn({WCN_CACHE:cache},now,requester);
const snapshot=responses.get('snapshot.json');
const snapshotAge=now.getTime()-Date.parse(snapshot?.generated_at||'');
const snapshotFresh=!!snapshot&&Number.isFinite(snapshotAge)&&snapshotAge>=-300000&&snapshotAge<=48*3600000&&Array.isArray(snapshot.shows);
const programs=(collected?.programs||[]).filter(p=>p.matches?.length||p.appearances?.length);
// Never promote an event whose advertised airdate is already in the past.
// Use New York local calendar dates for the US-based weekly broadcast schedule.
const easternParts=Object.fromEntries(new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now).filter(p=>p.type!=='literal').map(p=>[p.type,p.value]));
const easternDate=`${easternParts.year}-${easternParts.month}-${easternParts.day}`;
const isCurrentOrFuture=(date)=>/^\d{4}-\d{2}-\d{2}$/.test(date)&&date>=easternDate;
const entries=[];
const feeds={};
if(snapshotFresh){
 const scoped=structuredClone(snapshot);
 for(const p of programs){const s=scoped.shows.find(s=>s.id===p.show_id);if(s)s.next={...s.next,date:p.airdate};}
 feeds['snapshot.json']=scoped;
 feeds['reported.json']={schema_version:1,mode:'REPORTED_MATCHES_UNVERIFIED',generated_at:now.toISOString(),display_attribution:'Wrestling Central News (wrestlingcentralnews.com)',programs,total_reported_matches:programs.reduce((n,p)=>n+p.matches.length,0),total_reported_appearances:programs.reduce((n,p)=>n+p.appearances.length,0)};
 // Supply ONE source-confirmed next-broadcast candidate for each weekly show.
 // A schedule-only preview is valid even if no matches/appearances have been
 // announced; do not invent any. The live playlist selects only the nearest
 // show from these choices. Evolve remains a recap, never an upcoming card.
 for(const show of scoped.shows){
  if(!['raw','smackdown','nxt','aaa','tna'].includes(show.id))continue;
  const board=library.records.find(r=>r.id==='weekly-upcoming-'+show.id);
  // Some schedule spines roll a same-day broadcast into "previous" before
  // it has aired. Keep today's announced show eligible until a verified
  // finished-episode record supersedes it, instead of skipping to next week.
  const previousIsToday=show.previous?.date===easternDate&&show.next?.date>easternDate;
  const date=previousIsToday?show.previous.date:show.next?.date;
  if(show.schedule_status!=='fresh'||!board?.source_available||!board.design_approved||!isCurrentOrFuture(date))continue;
  if(previousIsToday)show.next={...show.previous};
  const reported=programs.find(p=>p.show_id===show.id&&p.airdate===date);
  entries.push({
   id:board.id,title:board.label,show:show.id,kind:'upcoming',airdate:date,
   source_available:true,design_approved:true,content_status:'current',
   verification:'SOURCE_REPORTED',has_content:!!reported,schedule_confirmed:true,
   checked_at:now.toISOString(),source_name:reported?'Wrestling Central News':'Published episode schedule',
   source_url:reported?.source_url||sourceRoot+'snapshot.json',venue:null
  });
 }
}
// Existing reviewed results can be reused only when their exact current episode
// and original board contract are already independently verified. A draft from
// the recovered Floot parser is never automatically promoted to reviewed fallout.
const officialHosts={raw:['www.wwe.com','wwe.com'],smackdown:['www.wwe.com','wwe.com'],nxt:['www.wwe.com','wwe.com'],aaa:['www.wwe.com','wwe.com','luchalibreaaa.com'],tna:['tnawrestling.com','www.tnawrestling.com']};
function isOfficialResultsSource(show,value){try{const url=new URL(value);return url.protocol==='https:'&&(officialHosts[show]||[]).includes(url.hostname);}catch{return false;}}
const resultFeeds=['raw','smackdown','nxt','aaa','tna'];
for(const show of resultFeeds){
 try{
  const r=await requester(sourceRoot+show+'-verified-results.json',{headers:{Accept:'application/json'}});
  if(!r.ok)continue;const data=await r.json();
  if(data.mode!=='EDITORIALLY_VERIFIED_OFFICIAL_RESULTS'||!Array.isArray(data.programs))continue;
  const expected=snapshot?.shows?.find(s=>s.id===show)?.previous?.date;
  const program=data.programs.find(p=>p.show_id===show&&p.airdate===expected&&p.verification==='OFFICIAL_RESULTS_REVIEWED'&&Array.isArray(p.segments)&&p.segments.length);
  const board=library.records.find(b=>b.id==='weekly-results-'+show);
  if(!snapshotFresh||!program||!board?.source_available||!board.design_approved||!isOfficialResultsSource(show,program.source_url))continue;
  feeds[show+'-verified-results.json']=data;
  entries.push({id:board.id,title:board.label,show,kind:'results',airdate:program.airdate,source_available:true,design_approved:true,content_status:'current',verification:'EDITORIALLY_VERIFIED',completed:true,checked_at:now.toISOString(),source_name:program.source_name||'Official results',source_url:program.source_url});
 }catch(error){console.log(show+' reviewed result feed unavailable: '+error.name);}
}
const reviewed=await collectReviewedArchiveFallback({library,now,root,snapshot,requester});
for(const candidate of reviewed.entries){
 if(entries.some(e=>e.show===candidate.show&&(e.kind==='results'||e.kind==='evolve')))continue;
 entries.push(candidate);
 const key=candidate.show+'-verified-results.json';
 feeds[key]=reviewed.feeds[key];
 // A schedule may label the unaired current show as the most recent episode.
 // Board runtime must see the latest *verified* episode's identity, not the
 // premature source-spine rollover date.
 const showing=feeds['snapshot.json']?.shows?.find(s=>s.id===candidate.show);
 if(showing)showing.previous={date:candidate.airdate,time:null,title:reviewed.feeds[key]?.programs?.[0]?.source_name||'Latest officially reviewed episode'};
}
// Deterministically extract explicit winners from the matching dated official
// result article. These facts are source-verified, NOT claimed to be editorially
// reviewed. Keep any independently reviewed feed at the same episode date.
const officialWeekly=snapshotFresh?await collectOfficialWeeklyResults({library,routes:assetRoutes,snapshot,now,requester}):{entries:[],feeds:{},warnings:[]};
for(const candidate of officialWeekly.entries){
 if(entries.some(e=>e.show===candidate.show&&(e.kind==='results'||e.kind==='evolve')&&e.airdate===candidate.airdate))continue;
 entries.push(candidate);
 feeds[candidate.show+'-verified-results.json']=officialWeekly.feeds[candidate.show+'-verified-results.json'];
}
const events=await collectOfficialEvents({library,now,requester});
entries.push(...events.entries);
feeds['official-events.json']=events.feed;
const result={schema_version:1,mode:'SOURCE_GATED_STAGING',generated_at:now.toISOString(),entries,feeds,collection:{...stats,snapshot_fresh:!!snapshotFresh,official_event_count:events.entries.length,official_event_warnings:events.errors,approved_result_count:reviewed.entries.length,approved_result_warnings:reviewed.warnings,official_weekly_result_count:officialWeekly.entries.length,official_weekly_warnings:officialWeekly.warnings},notes:['Archived examples remain excluded from current programming. Event matches must clear official-source and approved-portrait checks. Only explicit winners from dated official sources are promoted. Evolve remains held until the exact approved source and episode facts are integrated.','Source credits retained privately; public hosting clearance confirmed by owner 2026-10-30.']};
await writeFile(new URL('data/programming.json',root),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({generated_at:result.generated_at,source_programs:programs.length,active_candidates:entries.length,collection:result.collection}));
