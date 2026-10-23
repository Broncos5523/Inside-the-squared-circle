const fs=require('fs'),assert=require('node:assert/strict');
const content=fs.readFileSync('web/preview-v4-39-smackdown-full-broadcast.html','utf8');
const i=content.indexOf('  const bd=(id)=>');
const j=content.indexOf('  function sdMatchHero(text){',i);
assert(i>0&&j>i,'Exact rendering function not located');
class Element{
 constructor(tag){this.tag=tag;this.children=[];this.hidden=true;this.className='';this._text='';this.classList={toggle:()=>{},add:()=>{},remove:()=>{}}}
 replaceChildren(...children){this.children=children;this._text=''}
 append(...children){this.children.push(...children)}
 set textContent(text){this._text=String(text);this.children=[]}
 get textContent(){return this._text+this.children.map(x=>x.textContent||'').join(' ')}
 querySelector(sel){if(sel==='.bd-photo')return this.children.find(x=>x.className.startsWith('bd-photo'))||null;return null}
}
const ids={};for(const id of ['hero','date','time','primary','side','others','notes','prime-title','side-title','notes-title','ticker','dates','credit-left','sd-broadcast'])ids[id]=new Element(id);
const board=new Element('board');
const photos=[];
const $=id=>id==='board'?board:ids[id];
const document={getElementById:id=>$(id),createElement:t=>new Element(t)};
const players=['chelsea green','roxanne perez','giulia','alexa bliss'];
let matches=[
 {text:'Chelsea Green vs. Roxanne Perez',stipulation:'SINGLES MATCH'},
 {text:'Giulia vs. Blake Monroe',stipulation:'STREET FIGHT'},
 {text:'Alexa Bliss & Tatum Paxley vs. Michin & B-Fab',stipulation:'WWE WOMEN TAG TITLE MATCH'},
 {text:'MFTs vs. Bakusai',stipulation:'TAG TEAM MATCH'}
];
let appearances=[];
const getRows=(_,__,kind)=>kind==='matches'?matches:appearances;
const named=()=>players;
const image=name=>{const el=new Element('img');el.name=name;photos.push(name);return el};
const shows=['raw','smackdown','nxt','aaa','tna'].map(id=>({id,next:{date:'2026-10-23',title:'Toyota Arena, Ontario, CA'}}));
const fn=new Function('$','document','reportedRows','sdNamedCompetitors','sdApprovedPhoto','data','position','formatted','labels','abbrev','forceBroadcast',content.slice(i,j)+'return renderSdBroadcast;');
const render=fn($,document,getRows,named,image,{shows},1,s=>'FRIDAY, OCT 23',Object.fromEntries(shows.map(s=>[s.id,s.id.toUpperCase()])),s=>'10/23',true);
render(shows[1],'smackdown');
assert.equal(ids['sd-broadcast'].hidden,false);
assert.equal(ids.hero.children.filter(x=>x.className.startsWith('bd-photo')).length,3);
assert.deepEqual(photos.slice(0,3),['roxanne perez','giulia','alexa bliss']);
assert.equal(ids['prime-title'].textContent,'FEATURED MATCH · 2 / 4');
assert.equal(ids['notes-title'].textContent,'MORE ON THE CARD');
assert.equal(ids.notes.children.length,3);
assert.equal(ids.others.children.length,3);
assert.equal(ids.dates.children.length,5);
assert.equal(ids['side-title'].textContent,'CHAMPIONSHIP WATCH');
assert(ids.ticker.textContent.includes('Giulia vs. Blake Monroe'));
assert(!ids.notes.textContent.includes('RETURNING TONIGHT'));
appearances=[{text:'Cody Rhodes',type:'SPECIAL APPEARANCE'}];
render(shows[1],'smackdown');
assert.equal(ids['notes-title'].textContent,'ADVERTISED APPEARANCES');
assert.equal(ids.notes.children[0].textContent,'Cody Rhodes');
matches=[];appearances=[];render(shows[1],'smackdown');
assert.equal(ids['prime-title'].textContent,'UPCOMING MATCH CARD');
assert(!ids.primary.textContent.includes('Giulia vs'));
console.log('V4.39 real-data/no-fabrications/full-broadcast rendering PASS');
