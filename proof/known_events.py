"""Remember source-observed event IDs, NOT published match text, across index gaps.

Only a successful live lookupevent response may put a known event's matches
on a broadcast. Local date and show filters are applied in reported_cards.py.
"""
from __future__ import annotations
import argparse
from datetime import datetime, date, timedelta
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

TZ=ZoneInfo("America/New_York")
ALLOWED={"raw","smackdown","nxt","tna"}
MODE="KNOWN_PROVIDER_EVENT_IDENTIFIERS"
ID=re.compile(r"[1-9]\d{0,14}")


def build_known(previous: dict, report: dict, today: date) -> dict:
    """Preserve source-observed IDs across broadcast day and short index gaps.

    IDs are NOT match claims. Results intake always re-fetches the event and
    checks exact show, league and airdate before generating an outcome.
    """
    if report.get("mode")!="REPORTED_MATCHES_UNVERIFIED":
        raise ValueError("Untrusted reported feed")
    earliest=today-timedelta(days=14)
    latest=today+timedelta(days=365)
    merged={}
    def accept(sid,air,values):
        if sid not in ALLOWED:
            return
        try:
            day=date.fromisoformat(air)
        except (TypeError,ValueError):
            return
        if not earliest<=day<=latest:
            return
        key=(sid,air)
        ids=merged.setdefault(key,[])
        for v in values:
            val=str(v)
            if ID.fullmatch(val) and val not in ids and len(ids)<4:
                ids.append(val)
    for old in previous.get("entries",[]) if isinstance(previous.get("entries"),list) else []:
        if isinstance(old,dict):
            accept(old.get("show_id"),old.get("airdate"),(old.get("event_ids") or [])[:8])
    for program in report.get("programs",[]):
        if not isinstance(program,dict):
            continue
        source=(program.get("matches") or [])+(program.get("appearances") or [])
        accept(program.get("show_id"),program.get("airdate"),
               [row.get("provider_event_id") for row in source if isinstance(row,dict)])
    entries=[{"show_id":sid,"airdate":day,"event_ids":ids}
             for (sid,day),ids in sorted(merged.items())
             if ids]
    return {
        "schema_version":1,"mode":MODE,
        "generated_at":datetime.now(TZ).isoformat(),
        "policy":"Identifiers only, retained 14 days after airdate to permit post-show lookup. Always re-fetch source event and recheck league/show/local day; never copy historic match claims.",
        "entries":entries
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--previous",default="web/data/known-events.json")
    ap.add_argument("--reported",default="web/data/reported.json")
    ap.add_argument("--out",default="web/data/known-events.json")
    args=ap.parse_args()
    try:
        previous=json.loads(Path(args.previous).read_text(encoding="utf-8"))
    except (OSError,ValueError):
        previous={}
    report=json.loads(Path(args.reported).read_text(encoding="utf-8"))
    result=build_known(previous,report,datetime.now(TZ).date())
    target=Path(args.out)
    temp=target.with_suffix(".tmp")
    temp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    temp.replace(target)
    print("Known event ID references retained:",sum(len(x["event_ids"]) for x in result["entries"]))


if __name__=="__main__":
    main()
