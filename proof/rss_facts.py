"""Very limited factual match-outcome leads from *syndicated RSS headlines*.

Inputs are ONLY public publisher RSS headlines/links already collected by
proof.recap_links. No publisher-article scraping, no full feed descriptions.
Do not infer match outcomes or title changes from generic article headlines,
preview matchups, or pre-telecast 'live results' titles.
"""
from __future__ import annotations
import argparse
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from proof.results_intake import broadcast_complete

TZ=ZoneInfo("America/New_York")
MODE="POST_BROADCAST_RSS_EXPLICIT_FACTS_UNVERIFIED"
FEED_MODE="PUBLISHER_RSS_POST_SHOW_LINKS_ONLY"
ALLOWED={"raw","smackdown","nxt","tna","evolve"}
APPROVED={
    "411Mania":{"411mania.com","www.411mania.com"},
    "Fightful":{"fightful.com","www.fightful.com"},
    "F4W / Wrestling Observer":{"f4wonline.com","www.f4wonline.com"},
}
SHOW={
  "raw":re.compile(r"\b(?:wwe\s+)?raw\b",re.I),
  "smackdown":re.compile(r"\bsmack[\s-]?down\b",re.I),
  "nxt":re.compile(r"\b(?:wwe\s+)?nxt\b",re.I),
  "tna":re.compile(r"\b(?:tna\s+)?(?:impact|iMPACT!)\b",re.I),
  "evolve":re.compile(r"\b(?:wwe\s+)?evolve\b",re.I),
}
DATE_FORMATS=("%m/%d/%Y","%m/%d/%y","%m.%d.%Y","%m.%d.%y","%m-%d-%Y","%m-%d-%y")
DATE_TOKEN=re.compile(r"(?<!\d)(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})(?!\d)")
NAME=r"[A-Z][A-Za-zÀ-ÿ0-9.'\-\s&]{1,66}"
MATCH=re.compile(r"^\s*("+NAME+r")\s+(?:defeats?|defeated|def\.)\s+("+NAME+r")\s*$",re.I)
# Only source-headline claims about a completed episode; no preview claims.
REJECT=re.compile(r"\b(?:preview|spoilers?|rumou?r|prediction|taping|"
                  r"possible|could|might|may|would|likely|expected|tonight|will|"
                  r"to\s+face|to\s+return|upcoming|next\s+week|"
                  r"live\s+results|simulation|fantasy)\b",re.I)
LABEL=re.compile(r"\b(?:results?|recap|review|fallout)\b",re.I)
PUBLISHED_WINDOW=timedelta(hours=72)
AGE_LIMIT=10


def current_completed_airdate(show:dict, sid:str, now:datetime)->str|None:
    today=now.astimezone(TZ).date()
    dates=set()
    for key in ("previous","next"):
        day=(show.get(key) or {}).get("date")
        try:
            date_value=date.fromisoformat(day)
        except (ValueError,TypeError):
            continue
        if 0 <= (today-date_value).days<=AGE_LIMIT and broadcast_complete(sid,day,now):
            dates.add(day)
    return max(dates) if dates else None


def explicitly_dated(headline:str, airdate:str)->bool:
    """Deny generic coverage claims without an explicit episode date."""
    expected=date.fromisoformat(airdate)
    for m in DATE_TOKEN.finditer(headline):
        token=m.group(1)
        for fmt in DATE_FORMATS:
            try:
                if datetime.strptime(token,fmt).date()==expected:
                    return True
            except ValueError:
                continue
    # Accept same-date URL dates only in the collector if headline undated?
    # No: the broadcast should not transform a generic headline into an
    # episode-specific match result just because publication time is close.
    return False


def explicit_outcome_from_headline(headline:str, sid:str, day:str)->dict|None:
    if not isinstance(headline,str) or len(headline)>160 or REJECT.search(headline):
        return None
    if not LABEL.search(headline) or not SHOW[sid].search(headline):
        return None
    if sum(bool(p.search(headline)) for p in SHOW.values()) != 1:
        return None
    if not explicitly_dated(headline,day):
        return None
    # Require "results: X defeated Y" after the show name/date; avoid
    # parsing "X vs Y", which is often just an advance card.
    if ":" not in headline:
        return None
    result_clause=headline.rsplit(":",1)[-1].strip()
    match=MATCH.fullmatch(result_clause)
    if not match:
        return None
    winner,loser=(" ".join(x.split()) for x in match.groups())
    if len(winner)<3 or len(loser)<3 or winner.casefold()==loser.casefold():
        return None
    if re.search(r"\b(?:news|results?|championship|live|date|updates)\b",
                 winner+" "+loser,re.I):
        return None
    return {"text":f"{winner} defeated {loser}","match_type":"Match result"}


