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
# Standard publisher RSS syndication paths for results-specific categories.
# Optional: unsupported URLs are simply ignored, never scraped as HTML.
FEED_URLS = (
    FEED_URL,
    "https://www.f4wonline.com/category/news/wwe/results/feed/",
    "https://www.f4wonline.com/category/news/nxt/nxt-results/feed/",
    "https://411mania.com/wrestling/feed/",
    "https://411mania.com/wrestling/category/tv-report/feed/",
    "https://www.fightful.com/wrestling/rss",
    "https://gerweck.net/category/results/feed/",
    "https://www.tpww.net/feed/",
)
PUBLISHERS={
    "www.f4wonline.com":"F4W / Wrestling Observer",
    "f4wonline.com":"F4W / Wrestling Observer",
    "411mania.com":"411Mania",
    "www.411mania.com":"411Mania",
    "www.fightful.com":"Fightful",
    "fightful.com":"Fightful",
    "gerweck.net":"Gerweck.net",
    "www.gerweck.net":"Gerweck.net",
    "tpww.net":"TPWW",
    "www.tpww.net":"TPWW",
}
ALLOWED_HOSTS = frozenset(PUBLISHERS)
RESULT_WORDS = re.compile(r"\b(?:results?|recap|fallout|reviews?|highlights)\b", re.I)
EXCLUDE = re.compile(
    r"\b(?:spoilers?|taping|predictions?|preview|ratings|retro|rewatch|"
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
INLINE_DATE = re.compile(r"\b(\d{1,2})[./-](\d{1,2})(?:[./-]\d{2,4})?\b")
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


def request_rss(timeout: int = 14, url: str = FEED_URL) -> bytes:
    if url not in FEED_URLS:
        raise ValueError('RSS URL not approved')
    req = Request(url, headers={
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
        entries.append({"title":title,"url":url,"published_at":stamp,
                        "source_name":PUBLISHERS[urlsplit(url).hostname]})
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


def safe_retained_links(previous: dict | None, sid: str, aired: str,
                        window_start: datetime, window_end: datetime,
                        now: datetime) -> list[dict]:
    """Keep previously observed publisher HEADLINES if they still match
    this week's last broadcast. This is not a cached match result.
    """
    if not isinstance(previous,dict) or previous.get("mode")!=MODE:
        return []
    old=next((x for x in previous.get("programs",[]) if
              isinstance(x,dict) and x.get("show_id")==sid
              and x.get("airdate")==aired),None)
    if not old:
        return []
    result=[]
    for item in (old.get("links") or [])[:8]:
        if not isinstance(item,dict) or item.get("status")!="PUBLISHER_HEADLINE_LINK_ONLY":
            continue
        title=filter_title(item.get("headline"),sid,aired)
        url=clean_link(item.get("url"))
        if not title or not url or PUBLISHERS[urlsplit(url).hostname]!=item.get("source_name"):
            continue
        try:
            stamp=datetime.fromisoformat(item["published_at"])
        except (TypeError,ValueError,KeyError):
            continue
        if stamp.tzinfo is None or not window_start <= stamp.astimezone(TZ) <= window_end:
            continue
        if stamp.astimezone(TZ)>now.astimezone(TZ):
            continue
        result.append({"headline":title,"url":url,
                       "published_at":stamp.isoformat(),
                       "source_name":item["source_name"],
                       "status":"PUBLISHER_HEADLINE_LINK_ONLY",
                       "retained_from_previous":True})
    return result


def build_links(snapshot: dict, entries: list[dict], now=None, previous=None) -> dict:
    now = now or datetime.now(TZ)
    programs=[]
    for show in snapshot.get("shows",[]):
        sid=show.get("id")
        row={"show_id":sid,"airdate":None,"links":[],
             "source_name":"Multiple publisher RSS feeds",
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
                provider=PUBLISHERS[urlsplit(url).hostname]
                if entry.get("source_name",provider)!=provider:
                    continue
                matches.append({"headline":title,"url":url,
                                "published_at":stamp.isoformat(),
                                "source_name":provider,
                                "status":"PUBLISHER_HEADLINE_LINK_ONLY"})
            # A syndicated feed may roll a review off its latest-10 list
            # before the next weekly episode airs. Preserve its *attributed
            # headline link* only for the exact show/airdate, with validation.
            seen_urls={x["url"] for x in matches}
            for saved in safe_retained_links(previous,sid,day,
                                              day_start-timedelta(hours=3),latest,now):
                if saved["url"] not in seen_urls:
                    matches.append(saved)
                    seen_urls.add(saved["url"])
            if matches:
                row.update(airdate=day,links=sorted(matches,key=lambda x:x["published_at"],reverse=True)[:5],
                           status="publisher_coverage_links")
                break
        programs.append(row)
    return {"schema_version":1,"mode":MODE,"generated_at":now.astimezone(TZ).isoformat(),
            "source_name":"Multiple publisher RSS feeds",
            "source_url":FEED_URL,
            "approved_publishers":["F4W / Wrestling Observer","411Mania","Fightful"],
            "policy":"F4W, 411Mania and Fightful publisher-syndicated RSS headlines and links only. No article-body scraping or republishing. Coverage leads, not independently confirmed match outcomes; local airdate and after-air safeguards. Never infer winners or storylines.",
            "programs":programs,
            "total_links":sum(len(x["links"]) for x in programs),
            "retained_link_count":sum(sum(bool(e.get('retained_from_previous')) for e in x['links']) for x in programs)}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--snapshot",default="web/data/snapshot.json")
    ap.add_argument("--out",default="web/data/recap-links.json")
    ap.add_argument("--previous",default="web/data/recap-links.json")
    args=ap.parse_args()
    snap=json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    if snap.get("schema_version")!=1 or len(snap.get("shows",[]))!=6:
        raise SystemExit("Invalid schedule; no RSS result written")
    items=[]
    links_seen=set()
    working_feeds=[]
    for feed in FEED_URLS:
        try:
            parsed=parse_feed(request_rss(url=feed))
        except Exception as exc:
            print("RSS syndicated feed unavailable:",feed,
                  type(exc).__name__,str(exc)[:100])
            continue
        print("RSS provider items from syndicated URL:",feed,len(parsed))
        working_feeds.append(feed)
        for item in parsed:
            if item["url"] not in links_seen:
                links_seen.add(item["url"])
                items.append(item)
    status="ok" if working_feeds else "rss_unavailable"
    # Before replacing the public JSON, load its previous source-attributed
    # headline links so brief feed gaps do not blank the weekly display.
    try:
        previous=json.loads(Path(args.previous).read_text(encoding="utf-8"))
    except (OSError,ValueError):
        previous=None
    data=build_links(snap,items,previous=previous)
    data["collection_status"]=status
    data["successful_feed_urls"]=working_feeds
    out=Path(args.out)
    tmp=out.with_suffix(".tmp")
    tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    tmp.replace(out)
    print("Attribution-only post-show article links:",data["total_links"])


if __name__=="__main__":
    main()
