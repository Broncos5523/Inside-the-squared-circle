"""WCN PERSONAL / NONCOMMERCIAL home-card collector; output never public.

Written WCN permission in October 2026: personal match-card caching with
on-display Wrestling Central News credit; request at reasonable intervals.
Permission does not include a publicly accessible rebroadcast or site.
Only WCN RSS and its own exact-date WEEKLY Card & preview sections are used.
"""
from __future__ import annotations
import argparse,json,re
from datetime import datetime,date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request,urlopen
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo
ET_TZ=ZoneInfo("America/New_York")
BASE="https://wrestlingcentralnews.com"
FEED=BASE+"/feed.xml"
MODE="PERSONAL_WCN_REPORTED_CARD_FACTS_V1"
SOURCE="Wrestling Central News (wrestlingcentralnews.com)"
WEEKLY={"raw":"wwe-raw","smackdown":"wwe-smackdown","nxt":"wwe-nxt","tna":"tna-impact"}
# Wrestling names must be capitalized, not generic prose. Each short
# match pairing is extracted deterministically and remains unverified.
WORD=r"[A-ZÀ-Ý][A-Za-zÀ-ÿ0-9’'\-]*"
PERSON=rf"{WORD}(?:\s+{WORD}){{0,3}}"
SIDE=rf"(?:The\s+)?{PERSON}(?:\s+(?:&|and)\s+{PERSON})?"
BOUT=re.compile(rf"(?P<a>{SIDE})(?:\s*\([^)]{{1,85}}\))?\s+"
    rf"(?:once\s+again\s+)?(?:faces?|facing|takes?\s+on|collide(?:s)?\s+with|"
    rf"meet(?:s)?|challenge(?:s)?|vs\.?|versus)\s+(?P<b>{SIDE})(?=\s|[.;,!?]|$)")
TITLE_DEFENSE=re.compile(rf"(?P<a>{SIDE})\s+(?:will\s+)?(?:defends?|put(?:s)?|make(?:s)?)\b"
    rf"[^.;:]{{0,130}}?\s+against\s+(?P<b>{SIDE})(?=\s|[.;,!?]|$)")
BETWEEN=re.compile(rf"\b(?:match|bout)\s+between\s+(?P<a>{PERSON})\s+and\s+(?P<b>{PERSON})"
    rf"(?=\s|[.;,!?]|$)")
NOT_THIS_EPISODE=re.compile(
    r"\b(?:pay-per-view|PPV|Destination X|Crown Jewel|Survivor Series|"
    r"next month's event|other promotion|separate event)\b",re.I)
STOPPED=re.compile(r"\b(?:defeated|defeats|pinned|won|retained|winner|spoiler|"
    r"cancelled|canceled|postponed|not medically cleared)\b",re.I)
BAD_NAME=re.compile(r"\b(?:match|championship|title|episode|story|preview|"
    r"card|tonight|last|next|another|bout|event|general manager)\b",re.I)
ADVERTISED=re.compile(r"\bAlso advertised:\s*([^.]{6,260})",re.I)

def approved(url):
    p=urlsplit(url)
    return (p.scheme=="https" and p.hostname in ("wrestlingcentralnews.com","www.wrestlingcentralnews.com")
        and not(p.username or p.password or p.query or p.fragment)
        and (p.path=="/feed.xml" or bool(re.fullmatch(
          r"/events/\d{4}-\d{2}-\d{2}-(?:wwe-raw|wwe-smackdown|wwe-nxt|tna-impact)/",p.path))))

def fetch(url):
    if not approved(url):raise ValueError("URL outside WCN approved scope")
    req=Request(url,headers={"User-Agent":"InsideSquaredCirclePersonalHomeBoard/1.0 (4-hour refresh)",
                              "Accept":"application/rss+xml,text/xml,text/html"})
    with urlopen(req,timeout=14) as resp: raw=resp.read(1_000_001)
    if len(raw)>1_000_000:raise ValueError("Oversize WCN response")
    return raw

def feed_count(raw):
    if len(raw)>1_000_000:raise ValueError("Oversize RSS")
    root=ET.fromstring(raw)
    if root.tag!="rss":raise ValueError("Not a WCN RSS feed")
    return sum(bool((i.findtext("title") or "").strip()) for i in root.findall("./channel/item")[:150])

