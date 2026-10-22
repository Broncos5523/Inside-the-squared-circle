"""Safe, limited automated match *mentions* from TVmaze's documented episode API.

This source is licensed CC BY-SA. No WWE/TNA page scraping, no fabricated card,
no winner/result inference, no AAA event/taping assignment and no Evolve previews.
TVmaze summaries are supplemental editorial descriptions, NEVER WWE confirmations.
"""
from __future__ import annotations
import argparse
from datetime import date, datetime
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
SHOW_IDS = {"raw":802, "smackdown":803, "nxt":2266, "tna":1349}
BLOCKED = re.compile(
    r"\b(?:dark match|house show|non[- ]televised|spoiler|prediction|"
    r"fantasy booking|results?|winner|defeated|defeats|pinfall|"
    r"last week|last night|yesterday|previously|"
    r"was scheduled|was cancelled|was canceled)\b", re.I)
VS = re.compile(r"\s+vs\.?\s+", re.I)
STIP = re.compile(
    r"^(?:[A-Za-z][A-Za-z0-9 '\-#&().]{2,85} (?:match|fight|semifinal|semi-final|title|championship))$",
    re.I)
NAME = re.compile(r"^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9 ,.'()&/#\-]{1,100}$")
MAX_SUMMARY = 12000

class Blocks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
    def handle_starttag(self,tag,attrs):
        if tag in ("p","li","br","h3","h4","ul","ol"):
            self.parts.append("\n")
    def handle_endtag(self,tag):
        if tag in ("p","li","h3","h4","ul","ol"):
            self.parts.append("\n")
    def handle_data(self,data):
        self.parts.append(data)

# Limited syntactic recognition of prospective title defenses in natural prose.
# No wrestler-name dictionary, no predictions, no past-tense "defeated" text.
TITLE_DEFENSE = re.compile(
    r"^(?P<left>[A-Z][A-Za-zÀ-ÿ'.-]{1,35}(?: [A-Z][A-Za-zÀ-ÿ'.-]{1,35}){1,2})"
    r" is set to put (?P<title>[^,.!?]{8,100}?) on the line against "
    r"(?:(?:The|the) [A-Za-z ]{2,42}'s )?"
    r"(?P<right>[A-Z][A-Za-zÀ-ÿ'.-]{1,35}(?: [A-Z][A-Za-zÀ-ÿ'.-]{1,35}){1,2})"
    r" this (?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
    re.I,
)

def direct_title_defense(text: str) -> dict | None:
    """Construct only the explicitly named pair of a future-tense title defense."""
    if BLOCKED.search(text):
        return None
    first_clause = text.split(",",1)[0].strip()
    match = TITLE_DEFENSE.search(first_clause)
    if not match:
        return None
    left,right = match.group("left"),match.group("right")
    title = re.sub(r"^(?:her|his|their|the) ", "", match.group("title").strip(), flags=re.I)
    if not title.lower().endswith(("championship","title")):
        return None
    names=f"{left} vs. {right}"
    if len(names)>150:
        return None
    return {"text":names,"stipulation":title+" Match"}

def candidates_from_summary(summary: object) -> list[dict]:
    """Accept only explicit X vs Y formulations in prospective episode descriptions.

    We *do not* infer participants from a narrative or infer a show card from
    episode titles, other programs, tapings, recaps, predictions or results.
    """
    if not isinstance(summary,str) or len(summary)>MAX_SUMMARY:
        return []
    parser = Blocks()
    parser.feed(summary)
    raw = "".join(parser.parts).replace("\r","")
    raw = re.sub(r"\bvs\.\s+", "vs ", raw, flags=re.I) # protect vs. sentence splitting
    entries=[]
    seen=set()
    for block in re.split(r"[\n;]+|(?<=[.!?])\s+(?=[A-Z])", raw):
        b=" ".join(block.split()).strip(" \t-•")
        if not b or len(b)>210 or BLOCKED.search(b):
            continue
        defense=direct_title_defense(b)
        if defense:
            sig=re.sub(r"[^a-z0-9]","",defense["text"].casefold())
            if sig not in seen:
                seen.add(sig)
                entries.append(defense)
            if len(entries)>=8:
                break
            continue
        # Only a short explicit match entry, optionally preceded by a
        # stipulation and delimiter, is extracted. Narrative clauses rejected.
        label="Reported match"
        match=b
        if ":" in b:
            left,right=b.split(":",1)
            if not STIP.fullmatch(left.strip()) and left.strip().lower() not in (
                 "match card","upcoming matches","scheduled matches","announced matches"):
                continue
            label=left.strip() if STIP.fullmatch(left.strip()) else label
            match=right.strip()
        if not VS.search(match):
            continue
        sides=VS.split(match)
        if not 2 <= len(sides) <= 4:
            continue
        if not all(NAME.fullmatch(side.strip()) for side in sides):
            continue
        if len(match)>160:
            continue
        key=re.sub(r"[^a-z0-9]","",match.casefold())
        if key in seen:
            continue
        seen.add(key)
        entries.append({"text":match,"stipulation":label})
        if len(entries)>=8:
            break
    return entries

