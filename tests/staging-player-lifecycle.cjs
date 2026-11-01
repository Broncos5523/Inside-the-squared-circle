const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {webcrypto}=require('node:crypto');
const playlist=require('../web/staging/playlist-engine.js');
const root=path.resolve(__dirname,'../web/staging');
const programming=JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures/staging-programming-20261031.json')));
const actualDate=Date;
class Clock extends actualDate {constructor(...args){super(...(args.length?args:[Clock.now()]));}static now(){return actualDate.parse(programming.generated_at)+(Clock.offset||0);}}
function harness(search,options={}){
 Clock.offset=0;
 let rememberedUrl='';const elements={},timers=new Map(),listeners={},stats={replacements:0,thumbnailNodes:0,sourceRequests:[]};let serial=0;
 class Node {
  constructor(id=''){this.id=id;this.contentWindow={};this.childNodes=[];this.dataset={};this.style={};this.hidden=false;this.connected=true;this.srcdoc='';this.clientWidth=390;this.clientHeight=694;this.classes=new Set();this.classList={toggle:(k,enabled)=>{if(enabled===undefined)enabled=!this.classes.has(k);enabled?this.classes.add(k):this.classes.delete(k);},add:k=>this.classes.add(k),remove:k=>this.classes.delete(k),contains:k=>this.classes.has(k)};}
  append(...nodes){this.childNodes.push(...nodes);}
  replaceChildren(...nodes){this.childNodes=nodes;}
  cloneNode(){return new Node(this.id);}
  removeAttribute(name){if(name==='srcdoc')this.srcdoc='';else delete this[name];}
  replaceWith(node){this.connected=false;elements[this.id]=node;stats.replacements++;}
  addEventListener(){}
  querySelector(selector){if(selector==='.screen')return elements.screen;return null;}
  scrollIntoView(){}
 }
 for(const id of ['preview','screen','review-panel','active-panel','gallery','rotate','board','loading','status','duration','board-title','board-count','library-tab','active-tab','watch-active','active-summary','active-list','feed-stamp','previous','next','fullscreen','stats','filters'])elements[id]=new Node(id);
 elements.duration.value='45';
 elements.preview.clientWidth=options.width||390;elements.preview.clientHeight=options.height||694;
 const body=new Node();
 const document={body,getElementById:id=>elements[id],querySelectorAll:()=>[],addEventListener:(name,fn)=>{listeners['document:'+name]=fn;},createElement:tag=>{if(tag==='img')stats.thumbnailNodes++;return new Node();}};
 const window={crypto:webcrypto,innerHeight:options.height||694,addEventListener:(name,fn)=>{listeners[name]=fn;}};
 const location={href:'https://broncos5523.github.io/Inside-the-squared-circle/staging/'+search,hostname:'broncos5523.github.io',search};
 const context={window,document,location,URL,URLSearchParams,TextDecoder,crypto:webcrypto,Date:Clock,Intl,ISCPlaylist:playlist,history:{pushState(){},replaceState(state,title,url){rememberedUrl=String(url);}},
  setTimeout:(fn,ms)=>{const id=++serial;timers.set(id,{fn,ms});return id;},clearTimeout:id=>timers.delete(id),setInterval:()=>++serial,
  fetch:async (value,init)=>{const url=new URL(String(value),location.href),name=decodeURI(url.pathname).replace('/Inside-the-squared-circle/staging/','');const file=path.join(root,name);const source=name.startsWith('delivery/');let corrupt=false;if(source){stats.sourceRequests.push({url:url.href,cache:init?.cache});corrupt=options.corruptSource?.(name,stats.sourceRequests.length)===true;}return {ok:fs.existsSync(file),json:async()=>name==='data/programming.json'?JSON.parse(JSON.stringify(programming)):JSON.parse(fs.readFileSync(file)),arrayBuffer:async()=>{const b=corrupt?Buffer.from('<html>older cached board</html>'):fs.readFileSync(file);return b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength);}};}};
 vm.runInNewContext(fs.readFileSync(path.join(root,'board-adapter.js'),'utf8'),context);
 context.ISCBoardAdapter=window.ISCBoardAdapter;
 vm.runInNewContext(fs.readFileSync(path.join(root,'review.js'),'utf8'),context);
 return {window,elements,timers,stats,getUrl:()=>rememberedUrl,resize:(width,height)=>{elements.preview.clientWidth=width;elements.preview.clientHeight=height;window.innerHeight=height;listeners.resize();},advanceTime:ms=>{Clock.offset+=ms;},message:data=>listeners.message({source:elements.board.contentWindow,data})};
}
async function settle(check){for(let i=0;i<2000;i++){if(check())return;await new Promise(setImmediate);}throw Error('Player did not settle');}
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

