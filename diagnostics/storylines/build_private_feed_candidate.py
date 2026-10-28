"""Build a structured private-feed candidate from reviewed storyline data.
No publishing: writes local JSON for GitHub Actions artifact only.
"""
import json
import pathlib
import re
import urllib.request
from html.parser import HTMLParser

ROOT=pathlib.Path(__file__).resolve().parents[2]
review=json.loads((ROOT/"diagnostics/storylines/smackdown-2026-10-23.review.json").read_text())
url=review["source"]["url"]
class Reader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts=[]
    def handle_data(self,value):
        value=" ".join(value.split())
        if value:self.parts.append(value)
req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
with urllib.request.urlopen(req,timeout=20) as response:
    html=response.read(1500000).decode("utf-8","replace")
reader=Reader()
reader.feed(html)
results=[]
for line in reader.parts:
    if len(line)>250 or " def. " not in line.lower():continue
    m=re.match(r"^(.+?)\s+def[.]\s+(.+)$",line,re.I)
    if not m:continue
    winner,loser=m.groups()
    dq=bool(re.search(r" by disqualification$",loser,re.I))
    loser=re.sub(r" by disqualification$","",loser,flags=re.I)
    stipulation=None
    for suffix in (" in a WWE Women's Championship Match"," in a Street Fight"):
        if loser.endswith(suffix):
            loser=loser[:-len(suffix)]
            stipulation=suffix.strip()[5:]
            break
    title_change=bool(re.search(r"\bto capture\b|\bto win\b",loser,re.I))
    loser=re.split(r"\s+to capture\b|\s+to win\b",loser,maxsplit=1,flags=re.I)[0]
    result={"winner":winner,"loser":loser,"finish":"disqualification" if dq else None,"stipulation":stipulation,"title_change":title_change}
    if result not in results:results.append(result)
# This reviewed date has exactly five official completed match headings.
if len(results)!=5:
    raise SystemExit(f"Source changed: expected 5 matches, found {len(results)}; refusing to export")
# Each reviewed storyline requires all named participants to be present somewhere in source text.
source_text=" ".join(reader.parts).casefold()
storylines=[]
for item in review["storylines"]:
    missing=[name for name in item["participants"] if name.casefold() not in source_text]
    if missing:
        raise SystemExit(f"Storyline {item['id']} has names absent from source: {missing}")
    storylines.append(item)
payload={"schema_version":1,"show":review["show"],"episode_date":review["episode_date"],"source":review["source"],"review_status":"human_reviewed_example","matches":results,"storylines":storylines,"display_rules":review["display_rules"]}
out=ROOT/"private-feed-preview.json"
out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
print(f"PRIVATE_FEED_CANDIDATE|matches={len(results)} storylines={len(storylines)} validated_names=yes; payload retained as short-lived workflow artifact only")
