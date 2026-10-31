// Automatic source-verified episode RESULTS from official WWE / TNA result pages.
// Does not assert editorial review. No inferred winners, substituted portraits,
// or title changes. Never republishes full articles: only factual match summaries.
const SOURCES={
 raw:{host:'www.wwe.com',path:d=>'/shows/raw/'+d+'/results',label:'Raw',source:'WWE'},
 nxt:{host:'www.wwe.com',path:d=>'/shows/wwenxt/'+d+'/results',label:'NXT',source:'WWE'},
 smackdown:{host:'www.wwe.com',path:d=>'/shows/smackdown/'+d+'/results',label:'SmackDown',source:'WWE'},
 tna:{host:'tnawrestling.com',path:d=>{const [year,month,day]=d.split('-');const name=['','january','february','march','april','may','june','july','august','september','october','november','december'][Number(month)];return '/news/tna-thursday-night-impact-on-amc-results-'+name+'-'+Number(day)+'-'+year;},label:'TNA',source:'TNA Wrestling'}
};
const SHORT=['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const LONG=['','January','February','March','April','May','June','July','August','September','October','November','December'];
function etDay(now){const p=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now);const x=Object.fromEntries(p.map(v=>[v.type,v.value]));return x.year+'-'+x.month+'-'+x.day;}
function decode(s){return String(s||'').replace(/<[^>]*>/g,' ').replace(/&(?:amp|#0*38);/gi,'&').replace(/&(?:nbsp|#0*160);/gi,' ').replace(/&(?:quot|#0*34);/gi,'"').replace(/&#(?:0*39|x0*27);|&(?:apos|rsquo|lsquo);/gi,"'").replace(/&(?:ndash|mdash);/gi,'–').replace(/\s+/g,' ').trim();}
function dateMatchesTitle(title,date){const [y,m,d]=date.split('-').map(Number);if(!m||m>12)return false;return new RegExp('(?:'+SHORT[m]+'\\.?|'+LONG[m]+')\\s+'+d+',?\\s*'+y,'i').test(title);}
function officialHeadings(html,show){
 // Only result bold headings, and only when the expected editorial body exists.
 if(!html.includes(show==='tna'?'article-body':'field--name-body'))return [];
 const strong=/<strong\b[^>]*>([\s\S]*?)<\/strong>/gi;
 const found=[],seen=new Set();
 for(const m of html.matchAll(strong)){
  const text=decode(m[1]);
  if(!/\s+def(?:\.|eated)\s+/i.test(text)||text.length>220||text.length<8)continue;
  if(seen.has(text.toLowerCase()))continue;
  seen.add(text.toLowerCase());found.push(text);
 }
 return found;
}
function splitOutcome(line){
 const bits=line.split(/\s+def(?:\.|eated)\s+/i);
 if(bits.length!==2)return null;
 let winner=bits[0].trim();
 winner=winner.replace(/^(?:(?:TNA )?(?:Knockouts TV|X-Division|North American|World Tag Team|NXT North American)\s+Champion\s+)/i,'')
  .replace(/\s+acc\.\s+by\s+.*$/i,'').trim();
 let loser=bits[1].split(/\s+(?:by\s+Disqualification|in\s+(?:(?:a|an|the)\s+)?(?:No\s+Disqualification|WWE\s+Women's?|AAA\s+World|Undisputed\s+WWE|Dusty\s+Rhodes))|\s*\|\s*|\s+-\s+(?:Singles Match|TNA|No Disqualification)|\s+–\s+/i)[0].trim();
 loser=loser.replace(/\s+acc\.\s+by\s+.*$/i,'').trim();
 if(!winner||!loser||winner.length>88||loser.length>95)return null;
 return {winner,loser};
}
const KNOWN_TEAMS={
 'ethan page & big cass':['ethan-page','big-cass'],
 'romeo moreno & noam dar':['romeo-moreno','noam-dar'],
 'hank & tank':['hank-walker','tank-ledger']
};
const NAMES={
 'iyo sky':'iyo-sky','rey fenix':'rey-fenix','m by elegance':'m-by-elegance',
 'aj francis':'aj-francis','big cass':'big-cass','noam dar':'noam-dar',
 'tony d’angelo':'tony-d-angelo','tna x-division champion amazing red':'amazing-red',
 'zer0':'agent-zero','zero':'agent-zero','agent zero':'agent-zero'
};
function slugsFor(winner){
 const simple=winner.toLowerCase().trim().replace(/[’‘]/g,"'");
 if(KNOWN_TEAMS[simple])return KNOWN_TEAMS[simple];
 if(simple.includes(' & ')||simple.includes(' and '))return [];
 if(NAMES[simple])return [NAMES[simple]];
 return [simple.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/['.]/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')];
}
function portraitExists(routes,slug){
 return ['RAW','NXT','SmackDown','AAA','TNA'].some(show=>
  ['/boards/RESULTS/','/boards/UPCOMING/'].some(prefix=>
   Boolean(routes[prefix+show+'/assets/portraits/'+slug+'.png']||
           routes[prefix+show+'/assets/portrait-display/'+slug+'.png'])));
}
function beltFor(show,line,routes){
 const l=line.toLowerCase(),choices=[];
 if(show==='smackdown'){
  if(l.includes('wwe women')&&l.includes('championship match'))choices.push('wwe_wwe-womens-championship.png');
  if(l.includes('undisputed wwe title match'))choices.push('wwe_undisputed-wwe-championship.png');
  if(l.includes('aaa world cruiserweight championship'))choices.push('cruiserweight.png');
 }
 if(show==='nxt'&&l.includes('nxt north american champion'))choices.push('nxt_north_american.png');
 if(show==='tna'&&l.includes('tna x-division champion'))choices.push('tna_x_division.png');
 // Never use a different title belt merely because an approved one exists.
 for(const belt of choices){
  if(Object.keys(routes).some(k=>k.includes('/assets/belts/')&&k.endsWith('/'+belt)))return belt;
 }
 return null;
}
function segment(line,show,index,routes,day){
 const outcome=splitOutcome(line);if(!outcome)return null;
 const photos=slugsFor(outcome.winner).filter(slug=>portraitExists(routes,slug));

 const stipulation=/(?:Disqualification|No Disqualification|Title Match|Championship Match|Dusty Rhodes Tag Team Classic|Singles Match)/i.exec(line);
 const date=day.split('-'),d=LONG[Number(date[1])]+' '+Number(date[2])+', '+date[0];
 const detail=stipulation?stipulation[0].toUpperCase()+' • '+d:'OFFICIAL RESULTS • '+d;
 const belt=beltFor(show,line,routes);
 return {id:'official-'+show+'-'+day+'-'+(index+1),
  kind:'result',category:stipulation?stipulation[0].toUpperCase():'MATCH RESULT',
  strap:belt?'CHAMPIONSHIP RESULT':'OFFICIAL MATCH RESULT',
  headline:outcome.winner.toUpperCase(),subhead:'def. '+outcome.loser,
  detail,portraits:photos,portrait_rule:'winners_only',
  ...(belt?{belt}:{}),
  ticker:outcome.winner.toUpperCase()+' DEFEATS '+outcome.loser.toUpperCase()};
}
export async function collectOfficialWeeklyResults({library,routes,snapshot,now=new Date(),requester=fetch}){
 const today=etDay(now),entries=[],feeds={},warnings=[];
 if(!snapshot?.shows||!routes||!library?.records)return {entries,feeds,warnings};
 for(const [show,spec] of Object.entries(SOURCES)){
  const last=snapshot.shows.find(x=>x.id===show)?.previous?.date;
  const board=library.records.find(x=>x.id==='weekly-results-'+show);
  if(!board?.source_available||!board.design_approved||!last||!/^\d{4}-\d{2}-\d{2}$/.test(last)||last>today)continue;
  const url='https://'+spec.host+spec.path(last);
  try{
   const response=await requester(url,{redirect:'error',headers:{Accept:'text/html'}});
   if(!response.ok)throw Error('Official results HTTP '+response.status);
   const html=await response.text();
   if(html.length<3000||html.length>2_000_000)throw Error('Official HTML absent or oversized');
   const title=decode(html.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i)?.[1]||'');
   if(!new RegExp(spec.label,'i').test(title)||!/\bresults?\b/i.test(title)||!dateMatchesTitle(title,last))
    throw Error('Episode date/title not confirmed by official result page');
   const lines=officialHeadings(html,show);
   const segments=lines.map((line,i)=>segment(line,show,i,routes,last)).filter(Boolean);
   if(segments.length<3||segments.length>15)throw Error('Too few or too many explicit match results in official article');
   if(segments.some(s=>!s.headline||!s.subhead||!s.portrait_rule))throw Error('Unsafe match result');
   const program={show_id:show,airdate:last,venue:null,location:null,
    source_name:spec.source+' official '+spec.label+' results, '+last,
    source_url:url,verification:'OFFICIAL_SOURCE_EXTRACTED',segments};
   feeds[show+'-verified-results.json']={
    schema_version:1,mode:'OFFICIAL_EXTRACTED_RESULTS',
    source_policy:'Only explicit match winners directly extracted from dated official source; not human editorial review. Winners-only original approved portraits; never invent matches or champions.',
    programs:[program]};
   entries.push({id:board.id,title:board.label,show,kind:'results',airdate:last,
    source_available:true,design_approved:true,content_status:'current',
    verification:'OFFICIAL_VERIFIED',completed:true,checked_at:now.toISOString(),
    source_name:spec.source,source_url:url});
  }catch(error){warnings.push(show+':'+String(error?.message||error));}
 }
 return {entries,feeds,warnings};
}