class Preview(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.section="";self.tag=None;self.parts=[];self.paragraphs=[]
    def handle_starttag(self,tag,attrs):
        if tag in ("h2","p"):self.tag=tag;self.parts=[]
    def handle_data(self,data):
        if self.tag:self.parts.append(data)
    def handle_endtag(self,tag):
        if tag!=self.tag:return
        txt=" ".join("".join(self.parts).split())
        if tag=="h2":self.section=txt.lower()
        if tag=="p" and self.section=="card & preview" and txt:self.paragraphs.append(txt[:1200])
        self.tag=None;self.parts=[]

def normal_side(name):
    # The role prefix is not part of the wrestler's name.
    name=re.split(r"\bChampions?\s+",name)[-1]
    name=re.sub(r"\s+and\s+"," & "," ".join(name.split()))
    return name.strip()

def pairs(paragraph):
    """Use direct future card pairings only. Never infer winners/rumours."""
    if NOT_THIS_EPISODE.search(paragraph):return []
    found=[]
    for chunk in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý])",paragraph):
        # A sentence may list multiple matches separated by semicolons.
        for segment in re.split(r";\s*",chunk):
            if STOPPED.search(segment):continue
            # Intro text ("WWE has announced ...:") is not a wrestler.
            segment=segment.rsplit(":",1)[-1]
            for regex in (BOUT,TITLE_DEFENSE,BETWEEN):
                for match in regex.finditer(segment):
                    a,b=(normal_side(match.group(k)) for k in ("a","b"))
                    if a.casefold()==b.casefold() or BAD_NAME.search(a) or BAD_NAME.search(b):
                        continue
                    if not (3<=len(a)<=70 and 3<=len(b)<=70):continue
                    if any(c in a+b for c in "<>{}[]\n"):continue
                    text=a+" vs. "+b
                    if text not in found:found.append(text)
    return found[:8]

def advertised(paragraph):
    """Explicitly advertised talent only; match competitors are not assumed."""
    if NOT_THIS_EPISODE.search(paragraph) or STOPPED.search(paragraph):return []
    mention=ADVERTISED.search(paragraph)
    if not mention:return []
    people=[]
    for piece in mention.group(1).split(",")[:10]:
        value=" ".join(piece.split())
        if 3<=len(value)<=60 and re.fullmatch(rf"{PERSON}",value) and not BAD_NAME.search(value):
            if value not in people:people.append(value)
    return people[:8]

def parse_page(raw):
    page=Preview()
    page.feed(raw.decode("utf-8","replace")[:1_000_000])
    bouts=[];appearances=[]
    for paragraph in page.paragraphs:
        for bout in pairs(paragraph):
            if bout not in bouts:bouts.append(bout)
        for person in advertised(paragraph):
            if person not in appearances:appearances.append(person)
    return {"matches":bouts[:8],"appearances":appearances[:8]}

def build(snapshot,requester=fetch,now=None):
    now=(now or datetime.now(ET_TZ)).astimezone(ET_TZ)
    if snapshot.get("schema_version")!=1 or len(snapshot.get("shows",[]))!=6:
        raise ValueError("Six-show TVmaze snapshot required")
    try: count=feed_count(requester(FEED));rss_status="ok"
    except Exception as exc:count=0;rss_status=type(exc).__name__
    out=[]
    for show in snapshot["shows"]:
        sid=show.get("id");air=(show.get("next") or {}).get("date")
        row={"show_id":sid,"airdate":air,"matches":[],"appearances":[],"source_name":SOURCE}
        if sid not in WEEKLY or show.get("schedule_status")!="fresh":
            out.append(row);continue
        try:
            air_day=date.fromisoformat(air)
            if not 0<=(air_day-now.date()).days<=14:out.append(row);continue
        except (ValueError,TypeError):out.append(row);continue
        url=BASE+"/events/"+air+"-"+WEEKLY[sid]+"/"
        try:
            parsed=parse_page(requester(url))
            for result in parsed["matches"]:
                row["matches"].append({"text":result,"stipulation":"MATCH",
                   "status":"REPORTED_UNVERIFIED","source_name":SOURCE,"evidence_url":url})
            for name in parsed["appearances"]:
                row["appearances"].append({"text":name,"type":"Advertised appearance",
                   "status":"REPORTED_UNVERIFIED","source_name":SOURCE,"evidence_url":url})
        except Exception as exc:row["source_delayed"]=type(exc).__name__
        out.append(row)
    return {"schema_version":1,"mode":MODE,"generated_at":now.isoformat(),
            "usage":"PERSONAL_NONCOMMERCIAL_HOME_DISPLAY_ONLY",
            "display_attribution":SOURCE,"rss_status":rss_status,
            "rss_headlines_examined":count,"programs":out,
            "total_reported_matches":sum(len(x["matches"]) for x in out),
            "total_reported_appearances":sum(len(x["appearances"]) for x in out)}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot",default="web/data/snapshot.json")
    p.add_argument("--out",default="private/wcn-match-cards.json")
    args=p.parse_args();path=Path(args.out)
    if path.as_posix() not in {"private/wcn-match-cards.json","web/data/wcn-match-cards-private.json"} and not path.as_posix().startswith("/tmp/"):
        p.error("Output must be private/ignored or ephemeral /tmp")
    try:
        prior=json.loads(path.read_text(encoding="utf-8"))
        stamp=datetime.fromisoformat(prior["generated_at"]).astimezone(ET_TZ)
        if 0<=(datetime.now(ET_TZ)-stamp).total_seconds()<900:
            print("WCN private cache younger than 15 minutes; no request")
            return
    except (OSError,ValueError,KeyError,TypeError):pass
    snapshot=json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    output=build(snapshot)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(".tmp")
    tmp.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    tmp.replace(path)
    print("WCN PRIVATE audit: RSS",output["rss_status"],"headlines",output["rss_headlines_examined"],
          "dated advance-card matchups",output["total_reported_matches"],
          "explicit advertised appearances",output["total_reported_appearances"],"NOT PUBLISHED")

if __name__=="__main__":main()
