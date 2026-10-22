"""TVmaze's licensed Evolve episode synopsis, NOT inferred match results.

Uses the documented TVmaze episodes-by-date JSON endpoint. Episode synopsis is
a description of the episode, not an after-the-fact result report. No scraping
of WWE, Tubi, or third-party publisher pages.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
SHOW_ID = 82403
MODE = "TVMAZE_EVOLVE_EPISODE_SYNOPSIS_ONLY"


class PlainSynopsis(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.words = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag in ("p", "li", "br"):
            self.words.append(" ")
    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(self.skip - 1, 0)
        elif tag in ("p", "li"):
            self.words.append(" ")
    def handle_data(self, data):
        if not self.skip:
            self.words.append(data)


def summary_text(html: object) -> str:
    if not isinstance(html, str) or len(html) > 16000:
        return ""
    parser = PlainSynopsis()
    parser.feed(html)
    text = " ".join("".join(parser.words).split())
    # Content can be a plot synopsis with pre-air phrasing; not a result.
    return text[:240].rstrip() if len(text) <= 240 else text[:237].rstrip() + "…"


def request_episodes(day: str, timeout: int = 15) -> list:
    url = f"https://api.tvmaze.com/shows/{SHOW_ID}/episodesbydate?date={day}"
    request = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "InsideSquaredCircleHouseholdResearch/0.7",
    })
    with urlopen(request, timeout=timeout) as response:
        data = json.load(response)
    if not isinstance(data, list):
        raise ValueError("Unexpected TVmaze episode-by-date response")
    return data


def build_evolve(snapshot: dict, requester=request_episodes, now=None) -> dict:
    now = now or datetime.now(ET)
    result = {"schema_version":1,"mode":MODE,"generated_at":now.astimezone(ET).isoformat(),
              "show_id":"evolve","airdate":None,"episode_id":None,"synopsis":None,
              "evidence_url":None,"source_name":"TVmaze","license":"CC BY-SA",
              "status":"no_recent_finished_episode",
              "policy":"Episode synopsis only: no outcomes or title changes implied. Source TVmaze (CC BY-SA)."}
    program = next((s for s in snapshot.get("shows",[]) if s.get("id")=="evolve"), None)
    if not program:
        result["status"]="no_schedule"
        return result
    previous = (program.get("previous") or {})
    day = previous.get("date")
    try:
        d = date.fromisoformat(day)
    except (ValueError,TypeError):
        return result
    age = (now.astimezone(ET).date()-d).days
    if not 0 <= age <= 14:
        result["status"]="outside_recap_window"
        return result
    if program.get("schedule_status")!="fresh":
        result["status"]="schedule_stale"
        return result
    try:
        episodes = requester(day)
        for ep in episodes:
            if not isinstance(ep,dict) or ep.get("airdate")!=day:
                continue
            ident = ep.get("id")
            if not isinstance(ident,int) or ident<=0:
                continue
            description = summary_text(ep.get("summary"))
            if not description:
                continue
            result.update(airdate=day,episode_id=ident,synopsis=description,
                          evidence_url=f"https://api.tvmaze.com/episodes/{ident}",
                          status="episode_synopsis_available")
            break
        else:
            result["status"]="no_episode_synopsis"
    except Exception as exc:
        result["status"]="api_unavailable"
        print(f"Evolve synopsis delayed: {type(exc).__name__}: {str(exc)[:100]}")
    return result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--snapshot",default="web/data/snapshot.json")
    ap.add_argument("--out",default="web/data/evolve-synopsis.json")
    args=ap.parse_args()
    snapshot=json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    if snapshot.get("schema_version")!=1 or len(snapshot.get("shows",[]))!=6:
        raise SystemExit("Invalid schedule, not overwriting Evolve synopsis")
    result=build_evolve(snapshot)
    path=Path(args.out)
    tmp=path.with_suffix(".tmp")
    tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    tmp.replace(path)
    print("EVOLVE SYNOPSIS:", result["status"])


if __name__=="__main__":
    main()
