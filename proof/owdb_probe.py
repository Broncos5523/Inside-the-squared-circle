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

def probe_matches_root(requester=None) -> dict:
    """Follow only the matches route explicitly advertised by OWDB."""
    if requester is None:
        def requester():
            root_req=Request(ROOT,headers={"Accept":"application/json",
                     "User-Agent":"InsideSquaredCircle/1.0 (public API research)"})
            with urlopen(root_req,timeout=12) as response:
                if "json" not in response.headers.get("Content-Type","").lower():
                    return {"status":"not_json"}
                index=json.load(response)
            if not isinstance(index,dict) or index.get("matches")!="https://wrestlingdb.org/api/matches/":
                return {"status":"no_declared_matches_route"}
            req=Request(index["matches"],headers={"Accept":"application/json",
                        "User-Agent":"InsideSquaredCircle/1.0 (public API research)"})
            with urlopen(req,timeout=12) as response:
                if "json" not in response.headers.get("Content-Type","").lower():
                    return {"status":"not_json"}
                return json.load(response)
    try:
        body=requester()
    except (HTTPError,URLError,TimeoutError,ValueError,OSError) as exc:
        return {"status":"unavailable","reason":type(exc).__name__}
    if not isinstance(body,(dict,list)):
        return {"status":"unexpected_schema","kind":type(body).__name__}
    if isinstance(body,list):
        items=body
        output={"kind":"list","total_returned":len(items)}
    else:
        output={"kind":"object","top_level_keys":[str(x)[:50] for x in list(body)[:20]]}
        items=next((body.get(k) for k in ("results","data","matches","items")
                    if isinstance(body.get(k),list)),[])
        for count in ("count","total","total_count"):
            if isinstance(body.get(count),int):output["declared_count"]=body[count]
    if items and isinstance(items[0],dict):
        row=items[0]
        output["first_row_keys"]=[str(x)[:50] for x in list(row)[:35]]
        for k in ("id","event","event_id","event_name","event_date","date",
                  "match_date","winner","result","winners","participants","promotion",
                  "match_type"):
            if k in row:
                output["example_"+k]=str(row[k])[:160]
    return {"status":"matches_json_discovered","schema":output}

if __name__=="__main__":
    print("OWDB public API non-publishing probe:",json.dumps(probe(),sort_keys=True))
    print("OWDB documented matches schema probe:",json.dumps(probe_matches_root(),sort_keys=True))