test('AAA cycle completion advances to RAW even when the long parent timeout never fires',async()=>{
 const h=harness('?view=tv');await settle(()=>h.elements.board.srcdoc&&h.timers.size);
 h.timers.clear();h.advanceTime(98000);
 const old=h.elements.board;
 h.message({type:'isc-board-cycle',id:'weekly-results-aaa',index:1,total:7,complete:true});
 await settle(()=>h.elements.board!==old&&h.elements.board.srcdoc);
 assert.equal(h.window.__iscReview.getCurrent().id,'weekly-results-raw');
});
test('the final AAA card arms a short switch instead of restarting all seven cards',async()=>{
 const h=harness('?view=tv');await settle(()=>h.elements.board.srcdoc&&h.timers.size);
 h.advanceTime(84000);
 h.message({type:'isc-board-cycle',id:'weekly-results-aaa',index:7,total:7,complete:false});
 assert.equal(h.timers.size,1);
 assert.equal([...h.timers.values()][0].ms,14000);
 advance(h);await settle(()=>h.window.__iscReview.getCurrent().id==='weekly-results-raw');
});
test('manual pause ignores the embedded card-cycle completion signal',async()=>{
 const h=harness('?view=tv');await settle(()=>h.elements.board.srcdoc&&h.timers.size);
 h.elements.rotate.onclick();h.advanceTime(98000);
 h.message({type:'isc-board-cycle',id:'weekly-results-aaa',index:1,total:7,complete:true});
 assert.equal(h.window.__iscReview.getCurrent().id,'weekly-results-aaa');
 assert.equal(h.timers.size,0);
});

test('TNA, Halloween Havoc and Crown Jewel can each start active playback directly',async()=>{
 const ids=['weekly-results-tna','preview-nxt_halloween_havoc_preview_v4_approved_locked_20261027-night_one','preview-crown_jewel_preview_v1_approved_locked_20261027-night_one'];
 for(const id of ids){
  const h=harness('?view=tv&mode=active&id='+id);await settle(()=>h.elements.board.srcdoc&&h.timers.size);
  assert.equal(h.window.__iscReview.getCurrent().id,id);
  assert.equal(new URL(h.getUrl()).searchParams.get('id'),id);
  assert.equal(h.timers.size,1,'direct start paused automatic rotation');
  const before=h.elements.board;advance(h);await settle(()=>h.elements.board!==before&&h.elements.board.srcdoc);
  assert.notEqual(h.window.__iscReview.getCurrent().id,id);
 }
});
test('active deep links cannot bypass source gates to play an unrelated archived design',async()=>{
 const h=harness('?view=tv&mode=active&id=champions-raw');await settle(()=>h.elements.board.srcdoc&&h.timers.size);
 assert.equal(h.window.__iscReview.getCurrent().id,'weekly-results-aaa');
});

