"""Extract brief factual outcomes only from publishers' own syndicated RSS excerpts.

No website scraping, no article bodies, no redistributing excerpts.
Strictly date-matched, broadcast-completed result headlines, approved RSS hosts,
visible 'defeated' statements only. Each extracted fact retains source evidence,
and is never treated as officially confirmed.
"""
from __future__ import annotations
import argparse,json,re
from datetime import datetime,date,timedelta,time
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as XML
from zoneinfo import ZoneInfo

from proof.recap_links import (
    FEED_URLS,PUBLISHERS,clean_link,filter_title,request_rss
)
from proof.rss_facts import current_completed_airdate,explicitly_dated
from proof.results_intake import broadcast_complete

ET=ZoneInfo("America/New_York")
MODE="POST_BROADCAST_RSS_SYNDICATED_EXCERPT_FACTS_UNVERIFIED"
SHOWS=("raw","smackdown","nxt","aaa","tna","evolve")
MAX_EXCERPT=3000
# A subset of syndicated recap summaries begin with an explicit in-show
# context phrase. Accept only these narrow intros, never arbitrary prose.
CONTEXT_PREFIX=re.compile(
    r"^(?:In the opening contest,?\s*|In the main event,?\s*|"
    r"In the opener,?\s*|In the opening match,?\s*)",re.I)
CONTEXT_SUFFIX=re.compile(r"\s+in (?:a|an|the) (?:great|hard-fought|competitive|back-and-forth|"
                           r"exciting|entertaining|singles|tag(?: team)?)?[\s-]*(?:match|encounter)\.?$",re.I)
WIN=re.compile(
    r"^\s*([A-Z][A-Za-zÀ-ÿ0-9'’.,()\-& ]{2,80}?)\s+"
    r"(?:defeated|defeats|def\.|beat)\s+"
    r"([A-Z][A-Za-zÀ-ÿ0-9'’.,()\-& ]{2,95}?)"
    r"(?:\s+(?:by\s+(?:pinfall|submission|countout|disqualification)|via\s+(?:DQ|pinfall|submission)))?"
    r"[.!]?\s*$",re.I)
BLOCK=re.compile(r"\b(?:spoiler|rumou?r|prediction|preview|hypothetical|might|"
                 r"may|could|would|likely|expected|next\s+week|last\s+week|"
                 r"last\s+night|earlier\s+this\s+month|dark\s+match|"
                 r"taping|tonight|will\s+face)\b",re.I)

