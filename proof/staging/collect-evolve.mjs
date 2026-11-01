// Source-check a single editorially verified Evolve episode against the
// authoritative recovered user-approved HTML and approved original portraits.
// Do NOT generate new layouts, invent future episode results, or continue to
// broadcast the previous Wednesday after a new episode is due.
const SOURCE='https://www.fightful.com/wrestling/wwe-evolve-results-10-28/';
const REQUIRED=[
 'Harley Riggins','Milosh Jovic','Jax Presley','Jasper Troy',
 'Elijah Holyfield','Braxton Cole','Marcus Mathers',
 'Nikkita Lyons','Anya Rune','Skylar Raye','Wendy Choo',
 'Thea Hail','Kale Dixon','Alix Brooks','Aaron Rourke','Laynie Luck'
];
export function latestCompletedWednesday(now){
 const entries=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',hourCycle:'h23',minute:'2-digit'}).formatToParts(now);
 const p=Object.fromEntries(entries.map(x=>[x.type,x.value]));
 const utc=new Date(Date.UTC(Number(p.year),Number(p.month)-1,Number(p.day)));
 let delta=(utc.getUTCDay()+7-3)%7;
 if(utc.getUTCDay()===3&&(Number(p.hour)*60+Number(p.minute)<22*60))delta=7;
 utc.setUTCDate(utc.getUTCDate()-delta);
 return utc.toISOString().slice(0,10);
}
export async function collectEvolve({library,routes,payload,now=new Date(),requester=fetch}){
 const entries=[],feeds={},warnings=[];
 const record=library?.records?.find(x=>x.id==='weekly-results-evolve');
 const expected=latestCompletedWednesday(now);
 if(!record?.source_available||!record.design_approved||record.delivery_sha256!=='8ae868647a715faf96ad91dda6d5771e0246ae3a587f345252aafe3957a02089')
  return {entries,feeds,warnings:['Evolve exact approved source is unavailable or hash differs']};
 if(!payload||payload.episode_date!==expected||payload.edition!==expected||
   payload.show_id!=='evolve'||!Array.isArray(payload.segments)||payload.segments.length!==6)
  return {entries,feeds,warnings:['Evolve episode does not match most recently completed Wednesday; previous episode held']};
 for(const s of payload.segments){
  if(!s||!s.id||!['result','fallout'].includes(s.kind)||!s.headline||!s.strap||
     !Array.isArray(s.portraits)||s.portraits.some(p=>!/^[a-z0-9-]+$/.test(p)||!routes['/boards/RESULTS/Evolve/assets/portraits/'+p+'.png'])){
   warnings.push('Evolve episode has unverified or missing approved portrait: '+String(s?.id));return {entries,feeds,warnings};
  }
 }
 if(!Array.isArray(payload.provenance)||!payload.provenance.some(x=>x.url===SOURCE&&x.verified_matches===true))
  return {entries,feeds,warnings:['Evolve primary dated verification is missing']};
 try{
  const response=await requester(SOURCE,{headers:{Accept:'text/html'},redirect:'error'});
  if(!response.ok)throw Error('Fightful source HTTP '+response.status);
  const html=await response.text(),normalized=html.toLowerCase().replace(/<[^>]*>/g,' ').replace(/&(?:amp|nbsp);/g,' ');
  if(html.length<1000||html.length>1_500_000||!normalized.includes('evolve results (10/28)')||
     !normalized.includes('october 28, 2026')||
     !REQUIRED.every(name=>normalized.includes(name.toLowerCase())))throw Error('October 28 article/date/participants could not be verified');
 }catch(e){warnings.push('Evolve official-date recap source unavailable: '+String(e?.message||e));return {entries,feeds,warnings};}
 const program={...payload,source_url:SOURCE,verification:'EDITORIALLY_VERIFIED',source_name:'Fightful (verified Oct 28 results)'};
 const feed={schema_version:2,mode:'EDITORIALLY_VERIFIED_EVOLVE_EPISODE',generated_at:now.toISOString(),
  episode_date:expected,programs:[{show_id:'evolve',airdate:expected,segments:program.segments}],
  episode:program};
 feeds['evolve-verified-results.json']=feed;
 entries.push({id:record.id,title:record.label,show:'evolve',kind:'evolve',airdate:expected,
  source_available:true,design_approved:true,content_status:'current',verification:'EDITORIALLY_VERIFIED',
  completed:true,checked_at:now.toISOString(),source_name:'Fightful',source_url:SOURCE});
 return {entries,feeds,warnings};
}
