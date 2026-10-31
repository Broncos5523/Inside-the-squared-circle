(function(root){
 'use strict';
 function shim(config){
  var map=config.routes,logical=new URL(config.logical,'https://isc.invalid'),nativeFetch=window.fetch.bind(window);
  function resolve(value){
   if(typeof value!=='string'||!value||/^(?:data:|blob:|#)/i.test(value))return value;
   try{var url=new URL(value,logical),key=decodeURI(url.pathname),mapped=map[key];
    if(!mapped&&key.indexOf('/assets/')===0)mapped=map[logical.pathname.slice(0,logical.pathname.lastIndexOf('/')+1)+key.slice(1)];
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
   if(/broncos5523\.github\.io\/Inside-the-squared-circle\/data\//i.test(url)){
    var name=new URL(url).pathname.split('/').pop();
    if(config.mode==='active'&&Object.prototype.hasOwnProperty.call(config.feeds,name))return Promise.resolve(new Response(JSON.stringify(config.feeds[name]),{status:200,headers:{'Content-Type':'application/json'}}));
    return Promise.resolve(new Response('{}',{status:404,headers:{'Content-Type':'application/json'}}));
   }
   var remapped=resolve(url);return nativeFetch(remapped!==url?remapped:input,options);
  };
  if(config.night){var interval=window.setInterval.bind(window);window.setInterval=function(fn,ms){if(typeof fn==='function'&&/currentCard\+\+/.test(fn.toString()))return 0;return interval.apply(window,arguments);};}
  // Archive content never silently refreshes into a different episode.
  window.addEventListener('load',function(){setTimeout(function(){
   if(config.mode==='active'){
    var venue=document.getElementById('wb-venue'),city=document.getElementById('wb-city');
    var oldLocation=[venue&&venue.textContent,city&&city.textContent].filter(Boolean);
    if(venue)venue.textContent=config.current_location&&config.current_location.arena||'';
    if(city)city.textContent=config.current_location&&config.current_location.city||'';
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
 function build(html,record,routes,base,mode,feeds){
  var assetBase=/\.chatgpt\.site$/i.test(new URL(base).hostname)?'https://raw.githubusercontent.com/Broncos5523/Inside-the-squared-circle/work/all-boards-github-pages/web/staging/':base;
  html=html.replace(/__ISC_BASE__/g,assetBase);
  var logical=record.href.split('?')[0],page=new URL(logical,'https://isc.invalid'),boardMap={};
  var prefix=page.pathname.slice(0,page.pathname.lastIndexOf('/')+1);
  Object.keys(routes).forEach(function(k){if(k.indexOf(prefix)===0)boardMap[k]=routes[k];});
  function resolve(value){try{var key=decodeURI(new URL(value,page).pathname);var target=boardMap[key];return target?new URL('originals'+target,assetBase).href:value;}catch(_){return value;}}
  // Rewrite only delivery URLs in memory; the committed original HTML is unchanged.
  html=html.replace(/(["'])([^"'<>\r\n]{1,500})\1/g,function(all,q,v){var mapped=resolve(v);return mapped===v?all:q+mapped+q;});
  html=html.replace(/url\(\s*(['"]?)([^)'"\r\n]+)\1\s*\)/g,function(all,q,v){var mapped=resolve(v);return mapped===v?all:'url("'+mapped+'")';});
  var night=/summerslam.*preview/i.test(record.id)?(/night_two/i.test(record.id)?2:1):null;
  var query=(record.href.split('?')[1]||'')+(mode==='archive'?'&demo=1':'&live=1')+(night?'&card='+night:'');
  html=html.replace(/new URLSearchParams\(location\.search\)/g,'new URLSearchParams('+JSON.stringify(query)+')');
  var config={id:record.id,logical:logical,base:assetBase,routes:boardMap,mode:mode,feeds:feeds||{},night:night,source_credit:record.source_credit||null,current_location:record.current_location||null};
  var injected='<base href="'+new URL('originals'+prefix,base).href+'"><script>('+shim.toString()+')('+JSON.stringify(config).replace(/</g,'\\u003c')+');<\/script>';
  return html.replace(/<head(?:\s[^>]*)?>/i,function(head){return head+injected;});
 }
 root.ISCBoardAdapter={build:build};
})(window);
