"""Research-only health probe for the openly advertised OWDB JSON API.

No scraping, no page parsing, no assumptions about match results.
Do not publish or display information from this provider until the schema,
weekly coverage, and permissions have been verified independently.
"""
from __future__ import annotations
import json
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

ROOT="https://wrestlingdb.org/api/"
def probe(requester=None):
    if requester is None:
        def requester():
            req=Request(ROOT,headers={"Accept":"application/json",
                 "User-Agent":"InsideSquaredCircle/1.0 (source compatibility research)"})
            with urlopen(req,timeout=12) as response:
                content_type=response.headers.get("Content-Type","")
                if "json" not in content_type.lower(): return {"status":"not_json"}
                return json.load(response)
    try:
        body=requester()
    except (HTTPError,URLError,TimeoutError,ValueError,OSError) as exc:
        return {"status":"unavailable","reason":type(exc).__name__}
    if not isinstance(body,dict):
        return {"status":"unexpected_schema"}
    # Print only top-level keys and candidate explicitly advertised paths.
    # Don't leak user data and don't pretend a collection is match results.
    items=sorted(str(k)[:40] for k in body)[:18]
    paths=[]
    for k,v in body.items():
        if str(k).lower() in ("links","endpoints","routes","resources","collections") and isinstance(v,dict):
            paths=[str(x)[:70] for x in list(v.keys())[:18]]
        elif str(k).lower() in ("links","endpoints","routes","resources","collections") and isinstance(v,list):
            paths=[str(x)[:70] for x in v[:12] if isinstance(x,str)]
    # One top-level sample for documented discovery; do not request pages.
    matches=body.get("matches")
    sample={"type":type(matches).__name__}
    if isinstance(matches,str):sample["value"]=matches[:160]
    elif isinstance(matches,dict):sample["keys"]=[str(x)[:80] for x in list(matches)[:10]]
    elif isinstance(matches,list):
        sample["count"]=len(matches)
        if matches and isinstance(matches[0],dict):
            sample["first_object_keys"]=[str(x)[:40] for x in list(matches[0])[:12]]
    elif isinstance(matches,int):sample["count"]=matches
    return {"status":"json_schema_discovered","top_level_keys":items,"declared_routes":paths,
            "matches_shape":sample}
if __name__=="__main__":
    print("OWDB public API non-publishing probe:",json.dumps(probe(),sort_keys=True))
