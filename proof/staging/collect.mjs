import {writeFile,readFile} from 'node:fs/promises';
import {collectWcn} from './wcn-collector.mjs';
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
const snapshotFresh=snapshot&&Number.isFinite(Date.parse(snapshot.generated_at))&&now.getTime()-Date.parse(snapshot.generated_at)<=48*3600000;
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
 for(const p of programs){
  const board=library.records.find(r=>r.id==='weekly-upcoming-'+p.show_id);
  if(!board?.source_available||!board.design_approved||!isCurrentOrFuture(p.airdate))continue;
  entries.push({id:board.id,title:board.label,show:p.show_id,kind:'upcoming',airdate:p.airdate,source_available:true,design_approved:true,content_status:'current',verification:'SOURCE_REPORTED',has_content:true,checked_at:now.toISOString(),source_name:'Wrestling Central News',source_url:p.source_url,venue:null});
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
const result={schema_version:1,mode:'SOURCE_GATED_STAGING',generated_at:now.toISOString(),entries,feeds,collection:{...stats,snapshot_fresh:!!snapshotFresh},notes:['Examples remain excluded. Championships, PLEs and Evolve require complete verified data plus their exact approved source.','Source credits retained. Public hosting clearance confirmed by owner 2026-10-30.']};
await writeFile(new URL('data/programming.json',root),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({generated_at:result.generated_at,source_programs:programs.length,active_candidates:entries.length,collection:result.collection}));
