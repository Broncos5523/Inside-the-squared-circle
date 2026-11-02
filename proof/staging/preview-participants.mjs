// Dated announcement, not a permanent faction roster assumption.
export const VISION_SOURCE='https://www.tpww.net/2026/11/roman-reigns-appearance-penta-jevon-evans-dragon-lee-vs-the-vision-in-six-man-tag-and-all-ego-ethan-page-vs-chad-gable-for-wwe-intercontinental-title-matches-set-for-11-2-wwe-raw-sh/';
export async function enrichPreviewParticipants(program,requester=fetch){
 if(program.show_id!=='raw'||program.airdate!=='2026-11-02')return program;
 const match=program.matches.find(m=>/The Vision/i.test(m.text)&&/Penta/i.test(m.text)&&/Dragon Lee/i.test(m.text));
 if(!match)return program;
 try{
  const r=await requester(VISION_SOURCE,{headers:{Accept:'text/html'}});if(!r.ok)return program;
  const html=await r.text();
  const text=html.replace(/<[^>]*>/g,' ').replace(/&#(?:0*38);|&amp;/g,'&').replace(/&#(?:8217|0*39);|&rsquo;|’/g,"'").replace(/\s+/g,' ');
  if(!/November 2nd WWE RAW/i.test(text)||!['Penta',"Je'Von Evans",'Dragon Lee','Austin Theory','Bronson Reed','Bron Breakker'].every(n=>text.includes(n)))return program;
  match.participant_sides=[{label:'The Vision',members:['Austin Theory','Bronson Reed','Bron Breakker']}];
  match.participants_source_url=VISION_SOURCE;
 }catch{}
 return program;
}
