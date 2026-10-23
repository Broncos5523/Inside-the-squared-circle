"""Validate opt-in, human-reviewed wrestling episode facts. No scraping or autofill."""
from __future__ import annotations
import argparse
import json
import re
from datetime import date, datetime, time, timedelta
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
MODE = "REVIEWED_WEEKLY_EPISODE_FACTS_V1"
SHOWS = {"raw", "smackdown", "nxt", "aaa", "tna", "evolve"}
HOSTS = {"wwe.com", "tnawrestling.com", "411mania.com", "f4wonline.com",
         "fightful.com", "blogofdoom.com", "thesmackdownhotel.com",
         "prowrestling.net", "tpww.net", "gerweck.net", "wrestlingheadlines.com"}
WINNER = re.compile(r"\b(defeated|defeats|beat|won|ended in|draw|no contest|count.out|"
                    r"disqualification|retained)\b", re.I)

class ReviewError(ValueError):
    pass

def check(condition, msg):
    if not condition: raise ReviewError(msg)

def parse_day(value):
    check(isinstance(value, str) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)),
          "Exact YYYY-MM-DD airdate required")
    try: return date.fromisoformat(value)
    except ValueError as e: raise ReviewError("Invalid airdate") from e

def allowed_url(value):
    if not isinstance(value, str) or len(value)>500: return False
    u=urlsplit(value)
    return (u.scheme=="https" and u.hostname in HOSTS | {"www."+h for h in HOSTS}
            and bool(u.path and u.path!="/") and not u.username and not u.password
            and not u.fragment)

def episode_complete(show,day):
    # Conservative gate: no result before completion of the broadcast.
    if show=="tna": return datetime.combine(day,time(23,15),ET)
    return datetime.combine(day+timedelta(days=1),time(4),ET)

def validate_feed(feed,now=None):
    now=(now or datetime.now(ET)).astimezone(ET)
    check(isinstance(feed,dict),"Root JSON object required")
    check(feed.get("schema_version")==1 and feed.get("mode")==MODE,"Invalid schema/mode")
    programs=feed.get("programs")
    check(isinstance(programs,list) and len(programs)<=6,"At most six shows")
    stamp=feed.get("reviewed_at_et")
    if not programs:
        check(stamp is None or isinstance(stamp,str),"Invalid review timestamp")
        return feed
    check(isinstance(stamp,str),"Review timestamp required")
    try:
        reviewed=datetime.fromisoformat(stamp)
        check(reviewed.tzinfo is not None,"Review timestamp needs timezone offset")
        reviewed=reviewed.astimezone(ET)
    except (TypeError,ValueError) as exc:
        raise ReviewError("Invalid human review timestamp") from exc
    check(reviewed<=now+timedelta(minutes=5),"Future review timestamp")
    seen=set()
    for rec in programs:
        check(isinstance(rec,dict),"Invalid show entry")
        sid=rec.get("show_id")
        check(sid in SHOWS and sid not in seen,"Invalid or duplicate show")
        seen.add(sid)
        airdate=parse_day(rec.get("airdate"))
        check(episode_complete(sid,airdate)<=reviewed,"Episode has not finished broadcasting")
        check(rec.get("review_method")=="MANUAL_SOURCE_REVIEW","Human review is required")
        check(rec.get("reuse_basis")=="FACT_ONLY_PARAPHRASE","Only original factual paraphrases")
        check(isinstance(rec.get("source_name"),str) and
              3<=len(rec["source_name"])<=100,"Named publisher required")
        check(allowed_url(rec.get("source_url")),"Unapproved source URL")
        results,notes=rec.get("results"),rec.get("developments")
        check(isinstance(results,list) and isinstance(notes,list)
              and len(results)<=10 and len(notes)<=10 and
              bool(results or notes),"One or more facts, max ten of each")
        facts_seen=set()
        for rows,kind,limit,is_result in [(results,"match_type",110,True),
                                           (notes,"type",100,False)]:
            for row in rows:
                check(isinstance(row,dict),"Fact object required")
                check(row.get("status")=="REPORTED_UNVERIFIED","Source confidence required")
                title=row.get("text")
                check(isinstance(title,str) and 8<=len(title)<=190
                      and "<" not in title and ">" not in title
                      and "\n" not in title,"Short fact-only paraphrase required")
                field=row.get(kind)
                check(isinstance(field,str) and 2<=len(field)<=limit,
                      "Match type or storyline type required")
                check(allowed_url(row.get("source_url",rec["source_url"])),
                      "Fact must preserve a source URL")
                if is_result:
                    check(bool(WINNER.search(title)),"Advance card is not a match outcome")
                signature=re.sub(r"\W","",title.lower())
                check(signature not in facts_seen,"Duplicate episode fact")
                facts_seen.add(signature)
    return feed

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",default="web/data/reviewed-recaps.json")
    p.add_argument("--out",help="Write validated reviewed JSON only by explicit action")
    p.add_argument("--verify",action="store_true",help="Validate without writing")
    args=p.parse_args()
    if args.out and args.verify: p.error("--out and --verify conflict")
    try:
        feed=validate_feed(json.loads(Path(args.input).read_text(encoding="utf-8")))
    except (ReviewError,ValueError,OSError) as exc:
        p.error(str(exc))
    if args.out:
        out=Path(args.out)
        out.parent.mkdir(parents=True,exist_ok=True)
        tmp=out.with_suffix(".tmp")
        tmp.write_text(json.dumps(feed,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        tmp.replace(out)
    print("Reviewed episodes:",len(feed["programs"]),
          "outcomes:",sum(len(x["results"]) for x in feed["programs"]),
          "developments:",sum(len(x["developments"]) for x in feed["programs"]))

if __name__=="__main__": main()
