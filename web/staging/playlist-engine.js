(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.ISCPlaylist=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 // Live TV PROGRAMMING RULES, not a carousel of every approved design:
 // 1. Last verified episode of each weekly show (including Evolve recap), oldest to newest.
 // 2. The single next advertised weekly show preview (AAA, RAW, NXT, TNA, SmackDown).
 // 3. Every upcoming verified PLE or special-event preview within 14 calendar days.
 // 4. Verified PLE/special-event results from the last 7 calendar days.
 // Championship boards and unrelated/archive designs are NOT always-on TV slots.
 var weekly=['aaa','raw','nxt','evolve','tna','smackdown'],shows=['aaa','raw','nxt','tna','smackdown'];
 function etDay(now){var p=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now),v={};p.forEach(function(x){v[x.type]=x.value;});return v.year+'-'+v.month+'-'+v.day;}
 function days(a,b){return (Date.parse(a+'T12:00:00Z')-Date.parse(b+'T12:00:00Z'))/86400000;}
 function stamp(x){return /^(?:ple|special)-/.test(x.kind||'')?(x.event_date||''):(x.airdate||x.event_date||'');}
 function verified(x){return x.verification==='OFFICIAL_VERIFIED'||x.verification==='EDITORIALLY_VERIFIED';}
 function select(entries,now){
  now=now||new Date();
  var today=etDay(now),out=[],seen={};
  var usable=(entries||[]).filter(function(x){
   var checked=x&&Date.parse(x.checked_at||'');
   return x&&typeof x.id==='string'&&x.source_available===true&&x.design_approved===true&&
    x.content_status==='current'&&typeof x.source_url==='string'&&/^https:\/\//.test(x.source_url)&&
    Number.isFinite(checked)&&checked<=now.getTime()+300000&&now.getTime()-checked<=48*3600000&&
    /^\d{4}-\d{2}-\d{2}$/.test(stamp(x));
  });
  function add(x){if(x&&!seen[x.id]){seen[x.id]=true;out.push(x);}}
  function newest(rows){return rows.slice().sort(function(a,b){return stamp(b).localeCompare(stamp(a))||String(a.id).localeCompare(String(b.id));})[0];}
  var results=usable.filter(function(x){
   return (x.kind==='results'||x.kind==='evolve')&&verified(x)&&x.completed===true&&stamp(x)<=today;
  });
  // Results persist until a newer VERIFIED result is available. They do not expire
  // after 14 days, unlike special-event results, but the collector itself must stay fresh.
  var latest=weekly.map(function(show){
   return newest(results.filter(function(x){return x.show===show&&
    (show==='evolve'?x.kind==='evolve'||x.kind==='results':x.kind==='results');}));
  }).filter(Boolean);
  latest.sort(function(a,b){return stamp(a).localeCompare(stamp(b))||
    weekly.indexOf(a.show)-weekly.indexOf(b.show);}).forEach(add);

  // Only the NEXT weekly broadcast, not every future show. A scheduled preview
  // may contain an accurate date/venue without advertised matches or appearances.
  var previews=usable.filter(function(x){
   return x.kind==='upcoming'&&shows.indexOf(x.show)>=0&&
    (x.verification==='SOURCE_REPORTED'||verified(x))&&
    (x.has_content===true||x.schedule_confirmed===true)&&
    x.airdate>=today&&days(x.airdate,today)>=0&&
    !results.some(function(r){return r.show===x.show&&r.airdate===x.airdate;});
  });
  previews.sort(function(a,b){return a.airdate.localeCompare(b.airdate)||
   shows.indexOf(a.show)-shows.indexOf(b.show);});
  add(previews[0]);

  // Specials are independent of weekly episodes. Show all within 14 days,
  // including the day of the event. Once a verified result is available, hide preview.
  var specialResults=usable.filter(function(x){
   return (x.kind==='ple-results'||x.kind==='special-results')&&verified(x)&&
    x.completed===true&&stamp(x)<=today;
  });
  usable.filter(function(x){
   return (x.kind==='ple-preview'||x.kind==='special-preview')&&x.date_confirmed===true&&
    (x.has_content===true||x.schedule_confirmed===true)&&
    (x.verification==='SOURCE_REPORTED'||verified(x))&&
    x.event_date>=today&&days(x.event_date,today)<=14&&
    !specialResults.some(function(r){return r.event_id&&x.event_id&&r.event_id===x.event_id&&r.event_date===x.event_date;});
  }).sort(function(a,b){return a.event_date.localeCompare(b.event_date)||
   String(a.id).localeCompare(String(b.id));}).forEach(add);

  // Results from special events are relevant for 7 days, including event day.
  specialResults.filter(function(x){return days(today,stamp(x))<=7;})
   .sort(function(a,b){return stamp(b).localeCompare(stamp(a))||String(a.id).localeCompare(String(b.id));})
   .forEach(add);
  return out;
 }
 return {select:select,etDay:etDay,days:days};
});
