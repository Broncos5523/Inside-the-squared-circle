"""Limited attribution-only post-show coverage discovery from an explicit RSS feed.

Use only the publicly syndicated headline, date and hyperlink. Never fetch
article bodies, derive winners, imply results verification or scrape WWE/TNA.
This is useful when API-level match results are unavailable.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, time, timezone
from email.utils import parsedate_to_datetime
import json
from pathlib import Path
import re
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

from proof.results_intake import broadcast_complete

TZ = ZoneInfo("America/New_York")
MODE = "PUBLISHER_RSS_POST_SHOW_LINKS_ONLY"
FEED_URL = "https://www.f4wonline.com/rss.xml"
ALLOWED_HOSTS = {"www.f4wonline.com", "f4wonline.com"}
RESULT_WORDS = re.compile(r"\b(?:results?|recap|fallout)\b", re.I)
EXCLUDE = re.compile(
    r"\b(?:spoilers?|taping|predictions?|preview|ratings|"
    r"rumou?rs?|upcoming|advertised|tonight|"
    r"live\s+coverage\s+preview)\b", re.I
)
SHOW_MARKERS = {
    "raw": re.compile(r"\b(?:wwe[\s:-]+)?raw\b", re.I),
    "smackdown": re.compile(r"\bsmack[\s-]?down\b", re.I),
    "nxt": re.compile(r"\b(?:wwe[\s:-]+)?nxt\b", re.I),
    "tna": re.compile(r"\b(?:tna[\s:-]+impact|impact[\s:-]+wrestling)\b", re.I),
    "evolve": re.compile(r"\b(?:wwe[\s:-]+)?evolve\b", re.I),
}
INLINE_DATE = re.compile(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-]\d{2,4})?\b")
MONTHS = ("January","February","March","April","May","June","July",
          "August","September","October","November","December")
WRITTEN_DATE = re.compile(
    r"\b("+"|".join(MONTHS)+r")\s+([0-3]?\d)(?:st|nd|rd|th)?\b", re.I
)


def clean_link(url: object) -> str | None:
    if not isinstance(url, str):
        return None
    try:
        p = urlsplit(url.strip())
    except ValueError:
        return None
    if p.scheme != "https" or p.hostname not in ALLOWED_HOSTS or p.username or p.password:
        return None
    if not p.path.startswith("/") or len(p.path) < 3:
        return None
    return urlunsplit(("https",p.hostname,p.path,"",""))


def filter_title(title: object, show_id: str, aired: str) -> str | None:
    """Title is a *publisher headline link*, not a verified match result."""
    if not isinstance(title, str):
        return None
    title = " ".join(title.split()).strip()
    if not 12 <= len(title) <= 150 or EXCLUDE.search(title) or not RESULT_WORDS.search(title):
        return None
    marker = SHOW_MARKERS.get(show_id)
    if not marker or not marker.search(title):
        return None
    # Prevent crossover NXT/SmackDown/WWE RAW article from being assigned
    # across programs merely because another show was mentioned.
    if sum(bool(regex.search(title)) for regex in SHOW_MARKERS.values()) != 1:
        return None
    try:
        d = date.fromisoformat(aired)
    except (TypeError, ValueError):
        return None
    for m in INLINE_DATE.finditer(title):
        mon, day = int(m.group(1)), int(m.group(2))
        if 1 <= mon <= 12 and 1 <= day <= 31 and (mon,day) != (d.month,d.day):
            return None
    for m in WRITTEN_DATE.finditer(title):
        mon=next((i+1 for i,name in enumerate(MONTHS) if name.lower()==m.group(1).lower()),None)
        if mon and (mon,int(m.group(2))) != (d.month,d.day):
            return None
    return title


def request_rss(timeout: int = 14) -> bytes:
    req = Request(FEED_URL, headers={
        "User-Agent":"InsideSquaredCircleHouseholdResearch/0.8",
        "Accept":"application/rss+xml,application/xml,text/xml",
    })
    with urlopen(req, timeout=timeout) as response:
        result = response.read(2_000_001)
    if len(result)>2_000_000:
        raise ValueError("RSS response exceeded limit")
    return result


def parse_feed(raw: bytes) -> list[dict]:
    if not isinstance(raw, bytes) or len(raw)>2_000_000:
        raise ValueError("Invalid RSS source")
    root = ET.fromstring(raw)
    # RSS feed is deliberately explicit; no HTML/article scraping.
    if root.tag != "rss":
        raise ValueError("Unexpected syndication schema")
    entries = []
    for item in root.findall("./channel/item")[:200]:
        title = item.findtext("title") or ""
        url = clean_link(item.findtext("link"))
        posted = item.findtext("pubDate")
        if not url or not posted:
            continue
        try:
            stamp = parsedate_to_datetime(posted)
            if stamp.tzinfo is None:
                continue
            stamp = stamp.astimezone(timezone.utc)
        except (ValueError, TypeError, IndexError):
            continue
        entries.append({"title":title,"url":url,"published_at":stamp})
    return entries


def eligible_dates(program: dict, now: datetime) -> list[str]:
    if program.get("id") not in SHOW_MARKERS:
        return []
    sid = program["id"]
    today=now.astimezone(TZ).date()
    dates=[]
    for field in ("next","previous"):
        aired=(program.get(field) or {}).get("date")
        try:
            d=date.fromisoformat(aired)
        except (ValueError,TypeError):
            continue
        if 0 <= (today-d).days <= 10 and broadcast_complete(sid,aired,now):
            if aired not in dates:
                dates.append(aired)
    return sorted(dates,reverse=True)


def build_links(snapshot: dict, entries: list[dict], now=None) -> dict:
    now = now or datetime.now(TZ)
    programs=[]
    for show in snapshot.get("shows",[]):
        sid=show.get("id")
        row={"show_id":sid,"airdate":None,"links":[],
             "source_name":"F4W / Wrestling Observer",
             "status":"not_supported" if sid=="aaa" else "no_matching_published_coverage"}
        for day in eligible_dates(show,now):
            day_start=datetime.combine(date.fromisoformat(day),time.min,tzinfo=TZ)
            latest=day_start+timedelta(hours=72)
            matches=[]
            seen=set()
            for entry in entries:
                if not isinstance(entry,dict):
                    continue
                title=filter_title(entry.get("title"),sid,day)
                url=clean_link(entry.get("url"))
                stamp=entry.get("published_at")
                if not title or not url or not isinstance(stamp,datetime) or stamp.tzinfo is None:
                    continue
                if not day_start-timedelta(hours=3) <= stamp.astimezone(TZ) <= latest:
                    continue
                if stamp>now.astimezone(timezone.utc):
                    continue
                if url in seen:
                    continue
                seen.add(url)
                matches.append({"headline":title,"url":url,
                                "published_at":stamp.isoformat(),
                                "source_name":"F4W / Wrestling Observer",
                                "status":"PUBLISHER_HEADLINE_LINK_ONLY"})
            if matches:
                row.update(airdate=day,links=sorted(matches,key=lambda x:x["published_at"],reverse=True)[:3],
                           status="publisher_coverage_links")
                break
        programs.append(row)
    return {"schema_version":1,"mode":MODE,"generated_at":now.astimezone(TZ).isoformat(),
            "source_name":"F4W / Wrestling Observer",
            "source_url":FEED_URL,
            "policy":"RSS headlines and article links only. Not licensed article bodies, not verified match outcomes or official results. No inference of winners, titles or storylines. Date-window association is informational, not proof of episode coverage.",
            "programs":programs,
            "total_links":sum(len(x["links"]) for x in programs)}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--snapshot",default="web/data/snapshot.json")
    ap.add_argument("--out",default="web/data/recap-links.json")
    args=ap.parse_args()
    snap=json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    if snap.get("schema_version")!=1 or len(snap.get("shows",[]))!=6:
        raise SystemExit("Invalid schedule; no RSS result written")
    status="ok"
    try:
        items=parse_feed(request_rss())
        print("RSS_DIAGNOSTIC_PARSED_COUNT:",len(items))
        print("RSS_DIAGNOSTIC_RESULTS_HEADLINES:", [
            (x["title"][:110], x["published_at"].isoformat())
            for x in items if RESULT_WORDS.search(x.get("title") or "")][:18])
    except Exception as exc:
        status="rss_unavailable"
        print("RSS source temporarily unavailable:",type(exc).__name__,str(exc)[:120])
        items=[]
    data=build_links(snap,items)
    data["collection_status"]=status
    out=Path(args.out)
    tmp=out.with_suffix(".tmp")
    tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    tmp.replace(out)
    print("Attribution-only post-show article links:",data["total_links"])


if __name__=="__main__":
    main()
