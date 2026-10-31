// Ingest *already editorially reviewed* source originals, never scrape
// arbitrary new results into a winner/portrait claim. Byte hashes must match
// the preserved source registry, and the primary results article must remain
// available and date-identifiable at the claimed official URL.
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
function easternDay(now){const p=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now);
 const x=Object.fromEntries(p.map(e=>[e.type,e.value]));return x.year+'-'+x.month+'-'+x.day;}
function days(a,b){return (Date.parse(a+'T12:00:00Z')-Date.parse(b+'T12:00:00Z'))/86400000;}
function dateTitleMatches(html,date){const [year,m,d]=date.split('-').map(Number);
 const short=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m-1];
 if(!short)return false;
 const titles=[...html.matchAll(/<title\b[^>]*>([\s\S]*?)<\/title>/gi)].map(x=>x[1].replace(/<[^>]*>/g,' '));
 return titles.some(t=>new RegExp(short+'(?:ober|uary|ruary|ch|il|e|y|ust|tember|tober|ember|cember)?\\.?\\s+'+d+',?\\s*'+year,'i').test(t));
}
export async function collectReviewedArchiveFallback({library,now,root,snapshot,requester}){
 const today=easternDay(now),entries=[],feeds={},warnings=[];
 if(!snapshot||!Array.isArray(snapshot.shows))return {entries,feeds,warnings};
 // Narrowly limit current fallback to already-approved results boards; this
 // collector cannot create new editorial results on its own.
 for(const show of ['aaa','raw','nxt','smackdown','tna']){
  const record=library.records.find(x=>x.id==='weekly-results-'+show);
  if(!record?.source_available||!record.design_approved||!record.delivery||!record.delivery_sha256)continue;
  try{
   const bytes=await readFile(new URL(record.delivery,root));
   if(createHash('sha256').update(bytes).digest('hex')!==record.delivery_sha256)throw Error('original source hash mismatch');
   const markup=bytes.toString('utf8'),match=markup.match(/<script\s+id="review-verified-results"\s+type="application\/json"\s*>([\s\S]*?)<\/script>/i);
   if(!match)throw Error('approved review data absent');
   const archive=JSON.parse(match[1]);
   const program=archive.programs?.find(p=>p.show_id===show&&p.verification==='OFFICIAL_RESULTS_REVIEWED');
   if(archive.mode!=='EDITORIALLY_VERIFIED_OFFICIAL_RESULTS'||!program||!Array.isArray(program.segments)||!program.segments.length)continue;
   const expected=snapshot.shows.find(s=>s.id===show)?.previous?.date;
   const age=days(today,program.airdate);
   // Source spines sometimes label an unaired show as previous earlier in the
   // same day. Accept the verified prior broadcast in that narrow case only.
   const sameDayRollover=expected===today&&age>=0&&age<=8;
   if(program.airdate!==expected&&!sameDayRollover)continue;
   if(program.airdate>today||!Number.isFinite(age))continue;
   const url=new URL(program.source_url);
   const hosts={aaa:['wwe.com','www.wwe.com'],raw:['wwe.com','www.wwe.com'],nxt:['wwe.com','www.wwe.com'],smackdown:['wwe.com','www.wwe.com'],tna:['tnawrestling.com','www.tnawrestling.com']};
   if(url.protocol!=='https:'||!hosts[show].includes(url.hostname))continue;
   if(!program.segments.every(seg=>seg&&seg.id&&seg.category&&seg.strap&&seg.headline&&seg.subhead&&seg.detail&&seg.ticker&&Array.isArray(seg.portraits)))continue;
   const response=await requester(program.source_url,{headers:{Accept:'text/html'}});
   if(!response.ok)throw Error('official result link not available');
   const article=await response.text();
   if(article.length<1000||!dateTitleMatches(article,program.airdate))throw Error('official date/title does not match reviewed episode');
   const full={...archive,programs:[program]};
   feeds[show+'-verified-results.json']=full;
   entries.push({
    id:record.id,title:record.label,show,kind:'results',airdate:program.airdate,
    source_available:true,design_approved:true,content_status:'current',
    verification:'EDITORIALLY_VERIFIED',completed:true,checked_at:now.toISOString(),
    source_name:program.source_name||'Official results',source_url:program.source_url
   });
  }catch(e){warnings.push(show+':'+String(e?.message||e));}
 }
 return {entries,feeds,warnings};
}