def request_episodes(show_id:int,day:str,timeout:int=15)->list[dict]:
    url=f"https://api.tvmaze.com/shows/{show_id}/episodesbydate?date={day}"
    req=Request(url,headers={"Accept":"application/json","User-Agent":"InsideSquaredCircleHouseholdDemo/0.3"})
    try:
        with urlopen(req,timeout=timeout) as response:
            value=json.load(response)
    except HTTPError as e:
        if e.code==404:
            return []
        raise
    if not isinstance(value,list):
        raise ValueError("Unexpected TVmaze episode response")
    return value

def build_tvmaze(snapshot:dict, requester=request_episodes,now=None)->dict:
    now=now or datetime.now(ET)
    today=now.astimezone(ET).date()
    output=[]
    for s in snapshot.get("shows",[]):
        key=s.get("id")
        day=(s.get("next") or {}).get("date")
        record={"show_id":key,"airdate":day,"source_name":"TVmaze","matches":[],"appearances":[],
                "collection_status":"not_supported" if key not in SHOW_IDS else "no_upcoming_episode_summary"}
        if key not in SHOW_IDS:
            output.append(record)
            continue
        try:
            parsed=date.fromisoformat(day)
        except (TypeError,ValueError):
            output.append(record)
            continue
        if parsed<today or (parsed-today).days>20:
            output.append(record)
            continue
        if s.get("schedule_status")!="fresh":
            record["collection_status"]="schedule_stale_not_queried"
            output.append(record)
            continue
        try:
            episodes=requester(SHOW_IDS[key],day)
            matches=[]
            for episode in episodes:
                if not isinstance(episode,dict) or episode.get("airdate")!=day:
                    continue
                episode_id=episode.get("id")
                if not isinstance(episode_id,int) or episode_id<=0:
                    continue
                url=f"https://api.tvmaze.com/episodes/{episode_id}"
                for hit in candidates_from_summary(episode.get("summary")):
                    if hit["text"] in (m["text"] for m in matches):
                        continue
                    matches.append({
                        **hit,
                        "evidence_url":url,
                        "status":"REPORTED_UNVERIFIED",
                        "source_name":"TVmaze",
                        "provider_episode_id":episode_id,
                    })
            record["matches"]=matches[:8]
            record["collection_status"]="reported_mentions" if matches else "no_parseable_match_mentions"
        except Exception as exc:
            record["collection_status"]="api_unavailable"
            print(f"TVmaze {key} delayed: {type(exc).__name__}: {str(exc)[:120]}")
        output.append(record)
    return {"schema_version":1,
            "mode":"TVMAZE_EPISODE_SUMMARY_REPORTED_UNVERIFIED",
            "generated_at":now.isoformat(),
            "policy":"CC BY-SA TVmaze attributed episode-summary leads, not official advertised cards. Exact local airdate only; no spoilers or claims of completeness.",
            "programs":output,
            "total_reported_matches":sum(len(row["matches"]) for row in output)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--snapshot",default="web/data/snapshot.json")
    ap.add_argument("--out",default="web/data/tvmaze-reported.json")
    args=ap.parse_args()
    snap=json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    if snap.get("schema_version")!=1 or len(snap.get("shows",[]))!=6:
        raise SystemExit("Invalid snapshot. Refusing to generate TVmaze cards.")
    obj=build_tvmaze(snap)
    target=Path(args.out)
    target.parent.mkdir(parents=True,exist_ok=True)
    tmp=target.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    tmp.replace(target)
    print("TVmaze summary reported match mentions:",obj["total_reported_matches"])

if __name__=="__main__":
    main()
