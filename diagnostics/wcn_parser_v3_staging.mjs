// Private household WCN intake. Only text within "Card & Preview" is parsed.
// No entire article content is stored, redistributed, or shown.
export const CREDIT = 'Wrestling Central News (wrestlingcentralnews.com)';
export const FEED_URL = 'https://wrestlingcentralnews.com/feed.xml';
export const SNAPSHOT_URL = 'https://broncos5523.github.io/Inside-the-squared-circle/data/snapshot.json';
export const EVENT_SLUGS = Object.freeze({raw:'wwe-raw', smackdown:'wwe-smackdown', nxt:'wwe-nxt', tna:'tna-impact'});
const BAD = /\b(?:defeated|defeats|pinned|won|retained|winner|last week|last night|yesterday|previously|spoiler|rumou?r|cancelled|canceled|postponed|no longer|dark match|prediction)\b/i;
const BAD_NAME = /\b(?:match|championship|episode|preview|card|tonight|tomorrow|last|next|news|report|results|general manager|event|could|maybe)\b/i;
const WORD = "[A-ZÀ-Ý][A-Za-zÀ-ÿ0-9’'\\-]*";
const PERSON = `${WORD}(?:\\s+${WORD}){0,3}`;
const SIDE = `(?:The\\s+)?${PERSON}(?:\\s+(?:&|and)\\s+${PERSON})?`;
const BOUT = new RegExp(`(${SIDE})\\s+(?:vs\\.?|versus|faces?|takes? on|challenges?)\\s+(${SIDE})(?=\\s|[.;,!?]|$)`,'g');
const TITLE = new RegExp(`(${SIDE})\\s+(?:will\\s+)?(?:defend(?:s)?|put(?:s)?)\\s+[^.;:]{0,110}?\\s+against\\s+(${SIDE})(?=\\s|[.;,!?]|$)`,'g');
const APPEAR = /\bAlso advertised:\s*([^.]{6,250})/i;
const P_TAG=/<p\b[^>]*>([\s\S]*?)<\/p\s*>/gi;
const H2=/<h2\b[^>]*>([\s\S]*?)<\/h2\s*>/gi;
function entities(x){return x.replace(/&#(x[0-9a-f]+|\d+);/gi,(_,n)=>{const p=n[0].toLowerCase()==='x'?parseInt(n.slice(1),16):parseInt(n,10);return Number.isFinite(p)&&p>=32&&p<0x10ffff?String.fromCodePoint(p):' ';}).replace(/&(?:amp|nbsp|quot|apos|lt|gt);/gi,m=>({'&amp;':'&','&nbsp;':' ','&quot;':'"','&apos;':"'",'&lt;':' ','&gt;':' '}[m.toLowerCase()]||' '));}
function textContent(html){return entities(html.replace(/<[^>]*>/g,' ')).replace(/\s+/g,' ').trim();}
export function previewParagraphs(html){
 if(typeof html!=='string'||html.length>1_000_000||html.length<20)return [];
 H2.lastIndex=0;let active=false,offset=0,sections=[];let m;
 while((m=H2.exec(html))){const title=textContent(m[1]).toLowerCase();if(active){sections.push(html.slice(offset,m.index));break;}if(title==='card & preview'){active=true;offset=H2.lastIndex;}}
 if(active&&!sections.length)sections.push(html.slice(offset,Math.min(html.length,offset+12000)));
 if(!sections.length)return [];
 const result=[];P_TAG.lastIndex=0;for(const s of sections){P_TAG.lastIndex=0;while((m=P_TAG.exec(s))&&result.length<24)result.push(textContent(m[1]).slice(0,1000));}
 return result;
}
function reasonable(a,b){return a&&b&&a.toLowerCase()!==b.toLowerCase()&&a.length>=3&&b.length>=3&&a.length<75&&b.length<75&&!BAD_NAME.test(a)&&!BAD_NAME.test(b)}
export function parseWcnPage(html){
 const matches=[],appearances=[],seen=new Set(), seenAppearance=new Set();
 for(const paragraph of previewParagraphs(html)){
  if(BAD.test(paragraph)||/\b(?:pay-per-view|PPV|other promotion|next month's event)\b/i.test(paragraph))continue;
  const advertised=APPEAR.exec(paragraph);
  if(advertised){for(const item of advertised[1].split(',').slice(0,8)){
    const name=item.trim();if(name.length>2&&name.length<70&&new RegExp('^'+PERSON+'$').test(name)&&!BAD_NAME.test(name)&&!seenAppearance.has(name.toLowerCase())){appearances.push(name);seenAppearance.add(name.toLowerCase());}
  }}
  for(const sentence of paragraph.replace(/\bvs\.\s+/gi,'vs ').split(/;\s*|(?<=[.!?])\s+(?=[A-Z])/)){
    const piece=sentence.split(':').at(-1).trim();if(BAD.test(piece))continue;
    for(const regex of [BOUT,TITLE]){
      regex.lastIndex=0;let m;while((m=regex.exec(piece))){const a=m[1].trim(),b=m[2].trim();if(!reasonable(a,b))continue;const pair=`${a} vs. ${b}`;if(!seen.has(pair.toLowerCase())){seen.add(pair.toLowerCase());matches.push(pair);}if(matches.length>=8)break;}
      if(matches.length>=8)break;
    }
    if(matches.length>=8)break;
  }
 }
 return {matches:matches.slice(0,8),appearances:appearances.slice(0,8)};
}
// V3 private WCN show-index fallback: WCN sometimes publishes a real matchup
// in an episode-scoped article heading, while the event-page "Card & preview"
// paragraphs contain no explicit "X vs. Y" expression. This fallback uses
// only WCN's headline + short abstract and the SAME exact TV episode date.
// It cannot infer winners/appearances or assign PLE matches to weekly shows.
export const WCN_SHOW_INDEX = Object.freeze({
 raw:'https://wrestlingcentralnews.com/shows/wwe-raw/',
 smackdown:'https://wrestlingcentralnews.com/shows/wwe-smackdown/',
 nxt:'https://wrestlingcentralnews.com/shows/wwe-nxt/',
 tna:'https://wrestlingcentralnews.com/shows/tna-impact/'
});
const ARTICLE_H3=/<h3\b[^>]*>([\s\S]*?)<\/h3\s*>([\s\S]*?)(?=<h3\b|<\/main\b|$)/gi;
const HEADLINE_DATE=/\b(?:(20\d{2})-)?(\d{1,2})\/(\d{1,2})(?:\/(20\d{2}|\d{2}))?\b/g;
const WRITTEN_DATE=/\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan\.?|Feb\.?|Mar\.?|Apr\.?|Jun\.?|Jul\.?|Aug\.?|Sep\.?|Sept\.?|Oct\.?|Nov\.?|Dec\.?)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s*(20\d{2}))?/gi;
const MONTHS=['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'];
const SPECULATIVE=/\b(?:prediction|predicts?|fantasy booking|might|could|possibly|rumou?r|dark match|spoilers?|injured|cancelled|canceled|postponed|defeated|defeats|retained|pinned|winner)\b/i;
const SHOW_TOKENS={raw:/\braw\b/i,smackdown:/\bsmack\s?down\b/i,nxt:/\bnxt\b/i,tna:/\b(?:tna|impact)\b/i};
function articleDates(text,iso){
 const [yr,mo,day]=iso.split('-').map(Number);let match=false,invalid=false;let m;
 if(text.includes(iso))match=true;
 HEADLINE_DATE.lastIndex=0;
 while((m=HEADLINE_DATE.exec(text))){
  let y=Number(m[1]||m[4]||yr);if(y<100)y+=2000;
  if(y===yr&&Number(m[2])===mo&&Number(m[3])===day)match=true;
  else invalid=true;
 }
 WRITTEN_DATE.lastIndex=0;
 while((m=WRITTEN_DATE.exec(text))){
  const mon=MONTHS.indexOf(m[1].slice(0,3).toLowerCase())+1;
  if(mon===mo&&Number(m[2])===day&&(!m[3]||Number(m[3])===yr))match=true;
  else invalid=true;
 }
 return {match,invalid};
}
function personPart(raw,left){
 let s=raw.replace(/\b(?:title match|championship match|set for|added to|announced for|on smackdown|on raw|in smackdown|in raw)\b.*$/i,'')
   .replace(/\b(?:to defend|will defend|defends?)\b.*$/i,'').trim();
 const tokens=s.match(/[A-ZÀ-Ý][a-zA-ZÀ-ÿ0-9.'’\-]*/g)||[];
 let use=left?tokens.slice(-3):tokens.slice(0,3);
 if(use.length===3&&/^(?:the|new|wwe|with)$/i.test(use[0]))use=use.slice(1);
 if(use.length===3&&/^(?:to|will|is)$/i.test(use.at(-1)))use=use.slice(0,-1);
 const value=use.join(' ');
 if(use.length<2||use.length>3||value.length<4||value.length>70||BAD_NAME.test(value)
    ||/\b(?:smackdown|raw|nxt|impact|october|november|for|on|in|to)\b/i.test(value))return null;
 return value;
}
function headlinePair(head){
 const m=/\s+vs\.?\s+/i.exec(head);if(!m)return null;
 const a=personPart(head.slice(0,m.index),true);
 const b=personPart(head.slice(m.index+m[0].length),false);
 return a&&b&&a.toLowerCase()!==b.toLowerCase()?`${a} vs. ${b}`:null;
}
export function parseWcnShowIndex(html,show_id,airdate,now=new Date()){
 if(typeof html!=='string'||html.length>1_000_000||!Object.hasOwn(WCN_SHOW_INDEX,show_id)||!validDate(airdate))return [];
 const today=easternDate(now);
 if(airdate<today||Date.parse(airdate+'T00:00:00Z')>Date.parse(today+'T00:00:00Z')+14*86400_000)return [];
 // After a completed broadcast, never keep the previous preview alive.
 if(airdate===today){
  const hour=Number(new Intl.DateTimeFormat('en-US',{hour:'2-digit',hourCycle:'h23',timeZone:'America/New_York'}).format(now));
  if(show_id==='tna'?hour>=23:hour>=23)return [];
 }
 const matches=[],seen=new Set();let m;ARTICLE_H3.lastIndex=0;
 while((m=ARTICLE_H3.exec(html))&&matches.length<8){
  const head=textContent(m[1]);
  P_TAG.lastIndex=0;const p=P_TAG.exec(m[2]);const abstract=p?textContent(p[1]).slice(0,950):'';
  const titleDate=articleDates(head,airdate),bodyDate=articleDates(abstract,airdate);
  if(titleDate.invalid||!(titleDate.match||bodyDate.match))continue;
  const combined=head+' '+abstract;
  if(!SHOW_TOKENS[show_id].test(combined)||Object.entries(SHOW_TOKENS).some(([key,re])=>key!==show_id&&re.test(combined)))continue;
  if(SPECULATIVE.test(combined))continue;
  const pair=headlinePair(head);
  if(pair&&!seen.has(pair.toLowerCase())){seen.add(pair.toLowerCase());matches.push({text:pair,evidence_url:WCN_SHOW_INDEX[show_id]});}
 }
 return matches;
}

export function validDate(d){if(typeof d!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(d))return false;const n=new Date(d+'T00:00:00Z');return !Number.isNaN(n.getTime())&&n.toISOString().slice(0,10)===d;}
export function easternDate(now=new Date()){return new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(now);}
export function safeShows(snapshot,now=new Date()){
 if(snapshot?.schema_version!==1||!Array.isArray(snapshot?.shows)||snapshot.shows.length!==6)return [];
 const generated=new Date(snapshot.generated_at);if(!Number.isFinite(generated.getTime())||generated.getTime()>now.getTime()+5*60_000||now.getTime()-generated.getTime()>24*3600_000)return [];
 const today=easternDate(now);const start=Date.parse(today+'T00:00:00Z');
 return snapshot.shows.filter(s=>Object.hasOwn(EVENT_SLUGS,s.id)&&s.schedule_status==='fresh'&&validDate(s.next?.date)&&Date.parse(s.next.date+'T00:00:00Z')-start>=0&&Date.parse(s.next.date+'T00:00:00Z')-start<=14*86400_000)
   .map(s=>({show_id:s.id,airdate:s.next.date,url:`https://wrestlingcentralnews.com/events/${s.next.date}-${EVENT_SLUGS[s.id]}/`}));
}
export function sanitizedForDisplay(doc,now=new Date()){
 const today=easternDate(now);const collected=new Date(doc?.generated_at||0);
 if(!Number.isFinite(collected.getTime())||collected.getTime()>now.getTime()+5*60000||now.getTime()-collected.getTime()>36*3600_000)return {schema_version:1,mode:'PRIVATE_NONCOMMERCIAL_WCN_CARDS',generated_at:doc?.generated_at||null,credit:CREDIT,programs:[]};
 const programs=(doc?.programs||[]).filter(x=>Object.hasOwn(EVENT_SLUGS,x.show_id)&&validDate(x.airdate)&&x.airdate>=today&&x.airdate<=new Date(Date.parse(today+'T00:00:00Z')+14*86400_000).toISOString().slice(0,10))
 .map(x=>({...x,matches:(x.matches||[]).slice(0,8),appearances:(x.appearances||[]).slice(0,8)}));
 return {schema_version:1,mode:'PRIVATE_NONCOMMERCIAL_WCN_CARDS',generated_at:doc?.generated_at||null,credit:CREDIT,programs};
}

// Adapter for existing read-only Upcoming Show board JSON contract. This
// response MUST be served via an authenticated first-party private route,
// never as a JSON file in the public GitHub Pages repository.
export function privateReportedFeed(doc,now=new Date()){
 const usable=sanitizedForDisplay(doc,now);
 const map=new Map(usable.programs.map(x=>[x.show_id,x]));
 const programs=['raw','smackdown','nxt','aaa','tna','evolve'].map(show_id=>{
  const row=map.get(show_id);
  return {show_id,airdate:row?.airdate||null,
   matches:(row?.matches||[]).map((m)=>({text:m.text,stipulation:'MATCH',status:'REPORTED_UNVERIFIED',source_name:CREDIT,evidence_url:m.evidence_url})),
   appearances:(row?.appearances||[]).map((a)=>({text:a.text,type:'Advertised appearance',status:'REPORTED_UNVERIFIED',source_name:CREDIT,evidence_url:a.evidence_url})),
   error:null,source_name:CREDIT};
 });
 return {schema_version:1,mode:'REPORTED_MATCHES_UNVERIFIED',generated_at:usable.generated_at,valid_as_of_et:easternDate(now),
  attribution:CREDIT,usage:'PERSONAL_NONCOMMERCIAL_HOME_DISPLAY_ONLY',
  programs,total_reported_matches:programs.reduce((n,p)=>n+p.matches.length,0),
  total_reported_appearances:programs.reduce((n,p)=>n+p.appearances.length,0)};
}
