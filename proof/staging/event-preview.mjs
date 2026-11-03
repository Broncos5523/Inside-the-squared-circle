import {EVENT_SLUGS,articleDates} from './parser.mjs';
const clean=s=>String(s||'').replace(/<[^>]*>/g,' ').replace(/&#(?:x([0-9a-f]+)|(\d+));/gi,(_,x,n)=>String.fromCodePoint(parseInt(x||n,x?16:10))).replace(/&amp;/g,'&').replace(/&(?:nbsp|quot);/g,' ').replace(/\s+/g,' ').trim();
const shows={raw:/\braw\b/i,nxt:/\bnxt\b/i,smackdown:/\bsmackdown\b/i,tna:/\b(?:tna|impact)\b/i};
export function parseDatedEventBrief(html,show,date,routes={}){
 const slug=EVENT_SLUGS[show],canonical='https://wrestlingcentralnews.com/events/'+date+'-'+slug+'/';
 const h1=clean(html.match(/<h1\b[^>]*>([\s\S]*?)<\/h1>/i)?.[1]);
 if(!slug||!html.includes(canonical)||!shows[show].test(h1)||!articleDates(h1,date).match)return {matches:[],appearances:[]};
 const section=html.match(/<section\b[^>]*id=["']card["'][^>]*>([\s\S]*?)<\/section>/i)?.[1];
 if(!section)return {matches:[],appearances:[]};
 // Portrait routes are presentation data, never a dictionary of eligible
 // participants. Preserve explicitly named newcomers even before an image exists.
 const word="(?:[A-ZÀ-Ý][A-Za-zÀ-ÿ0-9’'\\-]*|['’][A-Z][A-Za-zÀ-ÿ0-9’'\\-]*)";
 const person=word+'(?:\\s+(?:(?:de|del|la|el|of|the)\\s+)?'+word+'){0,3}';
 const separator='(?:,\\s*(?:and\\s+)?|\\s+(?:&|and)\\s+)';
 const side=person+'(?:'+separator+person+'){0,3}';
 const bout=new RegExp('(?<![A-Za-zÀ-ÿ0-9’\\\'-])('+side+')\\s+(?:(?:will\\s+)?(?:face[sd]?|vs\\.?|versus|take[sd]?\\s+on|battle[sd]?)|(?:will\\s+)?(?:defend\\w*|put\\w*)[^.;]{0,90}?against|against)\\s+('+side+')(?![A-Za-zÀ-ÿ0-9’\\\'-])','g');
 const trailingParticipant=/^(?:\s*,\s*(?:and\s+)?(?=[A-ZÀ-Ý'’])|\s+(?:&|and)\s+\S)/;
 const leadingParticipant=new RegExp(person+separator+'$');
 const appearance=/([A-Z][A-Za-zÀ-ÿ’'\-]+(?:\s+[A-Z][A-Za-zÀ-ÿ’'\-]+){1,3})\s+(?:(?:is|has been)\s+)?(?:advertised\s+for|set\s+to\s+address|address(?:ing|es)\b|will\s+appear|returns?\b|will\s+undergo\s+(?:her|his|their)\s+initiation\b)/g;
 const matches=[],appearances=[],seen=new Set();let start_time=null;
 for(const block of section.matchAll(/<article\b[^>]*>([\s\S]*?)<\/article>/gi)){
  const head=clean(block[1].match(/<h3\b[^>]*>([\s\S]*?)<\/h3>/i)?.[1]);
  const body=clean(block[1].match(/<p\b[^>]*class=["']hs["'][^>]*>([\s\S]*?)<\/p>/i)?.[1]);
  const published=block[1].match(/<time\b[^>]*datetime=["'](\d{4}-\d{2}-\d{2})/i)?.[1];
  const gap=(Date.parse(date)-Date.parse(published))/86400000;
  const dates=articleDates(head+' '+body,date);
  if(!shows[show].test(head)||Object.entries(shows).some(([s,re])=>s!==show&&re.test(head))||!Number.isFinite(gap)||gap<0||gap>14||dates.invalid)continue;
  // An aggregator's episode wrapper does not date a separate taping story.
  // Relative future-event announcements need their own matching episode date.
  if(!dates.match&&/\b(?:later (?:this|next) month|next month|upcoming (?:TV|television) tapings|future (?:TV|television) tapings)\b/i.test(head+' '+body))continue;
  if(/\b(?:prediction|rumou?r|cancelled|canceled|spoiler)\b/i.test(head))continue;
  const clock=/(?:moves? to|start time (?:of|is)|at)\s+(\d{1,2})(?::(\d{2}))?\s*([ap])\.?\s*m\.?\s*(?:ET|Eastern)/i.exec(head+' '+body);
  if(clock&&articleDates(head+' '+body,date).match&&+clock[1]>=1&&+clock[1]<=12)start_time=String((+clock[1]%12)+(clock[3].toLowerCase()==='p'?12:0)).padStart(2,'0')+':'+(clock[2]||'00');
  for(const sentence of (head+'. '+body).replace(/\bvs\./gi,'vs').split(/[.!?]\s+|\bwhile\b/i)){
   if(Object.entries(shows).some(([s,re])=>s!==show&&re.test(sentence))||/\b(?:Crown Jewel|Survivor Series|Halloween Havoc|WrestleMania|SummerSlam|defeated|retained|last week)\b/i.test(sentence))continue;
   bout.lastIndex=0;
   for(const m of sentence.matchAll(bout)){
    // Never emit a shortened list when a bounded/ambiguous name was not read.
    if(trailingParticipant.test(sentence.slice(m.index+m[0].length))||leadingParticipant.test(sentence.slice(0,m.index)))continue;
    const sides=[m[1],m[2]].map(s=>s.replace(/^.*\bChampions?\s+/i,'').trim());
    if(sides.some(s=>!s)||/\b(?:Raw|WWE|NXT|Impact|TNA|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b/i.test(sides.join(' ')))continue;
    const text=sides.join(' vs. '),key=sides.map(s=>s.toLowerCase().replace(/[^a-z0-9]/g,'')).sort().join('|');
    if(!seen.has(key)){seen.add(key);matches.push({text,evidence_url:canonical,...(/Intercontinental Championship/i.test(sentence)?{stipulation:'INTERCONTINENTAL CHAMPIONSHIP'}:/six.man tag/i.test(sentence)?{stipulation:'SIX-MAN TAG TEAM MATCH'}:{})});}
   }
   appearance.lastIndex=0;
   for(const m of sentence.matchAll(appearance)){
    const name=m[1].replace(/^.*\bChampion\s+/i,'').trim();
    if(!/\b(?:Raw|WWE|NXT|Manager|Monday|Friday)\b/.test(name)&&!appearances.some(x=>x.text.toLowerCase()===name.toLowerCase()))appearances.push({text:name,evidence_url:canonical});
   }
  }
 }
 return {matches:matches.slice(0,8),appearances:appearances.slice(0,8),start_time};
}
