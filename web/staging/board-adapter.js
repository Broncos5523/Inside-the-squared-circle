(function(root){
 'use strict';
 function shim(config){
  var map=config.routes,logical=new URL(config.logical,'https://isc.invalid'),nativeFetch=window.fetch.bind(window);
  function resolve(value){
   if(typeof value!=='string'||!value||/^(?:data:|blob:|#)/i.test(value))return value;
   try{var url=new URL(value,logical),key=decodeURI(url.pathname),mapped=map[key];
    if(!mapped&&key.indexOf('/assets/')===0)mapped=map[logical.pathname.slice(0,logical.pathname.lastIndexOf('/')+1)+key.slice(1)];
    if(!mapped&&config.mode==='active'){
     var photo=/\/assets\/(?:portraits|portrait-display)\/([a-z0-9-]+)\.png$/.exec(key);
     if(photo&&config.resultPortraits&&config.resultPortraits[photo[1]])return config.resultPortraits[photo[1]];
     var belt=/\/assets\/belts-display\/([a-z0-9_-]+)\.png$/.exec(key);
     if(belt&&config.resultBelts&&config.resultBelts[belt[1]+'.png'])return config.resultBelts[belt[1]+'.png'];
    }
    return mapped?new URL('originals'+mapped,config.base).href:value;
   }catch(_){return value;}
  }
  function css(value){return typeof value==='string'?value.replace(/url\(\s*(['"]?)([^)'"\r\n]+)\1\s*\)/g,function(all,q,u){var v=resolve(u);return v===u?all:'url("'+v+'")';}):value;}
  var descriptor=Object.getOwnPropertyDescriptor(HTMLImageElement.prototype,'src');
  if(descriptor&&descriptor.set)Object.defineProperty(HTMLImageElement.prototype,'src',{get:descriptor.get,set:function(v){descriptor.set.call(this,resolve(v));},configurable:true});
  var attr=Element.prototype.setAttribute;
  Element.prototype.setAttribute=function(name,value){var n=String(name).toLowerCase();return attr.call(this,name,n==='src'||n==='href'?resolve(String(value)):n==='style'?css(String(value)):value);};
  ['background','backgroundImage','cssText'].forEach(function(name){var d=Object.getOwnPropertyDescriptor(CSSStyleDeclaration.prototype,name);if(d&&d.set)Object.defineProperty(CSSStyleDeclaration.prototype,name,{get:d.get,set:function(v){d.set.call(this,css(v));},configurable:true});});
  var prop=CSSStyleDeclaration.prototype.setProperty;
  CSSStyleDeclaration.prototype.setProperty=function(n,v,p){return prop.call(this,n,css(v),p);};
  function patch(el){if(!el||el.nodeType!==1)return;['src','href'].forEach(function(n){var v=el.getAttribute(n);if(v){var r=resolve(v);if(v!==r)attr.call(el,n,r);}});var st=el.getAttribute('style');if(st){var c=css(st);if(c!==st)attr.call(el,'style',c);}}
  new MutationObserver(function(ms){ms.forEach(function(m){if(m.type==='attributes')patch(m.target);else Array.prototype.forEach.call(m.addedNodes,function(n){patch(n);if(n.querySelectorAll)Array.prototype.forEach.call(n.querySelectorAll('[src],[href],[style]'),patch);});});}).observe(document,{childList:true,subtree:true,attributes:true,attributeFilter:['src','href','style']});
  window.fetch=function(input,options){
   var url=typeof input==='string'?input:input.url;
   // Approved results HTML fetches ./data/show-verified-results.json. In
   // about:srcdoc those paths are not hosted by GitHub, so serve ONLY this
   // source-validated player feed in memory rather than stale local review data.
   if(config.mode==='active'){
    var resultName=/(?:^|\/)data\/([a-z0-9-]+-verified-results\.json)(?:\?|$)/i.exec(String(url));
    if(resultName&&Object.prototype.hasOwnProperty.call(config.feeds,resultName[1]))
     return Promise.resolve(new Response(JSON.stringify(config.feeds[resultName[1]]),{status:200,headers:{'Content-Type':'application/json'}}));
   }
   if(/broncos5523\.github\.io\/Inside-the-squared-circle\/data\//i.test(url)){
    var name=new URL(url).pathname.split('/').pop();
    if(config.mode==='active'&&Object.prototype.hasOwnProperty.call(config.feeds,name))return Promise.resolve(new Response(JSON.stringify(config.feeds[name]),{status:200,headers:{'Content-Type':'application/json'}}));
    return Promise.resolve(new Response('{}',{status:404,headers:{'Content-Type':'application/json'}}));
   }
   var remapped=resolve(url);return nativeFetch(remapped!==url?remapped:input,options);
  };
  if(config.night){var interval=window.setInterval.bind(window);window.setInterval=function(fn,ms){if(typeof fn==='function'&&/currentCard\+\+/.test(fn.toString()))return 0;return interval.apply(window,arguments);};}
  // A results board reports its own card progress. This gives the host an
  // independent completion signal if a long parent timeout is delayed.
  var cycleReporterInstalled=false;
  function installCycleReporter(){
   if(cycleReporterInstalled||config.mode!=='active'||!config.weeklyResults)return;
   var counter=document.getElementById('result-slidecount')||document.getElementById('counter');
   if(!counter)return;
   cycleReporterInstalled=true;
   var lastIndex=0,lastTotal=0;
   function report(){
    var match=/^\s*(\d+)\s*\/\s*(\d+)\s*$/.exec(counter.textContent||'');
    if(!match)return;
    var index=Number(match[1]),total=Number(match[2]);
    if(index<1||index>total||total>100)return;
    if(total!==lastTotal){lastIndex=0;lastTotal=total;}
    if(index===lastIndex)return;
    var complete=lastIndex===total&&index===1;
    lastIndex=index;
    window.parent.postMessage({type:'isc-board-cycle',id:config.id,index:index,total:total,complete:complete},'*');
   }
   new MutationObserver(report).observe(counter,{childList:true,subtree:true,characterData:true});
   report();
  }
  window.addEventListener('DOMContentLoaded',installCycleReporter,{once:true});
  // Archive content never silently refreshes into a different episode.
  // Populate approved event layouts with ONLY officially verified announcements.
  // The original HTML, styling, belts and graphical assets remain untouched on disk.
  function populateOfficialEvent(){
   var event=config.officialEvent;
   if(config.mode!=='active'||!event||!event.cards||event.cards.length!==3)return;
   var halloween=event.event_id==='nxt-halloween-havoc-2026';
   var crown=event.event_id==='wwe-crown-jewel-2026';
   if(!halloween&&!crown)return;
   var cards=Array.prototype.slice.call(document.querySelectorAll(halloween?'.panel section.match':'.matches section.match'));
   if(cards.length!==event.cards.length)return;
   event.cards.forEach(function(data,i){
    var card=cards[i],title=card.querySelector(halloween?'header':'.heading');
    if(title)title.textContent=data.heading;
    var belt=card.querySelector('img.belt');
    if(belt&&!data.belt)belt.style.visibility='hidden';
    if(halloween){
     var people=card.querySelectorAll('.competitor'),names=card.querySelectorAll('.competitor span');
     if(people.length===2&&names.length===2){
      names[0].textContent=data.left.toUpperCase();
      names[1].textContent=data.right.toUpperCase();
      var images=[people[0].querySelector('img'),people[1].querySelector('img')];
      if(images[0]&&data.left_image)images[0].src=data.left_image;
      if(images[1]&&data.right_image)images[1].src=data.right_image;
     }
     var foot=card.querySelector('footer');if(foot)foot.textContent=data.footer||'OFFICIAL WWE MATCH ANNOUNCEMENT';
    }else{
     var left=card.querySelector('.fighter.left'),right=card.querySelector('.fighter.right');
     if(left&&data.left_image)left.src=data.left_image;
     if(right&&data.right_image)right.src=data.right_image;
     var namesEl=card.querySelector('.names');
     if(namesEl){
      var vs=document.createElement('strong');vs.textContent='VS';
      namesEl.replaceChildren(document.createTextNode(data.left.toUpperCase()+' '),vs,document.createTextNode(' '+data.right.toUpperCase()));
     }
    }
   });
   var note=document.querySelector(halloween?'.note':'.disclaimer');
   if(note)note.textContent='OFFICIAL WWE MATCH CARD • SUBJECT TO CHANGE';
   var notice=document.querySelector('.notice');
   if(notice)notice.textContent='OFFICIAL WWE EVENT PREVIEW';
  }
  window.addEventListener('load',function(){setTimeout(function(){
   installCycleReporter();
   populateOfficialEvent();
   if(config.mode==='active'){
    var venue=document.getElementById('wb-venue'),city=document.getElementById('wb-city');
    var oldLocation=[venue&&venue.textContent,city&&city.textContent].filter(Boolean);
    if(config.live_preview){
     var locationNodes=[venue,city,document.getElementById('wb-tile-top'),document.getElementById('wb-tile-bottom')];
     var locationText=config.current_location?[config.current_location.arena||'',config.current_location.city||'','LIVE FROM','']:['','','',''];
     var repairLocation=function(){locationNodes.forEach(function(node,i){if(node&&node.textContent!==locationText[i])node.textContent=locationText[i];});};
     repairLocation();locationNodes.forEach(function(node){if(node)new MutationObserver(repairLocation).observe(node,{childList:true,subtree:true,characterData:true});});
    }
    var ticker=document.getElementById('ticker-content');
    if(ticker&&config.source_credit){var repair=function(){var before=ticker.textContent;var parts=before.split(/◆|\u25c6/).map(function(part){return part.trim();}).filter(function(part){return part&&!oldLocation.some(function(value){return value.length>3&&part.toLowerCase().indexOf(value.toLowerCase())>=0;});});var text=parts.join(' ◆ '),credit='SOURCE: '+config.source_credit.toUpperCase();if(text.indexOf(credit)<0)text+=' ◆ '+credit;if(text!==before)ticker.textContent=text;};repair();new MutationObserver(repair).observe(ticker,{childList:true,subtree:true});}
   }
   if(config.night){
    var buttons=Array.prototype.slice.call(document.querySelectorAll('button,[role="tab"],a'));
    var desired=buttons.find(function(b){return new RegExp('night\\s*(?:'+config.night+'|'+(config.night===2?'two':'one')+')','i').test(b.textContent);});
    if(desired)desired.click();
   }
   window.parent.postMessage({type:'isc-board-ready',id:config.id,mode:config.mode},'*');
  },650);});
 }
/** Preserve original HTML bytes and update ONLY the episode facts and ticker in memory.
 * Caller must enforce source hash and current verified feed checks BEFORE calling.
 * Never used in archive design review.
 */
function evolveApplyVerifiedEpisode(html,payload){
  if(typeof html!=='string'||!payload||payload.show_id!=='evolve')throw Error('Invalid Evolve source or episode');
  if(!/^\d{4}-\d{2}-\d{2}$/.test(payload.episode_date)||!Array.isArray(payload.segments)||!payload.segments.length)throw Error('Invalid episode content');
  const rx=/(<script id="verified-episode" type="application\/json">)[\s\S]*?(<\/script>)/;
  if(!rx.test(html))throw Error('Evolve source contract changed');
  const sanitized=JSON.stringify(payload).replace(/</g,'\\u003c');
  let updated=html.replace(rx,(_,a,b)=>a+sanitized+b);
  const tickerRx=/function ticker\(\)\{[^\n]*\}/;
  if(!tickerRx.test(updated))throw Error('Evolve ticker source contract changed');
  const monthNames=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const [year,month,day]=payload.episode_date.split('-').map(Number);
  const tickerText='WWE EVOLVE ◆ '+monthNames[month-1].toUpperCase()+' '+day+', '+year+' ◆ '+payload.segments.map(x=>x.kind==='result'?(x.headline.replace(/\n/g,' ')+' '+x.subline):x.strap).join(' ◆ ')+' ◆ ';
  const code='function ticker(){ document.getElementById("ticker-text").textContent=('+JSON.stringify(tickerText)+').repeat(3); }';
  return updated.replace(tickerRx,code);
}

 function build(html,record,routes,base,mode,feeds){
  if(mode==='active'&&record.id==='weekly-results-evolve'){
   var evolveFeed=feeds&&feeds['evolve-verified-results.json'];
   var episode=evolveFeed&&evolveFeed.mode==='EDITORIALLY_VERIFIED_EVOLVE_EPISODE'&&evolveFeed.episode;
   if(!episode||episode.show_id!=='evolve'||episode.verification!=='EDITORIALLY_VERIFIED'||!Array.isArray(episode.segments)||episode.segments.length!==6||evolveFeed.episode_date!==episode.episode_date)throw Error('Reviewed Evolve episode unavailable');
   html=evolveApplyVerifiedEpisode(html,episode);
  }

  if(mode==='archive'&&record.id==='weekly-results-evolve')html=html.replace('function safeEpisode(){return data.episode_date===currentLatestCompleted()}', 'function safeEpisode(){return true}');
  // This user-supplied addition changes visual identity only, in memory.
  // The locked source retains its original example data and bytes on disk.
  function addApprovedAaaPortrait(data){
   if(routes['/boards/RESULTS/AAA/assets/portraits/big-mami.png']!=='/shared/26189e3adbcb40f6296f03fca6098606fc931f6e907308d53e6fd3f79d5a3b13.png')return data;
   (data.programs||[]).forEach(function(program){
    if(program.show_id!=='aaa')return;
    (program.segments||[]).forEach(function(segment){
     if(segment.id==='big-mami-return'&&segment.headline==='BIG MAMI RETURNS'&&segment.kind==='storyline'&&Array.isArray(segment.portraits)&&!segment.portraits.length)segment.portraits=['big-mami'];
    });
   });
   return data;
  }
  if(record.id==='weekly-results-aaa'){
   html=html.replace(/(<script id="review-verified-results" type="application\/json">)([\s\S]*?)(<\/script>)/,function(_,a,json,b){return a+JSON.stringify(addApprovedAaaPortrait(JSON.parse(json))).replace(/</g,'\\u003c')+b;});
  }
  var assetBase=/\.chatgpt\.site$/i.test(new URL(base).hostname)?'https://raw.githubusercontent.com/Broncos5523/Inside-the-squared-circle/work/all-boards-github-pages/web/staging/':base;
  html=html.replace(/__ISC_BASE__/g,assetBase);
  var logical=record.href.split('?')[0],page=new URL(logical,'https://isc.invalid'),boardMap={};
  var prefix=page.pathname.slice(0,page.pathname.lastIndexOf('/')+1);
  Object.keys(routes).forEach(function(k){if(k.indexOf(prefix)===0)boardMap[k]=routes[k];});
  function resolve(value){try{var key=decodeURI(new URL(value,page).pathname);var target=boardMap[key];return target?new URL('originals'+target,assetBase).href:value;}catch(_){return value;}}
  // Rewrite only delivery URLs in memory; the committed original HTML is unchanged.
  html=html.replace(/(["'])([^"'<>\r\n]{1,500})\1/g,function(all,q,v){var mapped=resolve(v);return mapped===v?all:q+mapped+q;});
  html=html.replace(/url\(\s*(['"]?)([^)'"\r\n]+)\1\s*\)/g,function(all,q,v){var mapped=resolve(v);return mapped===v?all:'url("'+mapped+'")';});
  // All original approved results HTML remains byte-for-byte untouched.
  // Extend its accepted source contract only in ACTIVE in-memory playback.
  if(mode==='active'&&record.category==='Weekly Results'){
   html=html.replace(/data\?\.mode!=='EDITORIALLY_VERIFIED_OFFICIAL_RESULTS'/g,
    "(data?.mode!=='EDITORIALLY_VERIFIED_OFFICIAL_RESULTS'&&data?.mode!=='OFFICIAL_EXTRACTED_RESULTS')");
   html=html.replace(/p\.verification==='OFFICIAL_RESULTS_REVIEWED'/g,
    "(p.verification==='OFFICIAL_RESULTS_REVIEWED'||p.verification==='OFFICIAL_SOURCE_EXTRACTED')");
  }
  var night=/summerslam.*preview/i.test(record.id)?(/night_two/i.test(record.id)?2:1):null;
  var query=(record.href.split('?')[1]||'')+(mode==='archive'?'&demo=1':'&live=1')+(night?'&card='+night:'');
  html=html.replace(/new URLSearchParams\(location\.search\)/g,'new URLSearchParams('+JSON.stringify(query)+')');
  var officialEvent=null;
  if(mode==='active'&&feeds&&feeds['official-events.json']&&
    feeds['official-events.json'].mode==='OFFICIAL_WWE_EVENT_PREVIEWS'){
   var available=(feeds['official-events.json'].programs||[]).find(function(e){
    return e.board_id===record.id&&e.render_ready===true&&e.verification==='OFFICIAL_VERIFIED';
   });
   if(available){
    var portrait=function(slug){
     if(!/^[a-z0-9-]+$/.test(slug))return null;
     var names=['NXT','RAW','SmackDown'];
     for(var n=0;n<names.length;n++){
      var target=routes['/boards/UPCOMING/'+names[n]+'/assets/portraits/'+slug+'.png'];
      if(target)return new URL('originals'+target,assetBase).href;
     }
     return null;
    };
    var cards=(available.cards||[]).map(function(c){
     return {heading:c.heading,left:c.left,right:c.right,
      left_image:portrait(c.left_portrait),right_image:portrait(c.right_portrait),
      belt:c.belt===true,footer:c.footer||null};
    });
    if(cards.length===3&&cards.every(function(c){return c.left_image&&c.right_image;})){
     officialEvent={event_id:available.event_id,cards:cards};
    }
   }
  }
  var resultPortraits={},resultBelts={};
  if(mode==='active'&&record.category==='Weekly Results'){
   var show=record.id.slice('weekly-results-'.length),resultFeed=feeds&&feeds[show+'-verified-results.json'];
   var program=resultFeed&&Array.isArray(resultFeed.programs)?resultFeed.programs.find(function(p){return p.show_id===show&&Array.isArray(p.segments);}):null;
   function existingAsset(kind,name){
    if(!/^[a-z0-9_-]+\.png$/.test(name))return null;
    var shows=[show==='raw'?'RAW':show==='nxt'?'NXT':show==='smackdown'?'SmackDown':show==='tna'?'TNA':'AAA','RAW','NXT','SmackDown','AAA','TNA'];
    for(var i=0;i<shows.length;i++){
     for(var j=0;j<2;j++){
      var key='/boards/'+(j?'UPCOMING':'RESULTS')+'/'+shows[i]+'/assets/'+kind+'/'+name;
      if(routes[key])return new URL('originals'+routes[key],assetBase).href;
     }
    }
    return null;
   }
   if(program){
    program.segments.forEach(function(seg){
     (seg.portraits||[]).forEach(function(slug){
      if(typeof slug!=='string'||!/^[a-z0-9-]+$/.test(slug))return;
      var found=existingAsset('portraits',slug+'.png')||existingAsset('portrait-display',slug+'.png');
      if(found)resultPortraits[slug]=found;
     });
     if(typeof seg.belt==='string'){
      var belt=existingAsset('belts',seg.belt)||existingAsset('belts-display',seg.belt);
      if(belt)resultBelts[seg.belt]=belt;
     }
    });
   }
  }
  var boardFeeds={};
  if(mode==='active'&&feeds){
   var ownShow=record.id.replace(/^weekly-(?:results|upcoming)-/,'');
   ['snapshot.json','reported.json',ownShow+'-verified-results.json'].forEach(function(name){if(feeds[name])boardFeeds[name]=feeds[name];});
   if(ownShow==='aaa'&&boardFeeds['aaa-verified-results.json'])boardFeeds['aaa-verified-results.json']=addApprovedAaaPortrait(JSON.parse(JSON.stringify(boardFeeds['aaa-verified-results.json'])));
  }
  var config={weeklyResults:record.category==='Weekly Results',id:record.id,logical:logical,base:assetBase,routes:boardMap,mode:mode,feeds:boardFeeds,night:night,source_credit:record.source_credit||null,current_location:record.current_location||null,live_preview:record.category==='Weekly Upcoming',officialEvent:officialEvent,resultPortraits:resultPortraits,resultBelts:resultBelts};
  var injected='<base href="'+new URL('originals'+prefix,base).href+'"><script>('+shim.toString()+')('+JSON.stringify(config).replace(/</g,'\\u003c')+');<\/script>';
  return html.replace(/<head(?:\s[^>]*)?>/i,function(head){return head+injected;});
 }
 root.ISCBoardAdapter={build:build};
})(window);
