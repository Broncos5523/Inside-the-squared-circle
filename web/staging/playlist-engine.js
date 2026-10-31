(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.ISCPlaylist=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 var shows=['raw','smackdown','nxt','aaa','tna'];
 function etDay(now){var p=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now),v={};p.forEach(function(x){v[x.type]=x.value;});return v.year+'-'+v.month+'-'+v.day;}
 function days(a,b){return (Date.parse(a+'T12:00:00Z')-Date.parse(b+'T12:00:00Z'))/86400000;}
 function select(entries,now){
  now=now||new Date();var today=etDay(now),out=[],seen={};
  var usable=(entries||[]).filter(function(x){return x&&x.source_available===true&&x.design_approved===true&&x.content_status==='current'&&x.source_url&&x.checked_at&&Date.parse(x.checked_at)<=now.getTime()+300000&&now.getTime()-Date.parse(x.checked_at)<=48*3600000&&/^\d{4}-\d{2}-\d{2}$/.test(x.airdate||x.event_date||'');});
  function add(x){if(x&&!seen[x.id]){seen[x.id]=1;out.push(x);}}
  function latest(rows){return rows.sort(function(a,b){return (b.airdate||b.event_date).localeCompare(a.airdate||a.event_date);})[0];}
  function verified(x){return x.verification==='OFFICIAL_VERIFIED'||x.verification==='EDITORIALLY_VERIFIED';}
  var results=usable.filter(function(x){return (x.kind==='results'||x.kind==='evolve')&&verified(x)&&x.completed===true&&x.airdate<=today&&days(today,x.airdate)<=14;});
  var previews=usable.filter(function(x){return x.kind==='upcoming'&&x.verification==='SOURCE_REPORTED'&&x.has_content===true&&x.airdate<=today&&days(today,x.airdate)<=1&&!results.some(function(r){return r.show===x.show&&r.airdate===x.airdate;});});
  // Multiple programs can air on one night. No weekday or event date is invented.
  previews.filter(function(x){return x.airdate===today;}).forEach(add);
  shows.forEach(function(show){add(latest(results.filter(function(x){return x.show===show&&x.kind==='results';})));});
  usable.filter(function(x){return x.kind==='champions'&&verified(x)&&x.data_verified===true&&x.belts_verified===true;}).forEach(add);
  usable.filter(function(x){return x.kind==='ple-preview'&&x.date_confirmed===true&&x.has_content===true&&['SOURCE_REPORTED','OFFICIAL_VERIFIED','EDITORIALLY_VERIFIED'].indexOf(x.verification)>=0&&days(x.event_date,today)>=-1&&days(x.event_date,today)<=45&&!usable.some(function(r){return r.kind==='ple-results'&&r.event_id===x.event_id&&verified(r)&&r.completed===true;});}).sort(function(a,b){return a.event_date.localeCompare(b.event_date);}).forEach(add);
  usable.filter(function(x){return x.kind==='ple-results'&&verified(x)&&x.completed===true&&x.event_date<=today&&days(today,x.event_date)<=14;}).forEach(add);
  add(latest(results.filter(function(x){return x.kind==='evolve';})));
  // Expired previews cannot bridge results delays.
  // Include the nearest future advertised show alongside verified recent results.
  add(previews.filter(function(x){return x.airdate>today;}).sort(function(a,b){return a.airdate.localeCompare(b.airdate);})[0]);
  return out;
 }
 return {select:select,etDay:etDay};
});