def build_facts(snapshot:dict, rss:dict,now:datetime|None=None)->dict:
    now=now or datetime.now(TZ)
    if rss.get("mode")!=FEED_MODE:
        raise ValueError("RSS link source mode mismatch")
    all_records=[]
    counted=0
    for show in snapshot.get("shows",[]):
        sid=show.get("id")
        air=current_completed_airdate(show,sid,now) if sid in ALLOWED else None
        record={"show_id":sid,"airdate":air,"results":[],"developments":[],
                "status":"no_post_broadcast_explicit_outcomes" if air else "no_completed_episode"}
        old=next((x for x in rss.get("programs",[]) if isinstance(x,dict)
                  and x.get("show_id")==sid and x.get("airdate")==air),None)
        if old and isinstance(old.get("links"),list):
            seen=set()
            for link in old["links"][:8]:
                if not isinstance(link,dict) or link.get("status")!="PUBLISHER_HEADLINE_LINK_ONLY":
                    continue
                publisher=link.get("source_name")
                if publisher not in APPROVED:
                    continue
                url=link.get("url","")
                try:
                    parts=urlsplit(url)
                except ValueError:
                    continue
                if parts.scheme!="https" or parts.hostname not in APPROVED[publisher] or parts.query or parts.fragment:
                    continue
                try:
                    published=datetime.fromisoformat(link["published_at"])
                except (KeyError,TypeError,ValueError):
                    continue
                if published.tzinfo is None:
                    continue
                published=published.astimezone(TZ)
                broadcast_end=(datetime.combine(date.fromisoformat(air),datetime.min.time(),tzinfo=TZ)
                               + (timedelta(hours=23,minutes=15) if sid=="tna"
                                  else timedelta(days=1,hours=4)))
                # Source publication MUST follow TV end; "live results"
                # titles that exist before the show may be a preview.
                if not broadcast_end <= published <= min(now.astimezone(TZ),broadcast_end+PUBLISHED_WINDOW):
                    continue
                claim=explicit_outcome_from_headline(link.get("headline"),sid,air)
                if not claim:
                    continue
                signature=re.sub(r"[^a-z0-9]","",claim["text"].lower())
                if signature in seen:
                    continue
                seen.add(signature)
                record["results"].append({
                    **claim,"source_name":publisher,"source_url":url,
                    "published_at":published.isoformat(),
                    "status":"REPORTED_UNVERIFIED",
                    "evidence_type":"RSS_EXPLICIT_HEADLINE",
                })
                if len(record["results"])>=5:
                    break
            if record["results"]:
                record["status"]="explicit_post_broadcast_results"
        counted+=len(record["results"])
        all_records.append(record)
    return {"schema_version":1,"mode":MODE,"generated_at":now.astimezone(TZ).isoformat(),
            "policy":"Extremely strict direct winner-vs-loser statements only from dated post-broadcast public RSS headlines. No full articles read; no title changes or storylines inferred. Source-attributed and unverified. Zero results is an expected safe outcome.",
            "programs":all_records,"total_reported_results":counted}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--snapshot",default="web/data/snapshot.json")
    ap.add_argument("--links",default="web/data/recap-links.json")
    ap.add_argument("--out",default="web/data/rss-facts.json")
    args=ap.parse_args()
    snap=json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    links=json.loads(Path(args.links).read_text(encoding="utf-8"))
    if snap.get("schema_version")!=1 or len(snap.get("shows",[]))!=6:
        raise SystemExit("Invalid show schedule, not overwriting RSS facts")
    data=build_facts(snap,links)
    out=Path(args.out)
    tmp=out.with_suffix(".tmp")
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    tmp.replace(out)
    print("Post-air dated RSS explicit outcomes:",data["total_reported_results"])


if __name__=="__main__":
    main()
