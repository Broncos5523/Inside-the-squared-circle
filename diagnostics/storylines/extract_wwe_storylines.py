"""Extract source-grounded storyline candidate segments from WWE's official episode recap.
Diagnostic only: no public feed, no image reuse, no automatic editorial approval.
"""
import json
import re
import urllib.request
from html.parser import HTMLParser

URL = "https://www.wwe.com/shows/smackdown/2026-10-23/results"
class Reader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, value):
        value = " ".join(value.split())
        if 35 <= len(value) <= 900:
            self.parts.append(value)

request = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(request, timeout=20) as response:
    raw = response.read(1500000).decode("utf-8", "replace")
reader = Reader()
reader.feed(raw)
rules = {
    "tag_to_six_man": ["Ricky Saints", "disqualification", "Penta"],
    "rhodes_orton": ["Cody Rhodes", "Randy Orton", "Last Man Standing"],
    "punk_owens": ["CM Punk", "Kevin Owens", "Brooklyn"],
    "womens_title_fallout": ["Chelsea Green", "Tiffany Stratton", "Judgment Day"],
    "tag_title_interference": ["Jade Cargill", "Tatum Paxley", "Michin"],
}
# Candidate detection across source segments, not hallucinated storyline summaries.
matches = {}
for key, keywords in rules.items():
    evidence = []
    for index, paragraph in enumerate(reader.parts):
        if any(word.casefold() in paragraph.casefold() for word in keywords):
            evidence.append({"segment_index": index, "matched_terms": [word for word in keywords if word.casefold() in paragraph.casefold()]})
    matches[key] = {
        "terms_found": sorted(set(term for item in evidence for term in item["matched_terms"])),
        "source_segment_count": len(evidence),
        "candidate_only": True,
    }
print("WWE_STORYLINES|" + json.dumps({"source": URL, "episode_date": "2026-10-23", "storyline_candidates": matches, "automatic_editorial_approval": False}))
