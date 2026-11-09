(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.ISCPlaylist=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 // Live TV PROGRAMMING RULES, not a carousel of every approved design:
 // 1. Cyclic weekly groups beginning with the next scheduled show.
 // 2. Each group: latest results, next preview (except Evolve), checked champions.
 // 3. Verified PLE/special-event results within 7 days, oldest to newest.
 // 4. Upcoming PLE/special-event previews within 14 days, soonest first.
 // Current verified champions follow their own show; archive designs stay excluded.
 var weekly=['aaa','raw','nxt','evolve','tna','smackdown'],shows=['aaa','raw','nxt','tna','smackdown'];
 function etDay(now){var p=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now),v={};p.forEach(function(x){v[x.type]=x.value;});return v.year+'-'+v.month+'-'+v.day;}
 function days(a,b){return (Date.parse(a+'T12:00:00Z')-Date.parse(b+'T12:00:00Z'))/86400000;}
 function stamp(x){return /^(?:ple|special)-/.test(x.kind||'')?(x.event_date||''):(x.airdate||x.event_date||x.as_of||'');}
 function verified(x){return x.verification==='OFFICIAL_VERIFIED'||x.verification==='EDITORIALLY_VERIFIED'||(x.verification==='SOURCE_CORROBORATED'&&Array.isArray(x.source_urls)&&new Set(x.source_urls.map(function(u){try{return new URL(u).hostname;}catch(_){return '';}}).filter(Boolean)).size>=2);}
 function select(entries,now,allowStaleResults){
  now=now||new Date();
  var today=etDay(now),out=[],seen={};
  var usable=(entries||[]).filter(function(x){
   var checked=x&&Date.parse(x.checked_at||'');
   return x&&typeof x.id==='string'&&x.source_available===true&&x.design_approved===true&&
    x.content_status==='current'&&typeof x.source_url==='string'&&/^https:\/\//.test(x.source_url)&&
    Number.isFinite(checked)&&checked<=now.getTime()+300000&&(now.getTime()-checked<=48*3600000||(allowStaleResults===true&&now.getTime()-checked<=14*86400000&&(x.kind==='results'||x.kind==='evolve')&&x.completed===true&&verified(x)))&&
    /^\d{4}-\d{2}-\d{2}$/.test(stamp(x));
  });
  function add(x){if(x&&!seen[x.id]){seen[x.id]=true;out.push(x);}}
  function newest(rows){return rows.slice().sort(function(a,b){return stamp(b).localeCompare(stamp(a))||String(a.id).localeCompare(String(b.id));})[0];}
  var results=usable.filter(function(x){
   return (x.kind==='results'||x.kind==='evolve')&&verified(x)&&x.completed===true&&stamp(x)<=today;
  });
  // Results persist until a newer VERIFIED result is available. They do not expire
  // after 14 days, unlike special-event results, but the collector itself must stay fresh.
  // One group per show, starting with the next scheduled broadcast.
  var previews=usable.filter(function(x){
   return x.kind==='upcoming'&&shows.indexOf(x.show)>=0&&
    (x.verification==='SOURCE_REPORTED'||verified(x))&&
    (x.has_content===true||x.schedule_confirmed===true)&&x.airdate>=today&&
    !results.some(function(r){return r.show===x.show&&r.airdate===x.airdate;});
  });
  var cycle=['raw','nxt','evolve','tna','smackdown','aaa'];
  var weekday={raw:1,nxt:2,evolve:3,tna:4,smackdown:5,aaa:6};
  var currentDay=new Date(today+'T12:00:00Z').getUTCDay();
  function nextDate(show){
   var advertised=previews.filter(function(p){return p.show===show;}).sort(function(a,b){return a.airdate.localeCompare(b.airdate);})[0];
   if(advertised)return advertised.airdate;
   var delta=(weekday[show]-currentDay+7)%7;
   if(delta===0&&results.some(function(r){return r.show===show&&r.airdate===today;}))delta=7;
   var date=new Date(today+'T12:00:00Z');date.setUTCDate(date.getUTCDate()+delta);return date.toISOString().slice(0,10);
  }
  var first=cycle.slice().sort(function(a,b){return nextDate(a).localeCompare(nextDate(b))||cycle.indexOf(a)-cycle.indexOf(b);})[0];
  var pivot=cycle.indexOf(first),ordered=cycle.slice(pivot).concat(cycle.slice(0,pivot));
  ordered.forEach(function(show){
   add(newest(results.filter(function(x){return x.show===show;})));
   if(show!=='evolve')add(previews.filter(function(x){return x.show===show;}).sort(function(a,b){return a.airdate.localeCompare(b.airdate);})[0]);
   add(newest(usable.filter(function(x){return x.kind==='champions'&&x.show===show&&verified(x);})));
  });

  // Specials are independent of weekly episodes. Show all within 14 days,
  // including the day of the event. Once a verified result is available, hide preview.
  var specialResults=usable.filter(function(x){
   return (x.kind==='ple-results'||x.kind==='special-results')&&verified(x)&&
    x.completed===true&&stamp(x)<=today;
  });
  // Results from special events are relevant for 7 days, including event day.
  specialResults.filter(function(x){return days(today,stamp(x))<=7;})
   .sort(function(a,b){return stamp(a).localeCompare(stamp(b))||String(a.id).localeCompare(String(b.id));})
   .forEach(add);

  usable.filter(function(x){
   return (x.kind==='ple-preview'||x.kind==='special-preview')&&x.date_confirmed===true&&
    (x.has_content===true||x.schedule_confirmed===true)&&
    (x.verification==='SOURCE_REPORTED'||verified(x))&&
    x.event_date>=today&&days(x.event_date,today)<=14&&
    !specialResults.some(function(r){return r.event_id&&x.event_id&&r.event_id===x.event_id&&r.event_date===x.event_date;});
  }).sort(function(a,b){return a.event_date.localeCompare(b.event_date)||
   String(a.id).localeCompare(String(b.id));}).forEach(add);

  return out;
 }
 // Give every verified match/result card enough time to display once.
 // Source result boards advance internally about every 14 seconds; cutting a
 // result board off at 45 seconds would hide most of a 5-7-segment episode.
 function dwellMs(entry,feeds,selectedMs){
  var base=Math.max(20000,Number(selectedMs)||45000);
  if(entry&&entry.kind==='champions'){
   var championship=feeds&&feeds['champions.json']?.programs?.find(function(p){return p.board_id===entry.id;});
   return Math.max(base,(championship?.champions?.length||0)*11000+6500);
  }
  if(entry&&entry.kind==='upcoming'){
   var preview=feeds&&feeds['reported.json']?.programs?.find(function(p){return p.show_id===entry.show&&p.airdate===entry.airdate;});
   var slides=(preview?.matches?.length||0)+(preview?.appearances?.length||0)+1;
   return Math.max(base,slides*14000+6500);
  }
  if(entry&&entry.kind==='ple-results'){
   var event=feeds&&feeds['official-event-results.json']?.programs?.find(function(p){return p.board_id===entry.id;});
   if(event?.matches){var champions=event.matches.filter(function(m){return !!m.belt;}).length;return Math.max(base,Math.max(champions,event.matches.length-champions)*14000+6500);}
  }
  if(!entry||(entry.kind!=='results'&&entry.kind!=='evolve'))return base;
  var feed=feeds&&feeds[entry.show+'-verified-results.json'];
  var programs=feed&&feed.programs;
  if(!Array.isArray(programs))return base;
  var program=programs.find(function(x){return x.show_id===entry.show&&x.airdate===entry.airdate;});
  var n=program&&Array.isArray(program.segments)?program.segments.length:0;
  return n>0?Math.max(base,n*14000+6500):base;
 }
 return {select:select,etDay:etDay,days:days,dwellMs:dwellMs};
});
