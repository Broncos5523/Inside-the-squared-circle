const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.resolve(__dirname,'../web/staging');
const library=JSON.parse(fs.readFileSync(path.join(root,'library.json')));
const routes=JSON.parse(fs.readFileSync(path.join(root,'asset-routes.json')));
const data=JSON.parse(fs.readFileSync(path.join(root,'data/programming.json')));
const base='https://player.example/';
function runtime(show){
 const host={};
 vm.runInNewContext(fs.readFileSync(path.join(root,'board-adapter.js'),'utf8'),{window:host,URL});
 const record=library.records.find(r=>r.id==='weekly-results-'+show);
 const original=fs.readFileSync(path.join(root,record.delivery),'utf8');
 const compiled=host.ISCBoardAdapter.build(original,record,routes,base,'active',data.feeds);
 const script=compiled.match(/<base[^>]*><script>([\s\S]*?)<\/script>/)[1];
 class Element {setAttribute(k,v){this[k]=v;} getAttribute(k){return this[k]||null;}}
 class HTMLImageElement extends Element {set src(v){this._src=v;}get src(){return this._src;}}
 class CSSStyleDeclaration {set backgroundImage(v){this._image=v;}get backgroundImage(){return this._image;}setProperty(k,v){this[k]=v;}}
 const window={fetch:async()=>{},addEventListener(){}};
 vm.runInNewContext(script,{window,URL,HTMLImageElement,Element,CSSStyleDeclaration,MutationObserver:class{observe(){}},document:{},Response,Promise});
 return {style:()=>new CSSStyleDeclaration(),image:()=>new HTMLImageElement(),compiled};
}
test('NXT and SmackDown resolve every declared winner portrait from either approved asset folder',()=>{
 for(const show of ['nxt','smackdown','raw']){
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
 const r=runtime('nxt'),style=r.style();style.backgroundImage='url(assets/portraits/chantel-monroe.png)';
 assert.equal(style.backgroundImage,'url(assets/portraits/chantel-monroe.png)');
});
test('a results iframe receives its own episode feed without retaining other show feeds',()=>{
 const {compiled}=runtime('smackdown');
 assert.match(compiled,/"smackdown-verified-results.json"/);
 assert.doesNotMatch(compiled,/"nxt-verified-results.json"/);
 assert.doesNotMatch(compiled,/"raw-verified-results.json"/);
});
