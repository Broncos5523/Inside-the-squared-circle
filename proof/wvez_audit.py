"""Research-only audit of MIT-licensed WVEZ WWE TV result corpus.

Uses public GitHub *repository artifacts*, never WWE/SmackDownHotel webpages.
No match data is published by this probe. It checks October 2026 freshness
before a separate, independently reviewed consumer is considered.
"""
import json, re, hashlib
from urllib.request import Request,urlopen
from datetime import date

BASE="https://raw.githubusercontent.com/warner-wvez/wrestling-dashboard/main/"
PATHS=("LICENSE","index.html","shards/matches-2025.json")
def fetch(path):
    if path not in PATHS: raise ValueError("Unapproved source")
    with urlopen(Request(BASE+path,headers={"User-Agent":"InsideSquaredCircle/1.0 (MIT data compatibility audit)"}),
                 timeout=25) as response:
        return response.read(8_000_001)

def inspect(licensed:bytes, page:bytes, shard:bytes):
    if not licensed.startswith(b"MIT License") or b"Copyright (c) 2026 Warner Varnado" not in licensed:
        raise ValueError("Source license mismatch")
    match=re.search(rb'<script id="wrestling-data" type="application/json">(.*?)</script>',page,re.S)
    if not match:raise ValueError("No published lean core")
    core=json.loads(match.group(1))
    shards=json.loads(shard)
    events=core.get("events",{})
    if not isinstance(events,dict) or not isinstance(shards,dict):
        raise ValueError("Malformed current data corpus")
    rows=[]
    for eid,event in events.items():
        if not isinstance(event,dict):continue
        air=event.get("air_date")
        if not isinstance(air,str) or not re.fullmatch(r"2026-10-\d\d",air):continue
        if not date(2026,10,1)<=date.fromisoformat(air)<=date(2026,10,31):continue
        rows.append((air,str(event.get("show_type")),str(event.get("title"))[:100],
                     len(shards.get(eid,[])),eid))
    rows.sort()
    print("WVEZ_MATCH_SOURCE_AUDIT="+json.dumps({
        "source":"warner-wvez/wrestling-dashboard (MIT)",
        "core_sha256":hashlib.sha256(page).hexdigest()[:16],
        "shard_sha256":hashlib.sha256(shard).hexdigest()[:16],
        "generated_at":core.get("meta",{}).get("generated_at"),
        "event_total":len(events),
        "october_2026_events":rows[-35:],
        "latest_october_date":max((r[0] for r in rows),default=None),
        "license":"MIT; facts only, no descriptions replicated",
    }))
if __name__=="__main__":
    inspect(*(fetch(p) for p in PATHS))
