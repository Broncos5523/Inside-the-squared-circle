// Permanent episode facts keep their original verification timestamp. A schedule
// rollover or a temporarily unavailable article cannot invent a newer result.
export function retainLastVerifiedResults({previous,entries,feeds,library,now=new Date()}){
 const kept=[];
 for(const old of previous?.entries||[]){
  const age=now.getTime()-Date.parse(old.checked_at||'');
  if(old.kind!=='results'||!['OFFICIAL_VERIFIED','EDITORIALLY_VERIFIED','SOURCE_CORROBORATED'].includes(old.verification)||!Number.isFinite(age)||age< -300000||age>48*3600000||!old.completed||old.content_status!=='current'||!/^\d{4}-\d{2}-\d{2}$/.test(old.airdate||'')||old.airdate>now.toISOString().slice(0,10))continue;
  if(entries.some(e=>e.show===old.show&&e.kind==='results'&&e.airdate>=old.airdate))continue;
  const board=library.records.find(r=>r.id===old.id);if(!board?.source_available||!board.design_approved)continue;
  const key=old.show+'-verified-results.json',feed=previous.feeds?.[key];
  if(!['OFFICIAL_EXTRACTED_RESULTS','EDITORIALLY_VERIFIED_OFFICIAL_RESULTS','SOURCE_CORROBORATED_RESULTS'].includes(feed?.mode))continue;
  const program=feed.programs?.find(p=>p.show_id===old.show&&p.airdate===old.airdate&&p.source_url===old.source_url&&Array.isArray(p.segments)&&p.segments.length);
  if(!program||!['OFFICIAL_SOURCE_EXTRACTED','OFFICIAL_RESULTS_REVIEWED','SOURCE_CORROBORATED'].includes(program.verification)||!/^https:\/\//.test(program.source_url||''))continue;
  if(old.verification==='SOURCE_CORROBORATED'&&new Set((old.source_urls||[]).map(u=>{try{return new URL(u).hostname;}catch{return '';}}).filter(Boolean)).size<2)continue;
  entries.push(structuredClone(old));feeds[key]={...structuredClone(feed),programs:[structuredClone(program)]};kept.push(old.id);
 }
 return kept;
}
