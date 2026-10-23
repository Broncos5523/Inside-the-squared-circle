"""Short sourced post-show rivalry and return facts from public RSS descriptions.

No article scraping, no article text redistribution, no invented winner or title
changes. Each factual subject-verb-object line must appear in a publisher's
syndicated excerpt and match an exact completed TV episode.
"""
from __future__ import annotations
import argparse,json,re
from datetime import date,datetime,timedelta,time
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from proof.recap_links import FEED_URLS,PUBLISHERS,clean_link,filter_title,request_rss
from proof.rss_excerpt_results import parse_syndicated_feed,SyndicatedExcerpt,MAX_EXCERPT
from proof.rss_facts import current_completed_airdate,explicitly_dated

ET=ZoneInfo("America/New_York")
MODE="POST_BROADCAST_RSS_FALLOUT_FACTS_UNVERIFIED"
BANNED=re.compile(r"\b(?:preview|spoiler|prediction|rumou?r|might|may|would|"
    r"could|likely|expected|scheduled|reportedly|according to|allegedly|"
    r"tonight|tomorrow|next week|last week|last night|"
    r"possibly|hypothetical|was expected|will|plans to|dark match)\b",re.I)
PERSON=r"([A-Z][A-Za-zÀ-ÿ0-9.'’&\- ]{2,67}?)"
CONFRONTATION=re.compile(r"^\s*"+PERSON+r"\s+(attacked|confronted|challenged|interrupted)\s+"
                         +PERSON+r"\s*[.!]?\s*$")
RETURN=re.compile(r"^\s*"+PERSON+
                  r"\s+returned\s+to\s+(?:WWE\s+)?(Raw|SmackDown|NXT|TNA|iMPACT!|Evolve)"
                  r"\s*[.!]?\s*$",re.I)
INVALID_NAME=re.compile(r"\b(?:news|report|results|recap|the fans|the show|review|"
                        r"highlights|our reporter|this week|wwe|tna|the company|"
                        r"the announcers|championship match)\b",re.I)
SHOWS=("raw","smackdown","nxt","aaa","tna","evolve")
TYPES={"attacked":"POST-MATCH FALLOUT","confronted":"CONFRONTATION",
       "challenged":"CHALLENGE","interrupted":"SEGMENT INTERRUPTION"}

def parse_developments(raw:object)->list[dict]:
    """Explicit statements only; not summaries, speculations, or match cards."""
    if not isinstance(raw,str) or len(raw)>MAX_EXCERPT or not raw.strip():
        return []
    parser=SyndicatedExcerpt()
    parser.feed(raw)
    out=[]
    for line in parser.finish():
        for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z])",line):
            s=" ".join(sentence.split()).strip(" \t-•")
            if not 10 <= len(s)<=175 or BANNED.search(s) or ":" in s or "?" in s:
                continue
            m=CONFRONTATION.fullmatch(s)
            if m:
                a,verb,b=(x.strip(" .,-") for x in m.groups())
                if not 3<=len(a)<=70 or not 3<=len(b)<=70:
                    continue
                if a.lower()==b.lower() or INVALID_NAME.search(a+" "+b):
                    continue
                out.append({"text":f"{a} {verb.lower()} {b}","type":TYPES[verb.lower()]})
            else:
                m=RETURN.fullmatch(s)
                if not m:continue
                who,show=m.group(1).strip(" .,-"),m.group(2)
                if len(who)<3 or INVALID_NAME.search(who):continue
                out.append({"text":f"{who} returned to {show}","type":"RETURN"})
            if len(out)>=6:return out
    return out

def build_fallout(snapshot:dict,entries:list[dict],now:datetime|None=None)->dict:
    now=now or datetime.now(ET)
    moment=now.astimezone(ET)
    rows=[]
    for show in snapshot.get("shows",[]):
        sid=show.get("id")
        aired=current_completed_airdate(show,sid,moment) if sid in SHOWS and sid!="aaa" else None
        row={"show_id":sid,"airdate":aired,"developments":[],
             "status":"no_explicit_fallout" if aired else "no_recent_broadcast"}
        if not aired:
            rows.append(row);continue
        end=(datetime.combine(date.fromisoformat(aired),time(23,15),tzinfo=ET)
             if sid=="tna" else datetime.combine(date.fromisoformat(aired)+timedelta(days=1),time(4),tzinfo=ET))
        signatures=set()
        for feed in entries:
            title=filter_title(feed.get("title"),sid,aired)
            if not title or not explicitly_dated(title,aired):continue
            url=clean_link(feed.get("url"))
            if not url or PUBLISHERS[urlsplit(url).hostname]!=feed.get("source_name"):continue
            stamp=feed.get("published_at")
            if not isinstance(stamp,datetime) or stamp.tzinfo is None:continue
            stamp=stamp.astimezone(ET)
            if not end<=stamp<=min(moment,end+timedelta(hours=72)):continue
            for fact in parse_developments(feed.get("excerpt")):
                signature=re.sub("[^a-z0-9]","",fact["text"].lower())
                if signature in signatures:continue
                signatures.add(signature)
                row["developments"].append({**fact,"status":"REPORTED_UNVERIFIED",
                    "source_name":feed["source_name"],"source_url":url,
                    "published_at":stamp.isoformat(),"evidence_type":"RSS_SYNDICATED_FALLOUT_FACT"})
                if len(row["developments"])>=6:break
            if len(row["developments"])>=6:break
        if row["developments"]:row["status"]="explicit_syndicated_fallout"
        rows.append(row)
    return {"schema_version":1,"mode":MODE,
            "generated_at":moment.isoformat(),
            "policy":"Post-broadcast exact-date subject/verb/object factual developments only. Original RSS excerpts not republished; no title-change or match-winner inference. Unverified provenance retained in JSON, not presented as official.",
            "programs":rows,
            "total_developments":sum(len(x["developments"]) for x in rows)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--snapshot",default="web/data/snapshot.json")
    p.add_argument("--out",default="web/data/rss-fallout.json")
    args=p.parse_args()
    snap=json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    if snap.get("schema_version")!=1 or len(snap.get("shows",[]))!=6:
        raise SystemExit("Invalid schedule, no overwrite")
    records=[];worked=0
    for feed in FEED_URLS:
        try:
            records.extend(parse_syndicated_feed(request_rss(url=feed)))
            worked+=1
        except Exception as error:
            print("Publisher fallout feed unavailable:",type(error).__name__,feed)
    out=build_fallout(snap,records)
    out["working_feeds"]=worked
    dest=Path(args.out);tmp=dest.with_suffix(".tmp")
    tmp.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    tmp.replace(dest)
    print("Exact-date TV fallout facts:",out["total_developments"],
          "working feeds:",worked)

if __name__=="__main__":main()
