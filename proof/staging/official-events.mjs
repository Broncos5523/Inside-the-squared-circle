// Official WWE source gate for upcoming PLE and special-event board templates.
// Exact approved board HTML and artwork live in web/staging/; this module
// collects facts ONLY and never modifies any original source files.
// 2026 event registry: extend with confirmed official event dates and approved
// board IDs, never generate events from calendar guesses.
const CATALOG=[
 {
  event_id:'nxt-halloween-havoc-2026',board_id:'preview-nxt_halloween_havoc_preview_v4_approved_locked_20261027-night_one',
  title:'NXT Halloween Havoc',event_date:'2026-10-31',show:'nxt',
  official_url:'https://www.wwe.com/shows/nxtple/nxt-halloween-havoc-2026',
  page_mark:'NXT Halloween Havoc',date_mark:/Saturday,?\s+Oct\.?\s*31/i,
  cards:[
   {heading:'NXT CHAMPIONSHIP',left:'Tony D’Angelo',left_portrait:'tony-d-angelo',right:'Grayson Waller',right_portrait:'grayson-waller',
    source_names:["Grayson Waller","Tony D'Angelo"],footer:'NXT CHAMPIONSHIP • TITLE MATCH',belt:true},
   {heading:'NXT WOMEN’S CHAMPIONSHIP',left:'Wren Sinclair',left_portrait:'wren-sinclair',right:'Kelani Jordan',right_portrait:'kelani-jordan',
    source_names:['Kelani Jordan','Wren Sinclair'],footer:'NXT WOMEN’S CHAMPIONSHIP • TITLE MATCH',belt:true},
   {heading:'NXT NORTH AMERICAN CHAMPION • NON-TITLE',left:'Izzi Dame',left_portrait:'izzi-dame',right:'Zaria',right_portrait:'zaria',
    source_names:['Zaria','Izzi Dame'],footer:'ZARIA VS. IZZI DAME • NON-TITLE MATCH',belt:false}
  ],
 },
 {
  event_id:'wwe-crown-jewel-2026',board_id:'preview-crown_jewel_preview_v1_approved_locked_20261027-night_one',
  title:'WWE Crown Jewel',event_date:'2026-11-07',show:'wwe',
  official_url:'https://www.wwe.com/shows/wwe-crown-jewel/crown-jewel-2026',
  page_mark:'Crown Jewel',date_mark:/Saturday,?\s+Nov\.?\s*7/i,
  cards:[
   {heading:'MEN’S CROWN JEWEL CHAMPIONSHIP',left:'Roman Reigns',left_portrait:'roman-reigns',right:'Sami Zayn',right_portrait:'sami-zayn',
    source_names:['Roman Reigns','Sami Zayn'],belt:true},
   {heading:'WOMEN’S CROWN JEWEL CHAMPIONSHIP',left:'Chelsea Green',left_portrait:'chelsea-green',right:'Liv Morgan',right_portrait:'liv-morgan',
    source_names:['Chelsea Green','Liv Morgan'],belt:true},
   {heading:'LAST MAN STANDING MATCH',left:'Cody Rhodes',left_portrait:'cody-rhodes',right:'Randy Orton',right_portrait:'randy-orton',
    source_names:['Cody Rhodes','Randy Orton'],belt:false}
  ],
 }
];
function dayDifference(a,b){return (Date.parse(a+'T12:00:00Z')-Date.parse(b+'T12:00:00Z'))/86400000;}
function dateEastern(now){const p=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now);
 const d=Object.fromEntries(p.map(x=>[x.type,x.value]));return d.year+'-'+d.month+'-'+d.day;}
function clean(x){return String(x||'').replace(/<[^>]*>/g,' ').replace(/&(?:amp|#38);/gi,'&').replace(/&#(?:39|x27);|&apos;|&rsquo;/gi,"'").replace(/&(?:nbsp|#160);/gi,' ').replace(/\s+/g,' ').trim();}
function headings(html){return [...html.matchAll(/<h3\b[^>]*>([\s\S]*?)<\/h3>/gi)].map(x=>clean(x[1]));}
function matchHeading(heading,needles){const norm=s=>s.toLowerCase().replace(/[’‘]/g,"'");return needles.every(needle=>norm(heading).includes(norm(needle)));}
export async function collectOfficialEvents({library,now=new Date(),requester=fetch}){
 const today=dateEastern(now),programs=[],entries=[],errors=[];
 for(const spec of CATALOG){
  const window=dayDifference(spec.event_date,today);
  if(window<0||window>14)continue;
  const board=library.records.find(r=>r.id===spec.board_id);
  if(!board?.source_available||!board.design_approved){errors.push(spec.event_id+':approved source missing');continue;}
  try{
   const r=await requester(spec.official_url,{headers:{Accept:'text/html'}});
   if(!r.ok)throw Error('HTTP '+r.status);
   const html=await r.text();
   if(html.length<1000||html.length>2_000_000)throw Error('Invalid page size');
   if(!html.includes(spec.page_mark)||!spec.date_mark.test(html)||!html.includes('2026'))throw Error('Official date/title not confirmed');
   const found=headings(html);
   const verifiedCards=spec.cards.map(card=>({...card,verified_heading:found.find(x=>matchHeading(x,card.source_names))||null}));
   if(!verifiedCards.every(x=>x.verified_heading))throw Error('Approved card mapping not fully confirmed by current official preview');
   const program={
    event_id:spec.event_id,board_id:spec.board_id,title:spec.title,show:spec.show,
    event_date:spec.event_date,source_url:spec.official_url,checked_at:now.toISOString(),
    verification:'OFFICIAL_VERIFIED',cards:verifiedCards,render_ready:true
   };
   programs.push(program);
   entries.push({
    id:spec.board_id,title:board.label,show:spec.show,kind:'ple-preview',event_id:spec.event_id,
    event_date:spec.event_date,source_available:true,design_approved:true,content_status:'current',
    verification:'OFFICIAL_VERIFIED',date_confirmed:true,has_content:true,schedule_confirmed:true,
    checked_at:now.toISOString(),source_name:'WWE',source_url:spec.official_url
   });
  }catch(err){errors.push(spec.event_id+':'+String(err?.message||err));}
 }
 return {entries,feed:{mode:'OFFICIAL_WWE_EVENT_PREVIEWS',generated_at:now.toISOString(),programs},errors};
}
