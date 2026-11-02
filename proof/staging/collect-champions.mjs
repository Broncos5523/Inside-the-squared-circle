import {readFile} from 'node:fs/promises';
const AAA_SOURCES=['https://www.sacnilk.com/news/current_lucha_libre_aaa_worldwide_champions_full_list_of_title_holders','https://www.thesmackdownhotel.com/roster/current-champions/?promotion=aaa'];
const clean=s=>String(s||'').replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,' ').replace(/<[^>]+>/g,' ').replace(/&#(?:x([0-9a-f]+)|(\d+));/gi,(_,h,d)=>String.fromCodePoint(parseInt(h||d,h?16:10))).replace(/&amp;/g,'&').replace(/&nbsp;/g,' ').replace(/&rsquo;/g,"'").replace(/\s+/g,' ').trim();
const key=s=>clean(s).normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]/g,'');
export function currentWweHolder(html){const text=clean(html);return text.match(/Championship Holder\s+(.+?)\s+Time Held/i)?.[1]||null;}
export async function collectChampions({library,routes,now=new Date(),requester=fetch,root=new URL('../../web/staging/',import.meta.url)}){
 const catalog=JSON.parse(await readFile(new URL('championship-catalog.json',import.meta.url),'utf8'));
 const programs=[],entries=[],warnings=[],cache=new Map();
 async function page(url){if(!cache.has(url))cache.set(url,(async()=>{const r=await requester(url,{headers:{Accept:'text/html'}});if(!r.ok)throw Error('HTTP '+r.status);const h=await r.text();if(h.length<1000||h.length>2000000)throw Error('Invalid source size');return h;})());return cache.get(url);}
 const as_of=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(now);
 for(const [show,original] of Object.entries(catalog)){
  const board=library.records.find(r=>r.id==='championship-'+show);if(!board?.design_approved||!board.source_available)continue;
  try{
   let champions=[],sources=[],verification='OFFICIAL_VERIFIED';
   if(show==='aaa'){
    const [one,two]=await Promise.all(AAA_SOURCES.map(page));
    const table=[...one.matchAll(/<table\b[^>]*>([\s\S]*?)<\/table>/gi)].find(m=>/Current Champion/i.test(clean(m[1])))?.[1];
    if(!table)throw Error('AAA current champions table unavailable');
    const rows=[...table.matchAll(/<tr\b[^>]*>([\s\S]*?)<\/tr>/gi)].map(m=>[...m[1].matchAll(/<t[dh]\b[^>]*>([\s\S]*?)<\/t[dh]>/gi)].map(c=>clean(c[1])));
    // The second source is a current-only roster; do not accept names from title history.
    const current=two.match(/<h[12][^>]*>[^<]*Current AAA Champions[\s\S]*?(?=<h[12]|$)/i)?.[0]||two;
    for(const c of original){const row=rows.find(r=>key(r[0])===key(c.title.replace('WORLD MIXED TAG CHAMPIONSHIP','WORLD MIXED TAG TEAM CHAMPIONSHIP')));if(!row||!c.members.every(m=>key(row[1]).includes(key(m)))||!c.members.every(m=>key(current).includes(key(m))))throw Error('AAA current titleholder disagreement: '+c.id);champions.push({...c,source:AAA_SOURCES[0],source_urls:AAA_SOURCES});}
    sources=AAA_SOURCES;verification='SOURCE_CORROBORATED';
   }else if(show==='tna'){
    const html=await page('https://tnawrestling.com/roster'),text=clean(html),current=text.match(/Meet Our Champions\s+([\s\S]*?)\s+Roster\s+Referees/i)?.[1];
    if(!current)throw Error('TNA current champions section missing');
    for(const c of original){if(!key(current).includes(key(c.name)))throw Error('TNA changed holder needs new approved asset mapping: '+c.id);champions.push({...c});}
    sources=['https://tnawrestling.com/roster'];
   }else{
    for(const c of original){const html=await page(c.source),holder=currentWweHolder(html);if(!holder)throw Error('Current holder unavailable: '+c.id);
     if(key(holder)!==key(c.name))throw Error('Changed holder needs approved asset mapping: '+c.id);
     const epoch=html.match(/data-reign-start-date=["'](\d{10})["']/)?.[1],since=epoch?new Date(Number(epoch)*1000).toISOString().slice(0,10):c.since_date;
     champions.push({...c,since_date:since,since:new Intl.DateTimeFormat('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}).format(new Date(since+'T12:00:00Z')).toUpperCase()});sources.push(c.source);
    }
   }
   // Every declared original image/belt remains resolved from the approved route inventory.
   for(const c of champions)for(const name of [...c.portraits,...(c.belt?[c.belt]:[])])if(!routes[board.href.slice(0,board.href.lastIndexOf('/')+1)+'assets/'+name])throw Error('Approved championship asset unavailable: '+name);
   programs.push({show,board_id:board.id,as_of,verification,champions,source_urls:[...new Set(sources)]});
   entries.push({id:board.id,title:board.label,show,kind:'champions',as_of,airdate:as_of,source_available:true,design_approved:true,content_status:'current',verification,checked_at:now.toISOString(),source_name:show==='aaa'?'Sacnilk / The SmackDown Hotel':show==='tna'?'TNA Wrestling':'WWE',source_url:sources[0],source_urls:[...new Set(sources)]});
  }catch(error){warnings.push(show+': '+error.message);}
 }
 return {entries,feed:{schema_version:1,mode:'SOURCE_CHECKED_CHAMPIONS',generated_at:now.toISOString(),programs},warnings};
}
