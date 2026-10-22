"""Conservative post-broadcast Results & Fallout data from TheSportsDB public API.

Only expose *actual outcome lines present in event.strResult*, after local
television broadcast completion. This is a provider report, NOT official WWE,
TNA, NXT or AAA confirmation. No WWE/TNA scraping, no invented result/storyline.
No Evolve or AAA taping-to-episode inference.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from proof.card_intake import (
    SHOWS, event_identity_matches, request_events, request_event_by_id
)

ET = ZoneInfo("America/New_York")
MODE = "PROVIDER_REPORTED_POST_BROADCAST_RESULTS_UNVERIFIED"
MAX_AGE_DAYS = 10
LINE_CAP = 8
ALLOWED = {"raw", "smackdown", "nxt", "tna"}
WIN = re.compile(r"^(.{2,90}?)\s+(?:defeats?|defeated|def\.)\s+(.{2,140})$", re.I)
BAD = re.compile(r"\b(?:spoiler|prediction|rumou?r|dark match|fantasy booking|"
                 r"no result|tbd|cancelled|postponed|not aired)\b", re.I)


def broadcast_complete(show: str, aired: str, at: datetime) -> bool:
    try:
        day = date.fromisoformat(aired)
    except (TypeError, ValueError):
        return False
    moment = at.astimezone(ET)
    if show == "tna":
        end = datetime.combine(day, time(23, 15), tzinfo=ET)
    else:
        end = datetime.combine(day + timedelta(days=1), time(4), tzinfo=ET)
    return moment >= end


def parse_result_lines(raw: object) -> list[dict]:
    """Require explicit event-result grammar; do not infer title changes."""
    if not isinstance(raw, str) or not raw or len(raw) > 14000 or "<" in raw or ">" in raw:
        return []
    output = []
    existing = set()
    blocks = re.split(r"\n\s*\n+", raw.replace("\r\n", "\n").replace("\r", "\n"))
    for block in blocks:
        parts = [re.sub(r"\s+", " ", x).strip() for x in block.split("\n") if x.strip()]
        if not 1 <= len(parts) <= 3:
            continue
        label = parts[0] if len(parts) >= 2 else "Reported result"
        line = parts[1] if len(parts) >= 2 else parts[0]
        if len(line) > 210 or len(label) > 110 or BAD.search(line) or BAD.search(label):
            continue
        winner = WIN.fullmatch(line)
        if not winner:
            continue
        left, right = winner.group(1).strip(), winner.group(2).strip()
        if not left or not right or any(t in (left + " " + right).lower()
            for t in ("last week", "on monday", "probably", "may defeat")):
            continue
        text = left + " defeats " + right
        key = re.sub(r"[^a-z0-9]", "", text.lower())
        if key in existing:
            continue
        existing.add(key)
        output.append({"text": text, "match_type": label})
        if len(output) >= LINE_CAP:
            break
    return output


RESULT_SECTION = re.compile(r"(?im)^[ \t]*(?:match[ \t]+)?results?[ \t]*:[ \t]*$")
def parse_explicit_description_results(raw: object) -> list[dict]:
    """Only parse a provider's explicitly headed, post-broadcast results
    section. Never turn a preview, unrelated storyline, or simple 'vs' into
    an outcome. This is a best-effort supplemental source field.
    """
    if not isinstance(raw,str) or not 10<len(raw)<=14000 or "<" in raw or ">" in raw:
        return []
    header=RESULT_SECTION.search(raw)
    if header is None:
        return []
    section=raw[header.end():]
    # Do not parse older storylines after a different section heading.
    section=re.split(r"(?m)^\s*(?:Storyline|Preview|Previously|Background|Next Week)\s*:",section,maxsplit=1,flags=re.I)[0]
    return parse_result_lines(section)


def eligible_episodes(show: dict, now: datetime) -> list[str]:
    """Recent broadcast + last-listed episode, only after finish time."""
    sid = show.get("id")
    if sid not in ALLOWED:
        return []
    today = now.astimezone(ET).date()
    days = []
    for key in ("next", "previous"):
        episode = show.get(key) or {}
        airdate = episode.get("date")
        try:
            day = date.fromisoformat(airdate)
        except (TypeError, ValueError):
            continue
        if 0 <= (today - day).days <= MAX_AGE_DAYS and broadcast_complete(sid, airdate, now):
            if airdate not in days:
                days.append(airdate)
    return sorted(days, reverse=True)


def request_past_league(league: int, timeout: int = 15) -> list[dict]:
    """Documented TheSportsDB v1 past-league endpoint (limited free-tier coverage)."""
    if league not in (4444, 4455):
        return []
    url = "https://www.thesportsdb.com/api/v1/json/123/eventspastleague.php?id=" + str(league)
    req = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "InsideSquaredCircleHouseholdResearch/0.6",
    })
    with urlopen(req, timeout=timeout) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError("Invalid past-league API response")
    events = payload.get("events")
    return events[:15] if isinstance(events, list) else []


def build_results(snapshot: dict, requester=request_events, event_lookup=request_event_by_id,
                  known=None, now=None, past_lookup=None) -> dict:

    now = now or datetime.now(ET)
    cache = {}
    lookup_cache = {}
    league_past_cache = {}
    programs = []
    known_rows = (known or {}).get("entries", [])
    if not isinstance(known_rows, list):
        known_rows = []
    for show in snapshot.get("shows", []):
        sid = show.get("id")
        entry = {"show_id": sid, "airdate": None, "results": [], "source_name": "TheSportsDB",
                 "status": "not_supported" if sid not in ALLOWED else "no_recent_finished_broadcast",
                 "partial_source_error": False}
        if sid not in ALLOWED:
            programs.append(entry)
            continue
        # Only the MOST RECENT completed broadcast is eligible. If the
        # new episode has no provider outcomes yet, do not resurrect the
        # previous week's recap merely because that older event is indexed.
        for day in eligible_episodes(show, now)[:1]:
            league = SHOWS[sid][0]
            dates = [day]
            if sid == "tna":
                dates.append((date.fromisoformat(day)+timedelta(days=1)).isoformat())
            events = {}
            for query_day in dates:
                key = (league, query_day)
                if key not in cache:
                    try:
                        cache[key] = requester(query_day, league)
                    except Exception:
                        cache[key] = None
                if cache[key] is None:
                    entry["partial_source_error"] = True
                    continue
                for event in cache[key]:
                    if event_identity_matches(sid, day, event):
                        events[str(event["idEvent"])] = event

            # Documented past-league feed is a limited safety net when the
            # daily date query drops a previously aired program. No inference
            # from league-only results: exact show/local day still required.
            if past_lookup is not None:
                if league not in league_past_cache:
                    try:
                        league_past_cache[league] = past_lookup(league)
                    except Exception:
                        league_past_cache[league] = None
                if league_past_cache[league] is None:
                    entry["partial_source_error"] = True
                else:
                    for event in league_past_cache[league]:
                        if event_identity_matches(sid, day, event):
                            events[str(event["idEvent"])] = event

            # Re-check only *historically observed* provider IDs for same show/day.
            for known_row in known_rows:
                if not isinstance(known_row, dict) or known_row.get("show_id")!=sid or known_row.get("airdate")!=day:
                    continue
                for identifier in (known_row.get("event_ids") or [])[:4]:
                    eid = str(identifier)
                    if not re.fullmatch(r"[1-9]\d{0,14}", eid) or eid in events:
                        continue
                    if eid not in lookup_cache:
                        try:
                            lookup_cache[eid] = event_lookup(eid)
                        except Exception:
                            lookup_cache[eid] = None
                    if lookup_cache[eid] is None:
                        entry["partial_source_error"] = True
                        continue
                    for event in lookup_cache[eid]:
                        if event_identity_matches(sid, day, event) and str(event.get("idEvent"))==eid:
                            events[eid] = event
            results = []
            seen = set()
            for event in events.values():
                if str(event.get("strPostponed", "")).lower() in ("yes","true","1"):
                    continue
                provider_lines=parse_result_lines(event.get("strResult"))
                description_lines=parse_explicit_description_results(event.get("strDescriptionEN"))
                for line in provider_lines+description_lines:
                    signature = re.sub(r"[^a-z0-9]","",line["text"].lower())
                    if signature in seen:
                        continue
                    seen.add(signature)
                    results.append({
                        **line, "status": "REPORTED_UNVERIFIED",
                        "source_name": "TheSportsDB",
                        "evidence_url": "https://www.thesportsdb.com/api/v1/json/123/lookupevent.php?id="+str(event["idEvent"]),
                        "provider_event_id": str(event["idEvent"]),
                        "provider_field": "strResult" if line in provider_lines else "strDescriptionEN/results_section",
                    })
                    if len(results)>=LINE_CAP:
                        break
                if len(results)>=LINE_CAP:
                    break
            if results:
                entry["airdate"]=day
                entry["results"]=results
                entry["status"]="reported_outcomes"
                break
            entry["status"]="no_parseable_source_results"
        programs.append(entry)
    return {"schema_version":1,"mode":MODE,"generated_at":now.astimezone(ET).isoformat(),
            "policy":"Post-broadcast TheSportsDB result lines only, labelled REPORTED / UNVERIFIED. No inferred title changes, rivalries or storylines; not official announcements.",
            "programs":programs,
            "total_reported_results":sum(len(p["results"]) for p in programs)}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--snapshot",default="web/data/snapshot.json")
    parser.add_argument("--known",default="web/data/known-events.json")
    parser.add_argument("--out",default="web/data/results.json")
    args=parser.parse_args()
    snap=json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    if snap.get("schema_version")!=1 or len(snap.get("shows", []))!=6:
        raise SystemExit("Invalid source schedule; not overwriting results")
    try:
        known=json.loads(Path(args.known).read_text(encoding="utf-8"))
        if known.get("mode")!="KNOWN_PROVIDER_EVENT_IDENTIFIERS":
            known={}
    except (ValueError, OSError, AttributeError):
        known={}
    feed=build_results(snap, known=known, past_lookup=request_past_league)
    out=Path(args.out)
    tmp=out.with_suffix(".tmp")
    tmp.write_text(json.dumps(feed,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    tmp.replace(out)
    print("POST-BROADCAST REPORTED_UNVERIFIED outcome lines:",feed["total_reported_results"])


if __name__=="__main__":
    main()
