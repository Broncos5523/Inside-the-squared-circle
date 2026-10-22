"""Research-only match-card intake from a public documented API.

No candidate becomes an announced or verified match. TVmaze controls the next
broadcast date. TheSportsDB descriptions are only possible research leads.
Airdate, promotion, and show-name conflicts are handled conservatively.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import json
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen

BASE = "https://www.thesportsdb.com/api/v1/json/123/eventsday.php"
NEXT_BASE = "https://www.thesportsdb.com/api/v1/json/123/eventsnextleague.php"
RESULT_OUTCOME = re.compile(
    r"\b(?:defeats?|defeated|pinn?ed|winner|winners|"
    r"won|lost|retained|pinfall|submission|no contest|"
    r"via dq|by disqualification|finished|completed)\b", re.I,
)
BLOCKED_EVENT_STATUS = re.compile(
    r"\b(?:cancelled|canceled|postponed|abandoned|finished|completed|"
    r"ended|result|taped|aired)\b", re.I,
)


def outcome_reported(event: dict) -> bool:
    status = event.get("strStatus")
    if isinstance(status,str) and re.search(r"\b(?:finished|completed|ended|result|aired|taped)\b", status, re.I):
        return True
    result=event.get("strResult")
    return isinstance(result,str) and bool(RESULT_OUTCOME.search(result))


def withdrawn_event(event: dict) -> bool:
    value=event.get("strPostponed")
    if value is True or str(value).strip().lower() in ("yes","y","true","1"):
        return True
    status=event.get("strStatus")
    return isinstance(status,str) and bool(re.search(r"\b(?:cancelled|canceled|postponed|abandoned)\b",status,re.I))


def unusable_upcoming_event(event: dict) -> bool:
    """Provider status and outcome annotations override early card mentions."""
    return outcome_reported(event) or withdrawn_event(event)


SHOWS = {
    "raw": (4444, re.compile(r"^raw\b", re.I)),
    "smackdown": (4444, re.compile(r"^smackdown\b", re.I)),
    "nxt": (4444, re.compile(r"^(wwe )?nxt\b", re.I)),
    "tna": (4455, re.compile(r"^(tna )?(impact!|impact)\b", re.I)),
    # AAA's named multi-week event is not necessarily the same as a TV episode.
    # Evolve is only a RESULTS/RECAP segment; neither receives auto cards.
}
MAX_BLOCKS = 30


def parse_bouts(description: str) -> list[dict]:
    """Extract discussion CANDIDATES, never confirmations, from plain text."""
    if not isinstance(description, str):
        return []
    text = description.replace("\r\n", "\n").replace("\r", "\n")[:12000]
    if "<" in text or ">" in text:  # do not parse HTML as reliable plain text
        return []
    found = []
    for paragraph in re.split(r"\n\s*\n+", text):
        lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
        if len(lines) < 2 or len(lines) > 4:
            continue
        label = lines[0]
        for line in lines[1:]:
            if len(line) > 210:
                continue
            # Provider descriptions may be updated AFTER taping or broadcast.
            # Never render a winner/result annotation as an upcoming match.
            if re.search(
                r"\b(?:winner|result|spoiler|defeated|defeats|pinned|"
                r"retained|won|lost|victory|post[- ]match)\b",
                line, flags=re.I,
            ):
                continue
            parts = re.split(r"\s+vs\.?\s+", line, flags=re.I)
            if len(parts) < 2 or any(len(p.strip()) < 2 for p in parts):
                continue
            if not re.search(r"\b(?:match|fight|title|championship|contendership|falls)\b", label, flags=re.I):
                continue
            found.append({
                "kind": "possible_match",
                "status": "UNVERIFIED_SOURCE_MENTION",
                "description": line[:210],
                "stipulation": label[:110],
            })
            if len(found) >= MAX_BLOCKS:
                return found
    return found


def broadcast_date(event: dict) -> str | None:
    local = event.get("dateEventLocal")
    if isinstance(local, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", local):
        return local
    normal = event.get("dateEvent")
    if isinstance(normal, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", normal):
        return normal
    return None


def event_identity_matches(show_id: str, day: str, event: dict) -> bool:
    """Pure show/promotion/local-airdate check, independent of outcome status."""
    if show_id not in SHOWS or not isinstance(event,dict):
        return False
    league, matcher=SHOWS[show_id]
    return (str(event.get("idLeague"))==str(league)
            and bool(matcher.search(str(event.get("strEvent",""))))
            and broadcast_date(event)==day
            and str(event.get("idEvent","")).isdigit())


def relevant_events(show_id: str, day: str, event_rows: list[dict]) -> list[dict]:
    """Reject outcomes/cancellations after exact show+date+promotion matching."""
    return [event for event in event_rows if
            event_identity_matches(show_id, day, event) and
            not unusable_upcoming_event(event)][:4]


def valid_upcoming(day: object, today: date) -> bool:
    try:
        value = date.fromisoformat(day)
        return today <= value <= today + timedelta(days=20)
    except (ValueError, TypeError):
        return False


def request_events(day: str, league: int, timeout: int = 15) -> list[dict]:
    url = BASE + "?d=" + day + "&l=" + str(league)
    req = Request(url, headers={
        "User-Agent": "InsideSquaredCircleHouseholdResearch/0.2",
        "Accept": "application/json"
    })
    for attempt in range(2):
        try:
            with urlopen(req, timeout=timeout) as response:
                data = json.load(response)
            if not isinstance(data, dict):
                raise ValueError("Unexpected TheSportsDB response")
            rows = data.get("events")
            return rows if isinstance(rows, list) else []
        except Exception:
            if attempt:
                raise
            time.sleep(2)
    return []



def request_next_league(league: int, timeout: int = 15) -> list[dict]:
    """Documented V1 API; free tier may return only ONE upcoming league event."""
    if league not in (4444, 4455):
        return []
    url = NEXT_BASE + "?id=" + str(league)
    req = Request(url, headers={
        "User-Agent": "InsideSquaredCircleHouseholdResearch/0.4",
        "Accept": "application/json",
    })
    with urlopen(req, timeout=timeout) as response:
        obj = json.load(response)
    if not isinstance(obj, dict):
        raise ValueError("Unexpected next-league source response")
    events = obj.get("events")
    return events[:10] if isinstance(events, list) else []



def request_event_by_id(event_id: str, timeout: int = 15) -> list[dict]:
    """Documented lookupevent API: revalidate an already observed event identifier."""
    if not re.fullmatch(r"[1-9]\d{0,14}", str(event_id)):
        raise ValueError("Invalid known event identifier")
    url = "https://www.thesportsdb.com/api/v1/json/123/lookupevent.php?id=" + str(event_id)
    request = Request(url, headers={
        "User-Agent": "InsideSquaredCircleHouseholdResearch/0.5",
        "Accept": "application/json",
    })
    with urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError("Invalid lookupevent response")
    rows = payload.get("events")
    return rows[:4] if isinstance(rows, list) else []


def build_report(snapshot: dict, requester=request_events, clock=None, next_lookup=None) -> dict:
    """Counts evidence candidates; no source is promoted to verified."""
    today = clock or datetime.now(timezone.utc).date()
    source_date = datetime.now(timezone.utc).isoformat()
    entries = []
    cache = {}
    league_cache = {}
    for show in snapshot.get("shows", []):
        sid = show.get("id", "")
        next_episode = show.get("next") or {}
        air_day = next_episode.get("date")
        item = {
            "show_id": sid,
            "airdate": air_day if isinstance(air_day, str) else None,
            "intake_status": "unsupported_show" if sid in ("aaa", "evolve") else "no_verified_card_source",
            "candidate_count": 0,
            "verified_match_count": 0,
            "verified_appearance_count": 0,
            "events_considered": [],
        }
        if sid not in SHOWS or not valid_upcoming(air_day, today):
            entries.append(item)
            continue
        league, _ = SHOWS[sid]
        # Certain events' dateEvent is UTC the day AFTER their local TV airdate.
        # Search both dates, then require the matching dateEventLocal.
        days = [air_day]
        if sid == "tna":
            days.append((date.fromisoformat(air_day) + timedelta(days=1)).isoformat())
        results = []
        failed = False
        for day in days:
            key = (league, day)
            if key not in cache:
                try:
                    cache[key] = requester(day, league)
                except Exception as e:
                    cache[key] = None
            rows = cache[key]
            if rows is None:
                failed = True
                continue
            results.extend(relevant_events(sid, air_day, rows))
        if next_lookup is not None:
            if league not in league_cache:
                try:
                    league_cache[league] = next_lookup(league)
                except Exception:
                    league_cache[league] = None
            if league_cache[league] is None:
                failed = True
            else:
                results.extend(relevant_events(sid, air_day, league_cache[league]))
        dedup = {}
        for row in results:
            dedup[str(row["idEvent"])] = row
        for event in dedup.values():
            possibilities = parse_bouts(event.get("strDescriptionEN") or "")
            item["candidate_count"] += len(possibilities)
            item["events_considered"].append({
                "event_id": str(event["idEvent"]),
                "event_title": str(event.get("strEvent", ""))[:100],
                "source_url": "https://www.thesportsdb.com/api/v1/json/123/lookupevent.php?id=" + str(event["idEvent"]),
                "possible_match_mentions": len(possibilities),
                "verification": "NOT_CONFIRMED",
            })
        item["intake_status"] = (
            "partial_source_error" if failed else
            "unverified_leads_found" if item["candidate_count"] else
            "no_parseable_leads"
        )
        entries.append(item)
    return {
        "schema_version": 1,
        "mode": "RESEARCH_LEADS_ONLY",
        "generated_at": source_date,
        "policy": "Mentions are NOT confirmations. Do not put candidate matches on the public broadcast.",
        "source": "TheSportsDB (free API); attribution required; no artwork fetched.",
        "programs": entries,
        "verified_matches": [],
        "verified_appearances": [],
        "total_unverified_possible_match_mentions": sum(x["candidate_count"] for x in entries),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", default="web/data/snapshot.json")
    ap.add_argument("--out", default="web/data/candidates.json")
    ap.add_argument("--also-next-league", action="store_true", help="Check the documented next-league API in addition to date queries")
    args = ap.parse_args()
    snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    if snapshot.get("schema_version") != 1 or len(snapshot.get("shows", [])) != 6:
        raise SystemExit("Refusing to scan malformed schedule JSON")
    result = build_report(snapshot, next_lookup=request_next_league if args.also_next_league else None)
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".tmp")
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(dest)
    print(json.dumps({
        "programs": len(result["programs"]),
        "unverified_possible_match_mentions": result["total_unverified_possible_match_mentions"],
        "verified_matches": len(result["verified_matches"]),
        "verified_appearances": len(result["verified_appearances"])
    }))


if __name__ == "__main__":
    main()
