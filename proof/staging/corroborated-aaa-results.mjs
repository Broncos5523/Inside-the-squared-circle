const seeds={
 '2026-10-31':[
  'https://www.fightful.com/wrestling/aaa-heroes-inmortales-week-two-results-10-31/',
  'https://www.tpww.net/2026/10/aaa-heroes-inmortales-2026-week-2-results-oct-31-2026-aaa-world-cruiserweight-open-challenge-wagner-brothers-vs-los-vipers/'
 ]
};
const clean=s=>String(s||'').replace(/<[^>]*>/g,' ').replace(/&amp;/g,'&').replace(/&#(?:8211|8212);/g,'–').replace(/&#0*39;|&rsquo;/g,"'").replace(/\s+/g,' ').trim();
const winnerKey=s=>s.replace(/\([^)]*\)/g,'').replace(/^The /i,'').toLowerCase().split(/\s*&\s*/).map(s=>s.replace(/[^a-z0-9]/g,'')).sort().join('&');
function dateInTitle(title,date){const [y,m,d]=date.split('-').map(Number),month=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m-1];return new RegExp('(?:'+m+'\\/'+d+'|'+month+'(?:[a-z]+)?\\.?\\s+'+d+')','i').test(title);}
export function parseAaaCorroboration(fightful,tpww,date,routes){
 for(const html of [fightful,tpww]){
  const title=clean(html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1]);
  if(!/AAA.*results/i.test(title)||!dateInTitle(title,date)||!html.includes(date.slice(0,4)))return [];
 }
 const published=fightful.match(/article:published_time["']\s+content=["']([^"']+)/i)?.[1];
 const publicationAge=(Date.parse(published)-Date.parse(date+'T00:00:00Z'))/86400000;
 if(!Number.isFinite(publicationAge)||publicationAge<0||publicationAge>2)return [];
 const other=[...tpww.matchAll(/<p\b[^>]*>([\s\S]*?)<\/p>/gi)].map(m=>clean(m[1])).filter(x=>/^Winner:/i.test(x)).map(x=>winnerKey(x.replace(/^Winner:\s*/i,'').split(/\s+via\s+/i)[0]));
 const rows=[];
 const start=fightful.search(/<div\b[^>]*class=["'][^"']*entry-content/);let body='';
 if(start>=0){const tags=/<\/?div\b[^>]*>/gi;tags.lastIndex=start;let depth=0;for(let m;(m=tags.exec(fightful));){depth+=/^<\//.test(m[0])?-1:1;if(depth===0){body=fightful.slice(start,m.index);break;}}}
 for(const match of body.matchAll(/<li\b[^>]*>([\s\S]*?)<\/li>/gi)){
  const line=clean(match[1]);if(!/\sdef\.\s/i.test(line))continue;
  const [left,right]=line.split(/\sdef\.\s/i);if(!right)continue;
  const winner=left.split(':').at(-1).replace(/\([^)]*\)/g,'').trim(),key=winnerKey(winner);
  if(!other.includes(key))return [];
  const names=/wagner brothers/i.test(winner)?['galeno']:winner.split(/\s*&\s*/).map(n=>n.toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,''));
  const belt=/World Tag Team Championship/i.test(left)?'world_tag.png':/World Cruiserweight Championship/i.test(left)?'cruiserweight.png':null;
  const portraits=names.filter(slug=>Object.keys(routes).some(k=>k.endsWith('/portraits/'+slug+'.png')));
  const loser=right.replace(/\([^)]*\)/g,'').replace(/\s+to retain.*$/i,'').trim().replace(/[.]$/,'');
  rows.push({id:'aaa-'+date+'-'+(rows.length+1),kind:'result',category:'MATCH RESULT',strap:belt?'CHAMPIONSHIP RESULT':'MATCH RESULT',headline:winner.toUpperCase(),subhead:'def. '+loser,detail:(belt?'AAA '+(belt==='world_tag.png'?'WORLD TAG TEAM CHAMPIONSHIP':'WORLD CRUISERWEIGHT CHAMPIONSHIP'):'TAG TEAM MATCH')+' • '+date,portraits,portrait_rule:'winners_only',...(belt?{belt}:{}),ticker:winner.toUpperCase()+' DEFEATS '+loser.toUpperCase()});
 }
 return rows.length>=3&&rows.length===other.length?rows:[];
}
export async function collectCorroboratedAaaResults({library,routes,snapshot,now=new Date(),requester=fetch}){
 const entries=[],feeds={},warnings=[],board=library.records.find(r=>r.id==='weekly-results-aaa'),date=snapshot?.shows?.find(s=>s.id==='aaa')?.previous?.date;
 if(!board?.source_available||!board.design_approved||!/^\d{4}-\d{2}-\d{2}$/.test(date||'')||date>now.toISOString().slice(0,10))return {entries,feeds,warnings};
 try{
  const pages=[];
  for(const [index,home] of ['https://www.fightful.com/','https://www.tpww.net/'].entries()){
   const candidates=[];if(seeds[date])candidates.push(seeds[date][index]);
   const listing=await requester(home,{headers:{Accept:'text/html'}});
   if(listing.ok){const html=await listing.text();for(const m of html.matchAll(/href=["']([^"']+)["']/gi)){try{const url=new URL(m[1],home);if(url.hostname===new URL(home).hostname&&/aaa/i.test(url.pathname)&&/results/i.test(url.pathname))candidates.push(url.href);}catch{}}}
   let found=null;
   for(const url of [...new Set(candidates)].slice(0,5)){
    const response=await requester(url,{headers:{Accept:'text/html'}});if(!response.ok)continue;
    const html=await response.text(),title=clean(html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1]);
    if(/AAA.*results/i.test(title)&&dateInTitle(title,date)&&html.includes(date.slice(0,4))){found={url,html};break;}
   }
   if(!found)throw Error('Dated AAA result source unavailable: '+home);pages.push(found);
  }
  const segments=parseAaaCorroboration(pages[0].html,pages[1].html,date,routes);if(!segments.length)throw Error('Independent AAA match winners do not fully agree');
  const source_urls=pages.map(x=>x.url),program={show_id:'aaa',airdate:date,source_url:source_urls[0],source_urls,source_name:'Fightful / TPWW • AAA results, '+date,verification:'SOURCE_CORROBORATED',segments};
  feeds['aaa-verified-results.json']={schema_version:1,mode:'SOURCE_CORROBORATED_RESULTS',source_policy:'Matching explicit winners from two independent dated result reports; not labeled as official WWE verification.',programs:[program]};
  entries.push({id:board.id,title:board.label,show:'aaa',kind:'results',airdate:date,source_available:true,design_approved:true,content_status:'current',verification:'SOURCE_CORROBORATED',completed:true,checked_at:now.toISOString(),source_name:'Fightful / TPWW',source_url:source_urls[0],source_urls});
 }catch(error){warnings.push(String(error.message||error));}
 return {entries,feeds,warnings};
}
