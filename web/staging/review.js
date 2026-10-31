(function(){
 'use strict';
 var base=new URL('./',location.href).href,library,routes,feeds={},programming={entries:[]},active=[],visible=[],current=null,timer=null,token=0,mode='archive';
 var params=new URLSearchParams(location.search),byId=function(id){return document.getElementById(id);};
 function getJSON(path){return fetch(new URL(path,base),{cache:'no-store'}).then(function(r){if(!r.ok)throw Error(path+' unavailable');return r.json();});}
 function label(record){if(record.id.indexOf('results-summerslam_night_one_')===0)return 'SummerSlam — Night One — Results & Fallout';if(record.id.indexOf('results-summerslam_night_two_')===0)return 'SummerSlam — Night Two — Results & Fallout';return record.label;}
 function scale(){var p=byId('preview'),screen=p.querySelector('.screen');p.style.height=(document.body.classList.contains('tv')?window.innerHeight:p.clientWidth*1280/720)+'px';var h=p.clientHeight,w=p.clientWidth,s=Math.min(w/720,h/1280);screen.style.transform='translateX(-50%) scale('+s+')';}
 function setTv(enabled){document.body.classList.toggle('tv',enabled);byId('review-panel').dataset.mode=mode==='archive'?'ARCHIVE DESIGN REVIEW':'';scale();}
 function candidates(){return mode==='active'?active.map(function(e){return library.records.find(function(r){return r.id===e.id;});}).filter(Boolean):visible.filter(function(r){return r.source_available;});}
 function stop(){if(timer)clearTimeout(timer);timer=null;byId('rotate').textContent='Play review';}
 function schedule(){if(timer)clearTimeout(timer);var ms=Number(byId('duration').value)*1000;timer=setTimeout(function(){step(1,true);},ms);byId('rotate').textContent=mode==='active'?'Pause playback':'Pause review';}
 function step(delta,keepPlaying){var list=candidates();if(!list.length)return;var pos=list.findIndex(function(r){return current&&r.id===current.id;});choose(list[(Math.max(pos,0)+delta+list.length)%list.length],keepPlaying);}
 async function choose(record,keepPlaying){
  if(!keepPlaying)stop();current=record;var mine=++token;var frame=byId('board');frame.classList.remove('ready');byId('loading').hidden=false;byId('loading').style.display='grid';
  byId('board-title').textContent=label(record);var list=candidates();byId('board-count').textContent=Math.max(0,list.findIndex(function(r){return r.id===record.id;}))+1+' / '+list.length;
  document.querySelectorAll('.card').forEach(function(el){el.classList.toggle('selected',el.dataset.id===record.id);});
  if(!record.source_available){frame.srcdoc='';byId('loading').textContent='Final Evolve board awaiting recovery. The approved design has not been substituted.';return;}
  byId('loading').textContent='Loading original source…';
  try{
   var response=await fetch(new URL(record.delivery||('originals'+record.href.split('?')[0]),base));if(!response.ok)throw Error('Source request failed');
   var bytes=await response.arrayBuffer();
   if(window.crypto&&crypto.subtle){var digest=await crypto.subtle.digest('SHA-256',bytes);var hash=Array.from(new Uint8Array(digest)).map(function(n){return n.toString(16).padStart(2,'0');}).join('');if(hash!==(record.delivery_sha256||record.original_sha256))throw Error('Original source delivery integrity check failed');}
   var html=new TextDecoder().decode(bytes);if(mine!==token)return;
   var selectedEntry=mode==='active'?active.find(function(e){return e.id===record.id;}):null;
   var renderRecord=selectedEntry?Object.assign({},record,{source_credit:selectedEntry.source_name,current_location:selectedEntry.venue||null}):record;
   frame.srcdoc=ISCBoardAdapter.build(html,renderRecord,routes,base,mode,feeds);
   if(keepPlaying)schedule();
  }catch(error){if(mine!==token)return;byId('loading').textContent=error.message+' · choose another source board.';byId('status').textContent='Source loading needs attention';if(keepPlaying)schedule();}
 }
 function gallery(category){
  visible=library.records.filter(function(r){return category==='All designs'||r.category===category;});var grid=byId('gallery');grid.replaceChildren();
  visible.forEach(function(r){var b=document.createElement('button');b.className='card';b.dataset.id=r.id;b.title=label(r);b.addEventListener('click',function(){mode='archive';choose(r,false);byId('preview').scrollIntoView({behavior:'smooth',block:'start'});});
   if(r.thumbnail){var img=document.createElement('img');img.src=new URL(r.thumbnail.replace(/^\//,''),base);img.alt=label(r)+' archive design';img.loading='lazy';b.append(img);}else{var hold=document.createElement('div');hold.className='hold';hold.textContent='EVOLVE\nFinal approved source\nawaiting recovery';b.append(hold);}
   var title=document.createElement('strong');title.textContent=label(r);b.append(title);grid.append(b);
  });
 }
 function switchPanel(activePanel){stop();byId('review-panel').hidden=activePanel;byId('active-panel').hidden=!activePanel;byId('library-tab').classList.toggle('selected',!activePanel);byId('active-tab').classList.toggle('selected',activePanel);if(!activePanel){mode='archive';setTv(false);}}
 async function refresh(){
  try{
   var external=location.hostname!=='broncos5523.github.io'&&location.hostname!=='terminal.local'&&location.hostname!=='127.0.0.1';
   if(external){try{var controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),4500);var result=await fetch('https://raw.githubusercontent.com/Broncos5523/Inside-the-squared-circle/work/all-boards-github-pages/web/staging/data/programming.json?t='+Math.floor(Date.now()/300000),{cache:'no-store',signal:controller.signal});clearTimeout(timeout);if(!result.ok)throw Error('Branch facts pending');programming=await result.json();}catch(_){programming=await getJSON('data/programming.json');}}
   else programming=await getJSON('data/programming.json');
   feeds=programming.feeds||{};
  }catch(_){programming={entries:[],generated_at:null};feeds={};}
  var feedAge=Date.now()-Date.parse(programming.generated_at||'');
  var feedFresh=Number.isFinite(feedAge)&&feedAge>=-300000&&feedAge<=6*3600000;
  // A browser reload is not evidence of a successful upstream collection.
  // Fail closed when the collector output is old; archive review remains available.
  active=feedFresh?ISCPlaylist.select(programming.entries,new Date()):[];
  byId('watch-active').disabled=!active.length;
  byId('active-summary').textContent=active.length?active.length+' current board'+(active.length===1?'':'s')+' selected from source-backed programming.': 'No current boards have cleared their source and data checks yet. The recovered designs are available in the design library.';
  var list=byId('active-list');list.replaceChildren();active.forEach(function(x){var d=document.createElement('div'),strong=document.createElement('strong'),small=document.createElement('small');strong.textContent=x.title;small.textContent=(x.airdate||x.event_date)+' · '+x.source_name;d.append(strong,small);list.append(d);});
  byId('feed-stamp').textContent=programming.generated_at?(feedFresh?'Collector last ran ':'STALE DATA — collector last ran ')+new Date(programming.generated_at).toLocaleString()+'. Browser checks for published updates every five minutes; this does not run the collector.':'Current-content collection is pending; archive examples are held outside the TV playlist.';
  if(!feedFresh)byId('active-summary').textContent='Live-data collection is stale or unavailable. Archived demonstrations remain in the design library and are not presented as live programming.';
  if(mode==='active'){
   var next=candidates()[0];
   if(current&&!active.some(function(x){return x.id===current.id;})){
    stop();current=null;
    if(next)choose(next,true);else{switchPanel(true);mode='active';if(new URLSearchParams(location.search).get('view')==='tv'){setTv(true);byId('loading').textContent='Waiting for fresh wrestling programming…';byId('loading').style.display='grid';}}
   }else if(!current&&next&&new URLSearchParams(location.search).get('view')==='tv'){
    switchPanel(false);mode='active';setTv(true);choose(next,true);
   }
  }
 }
 window.addEventListener('message',function(event){if(event.source!==byId('board').contentWindow||!event.data||event.data.type!=='isc-board-ready'||!current||event.data.id!==current.id)return;byId('board').classList.add('ready');byId('loading').style.display='none';byId('status').textContent=mode==='archive'?'Archive design · Original source verified':'Source-backed active playback';});
 window.addEventListener('resize',scale);window.addEventListener('orientationchange',scale);
 document.addEventListener('visibilitychange',function(){if(!document.hidden){refresh();scale();}});
 document.addEventListener('keydown',function(e){if(e.key==='ArrowRight')step(1,!!timer);if(e.key==='ArrowLeft')step(-1,!!timer);if(e.key==='Escape'){setTv(false);stop();}});
 byId('previous').onclick=function(){step(-1,false);};byId('next').onclick=function(){step(1,false);};byId('rotate').onclick=function(){if(timer)stop();else schedule();};
 byId('fullscreen').onclick=function(){setTv(true);var u=new URL(location.href);u.searchParams.set('view','tv');u.searchParams.set('mode',mode);if(current)u.searchParams.set('id',current.id);history.pushState({},'',u);};
 byId('library-tab').onclick=function(){switchPanel(false);if(current)choose(current,false);};byId('active-tab').onclick=function(){switchPanel(true);};
 byId('watch-active').onclick=function(){mode='active';switchPanel(false);mode='active';setTv(true);choose(candidates()[0],true);};
 window.addEventListener('popstate',function(){setTv(new URLSearchParams(location.search).get('view')==='tv');});
 Promise.all([getJSON('library.json'),getJSON('asset-routes.json')]).then(async function(values){
  library=values[0];routes=values[1];byId('stats').innerHTML='<span><b>'+library.source_slots+'</b> source-backed slots</span><span>·</span><span><b>1</b> recovery hold</span><span>·</span><span><b>68</b> library slots</span>';
  ['All designs','Weekly Upcoming','Weekly Results','Championships','PLE Preview','PLE Results'].forEach(function(category,i){var b=document.createElement('button');b.textContent=category;b.className=i===0?'selected':'';b.onclick=function(){document.querySelectorAll('#filters button').forEach(function(x){x.classList.toggle('selected',x===b);});gallery(category);};byId('filters').append(b);});
  gallery('All designs');var refreshed=refresh();
  // The default landing page must never masquerade an archived example as live.
  // Explicit archive URLs still support the original design-review workflow.
  mode=params.get('mode')==='archive'?'archive':'active';
  await refreshed;
  var first=mode==='active'?candidates()[0]:library.records.find(function(r){return r.id===params.get('id');})||library.records.find(function(r){return r.id==='weekly-results-smackdown';})||visible[0];
  if(!first){switchPanel(true);mode='active';if(params.get('view')==='tv'){setTv(true);byId('loading').textContent='Waiting for fresh wrestling programming…';byId('loading').style.display='grid';byId('active-summary').textContent='Live programming is temporarily unavailable. Waiting for a fresh verified collection; archive demonstrations are not being broadcast.';}setInterval(refresh,300000);return;}
  if(mode==='active'){switchPanel(true);mode='active';if(params.get('view')==='tv'){switchPanel(false);mode='active';setTv(true);await choose(first,true);}}
  else{setTv(params.get('view')==='tv');await choose(first,params.get('play')==='1');}
  scale();setInterval(refresh,300000);
 }).catch(function(error){byId('loading').textContent='Library could not load: '+error.message;});
 window.__iscReview={select:function(id){var r=library.records.find(function(x){return x.id===id;});if(r)return choose(r,false);},getLibrary:function(){return library;},getActive:function(){return active;},getCurrent:function(){return current;},getRoutes:function(){return routes;}};
})();
