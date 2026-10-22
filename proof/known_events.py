"""Remember source-observed event IDs, NOT published match text, across index gaps.

Only a successful live lookupevent response may put a known event's matches
on a broadcast. Local date and show filters are applied in reported_cards.py.
"""
from __future__ import annotations
import argparse
from datetime import datetime, date
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

TZ=ZoneInfo("America/New_York")
ALLOWED={"raw","smackdown","nxt","tna"}
MODE="KNOWN_PROVIDER_EVENT_IDENTIFIERS"
ID=re.compile(r"[1-9]\d{0,14}")


def build_known(previous: dict, report: dict, today:date) -> dict:
    if report.get("mode")!="REPORTED_MATCHES_UNVERIFIED":
        raise ValueError("Untrusted reported feed")
    old={(x.get("show_id"),x.get("airdate")):x.get("event_ids",[])
         for x in previous.get("entries",[]) if isinstance(x,dict)}
    entries=[]
    for p in report.get("programs",[]):
        sid,air=p.get("show_id"),p.get("airdate")
        if sid not in ALLOWED:
            continue
        try:
            when=date.fromisoformat(air)
        except (TypeError,ValueError):
            continue
        if not today<=when<=today.replace(year=today.year+1):
            # Date-scoped cache can never resurface an old TV card.
            continue
        ids=[]
        for val in list(old.get((sid,air),[]) or [])+[
            m.get("provider_event_id") for m in p.get("matches",[])+p.get("appearances",[])
            if isinstance(m,dict)]:
            s=str(val)
            if ID.fullmatch(s) and s not in ids:
                ids.append(s)
            if len(ids)>=4:
                break
        if ids:
            entries.append({"show_id":sid,"airdate":air,"event_ids":ids})
    return {
        "schema_version":1, "mode":MODE,
        "generated_at":datetime.now(TZ).isoformat(),
        "policy":"Identifiers only. Always re-fetch a live API event and recheck show/date/status before displaying; never copy historic match text.",
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
