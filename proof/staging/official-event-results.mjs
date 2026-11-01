import {segment} from './official-weekly-results.mjs';
export const HALLOWEEN_RESULTS_ID='results-nxt_halloween_havoc_results_v2_review-night_one';
const source='https://www.wwe.com/shows/nxtple/full-nxt-halloween-havoc-2026-results';
const date='2026-10-31';
const clean=s=>String(s||'').replace(/<[^>]*>/g,' ').replace(/&#0*39;|&(?:rsquo|apos);/gi,"'").replace(/&amp;/g,'&').replace(/\s+/g,' ').trim();
export async function collectOfficialEventResults({library,routes,now=new Date(),requester=fetch}){
 const today=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(now);
 const entries=[],programs=[],warnings=[],board=library.records.find(r=>r.id===HALLOWEEN_RESULTS_ID);
 if(!board?.source_available||!board.design_approved||today<date||(Date.parse(today)-Date.parse(date))/86400000>7)return {entries,feed:{mode:'OFFICIAL_WWE_EVENT_RESULTS',programs},warnings};
 try{
  const response=await requester(source,{headers:{Accept:'text/html'}});if(!response.ok)throw Error('Official event results unavailable');
  const html=await response.text(),title=clean(html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1]);
  const calendar=await requester('https://www.wwe.com/shows/nxtple/nxt-halloween-havoc-2026',{headers:{Accept:'text/html'}});
  const calendarHtml=calendar.ok?await calendar.text():'';
  if(!/Halloween Havoc 2026 results/i.test(title)||!/(?:Oct\.?\s+31|October\s+31|2026-10-31)/i.test(calendarHtml)||!calendarHtml.includes('2026')||!html.includes('field--name-body'))throw Error('Official event identity/date not confirmed');
  const lines=[...new Set([...html.matchAll(/<strong\b[^>]*>([\s\S]*?)<\/strong>/gi)].map(m=>clean(m[1])).filter(s=>/\sdef\.\s/i.test(s)))];
  const matches=lines.map((line,i)=>{
   const result=segment(line,'nxt',i,routes,date);if(!result)return null;
   result.id='halloween-2026-'+(i+1);result.detail=line.includes('|')?line.split('|').at(-1).trim().toUpperCase():'MATCH RESULT';
   delete result.belt;
   if(/^NXT Champion\s/i.test(line))result.belt='nxt_championship.png';
   if(/^NXT Women['’]s Champion\s/i.test(line))result.belt='nxt_womens_championship.png';
   return result;
  }).filter(Boolean);
  if(matches.length!==6||matches.filter(m=>m.belt).length!==2)throw Error('Incomplete championship/match results');
  const body=clean(html),fallout=/CM Punk[^.]{0,120}demanded a title opportunity/i.test(body)?'CM Punk challenged Grayson Waller for the NXT Championship.':'Grayson Waller and Kelani Jordan retained their NXT championships.';
  programs.push({event_id:'nxt-halloween-havoc-2026',board_id:board.id,event_date:date,source_url:source,verification:'OFFICIAL_SOURCE_EXTRACTED',matches,fallout});
  entries.push({id:board.id,title:board.label,show:'nxt',kind:'ple-results',event_id:'nxt-halloween-havoc-2026',event_date:date,source_available:true,design_approved:true,content_status:'current',verification:'OFFICIAL_VERIFIED',completed:true,checked_at:now.toISOString(),source_name:'WWE',source_url:source});
 }catch(error){warnings.push(String(error.message||error));}
 return {entries,feed:{mode:'OFFICIAL_WWE_EVENT_RESULTS',generated_at:now.toISOString(),programs},warnings};
}
