"""Build opt-in, clearly UNVERIFIED reported wrestling cards for the user.

No rumours are fabricated: every line must be present in TheSportsDB's
documented API. No line is called confirmed, advertised, or official.
No HTML scraping or AI hallucination.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo

from proof.card_intake import SHOWS, parse_bouts, relevant_events, request_events, request_next_league, request_event_by_id, valid_upcoming, event_identity_matches, outcome_reported, withdrawn_event

TZ = ZoneInfo("America/New_York")
MAX_SHOW_MATCHES = 8
MAX_TEXT = 210
MAX_APPEARANCES = 5


def broadcast_finished(show_id: str, airdate: str, now: datetime) -> bool:
    """Do not treat advance/taped spoilers as an aired television result.

    TNA's AMC U.S. linear broadcast is 9-11 p.m. Eastern; the extra 15 minutes
    prevents premature handoff. Until an equally reliable clock is available
    for other programs, use 4 a.m. ET on the following date conservatively.
    """
    try:
        day = date.fromisoformat(airdate)
    except (TypeError, ValueError):
        return False
    moment = now.astimezone(TZ)
    if show_id == "tna":
        end = datetime.combine(day, time(23, 15), tzinfo=TZ)
    else:
        end = datetime.combine(day + timedelta(days=1), time(4, 0), tzinfo=TZ)
    return moment >= end


def parse_reported_appearances(description: str) -> list[dict]:
    """Extract only explicitly labeled appearance/segment lines from API plain text.

    The claim is a source report, never an official advertisement or a result.
    Wrestlers appearing in a match are NOT assumed to have separate appearances.
    """
    if not isinstance(description, str) or "<" in description or ">" in description:
        return []
    text = description.replace("\r\n", "\n").replace("\r", "\n")[:12000]
    found = []
    headings = re.compile(
        r"^(?:in[- ]ring |backstage )?"
        r"(promo(?: segment)?|segment|interview|contract signing|face[- ]to[- ]face|appearance)$",
        re.I,
    )
    barred = re.compile(
        r"\b(?:vs\.?|defeat(?:ed|s)?|pinn?ed|winner|result|retained|"
        r"won|lost|match|spoiler|dark match|taping)\b",
        re.I,
    )
    for paragraph in re.split(r"\n\s*\n+", text):
        lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
        if len(lines) != 2 or not headings.fullmatch(lines[0]):
            continue
        statement = " ".join(lines[1].split())
        if not 6 <= len(statement) <= 160 or barred.search(statement):
            continue
        found.append({"type": lines[0][:48], "text": statement})
        if len(found) >= MAX_APPEARANCES:
            break
    return found



def build_reported(snapshot: dict, requester=request_events, now=None, next_lookup=None, known_events=None, event_lookup=None, previous=None) -> dict:
    now = now or datetime.now(TZ)
    local_today = now.astimezone(TZ).date()
    output = []
    cache = {}
    league_cache = {}
    id_cache = {}
    for s in snapshot.get("shows", []):
        slug = s.get("id")
        air = (s.get("next") or {}).get("date")
        has_aired = broadcast_finished(slug, air, now)
        entry = {
            "show_id": slug,
            "airdate": air if isinstance(air, str) else None,
            "display_label": "REPORTED · UNVERIFIED",
            "matches": [],
            "appearances": [],
            "error": None,
            "episode_outcome_detected": False,
            "episode_withdrawn": False,
            "episode_outcome_evidence_url": None,
            "source_name": "TheSportsDB",
        }
        # Once an outcome/cancellation has been SEEN for this exact show/date,
        # keep its safety flag through intermittent upstream outages. Never
        # carry state onto the following week's broadcast date.
        previous_items=(previous or {}).get("programs",[])
        if isinstance(previous_items,list):
            prior=next((p for p in previous_items if isinstance(p,dict)
                        and p.get("show_id")==slug and p.get("airdate")==air),None)
            if prior:
                entry["episode_outcome_detected"]=has_aired and prior.get("episode_outcome_detected") is True
                entry["episode_withdrawn"]=prior.get("episode_withdrawn") is True
                if entry["episode_outcome_detected"] and re.fullmatch(
                    r"https://www\.thesportsdb\.com/api/v1/json/123/lookupevent\.php\?id=\d+",
                    prior.get("episode_outcome_evidence_url") or ""):
                    entry["episode_outcome_evidence_url"]=prior["episode_outcome_evidence_url"]
        # AAA's named multi-week tape package cannot be assigned to a weekly episode.
        # Evolve is results-only. Matches must never be inferred for either.
        if slug not in SHOWS or not valid_upcoming(air, local_today):
            output.append(entry)
            continue
        league, _ = SHOWS[slug]
        days = [air]
        if slug == "tna":
            # TNA shows may have a UTC date one day later than dateEventLocal.
            from datetime import timedelta
            days.append((date.fromisoformat(air) + timedelta(days=1)).isoformat())
        events = {}
        had_error = False
        def observe_flags(rows):
            for candidate in rows:
                if not event_identity_matches(slug, air, candidate):
                    continue
                if has_aired and outcome_reported(candidate):
                    entry["episode_outcome_detected"] = True
                    provider_id=str(candidate.get("idEvent",""))
                    if re.fullmatch(r"[1-9]\d{0,14}",provider_id):
                        entry["episode_outcome_evidence_url"]=(
                            "https://www.thesportsdb.com/api/v1/json/123/lookupevent.php?id="+provider_id
                        )
                if withdrawn_event(candidate):
                    entry["episode_withdrawn"] = True

        for day in days:
            cache_key = (league, day)
            if cache_key not in cache:
                try:
                    cache[cache_key] = requester(day, league)
                except Exception:
                    cache[cache_key] = None
            if cache[cache_key] is None:
                had_error = True
                continue
            observe_flags(cache[cache_key])
            for event in relevant_events(slug, air, cache[cache_key]):
                events[str(event["idEvent"])] = event
        # The V1 next-league endpoint can supply a candidate when the day
        # index omits it. It is still subject to show+promotion+LOCAL airdate
        # matching and cancellation/result exclusions.
        if next_lookup is not None:
            if league not in league_cache:
                try:
                    league_cache[league] = next_lookup(league)
                except Exception:
                    league_cache[league] = None
            if league_cache[league] is None:
                had_error = True
            else:
                observe_flags(league_cache[league])
                for event in relevant_events(slug, air, league_cache[league]):
                    events.setdefault(str(event["idEvent"]), event)
        # Re-query previously observed (not guessed) event IDs through the
        # documented lookupevent endpoint when a date index is incomplete.
        # Never copy old match text: the live response must STILL match the
        # show, promotion, local airdate and cancelled/finished safety gates.
        known_rows = (known_events or {}).get("entries", [])
        if event_lookup is not None and isinstance(known_rows, list):
            for known in known_rows:
                if not isinstance(known, dict):
                    continue
                if known.get("show_id") != slug or known.get("airdate") != air:
                    continue
                for event_id in (known.get("event_ids") or [])[:4]:
                    sid = str(event_id)
                    if not re.fullmatch(r"[1-9]\d{0,14}", sid) or sid in events:
                        continue
                    if sid not in id_cache:
                        try:
                            id_cache[sid] = event_lookup(sid)
                        except Exception:
                            id_cache[sid] = None
                    if id_cache[sid] is None:
                        had_error = True
                        continue
                    observe_flags(id_cache[sid])
                    for event in relevant_events(slug, air, id_cache[sid]):
                        if str(event.get("idEvent")) == sid:
                            events[sid] = event
        unique = set()
        unique_appearances = set()
        for event in events.values():
            source_id = str(event["idEvent"])
            source_url = "https://www.thesportsdb.com/api/v1/json/123/lookupevent.php?id=" + source_id
            for mention in parse_reported_appearances(event.get("strDescriptionEN") or ""):
                signature = (mention["type"].casefold(), mention["text"].casefold())
                if signature in unique_appearances:
                    continue
                unique_appearances.add(signature)
                if len(entry["appearances"]) < MAX_APPEARANCES:
                    entry["appearances"].append({
                        "text": mention["text"],
                        "type": mention["type"],
                        "evidence_url": source_url,
                        "provider_event_id": source_id,
                        "status": "REPORTED_UNVERIFIED",
                        "source_name": "TheSportsDB",
                    })
            for match in parse_bouts(event.get("strDescriptionEN") or ""):
                wording = " ".join(match["description"].split())[:MAX_TEXT]
                stipulation = " ".join(match["stipulation"].split())[:110]
                normalized = (wording.casefold(), stipulation.casefold())
                if normalized in unique:
                    continue
                unique.add(normalized)
                entry["matches"].append({
                    "text": wording,
                    "stipulation": stipulation,
                    "evidence_url": source_url,
                    "provider_event_id": source_id,
                    "status": "REPORTED_UNVERIFIED",
                    "source_name": "TheSportsDB",
                })
                if len(entry["matches"]) >= MAX_SHOW_MATCHES:
                    break
            if len(entry["matches"]) >= MAX_SHOW_MATCHES:
                break
        if entry["episode_outcome_detected"] or entry["episode_withdrawn"]:
            # Never combine older reported bouts with a provider-known result
            # or cancellation, even when another source still lists that bout.
            entry["matches"] = []
            entry["appearances"] = []
        if had_error:
            entry["error"] = "PROVIDER_PARTIAL_OR_UNAVAILABLE"
        output.append(entry)
    return {
        "schema_version": 1,
        "mode": "REPORTED_MATCHES_UNVERIFIED",
        "generated_at": now.isoformat(),
        "valid_as_of_et": local_today.isoformat(),
        "policy": (
            "Opt-in UNVERIFIED match and explicit segment mentions only. May be stale, speculative, "
            "misassigned, dark matches, taped show results or subject to change. "
            "Not announcements from WWE, AAA or TNA. Taped/early results never withdraw "
            "advance cards before scheduled U.S. broadcast completion."
        ),
        "programs": output,
        "total_reported_matches": sum(len(x["matches"]) for x in output),
        "total_reported_appearances": sum(len(x["appearances"]) for x in output),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", default="web/data/snapshot.json")
    parser.add_argument("--out", default="web/data/reported.json")
    parser.add_argument("--also-next-league", action="store_true")
    parser.add_argument("--known-ids", default=None, help="Previously observed provider IDs, rechecked live")
    parser.add_argument("--recheck-ids", action="store_true")
    parser.add_argument("--previous", default=None, help="Prior reported JSON for monotonic same-date outcome/cancellation flags")
    args = parser.parse_args()
    snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    if snapshot.get("schema_version") != 1 or len(snapshot.get("shows", [])) != 6:
        raise SystemExit("Invalid schedule snapshot; do not overwrite reported feed")
    known = None
    if args.recheck_ids and args.known_ids:
        p = Path(args.known_ids)
        try:
            known = json.loads(p.read_text(encoding="utf-8"))
            if known.get("schema_version") != 1 or known.get("mode") != "KNOWN_PROVIDER_EVENT_IDENTIFIERS":
                known = None
        except (ValueError, OSError, AttributeError):
            known = None
    previous = None
    if args.previous:
        try:
            previous=json.loads(Path(args.previous).read_text(encoding="utf-8"))
            if previous.get("mode")!="REPORTED_MATCHES_UNVERIFIED":
                previous=None
        except (ValueError,OSError,AttributeError):
            previous=None
    result = build_reported(snapshot, next_lookup=request_next_league if args.also_next_league else None,
                            known_events=known, event_lookup=request_event_by_id if known is not None else None, previous=previous)
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(target)
    print("REPORTED_UNVERIFIED match lines:", result["total_reported_matches"])


if __name__ == "__main__":
    main()
