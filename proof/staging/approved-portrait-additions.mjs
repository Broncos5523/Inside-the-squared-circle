import {readFileSync} from 'node:fs';
const additions=JSON.parse(readFileSync(new URL('./approved-portrait-additions.json',import.meta.url),'utf8'));
// Update visual identity only. Source-reviewed episode facts and original HTML stay intact.
export function addApprovedPortraits(program){
 for(const segment of program.segments||[]){
  const approved=additions[program.show_id]?.[segment.id];
  if(!approved||segment.headline!==approved.headline||segment.kind!==approved.kind)continue;
  if(!Array.isArray(segment.portraits)||segment.portraits.length)continue;
  segment.portraits=[approved.portrait];
 }
 return program;
}
