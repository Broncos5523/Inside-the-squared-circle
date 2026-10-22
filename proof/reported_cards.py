"""Build opt-in, clearly UNVERIFIED reported wrestling cards for the user.

No rumours are fabricated: every line must be present in TheSportsDB's
documented API. No line is called confirmed, advertised, or official.
No HTML scraping or AI hallucination.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo

from proof.card_intake import SHOWS, parse_bouts, relevant_events, request_events, request_next_league, valid_upcoming

TZ = ZoneInfo("America/New_York")
MAX_SHOW_MATCHES = 8
MAX_TEXT = 210
MAX_APPEARANCES = 5


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



def build_reported(snapshot: dict, requester=request_events, now=None, next_lookup=None) -> dict:
    now = now or datetime.now(TZ)
    local_today = now.astimezone(TZ).date()
    output = []
    cache = {}
    league_cache = {}
    for s in snapshot.get("shows", []):
        slug = s.get("id")
        air = (s.get("next") or {}).get("date")
        entry = {
            "show_id": slug,
            "airdate": air if isinstance(air, str) else None,
            "display_label": "REPORTED · UNVERIFIED",
            "matches": [],
            "appearances": [],
            "error": None,
            "source_name": "TheSportsDB",
        }
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
                for event in relevant_events(slug, air, league_cache[league]):
                    events.setdefault(str(event["idEvent"]), event)
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
            "Not announcements from WWE, AAA or TNA."
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
    args = parser.parse_args()
    snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    if snapshot.get("schema_version") != 1 or len(snapshot.get("shows", [])) != 6:
        raise SystemExit("Invalid schedule snapshot; do not overwrite reported feed")
    result = build_reported(snapshot, next_lookup=request_next_league if args.also_next_league else None)
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(target)
    print("REPORTED_UNVERIFIED match lines:", result["total_reported_matches"])


if __name__ == "__main__":
    main()
