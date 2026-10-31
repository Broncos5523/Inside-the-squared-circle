const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const playlist=require('../web/staging/playlist-engine.js');
const root=path.resolve(__dirname,'../web/staging');
const programming=JSON.parse(fs.readFileSync(path.join(root,'data/programming.json')));
const actualDate=Date;
class Clock extends actualDate {constructor(...args){super(...(args.length?args:[programming.generated_at]));}static now(){return actualDate.parse(programming.generated_at);}}
function harness(search){
 const elements={},timers=new Map(),listeners={},stats={replacements:0,thumbnailNodes:0};let serial=0;
 class Node {
  constructor(id=''){this.id=id;this.childNodes=[];this.dataset={};this.style={};this.hidden=false;this.connected=true;this.srcdoc='';this.clientWidth=390;this.clientHeight=694;this.classes=new Set();this.classList={toggle:(k,enabled)=>{if(enabled===undefined)enabled=!this.classes.has(k);enabled?this.classes.add(k):this.classes.delete(k);},add:k=>this.classes.add(k),remove:k=>this.classes.delete(k),contains:k=>this.classes.has(k)};}
  append(...nodes){this.childNodes.push(...nodes);}
  replaceChildren(...nodes){this.childNodes=nodes;}
  cloneNode(){return new Node(this.id);}
  removeAttribute(name){delete this[name];}
  replaceWith(node){this.connected=false;elements[this.id]=node;stats.replacements++;}
  addEventListener(){}
  querySelector(selector){if(selector==='.screen')return elements.screen;return null;}
  scrollIntoView(){}
 }
 for(const id of ['preview','screen','review-panel','active-panel','gallery','rotate','board','loading','status','duration','board-title','board-count','library-tab','active-tab','watch-active','active-summary','active-list','feed-stamp','previous','next','fullscreen','stats','filters'])elements[id]=new Node(id);
 elements.duration.value='45';
 const body=new Node();
 const document={body,getElementById:id=>elements[id],querySelectorAll:()=>[],addEventListener:(name,fn)=>{listeners['document:'+name]=fn;},createElement:tag=>{if(tag==='img')stats.thumbnailNodes++;return new Node();}};
 const window={innerHeight:694,addEventListener:(name,fn)=>{listeners[name]=fn;}};
 const location={href:'https://broncos5523.github.io/Inside-the-squared-circle/staging/'+search,hostname:'broncos5523.github.io',search};
 const context={window,document,location,URL,URLSearchParams,TextDecoder,Date:Clock,Intl,ISCPlaylist:playlist,history:{pushState(){}},
  setTimeout:(fn,ms)=>{const id=++serial;timers.set(id,{fn,ms});return id;},clearTimeout:id=>timers.delete(id),setInterval:()=>++serial,
  fetch:async value=>{const name=decodeURI(new URL(String(value),location.href).pathname).replace('/Inside-the-squared-circle/staging/','');const file=path.join(root,name);return {ok:fs.existsSync(file),json:async()=>JSON.parse(fs.readFileSync(file)),arrayBuffer:async()=>{const b=fs.readFileSync(file);return b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength);}};}};
 vm.runInNewContext(fs.readFileSync(path.join(root,'board-adapter.js'),'utf8'),context);
 context.ISCBoardAdapter=window.ISCBoardAdapter;
 vm.runInNewContext(fs.readFileSync(path.join(root,'review.js'),'utf8'),context);
 return {window,elements,timers,stats};
}
async function settle(check){for(let i=0;i<100;i++){if(check())return;await new Promise(setImmediate);}throw Error('Player did not settle');}
function advance(h){const [id,timer]=h.timers.entries().next().value||[];assert.ok(timer,'rotation timer absent');h.timers.delete(id);timer.fn();}
test('iPhone TV entry starts one board and never constructs the 68-image design gallery',async()=>{
 const h=harness('?view=tv');
 await settle(()=>h.elements.board.srcdoc&&h.timers.size);
 assert.equal(h.window.__iscReview.getCurrent().id,'weekly-results-aaa');
 assert.equal(h.stats.replacements,1,'startup must not load the first board twice');
 assert.equal(h.stats.thumbnailNodes,0);
 assert.equal(h.elements.gallery.childNodes.length,0);
});
test('automatic playback gets past AAA, wraps the playlist, and disposes the prior iframe each time',async()=>{
 const h=harness('?view=tv');await settle(()=>h.elements.board.srcdoc&&h.timers.size);
 const ids=Array.from(h.window.__iscReview.getActive(),e=>e.id),seen=[h.window.__iscReview.getCurrent().id];
 for(let i=0;i<ids.length+1;i++){
  const previous=h.elements.board,priorCount=h.stats.replacements;
  advance(h);await settle(()=>h.stats.replacements>priorCount&&h.elements.board.srcdoc&&h.timers.size);
  assert.equal(previous.connected,false,'previous board remains attached');
  assert.equal(h.timers.size,1,'rotation timers accumulated');
  seen.push(h.window.__iscReview.getCurrent().id);
 }
 assert.equal(seen[1],'weekly-results-raw');
 assert.equal(seen[ids.length],ids[0]);
 assert.equal(h.stats.thumbnailNodes,0);
});
test('starting TV playback from the playlist menu also avoids thumbnail construction',async()=>{
 const h=harness('');await settle(()=>h.window.__iscReview?.getActive().length);
 h.elements['watch-active'].onclick();await settle(()=>h.elements.board.srcdoc&&h.timers.size);
 assert.equal(h.stats.thumbnailNodes,0);
 assert.equal(h.elements['review-panel'].hidden,false);
});
