import {readFile} from 'node:fs/promises';
const AAA_SOURCES=['https://www.sacnilk.com/news/current_lucha_libre_aaa_worldwide_champions_full_list_of_title_holders','https://www.thesmackdownhotel.com/roster/current-champions/?promotion=aaa'];
const clean=s=>String(s||'').replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,' ').replace(/<[^>]+>/g,' ').replace(/&#(?:x([0-9a-f]+)|(\d+));/gi,(_,h,d)=>String.fromCodePoint(parseInt(h||d,h?16:10))).replace(/&amp;/g,'&').replace(/&nbsp;/g,' ').replace(/&rsquo;|’/g,"'").replace(/\s+/g,' ').trim();
const key=s=>clean(s).normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]/g,'');
const titleKey=s=>key(clean(s).replace(/^TNA\s+/i,'').replace(/Champions?$/i,'Championship').replace(/\bTeam\b/gi,''));
export const easternDate=date=>new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(date);
export function currentWweHolder(html){const text=clean(html);return text.match(/Championship Holder\s+(.+?)\s+Time Held/i)?.[1]||null;}
function dateOnly(value,asOf){
 if(!value)return null;
 const d=new Date(value);if(!Number.isFinite(d.getTime()))return null;
 const day=d.toISOString().slice(0,10);return day<=asOf?day:null;
}
function tableRows(html){return [...html.matchAll(/<tr\b[^>]*>([\s\S]*?)<\/tr>/gi)].map(m=>[...m[1].matchAll(/<t[dh]\b[^>]*>([\s\S]*?)<\/t[dh]>/gi)].map(c=>clean(c[1])));}
export function tnaTitleholders(html){
 const section=html.match(/Meet Our Champions[\s\S]*?<\/section>/i)?.[0];
 if(!section)return [];
 return [...section.matchAll(/<a\b[^>]*>([\s\S]*?)<\/a>/gi)].map(m=>({name:clean(m[1].match(/<h5\b[^>]*>([\s\S]*?)<\/h5>/i)?.[1]),title:clean(m[1].match(/<h6\b[^>]*>([\s\S]*?)<\/h6>/i)?.[1])})).filter(c=>c.name&&c.title);
}
// Resolve exact identities only against already approved artwork. No remote image intake.
export function resolveChampion(c,holder,{catalog,routes,board,show,since=null,asOf}){
 holder=clean(holder);if(!holder||holder.length>180||/^(?:vacant|tbd|unknown)$/i.test(holder))throw Error('Current holder unavailable: '+c.id);
 const same=key(holder)===key(c.name);
 const known=Object.values(catalog).flat().find(x=>key(x.name)===key(holder));
 const explicit=holder.match(/^(.+?)\s*\(([^()]+)\)$/);
 const memberText=explicit?explicit[2]:holder;
 const members=known?known.members:memberText.split(/\s+(?:&|and)\s+|,\s*/i).map(s=>s.trim()).filter(Boolean);
 if(members.length<1||members.length>3)throw Error('Unsupported holder count: '+c.id);
 const prefix=board.href.slice(0,board.href.lastIndexOf('/')+1)+'assets/';
 let portraits=[],portrait_routes={};
 if(same){portraits=c.portraits.slice();}
 else{
  for(const member of members){
   const candidates=Object.keys(routes).filter(p=>/\/assets\/(?:portraits\/|portrait-display\/)?[a-z0-9-]+\.(?:png|webp)$/i.test(p)&&key(p.split('/').at(-1).replace(/\.[^.]+$/,''))===key(member));
   candidates.sort((a,b)=>Number(!a.startsWith('/boards/RESULTS/'+({raw:'RAW',nxt:'NXT',smackdown:'SmackDown',tna:'TNA',aaa:'AAA'}[show])+'/'))-Number(!b.startsWith('/boards/RESULTS/'+({raw:'RAW',nxt:'NXT',smackdown:'SmackDown',tna:'TNA',aaa:'AAA'}[show])+'/'))||a.localeCompare(b));
   const route=candidates[0];if(!route)throw Error('Approved portrait unavailable: '+member);
   const name=route.split('/').at(-1);portraits.push(name);portrait_routes[name]=route;
  }
 }
 for(const name of portraits)if(!routes[portrait_routes[name]||prefix+name])throw Error('Approved portrait unavailable: '+name);
 if(c.belt&&!routes[prefix+c.belt])throw Error('Approved belt unavailable: '+c.belt);
 const since_date=dateOnly(since,asOf)||(same?dateOnly(c.since_date,asOf):null);
 return {...c,name:holder.toUpperCase(),members,portraits,portrait_routes,kind:members.length>1||c.kind==='tag'?'tag':'singles',since_date,since:since_date?new Intl.DateTimeFormat('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}).format(new Date(since_date+'T12:00:00Z')).toUpperCase():null};
}
function aaaConfirmation(html,c,holder,catalog){
 const rows=tableRows(html),row=rows.find(r=>titleKey(r[0])===titleKey(c.title));
 if(row)return key(row[1])===key(holder);
 const current=html.match(/<h[12][^>]*>[^<]*Current AAA Champions[\s\S]*?(?=<h[12]|$)/i)?.[0]||html;
 const aaaKey=s=>titleKey(s).replace(/^aaa/,'').replace(/^world(?=tag|mixed|trios)/,'');
 const names=(holder.match(/\(([^()]+)\)/)?.[1]||holder).split(/\s+(?:&|and)\s+|,\s*/i);
 // SDH puts the holder in h3 BEFORE its title link. Compare within one card.
 const cards=[...current.matchAll(/<h3\b[^>]*>([\s\S]*?)<\/h3>([\s\S]*?)(?=<h[123]\b|$)/gi)];
 return cards.some(m=>{
  const titles=[...m[2].matchAll(/<a\b[^>]*>([\s\S]*?)<\/a>/gi)].map(a=>clean(a[1]));
  return titles.some(t=>aaaKey(t)===aaaKey(c.title))&&names.every(n=>key(m[1]).includes(key(n)));
 });
}
export async function collectChampions({library,routes,now=new Date(),requester=fetch}){
 const catalog=JSON.parse(await readFile(new URL('championship-catalog.json',import.meta.url),'utf8'));
 const programs=[],entries=[],warnings=[],cache=new Map(),as_of=easternDate(now);
 async function page(url){if(!cache.has(url))cache.set(url,(async()=>{const r=await requester(url,{headers:{Accept:'text/html'}});if(!r.ok)throw Error('HTTP '+r.status);const h=await r.text();if(h.length<1000||h.length>2000000)throw Error('Invalid source size');return h;})());return cache.get(url);}
 for(const [show,original] of Object.entries(catalog)){
  const board=library.records.find(r=>r.id==='championship-'+show);if(!board?.design_approved||!board.source_available)continue;
  const champions=[],sources=[];let verification='OFFICIAL_VERIFIED';
  let tna,aaa;
  try{
   if(show==='tna')tna=tnaTitleholders(await page('https://tnawrestling.com/roster'));
   if(show==='aaa'){const pages=await Promise.all(AAA_SOURCES.map(page));aaa={rows:tableRows(pages[0]),second:pages[1]};verification='SOURCE_CORROBORATED';}
  }catch(error){warnings.push(show+': '+error.message);continue;}
  for(const c of original){
   try{
    let holder,since,sourceUrls;
    if(show==='tna'){
     const matches=tna.filter(x=>titleKey(x.title)===titleKey(c.title));if(matches.length!==1)throw Error('Current title section unavailable: '+c.id);
     holder=matches[0].name;sourceUrls=['https://tnawrestling.com/roster'];
    }else if(show==='aaa'){
     const rows=aaa.rows.filter(r=>titleKey(r[0])===titleKey(c.title));if(rows.length!==1||!aaaConfirmation(aaa.second,c,rows[0][1],catalog))throw Error('AAA current titleholder disagreement: '+c.id);
     holder=rows[0][1];since=rows[0][2];sourceUrls=AAA_SOURCES;
     // Keep the original team display name when the row explicitly lists its same members.
     if(c.members.every(m=>key(holder).includes(key(m))))holder=c.name;
    }else{
     const html=await page(c.source);holder=currentWweHolder(html);if(!holder)throw Error('Current holder unavailable: '+c.id);
     const epoch=html.match(/data-reign-start-date=["'](\d{10})["']/)?.[1];since=epoch?easternDate(new Date(Number(epoch)*1000)):null;sourceUrls=[c.source];
    }
    const champion=resolveChampion(c,holder,{catalog,routes,board,show,since,asOf:as_of});
    champions.push({...champion,source:sourceUrls[0],source_urls:sourceUrls});sources.push(...sourceUrls);
   }catch(error){warnings.push(show+': '+c.id+': '+error.message);}
  }
  if(!champions.length)continue;
  programs.push({show,board_id:board.id,as_of,verification,champions,source_urls:[...new Set(sources)]});
  entries.push({id:board.id,title:board.label,show,kind:'champions',as_of,airdate:as_of,source_available:true,design_approved:true,content_status:'current',verification,checked_at:now.toISOString(),source_name:show==='aaa'?'Sacnilk / The SmackDown Hotel':show==='tna'?'TNA Wrestling':'WWE',source_url:sources[0],source_urls:[...new Set(sources)]});
 }
 return {entries,feed:{schema_version:1,mode:'SOURCE_CHECKED_CHAMPIONS',generated_at:now.toISOString(),programs},warnings};
}