test('a mismatched RAW transfer after AAA retries an immutable source without using the browser cache',async()=>{
 const library=JSON.parse(fs.readFileSync(path.join(root,'library.json')));
 const raw=library.records.find(r=>r.id==='weekly-results-raw');
 let rawRequests=0;
 const h=harness('?view=tv',{corruptSource:name=>name.includes(raw.delivery_sha256)&&++rawRequests===1});
 await settle(()=>h.elements.board.srcdoc&&h.timers.size);
 advance(h);
 await settle(()=>h.window.__iscReview.getCurrent().id==='weekly-results-raw'&&h.elements.board.srcdoc&&h.timers.size);
 const requests=h.stats.sourceRequests.filter(r=>r.url.includes(raw.delivery_sha256));
 assert.equal(requests.length,2);
 assert.ok(requests.every(r=>r.cache==='no-store'));
 assert.ok(new URL(requests[0].url).pathname.endsWith('/delivery/payloads/'+raw.delivery_sha256+'.bin'));
 assert.ok(new URL(requests[1].url).searchParams.has('retry'));
 assert.ok(h.elements.board.srcdoc.includes('RAW Results'));
 assert.ok(!h.elements.board.srcdoc.includes('older cached board'));
});

test('a persistently mismatched source never renders and does not prevent the next valid board',async()=>{
 const library=JSON.parse(fs.readFileSync(path.join(root,'library.json')));
 const raw=library.records.find(r=>r.id==='weekly-results-raw');
 const h=harness('?view=tv&id=weekly-results-raw',{corruptSource:name=>name.includes(raw.delivery_sha256)});
 await settle(()=>h.elements.loading.textContent?.includes('integrity check failed')&&h.timers.size);
 assert.equal(h.elements.board.srcdoc,'');
 assert.equal(h.stats.sourceRequests.length,2,'retry must remain bounded');
 advance(h);
 await settle(()=>h.window.__iscReview.getCurrent().id==='weekly-results-nxt'&&h.elements.board.srcdoc);
});

test('a browser without SHA-256 support cannot silently skip source verification',async()=>{
 const h=harness('?view=tv');h.window.crypto=null;
 await settle(()=>h.elements.loading.textContent?.includes('cannot verify the approved board'));
 assert.equal(h.elements.board.srcdoc,'');
 assert.equal(h.stats.sourceRequests.length,0);
});

test('ONN landscape TV output rotates the approved portrait surface to fill a physically upright TV',async()=>{
 const h=harness('?view=tv',{width:1280,height:720});
 await settle(()=>h.elements.board.srcdoc&&h.timers.size);
 assert.equal(h.elements.screen.dataset.rotation,'left');
 assert.equal(h.elements.screen.style.top,'50%');
 assert.match(h.elements.screen.style.transform,/rotate\(-90deg\) scale\(1\)/);
 const frame=h.elements.board,requests=h.stats.sourceRequests.length;
 h.resize(720,1280);
 assert.equal(h.elements.screen.dataset.rotation,'none');
 assert.equal(h.elements.screen.style.top,'0');
 assert.equal(h.elements.screen.style.transform,'translateX(-50%) scale(1)');
 assert.equal(h.elements.board,frame,'orientation changes must not rebuild or restart the board');
 assert.equal(h.stats.sourceRequests.length,requests);
});

test('rotation overrides and review mode preserve normal landscape and phone playback',async()=>{
 for(const [search,turn,pattern] of [
  ['?view=tv&rotate=none','none',/translateX/],
  ['?view=tv&rotate=right','right',/rotate\(90deg\)/],
  ['','none',/translateX/]
 ]){
  const h=harness(search,{width:1280,height:720});
  await settle(()=>h.window.__iscReview?.getActive().length);
  assert.equal(h.elements.screen.dataset.rotation,turn);
  assert.match(h.elements.screen.style.transform,pattern);
 }
 const phone=harness('?view=tv',{width:390,height:844});
 await settle(()=>phone.elements.board.srcdoc);
 assert.equal(phone.elements.screen.dataset.rotation,'none');
});
