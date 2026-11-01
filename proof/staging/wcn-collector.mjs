// Portable collector extracted from the recovered V5 source package. Public hosting clearance confirmed by the owner 2026-10-30.
import {CREDIT,FEED_URL,SNAPSHOT_URL,parseWcnPage,parseWcnPageForEpisode,parseWcnShowIndex,WCN_SHOW_INDEX,safeShows,sourceAlignedShows,WCN_UPCOMING_URL,sanitizedForDisplay,privateReportedFeed} from './parser.mjs';
import {parseDatedEventBrief} from './event-preview.mjs';
const KEY="wcn-staging-facts-v1";
const CHECK_INTERVAL_MS=15*60000;
const LIMIT_BYTES=1_000_000;
async function limitedFetch(url,accept,requester){const r=await requester(url,{redirect:'error',headers:{'User-Agent':'InsideSquaredCirclePersonalHomeDisplay/1.0 (30-minute polls)','Accept':accept}});if(!r.ok)throw Error('Remote source unavailable '+r.status);if(Number(r.headers.get('content-length')||0)>LIMIT_BYTES)throw Error('Remote response oversized');const value=await r.text();if(value.length>LIMIT_BYTES)throw Error('Remote response oversized');return value;}
export async function collectWcn(env,now=new Date(),requester=fetch,routes={}){
 if(!env.WCN_CACHE)throw Error('No private cache bound');
 const previous=await env.WCN_CACHE.get(KEY,'json');
 if(previous?.checked_at){const age=now.getTime()-new Date(previous.checked_at).getTime();if(age>=0&&age<CHECK_INTERVAL_MS)return {skipped:true,reason:'rate_guard',checked_at:previous.checked_at};}
 const audit={generated_at:now.toISOString(),checked_at:now.toISOString(),feed_status:'unavailable',snapshot_status:'unavailable',programs:[],error_count:0};
 let snap;
 try{snap=JSON.parse(await limitedFetch(SNAPSHOT_URL,'application/json',requester));}catch(e){audit.error_count++;}
 let upcomingHtml='';
 try{upcomingHtml=await limitedFetch(WCN_UPCOMING_URL,'text/html',requester);}catch(e){audit.error_count++;}
 const shows=sourceAlignedShows(snap,upcomingHtml,now);
 audit.snapshot_status=shows.length?'source_checked_exact_dates':'missing_stale_or_incomplete';
 audit.date_disagreements=shows.filter(x=>x.date_mismatch).map(x=>({show_id:x.show_id,snapshot_date:snap?.shows?.find(s=>s.id===x.show_id)?.next?.date||null,listing_date:x.airdate}));
 try{const rss=await limitedFetch(FEED_URL,'application/rss+xml,application/xml,text/xml',requester);audit.feed_status=/<rss\b/i.test(rss)?'responded':'invalid_feed';}catch(e){audit.error_count++;}
 for(const show of shows){
  let matches=[],appearances=[],start_time=null,entryStatus='no_supported_card_data';
  try{
   const html=await limitedFetch(show.url,'text/html',requester);
   const parsed=parseWcnPageForEpisode(html,show.show_id,show.airdate);
   matches=parsed.matches.map(text=>({text,source_name:CREDIT,status:'REPORTED_UNVERIFIED',evidence_url:show.url}));
   appearances=parsed.appearances.map(text=>({text,source_name:CREDIT,status:'REPORTED_UNVERIFIED',evidence_url:show.url}));
   const brief=parseDatedEventBrief(html,show.show_id,show.airdate,routes);
   for(const m of brief.matches)if(!matches.some(x=>x.text.toLowerCase()===m.text.toLowerCase()))matches.push({...m,source_name:CREDIT,status:'REPORTED_UNVERIFIED'});
   for(const a of brief.appearances)if(!appearances.some(x=>x.text.toLowerCase()===a.text.toLowerCase()))appearances.push({...a,source_name:CREDIT,status:'REPORTED_UNVERIFIED'});
   start_time=brief.start_time||null;
   if(matches.length||appearances.length)entryStatus='event_page_matches';
  }catch(e){audit.error_count++;}
  // Independent permitted WCN show-index fallback when event preview contains
  // no pairings, *including* when the one event URL is currently unavailable.
  if(matches.length===0 && Object.hasOwn(WCN_SHOW_INDEX,show.show_id)){
   try{
    const indexHtml=await limitedFetch(WCN_SHOW_INDEX[show.show_id],'text/html',requester);
    const hits=parseWcnShowIndex(indexHtml,show.show_id,show.airdate,now);
    matches=hits.map(hit=>({text:hit.text,source_name:CREDIT,status:'REPORTED_UNVERIFIED',evidence_url:hit.evidence_url}));
    if(matches.length)entryStatus='source_dated_show_article_headlines';
   }catch(e){audit.error_count++;}
  }
  audit.programs.push({show_id:show.show_id,airdate:show.airdate,matches,appearances,start_time,
    source_name:CREDIT,source_url:show.url,collection_status:entryStatus,schedule_source:show.schedule_source});
 }

 // Never preserve previous week's cards if upstream data disappears.
 // This key contains ONLY short, source-attributed match/appearance facts (not articles).
 await env.WCN_CACHE.put(KEY,JSON.stringify(audit),{expirationTtl:14*86400});
 return {skipped:false,show_count:shows.length,programs_with_data:audit.programs.filter(x=>x.matches.length||x.appearances.length).length,errors:audit.error_count};
}
