"""Free CC BY-SA TVmaze episode synopsis metadata for past wrestling programs.
A TVmaze episode description is a guide synopsis, NEVER a match result.
"""
from __future__ import annotations
import argparse,json,re
from datetime import date,datetime
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from zoneinfo import ZoneInfo
from proof.evolve_intake import summary_text
from proof.results_intake import broadcast_complete
ET=ZoneInfo("America/New_York")
SHOW_IDS={"raw":802,"smackdown":803,"nxt":2266,"aaa":89983,"tna":1349,"evolve":82403}
MODE="TVMAZE_FINISHED_EPISODE_GUIDE_SYNOPSIS_ONLY"

def request_episodes(show_id:int,day:str,timeout=14)->list:
    if show_id not in SHOW_IDS.values() or not re.fullmatch(r"\d{4}-\d{2}-\d{2}",day):
        raise ValueError("Unapproved show or date")
    req=Request(f"https://api.tvmaze.com/shows/{show_id}/episodesbydate?date={day}",
                headers={"Accept":"application/json","User-Agent":"InsideSquaredCircleHouseholdResearch/1.0"})
    try:
        with urlopen(req,timeout=timeout) as response:
            episodes=json.load(response)
    except HTTPError as err:
        if err.code==404:return []
        raise
    if not isinstance(episodes,list) or len(episodes)>15:
        raise ValueError("Unexpected episode list")
    return episodes

def most_recent_completed(show:dict,now:datetime)->str|None:
    sid=show.get("id")
    if sid not in SHOW_IDS or show.get("schedule_status")!="fresh":return None
    today=now.astimezone(ET).date()
    dates=[]
    for tag in ("previous","next"):
        s=(show.get(tag) or {}).get("date")
        try:day=date.fromisoformat(s)
        except (ValueError,TypeError):continue
        if 0<=(today-day).days<=10 and broadcast_complete(sid,s,now):dates.append(s)
    return max(dates) if dates else None

def build_briefs(snapshot:dict,requester=request_episodes,now=None,previous=None)->dict:
    now=now or datetime.now(ET)
    old=(previous or {}).get("programs",[])
    if not isinstance(old,list):old=[]
    rows=[]
    for show in snapshot.get("shows",[]):
        sid=show.get("id")
        day=most_recent_completed(show,now)
        row={"show_id":sid,"airdate":day,"synopsis":None,"episode_id":None,
             "evidence_url":None,"source_name":"TVmaze","license":"CC BY-SA",
             "status":"no_completed_episode" if not day else "no_synopsis"}
        if day:
            try:
                eps=requester(SHOW_IDS[sid],day)
                for ep in eps:
                    if not isinstance(ep,dict) or ep.get("airdate")!=day:continue
                    ident=ep.get("id")
                    if not isinstance(ident,int) or ident<=0:continue
                    text=summary_text(ep.get("summary"))
                    if len(text)<35 or text.lower().strip(" .") in ("tba","episode information coming soon"):continue
                    row.update(synopsis=text,episode_id=ident,
                               evidence_url=f"https://api.tvmaze.com/episodes/{ident}",
                               status="episode_synopsis")
                    break
            except Exception as exc:
                row["status"]="api_unavailable"
                print("TVmaze episode context delayed:",sid,type(exc).__name__)
            if row["synopsis"] is None:
                same=next((p for p in old if isinstance(p,dict)
                           and p.get("show_id")==sid and p.get("airdate")==day),None)
                if same and isinstance(same.get("episode_id"),int) and same["episode_id"]>0:
                    ident=same["episode_id"]
                    content=same.get("synopsis")
                    if (isinstance(content,str) and 35<=len(content)<=240
                        and same.get("evidence_url")==f"https://api.tvmaze.com/episodes/{ident}"
                        and same.get("license")=="CC BY-SA" and same.get("source_name")=="TVmaze"):
                        row.update(synopsis=content,episode_id=ident,
                                   evidence_url=same["evidence_url"],status="retained_same_episode")
        rows.append(row)
    return {"schema_version":1,"mode":MODE,"generated_at":now.astimezone(ET).isoformat(),
            "policy":"TVmaze CC BY-SA episode synopses only; these may have been written before broadcast. No match winners, title changes, storylines or confirmed appearances may be inferred.",
            "programs":rows,"synopses_available":sum(bool(x["synopsis"]) for x in rows)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--snapshot",default="web/data/snapshot.json")
    ap.add_argument("--out",default="web/data/episode-briefs.json")
    ap.add_argument("--previous",default="web/data/episode-briefs.json")
    args=ap.parse_args()
    snap=json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    if snap.get("schema_version")!=1 or len(snap.get("shows",[]))!=6:
        raise SystemExit("Invalid schedule, not overwriting episode guide")
    try:
        previous=json.loads(Path(args.previous).read_text(encoding="utf-8"))
        if previous.get("mode")!=MODE:previous={}
    except (OSError,ValueError,AttributeError):previous={}
    data=build_briefs(snap,previous=previous)
    path=Path(args.out);tmp=path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    tmp.replace(path)
    print("Licensed TVmaze episode synopses:",data["synopses_available"])
if __name__=="__main__":main()