class SyndicatedExcerpt(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lines=[]
        self.buffer=[]
        self.ignore=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","iframe"):
            self.ignore+=1
        if tag in ("p","div","li","br","h2","h3","h4"):
            self._flush()
    def handle_endtag(self,tag):
        if tag in ("script","style","iframe"):
            self.ignore=max(0,self.ignore-1)
        if tag in ("p","div","li","h2","h3","h4"):
            self._flush()
    def handle_data(self,data):
        if not self.ignore:self.buffer.append(data)
    def _flush(self):
        text=" ".join("".join(self.buffer).split())
        if text:self.lines.append(text)
        self.buffer=[]
    def finish(self):
        self._flush()
        return self.lines[:30]

def parse_excerpt_sentences(raw):
    if not isinstance(raw,str) or len(raw)>MAX_EXCERPT or not raw.strip():
        return []
    parser=SyndicatedExcerpt()
    parser.feed(raw)
    out=[]
    for line in parser.finish():
        for item in re.split(r"(?<=[.!?])\s+(?=[A-Z])",line):
            item=item.strip(" \t-•")
            if len(item)<5 or len(item)>195:continue
            if BLOCK.search(item):continue
            candidate=CONTEXT_PREFIX.sub('',item)
            candidate=CONTEXT_SUFFIX.sub('.',candidate)
            match=WIN.fullmatch(candidate)
            if not match:continue
            left,right=(re.sub(r"\s+"," ",v).strip(" .,") for v in match.groups())
            if left.lower()==right.lower() or len(left)<3 or len(right)<3:continue
            if any(re.search(r"\b"+re.escape(phrase)+r"\b",left+" "+right,re.I)
                   for phrase in ("results","recap","match","report","wwe","tna","tonight")):
                continue
            out.append({"text":f"{left} defeated {right}","match_type":"Match result"})
            if len(out)>=8:return out
    return out

def parse_syndicated_feed(raw):
    if not isinstance(raw,bytes) or len(raw)>2_000_000:
        raise ValueError("Unbounded RSS data")
    root=XML.fromstring(raw)
    if root.tag!="rss":raise ValueError("RSS syndication required")
    items=[]
    for item in root.findall("./channel/item")[:180]:
        title=item.findtext("title") or ""
        link=clean_link(item.findtext("link"))
        if not link:continue
        try:
            stamp=parsedate_to_datetime(item.findtext("pubDate") or "")
            if stamp.tzinfo is None:continue
        except (ValueError,TypeError,IndexError):
            continue
        # Only a publisher's intentionally syndicated summary: never
        # inspect content:encoded or fetch a separate publisher web page.
        excerpt=item.findtext("description") or ""
        if len(excerpt)>MAX_EXCERPT:continue
        items.append({"title":title,"url":link,"published_at":stamp.astimezone(ET),
                      "source_name":PUBLISHERS[urlsplit(link).hostname],
                      "excerpt":excerpt})
    return items

def build_results(snapshot,entries,now=None):
    now=now or datetime.now(ET)
    today=now.astimezone(ET)
    rows=[]
    for show in snapshot.get("shows",[]):
        sid=show.get("id")
        air=current_completed_airdate(show,sid,today) if sid in SHOWS and sid!="aaa" else None
        row={"show_id":sid,"airdate":air,"results":[],
             "status":"no_explicit_syndicated_results" if air else "no_completed_broadcast"}
        if not air:
            rows.append(row);continue
        broadcast_end=(datetime.combine(date.fromisoformat(air),time(23,15),tzinfo=ET) if sid=="tna"
                      else datetime.combine(date.fromisoformat(air)+timedelta(days=1),time(4),tzinfo=ET))
        seen=set()
        for item in entries:
            # Same exact TV episode, not a different show or adjacent taping.
            title=filter_title(item.get("title"),sid,air)
            if not title or not explicitly_dated(title,air):continue
            link=clean_link(item.get("url"))
            if not link or item.get("source_name")!=PUBLISHERS[urlsplit(link).hostname]:continue
            timestamp=item.get("published_at")
            if not isinstance(timestamp,datetime) or timestamp.tzinfo is None:continue
            stamp=timestamp.astimezone(ET)
            if not broadcast_end <= stamp <= min(today,broadcast_end+timedelta(hours=72)):
                continue
            for fact in parse_excerpt_sentences(item.get("excerpt")):
                sig=re.sub("[^a-z0-9]","",fact["text"].lower())
                if sig in seen:continue
                seen.add(sig)
                row["results"].append({**fact,"status":"REPORTED_UNVERIFIED",
                    "source_name":item["source_name"],"source_url":link,
                    "published_at":stamp.isoformat(),"evidence_type":"RSS_SYNDICATED_EXCERPT_FACT"})
                if len(row["results"])>=8:break
            if len(row["results"])>=8:break
        if row["results"]:row["status"]="explicit_source_outcomes"
        rows.append(row)
    return {"schema_version":1,"mode":MODE,"generated_at":today.isoformat(),
      "policy":"Short factual winner/loser statements only from approved publisher-syndicated RSS descriptions after broadcast. Excerpt not published. Zero is acceptable; no website scraping, source quotes, title changes or storyline inference.",
      "programs":rows,"total_reported_results":sum(len(x["results"]) for x in rows)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--snapshot",default="web/data/snapshot.json")
    p.add_argument("--out",default="web/data/rss-excerpt-results.json")
    args=p.parse_args()
    snapshot=json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    if snapshot.get("schema_version")!=1 or len(snapshot.get("shows",[]))!=6:
        raise SystemExit("Schedule invalid, no replacement")
    items=[]
    successful=0
    for url in FEED_URLS:
        try:
            items.extend(parse_syndicated_feed(request_rss(url=url)))
            successful+=1
        except Exception as exc:
            print("RSS excerpt provider unavailable:",type(exc).__name__,url)
    feed=build_results(snapshot,items)
    feed["working_rss_feeds"]=successful
    path=Path(args.out)
    tmp=path.with_suffix(".tmp")
    tmp.write_text(json.dumps(feed,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    tmp.replace(path)
    print("Post-TV publisher RSS excerpt results:",feed["total_reported_results"],
          "working feeds:",successful)

if __name__=="__main__":
    main()
