// Discover the current episode from WWE's dated banner, not the normal Tuesday
// schedule or the publication date embedded in individual preview article URLs.
const INDEX='https://www.wwe.com/shows/wwenxt';
const SUPPLEMENT='https://www.tpww.net/2026/10/wwe-nxt-halloween-havoc-2026-notes-nxt-tlc-event-announced-for-this-december-michael-chandler-to-special-guest-unsanctioned-match-nxt-womens-title-match-cm-punk-vs-grayson-waller-for-nxt-title/';
const clean=s=>String(s||'').replace(/<[^>]*>/g,' ').replace(/&#(?:x([0-9a-f]+)|(\d+));/gi,(_,h,d)=>String.fromCodePoint(parseInt(h||d,h?16:10))).replace(/&amp;/g,'&').replace(/&nbsp;/g,' ').replace(/&rsquo;/g,"'").replace(/\s+/g,' ').trim();
const key=s=>clean(s).toLowerCase().replace(/[^a-z0-9]/g,'');
const escape=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
const iso=(y,m,d)=>y+'-'+String(m).padStart(2,'0')+'-'+String(d).padStart(2,'0');
export function nextOfficialNxtDate(index,now=new Date()){
 const today=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(now),dates=[];
 const months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
 for(const m of index.matchAll(/data-a2a-url=["']https:\/\/www\.wwe\.com\/shows\/wwenxt\/(20\d{2})-(\d{1,2})-(\d{1,2})["'][^>]*data-a2a-title=["']([^"']+)/g)){
  const date=iso(m[1],m[2],m[3]),days=(Date.parse(date)-Date.parse(today))/86400000;
  if(!Number.isFinite(days)||days<0||days>14||new Date(date+'T12:00:00Z').toISOString().slice(0,10)!==date)continue;
  if(!new RegExp('WWE NXT:\\s*'+months[Number(m[2])-1]+'[a-z]*\\.?\\s+'+Number(m[3])+',?\\s*'+m[1],'i').test(clean(m[4])))continue;
  dates.push(date);
 }
 return dates.sort()[0]||null;
}
function bodyOf(html){const start=html.indexOf('field--name-body');if(start<0)return '';return html.slice(start,html.indexOf('</div>',start));}
export function parseOfficialNxtArticle(html,url,date,routes){
 const head=clean(html.match(/<meta[^>]*property=["']og:title["'][^>]*content=["']([^"']+)/i)?.[1]||html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1]).replace(/\s*\|\s*WWE$/i,'');
 const body=clean(bodyOf(html)),weekday=new Intl.DateTimeFormat('en-US',{weekday:'long',timeZone:'UTC'}).format(new Date(date+'T12:00:00Z'));
 if(!html.includes(url)||!new RegExp('NXT airs live on '+weekday,'i').test(body)&&!new RegExp('(?:live|edition).*'+weekday+'|'+weekday+'.*8 ET','i').test(body))return null;
 const slugs=[...new Set(Object.keys(routes).map(k=>k.match(/\/portraits\/([^/]+)\.png$/)?.[1]).filter(Boolean))].sort((a,b)=>b.length-a.length);
 const patterns=slugs.map(s=>s.split('-').map(escape).join("['’ -]*")).concat(['Hank\\s*&\\s*Tank']);
 const people=text=>[...text.matchAll(new RegExp('\\b(?:'+patterns.join('|')+')\\b','gi'))].map(m=>m[0]);
 const appearance=/\b(?:to appear|will appear|appears)\b/i.test(head),split=head.split(/\s+(?:challenges?|battles?|takes? on|faces?|vs\.?|against)\s+/i);
 const clock=body.match(/(?:at|live)\s+(\d{1,2})(?::(\d{2}))?\s*ET/i);
 const result={matches:[],appearances:[],start_time:clock?String((Number(clock[1])%12)+12).padStart(2,'0')+':'+(clock[2]||'00'):null};
 if(appearance){for(const name of people(head))result.appearances.push({text:name,evidence_url:url,source_name:'WWE'});}
 else if(split.length===2){
  const left=people(split[0]),right=people(split[1]);if(/mystery (?:opponent|challenger)/i.test(split[1]))right.push('Mystery Opponent');
  if(left.length&&right.length){
   const label=names=>names.join(' & '),text=label(left)+' vs. '+label(right),participant_sides=[];
   for(const [team,members] of [['Hank & Tank',['Hank Walker','Tank Ledger']],['The Vanity Project',['Jackson Drake','Brad Baylor','Ricky Smokes']]])if(key(head).includes(key(team))&&members.every(n=>key(body).includes(key(n))))participant_sides.push({label:team,members});
   const stipulation=/NXT Women['’]s (?:Championship|Title)/i.test(head)?"NXT WOMEN'S CHAMPIONSHIP":/NXT Championship/i.test(head)?'NXT CHAMPIONSHIP':/Dusty.*Final/i.test(head)?'DUSTY CUP FINAL':left.length+right.length>=4?'SIX-MAN TAG MATCH':'UPCOMING MATCH';
   result.matches.push({text,stipulation,evidence_url:url,source_name:'WWE',participant_sides});
  }
 }
 if(/Cody Rhodes/.test(body)&&/crown the winner|present.*trophy/i.test(body))result.appearances.push({text:'Cody Rhodes',evidence_url:url,source_name:'WWE'});
 return result;
}
export async function collectOfficialNxtPreview({routes,now=new Date(),requester=fetch}){
 try{
  const r=await requester(INDEX,{headers:{Accept:'text/html'}});if(!r.ok)return null;const index=await r.text();if(index.length>1500000)return null;
  const date=nextOfficialNxtDate(index,now);if(!date)return null;
  const links=[];for(const m of index.matchAll(/href=["']([^"']+)["']/g)){const u=new URL(m[1],INDEX);const p=u.pathname.match(/^\/shows\/wwenxt\/(20\d{2})-(\d{1,2})-(\d{1,2})\/[a-z0-9-]+$/);if(u.origin!=='https://www.wwe.com'||!p)continue;const gap=(Date.parse(date)-Date.parse(iso(p[1],p[2],p[3])))/86400000;if(gap>=0&&gap<=7)links.push(u.href);}
  const matches=[],appearances=[];let start_time=null;
  for(const url of [...new Set(links)].slice(0,8)){try{const page=await requester(url,{headers:{Accept:'text/html'}});if(!page.ok)continue;const html=await page.text();if(html.length>1000000)continue;const parsed=parseOfficialNxtArticle(html,url,date,routes);if(parsed){matches.push(...parsed.matches);appearances.push(...parsed.appearances);start_time=parsed.start_time||start_time;}}catch{}}
  if(matches.length<2)return null;
  // A dated reported supplement covers announcements not featured on WWE's index.
  if(date==='2026-11-04')try{const r=await requester(SUPPLEMENT,{headers:{Accept:'text/html'}});if(r.ok){const html=await r.text(),text=clean(html);if(text.length<1000000&&/November 4(?:th)?/i.test(text)&&/Current Card For Next Week['’]s WWE NXT Show/i.test(text)&&/Unsanctioned match\s*[–—-]\s*Cruz Montana vs\. Dion Lennox/i.test(text))matches.push({text:'Cruz Montana vs. Dion Lennox',stipulation:'UNSANCTIONED MATCH',note:/Michael Chandler/.test(text)?'Michael Chandler involved':null,evidence_url:SUPPLEMENT,source_name:'TPWW'});}}catch{}
  const unique=rows=>rows.filter((x,i)=>rows.findIndex(y=>key(y.text)===key(x.text))===i);
  return {show_id:'nxt',airdate:date,start_time,matches:unique(matches),appearances:unique(appearances),source_name:matches.some(m=>m.source_name==='TPWW')?'WWE / TPWW':'WWE',source_url:INDEX,official_date_verified:true,collection_status:'official_dated_episode_preview',schedule_source:'official_wwe_episode_banner'};
 }catch{return null;}
}
