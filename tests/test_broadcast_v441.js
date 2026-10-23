const fs=require('fs'),assert=require('node:assert/strict');
const html=fs.readFileSync('web/preview-v4-41-licensed-stars-broadcast.html','utf8');
const i=html.indexOf('  const bd=(id)=>'),j=html.indexOf('  function sdMatchHero(text){',i);
assert(i>0&&j>i,'Broadcast functions absent');
class El{
 constructor(tag){this.tag=tag;this.children=[];this.hidden=true;this.className='';this._text='';
 this.classList={toggle:()=>{},add:()=>{},remove:()=>{}}}
 replaceChildren(...rows){this.children=rows;this._text=''}
 append(...rows){this.children.push(...rows)}
 set textContent(value){this._text=String(value);this.children=[]}
 get textContent(){return this._text+this.children.map(c=>c.textContent||'').join(' ')}
 querySelector(name){return name==='.bd-photo'?this.children.find(c=>c.className.startsWith('bd-photo'))||null:null}
}
const ids={};for(const id of ['hero','hero-note','date','time','air-label','primary','side','others','others-title','notes','prime-title','side-title','notes-title','ticker','dates','credit-left','sd-broadcast'])ids[id]=new El(id);
const board=new El('board');
const $=id=>id==='board'?board:ids[id.startsWith('bd-')?id.slice(3):id];
const document={getElementById:id=>$(id),createElement:tag=>new El(tag)};
const nameplate=n=>{let e=new El('img');e.title=n;return e};
const show={id:'smackdown',next:{date:'2026-10-23',title:'Toyota Arena, Ontario'},
 previous:{date:'2026-10-16',title:'Golden 1 Center Sacramento'}};
const names=['chelsea green','roxanne perez','giulia','alexa bliss'];
let rows=[{status:'REPORTED_UNVERIFIED',text:'Chelsea Green vs. Roxanne Perez',stipulation:'WWE Women Championship'},
 {status:'REPORTED_UNVERIFIED',text:'Giulia vs. Blake Monroe',stipulation:'Street Fight'}];
let appearances=[];
const data={shows:['raw','smackdown','nxt','aaa','tna'].map(id=>({id,next:{date:'2026-10-23'}}))};
let currentNames=names;
const roster=()=>currentNames;
const record={airdate:'2026-10-16',results:[
 {status:'REPORTED_UNVERIFIED',text:'Damian Priest defeated R-Truth via referee stoppage',match_type:'Singles Match'},
 {status:'REPORTED_UNVERIFIED',text:'Cody Rhodes defeated Baron Corbin via disqualification',match_type:'Singles Match'}
],developments:[
 {status:'REPORTED_UNVERIFIED',text:'Alexa Bliss and Tatum Paxley fought off Fatal Influence',type:'Women Tag Division'},
 {status:'REPORTED_UNVERIFIED',text:'Randy Orton attacked Cody Rhodes',type:'Cody Rhodes Rivalry'}]};
const construct=new Function('$','document','reportedRows','sdNamedCompetitors','sdApprovedPhoto','data','position','formatted','labels','abbrev','forceBroadcast','forceAfterBell','editorialRecap','sdPhotoOrder',
  html.slice(i,j)+'return {renderSdBroadcast,sdReviewedRecapTalent};');
const make=(position,bc,after,recap)=>construct($,document,(_,__,kind)=>kind==='matches'?rows:appearances,
  roster,nameplate,data,position,s=>s==='2026-10-16'?'FRIDAY, OCT 16':'FRIDAY, OCT 23',
  Object.fromEntries(data.shows.map(x=>[x.id,x.id.toUpperCase()])),s=>'10/23',bc,after,()=>recap,names);
let runtime=make(1,true,false,null);
runtime.renderSdBroadcast(show,'smackdown');
assert.equal(ids['sd-broadcast'].hidden,false);
assert.equal(ids['hero-note'].textContent,'WRESTLERS ON THIS REPORTED MATCH CARD');
assert.equal(ids['air-label'].textContent,'NEXT ON');
assert.equal(ids['prime-title'].textContent,'FEATURED MATCH · 2 / 2');
assert.equal(ids['others-title'].textContent,'OTHER FEATURED MATCHES');
assert.equal(ids.hero.children.filter(x=>x.className.startsWith('bd-photo')).length,3);
currentNames=[];
runtime=make(1,true,false,null);
runtime.renderSdBroadcast(show,'smackdown');
const archivalPhotos=ids.hero.children.filter(x=>x.className.startsWith('bd-photo'))
 .map(x=>x.children[0].title);
assert.deepEqual(archivalPhotos,['la knight','roman reigns','cody rhodes']);
assert(ids['hero-note'].textContent.includes('NOT ADVERTISED APPEARANCES'));
assert(ids['credit-left'].textContent.includes('DIEGO SERRANO'));
runtime=make(1,false,true,record);
runtime.renderSdBroadcast(show,'smackdown');
assert.equal(ids['air-label'].textContent,'AFTER THE BELL');
assert(!ids['hero-note'].textContent.includes('NOT ADVERTISED APPEARANCES'));
assert.equal(ids.hero.children.filter(x=>x.className.startsWith('bd-photo')).length,1);
assert.equal(ids.hero.children.find(x=>x.className.startsWith('bd-photo')).children[0].title,'alexa bliss');
assert.equal(ids.date.textContent,'FRIDAY, OCT 16');
assert.equal(ids['prime-title'].textContent,'RESULTS & FALLOUT · 2 / 2');
assert(ids.primary.textContent.includes('Cody Rhodes defeated Baron Corbin'));
assert(ids.side.textContent.includes('Randy Orton attacked Cody Rhodes'));
assert(ids.side.textContent.includes('Alexa Bliss and Tatum Paxley'));
assert(ids.notes.textContent.includes('Randy Orton attacked Cody Rhodes'));
assert(ids.ticker.textContent.includes('RESULTS & FALLOUT'));
assert(!ids.primary.textContent.includes('Chelsea Green vs. Roxanne Perez'));
assert.equal(ids['others-title'].textContent,'OTHER MATCH RESULTS');
assert.deepEqual(runtime.sdReviewedRecapTalent(record.results,record.developments),['alexa bliss']);
assert(ids['credit-left'].textContent.includes('DIEGO SERRANO'));
runtime=make(1,false,true,null);
runtime.renderSdBroadcast(show,'smackdown');
assert.equal(ids['prime-title'].textContent,'LATEST RESULTS');
assert(!ids.primary.textContent.includes('Cody Rhodes defeated Baron Corbin'));
assert(ids.primary.textContent.includes('RECAP INFORMATION UPDATING'));
assert.equal(ids.date.textContent,'FRIDAY, OCT 16');
rows=[];appearances=[];
console.log('V4.41 editorial archives vs match and recap attribution PASS');
