"""Metrics-only coverage report: never confuse article links with match results."""
from __future__ import annotations
import argparse,json
from datetime import datetime,date
from pathlib import Path
from zoneinfo import ZoneInfo
from proof.results_intake import broadcast_complete
ET=ZoneInfo("America/New_York")
SOURCES={
 "reported":("REPORTED_MATCHES_UNVERIFIED","reported.json"),
 "results":("PROVIDER_REPORTED_POST_BROADCAST_RESULTS_UNVERIFIED","results.json"),
 "rss_facts":("POST_BROADCAST_RSS_EXPLICIT_FACTS_UNVERIFIED","rss-facts.json"),
 "rss_excerpts":("POST_BROADCAST_RSS_SYNDICATED_EXCERPT_FACTS_UNVERIFIED","rss-excerpt-results.json"),
 "fallout":("POST_BROADCAST_RSS_FALLOUT_FACTS_UNVERIFIED","rss-fallout.json"),
 "recap_links":("PUBLISHER_RSS_POST_SHOW_LINKS_ONLY","recap-links.json"),
 "episode_briefs":("TVMAZE_FINISHED_EPISODE_GUIDE_SYNOPSIS_ONLY","episode-briefs.json"),
}
SHOWS={"raw","smackdown","nxt","aaa","tna","evolve"}
def fresh(feed,now):
 try:
  stamp=datetime.fromisoformat(feed["generated_at"])
  diff=(now.astimezone(ET)-stamp.astimezone(ET)).total_seconds()/60
  return stamp.tzinfo is not None and 0<=diff<=480
 except (KeyError,ValueError,TypeError,AttributeError):return False
def latest_finished(show,now):
 if show.get("schedule_status")!="fresh":return None
 dates=[]
 for key in ("previous","next"):
  day=(show.get(key) or {}).get("date")
  try:dt=date.fromisoformat(day)
  except (ValueError,TypeError):continue
  delta=(now.astimezone(ET).date()-dt).days
  if 0<=delta<=14 and broadcast_complete(show["id"],day,now):dates.append(day)
 return max(dates,default=None)
def find(feed,sid,day):
 if not day or not isinstance(feed,dict):return {}
 return next((x for x in feed.get("programs",[]) if isinstance(x,dict)
             and x.get("show_id")==sid and x.get("airdate")==day),{})
def tally(row,key):
 return len(row.get(key,[])) if isinstance(row.get(key),list) else 0
def build(snapshot,feeds,editorial,now=None):
 now=now or datetime.now(ET)
 if snapshot.get("schema_version")!=1 or len(snapshot.get("shows",[]))!=6:
  raise ValueError("Invalid schedule")
 live={}
 source_health={}
 for key,(mode,_) in SOURCES.items():
  val=feeds.get(key)
  ok=isinstance(val,dict) and val.get("mode")==mode and fresh(val,now)
  live[key]=val if ok else {}
  source_health[key]={"fresh":ok,"generated_at":val.get("generated_at") if isinstance(val,dict) else None}
 editorial=editorial if isinstance(editorial,dict) and editorial.get("mode")=="DATED_MULTI_SOURCE_RECAP_REVIEW_UNVERIFIED" else {}
 programs=[]
 for show in snapshot["shows"]:
  sid=show.get("id")
  if sid not in SHOWS:raise ValueError("Unexpected show ID")
  last=latest_finished(show,now)
  coming=(show.get("next") or {}).get("date")
  upcoming=find(live["reported"],sid,coming)
  auto=sum(tally(find(live[k],sid,last),"results") for k in ("results","rss_facts","rss_excerpts"))
  fallout=tally(find(live["fallout"],sid,last),"developments")
  manual=find(editorial,sid,last)
  manual_count=tally(manual,"results") if last else 0
  manual_stories=tally(manual,"developments") if manual_count else 0
  synopsis=find(live["episode_briefs"],sid,last)
  notes=(isinstance(synopsis.get("synopsis"),str)
         and synopsis.get("source_name")=="TVmaze" and synopsis.get("license")=="CC BY-SA")
  headlines=tally(find(live["recap_links"],sid,last),"links")
  programs.append({
   "show_id":sid,"last_completed":last,"next_airdate":coming,
   "upcoming_reported_matches":tally(upcoming,"matches"),
   "upcoming_reported_appearances":tally(upcoming,"appearances"),
   "automatic_match_outcomes":auto,"automatic_storylines":fallout,
   "manually_reviewed_outcomes":manual_count,
   "manually_reviewed_storylines":manual_stories,
   "episode_synopsis_available":bool(notes),
   "publisher_headline_links":headlines,
   "results_data_status":("automatic_results_present" if auto else
     "manual_review_available" if manual_count else "no_usable_result_facts")
  })
 counts=("upcoming_reported_matches","upcoming_reported_appearances",
         "automatic_match_outcomes","automatic_storylines",
         "manually_reviewed_outcomes","manually_reviewed_storylines",
         "publisher_headline_links")
 totals={k:sum(x[k] for x in programs) for k in counts}
 diagnostics=feeds.get("rss_excerpts",{}).get("feed_diagnostics",{})
 if not isinstance(diagnostics,dict):diagnostics={}
 totals["rss_descriptions_with_defeated_word"]=sum(
   int(v.get("with_defeated_word",0)) for v in diagnostics.values() if isinstance(v,dict))
 totals["rss_explicit_winner_sentences"]=sum(
   int(v.get("with_explicit_outcome_sentence",0)) for v in diagnostics.values() if isinstance(v,dict))
 return {
  "schema_version":1,"mode":"WRESTLING_CONTENT_COVERAGE_COUNTS_ONLY",
  "generated_at":now.astimezone(ET).isoformat(),"source_health":source_health,
  "totals":totals,"programs":programs,
  "interpretation":"Counts of data availability, not match counts in the real world. Headline links and TVmaze episode synopses are not results. Automated source counts can duplicate the same match."
 }
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--data-dir",default="web/data")
 ap.add_argument("--out",default="web/data/coverage-health.json")
 args=ap.parse_args()
 root=Path(args.data_dir)
 def get(path):
  try:return json.loads((root/path).read_text(encoding="utf-8"))
  except (ValueError,OSError):return {}
 feeds={k:get(path) for k,(_,path) in SOURCES.items()}
 report=build(get("snapshot.json"),feeds,get("editorial-recaps-20261022.json"))
 out=Path(args.out);tmp=out.with_suffix(".tmp")
 tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 tmp.replace(out)
 print("COVERAGE FACTS:",report["totals"]["automatic_match_outcomes"],
       "auto match outcomes;",report["totals"]["automatic_storylines"],"auto storylines;",
       report["totals"]["publisher_headline_links"],"publisher article links")
if __name__=="__main__":main()
