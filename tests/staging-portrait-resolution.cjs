const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.resolve(__dirname,'../web/staging');
const library=JSON.parse(fs.readFileSync(path.join(root,'library.json')));
const routes=JSON.parse(fs.readFileSync(path.join(root,'asset-routes.json')));
const data=JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures/staging-programming-20261031.json')));
const base='https://player.example/';
function runtime(show,feeds=data.feeds){
 const host={};
 vm.runInNewContext(fs.readFileSync(path.join(root,'board-adapter.js'),'utf8'),{window:host,URL});
 const record=library.records.find(r=>r.id==='weekly-results-'+show);
 const original=fs.readFileSync(path.join(root,record.delivery),'utf8');
 const compiled=host.ISCBoardAdapter.build(original,record,routes,base,'active',feeds);
 const script=compiled.match(/<base[^>]*><script>([\s\S]*?)<\/script>/)[1];
 class Element {setAttribute(k,v){this[k]=v;} getAttribute(k){return this[k]||null;}}
 class HTMLImageElement extends Element {set src(v){this._src=v;}get src(){return this._src;}}
 class CSSStyleDeclaration {set backgroundImage(v){this._image=v;}get backgroundImage(){return this._image;}setProperty(k,v){this[k]=v;}}
 const listeners={},messages=[],counter={textContent:'01 / 07'};let cycleObserver;
 const window={fetch:async()=>{},parent:{postMessage:message=>messages.push(message)},addEventListener:(name,fn)=>{listeners[name]=fn;}};
 vm.runInNewContext(script,{window,URL,HTMLImageElement,Element,CSSStyleDeclaration,MutationObserver:class{constructor(fn){this.fn=fn;}observe(target){if(target===counter)cycleObserver=this.fn;}},document:{getElementById:id=>id==='result-slidecount'?counter:null},Response,Promise});
 return {style:()=>new CSSStyleDeclaration(),image:()=>new HTMLImageElement(),compiled,messages,feed:()=>window.fetch('./data/'+show+'-verified-results.json'),startCycle:()=>listeners.DOMContentLoaded(),card:index=>{counter.textContent=String(index).padStart(2,'0')+' / 07';cycleObserver();}};
}
test('weekly results resolve every declared winner portrait from either approved asset folder',()=>{
 for(const show of ['nxt','smackdown','raw','aaa','tna']){
  const r=runtime(show);
  for(const segment of data.feeds[show+'-verified-results.json'].programs[0].segments){
   for(const slug of segment.portraits){
    for(const folder of ['portraits','portrait-display']){
     const style=r.style();style.backgroundImage='url(assets/'+folder+'/'+slug+'.png)';
     const resolved=style.backgroundImage.match(/url\("?([^"\)]+)"?\)/)[1];
     assert.ok(resolved.startsWith(base+'originals/shared/'),show+': '+slug+' '+folder);
     assert.ok(fs.existsSync(path.join(root,new URL(resolved).pathname)),slug+' references missing bytes');
    }
   }
  }
 }
});
test('missing winner artwork stays missing rather than borrowing a different wrestler',()=>{
 const r=runtime('nxt'),style=r.style();style.backgroundImage='url(assets/portraits/unmapped-wrestler.png)';
 assert.equal(style.backgroundImage,'url(assets/portraits/unmapped-wrestler.png)');
});
test('Chantel Monroe and all Zero aliases resolve to the exact supplied artwork',()=>{
 const crypto=require('node:crypto');
 for(const [show,slugs,file] of [
  ['nxt',['chantel-monroe'],'38d20c88e02da1204f899dfed6d311dff8a7579d9e6f830127dfca6ce089f4ad.webp'],
  ['tna',['agent-zero','zero','zer0'],'a85eafc5364a482e2e18e3681f6910f157c3c9d3a3073baae37c96e279102186.png']
 ]){
  const bytes=fs.readFileSync(path.join(root,'originals/shared',file));
  assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),file.split('.')[0]);
  const r=runtime(show);
  for(const slug of slugs)for(const folder of ['portraits','portrait-display']){
   const style=r.style();style.backgroundImage='url(assets/'+folder+'/'+slug+'.png)';
   assert.equal(style.backgroundImage,'url("'+base+'originals/shared/'+file+'")');
  }
 }
});
test('older current feeds acquire approved portraits without changing episode facts or caller data',async()=>{
 const {addApprovedPortraits}=await import('../proof/staging/approved-portrait-additions.mjs');
 for(const [show,slug] of [['nxt','chantel-monroe'],['tna','agent-zero']]){
  const feeds=JSON.parse(JSON.stringify(data.feeds));
  const program=feeds[show+'-verified-results.json'].programs[0];
  program.segments[1].portraits=[];
  const before=JSON.stringify(feeds),expected=JSON.parse(JSON.stringify(program));
  expected.segments[1].portraits=[slug];
  const got=await (await runtime(show,feeds).feed()).json();
  assert.deepEqual(got.programs[0],expected);
  assert.equal(JSON.stringify(feeds),before);
  assert.deepEqual(addApprovedPortraits(program),expected);
 }
});
test('a results iframe receives its own episode feed without retaining other show feeds',()=>{
 const {compiled}=runtime('smackdown');
 assert.match(compiled,/"smackdown-verified-results.json"/);
 assert.doesNotMatch(compiled,/"nxt-verified-results.json"/);
 assert.doesNotMatch(compiled,/"raw-verified-results.json"/);
});

test('the embedded AAA reporter signals a completed card cycle on the seven-to-one boundary',()=>{
 const r=runtime('aaa');r.startCycle();
 for(let card=2;card<=7;card++)r.card(card);
 assert.equal(r.messages.length,7);
 assert.equal(r.messages[6].index,7);
 assert.equal(r.messages[6].complete,false);
 r.card(1);
 assert.equal(r.messages[7].type,'isc-board-cycle');
 assert.equal(r.messages[7].id,'weekly-results-aaa');
 assert.equal(r.messages[7].complete,true);
});
test('Big Mami uses the supplied original PNG in current playback and archived review',async()=>{
 const crypto=require('node:crypto');
 const asset='26189e3adbcb40f6296f03fca6098606fc931f6e907308d53e6fd3f79d5a3b13';
 const image=fs.readFileSync(path.join(root,'originals/shared/'+asset+'.png'));
 assert.equal(crypto.createHash('sha256').update(image).digest('hex'),asset);
 const host={};vm.runInNewContext(fs.readFileSync(path.join(root,'board-adapter.js'),'utf8'),{window:host,URL});
 const row=library.records.find(r=>r.id==='weekly-results-aaa');
 const original=fs.readFileSync(path.join(root,row.delivery),'utf8');
 const embedded=html=>JSON.parse(html.match(/<script id="review-verified-results" type="application\/json">([\s\S]*?)<\/script>/)[1]);
 assert.deepEqual(embedded(original).programs[0].segments.find(s=>s.id==='big-mami-return').portraits,[]);
 const archive=host.ISCBoardAdapter.build(original,row,routes,base,'archive',{});
 assert.deepEqual(embedded(archive).programs[0].segments.find(s=>s.id==='big-mami-return').portraits,['big-mami']);
 const {addApprovedPortraits}=await import('../proof/staging/approved-portrait-additions.mjs');
 const approved=addApprovedPortraits(embedded(original).programs[0]);
 assert.deepEqual(approved.segments.find(s=>s.id==='big-mami-return').portraits,['big-mami']);
});
