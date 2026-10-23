"""Dated, manually source-reviewed AAA Heroes Inmortales TV-week card safety checks."""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OLD=(ROOT/"web/preview-v4-30.html").read_text(encoding="utf-8")
NEW=(ROOT/"web/preview-v4-31.html").read_text(encoding="utf-8")
DATA=json.loads((ROOT/"web/data/aaa-tv-week-cards-20261023.json").read_text(encoding="utf-8"))

class AAAWeeks(unittest.TestCase):
    def test_valid_dated_week_assignments(self):
        self.assertEqual(DATA["mode"],"DATED_AAA_TV_WEEK_CARD_REVIEW_UNVERIFIED")
        self.assertEqual(DATA["reviewed_at_et"],"2026-10-23")
        self.assertEqual([x["airdate"] for x in DATA["programs"]],
                         ["2026-10-24","2026-10-31","2026-11-07"])
        self.assertEqual([len(x["matches"]) for x in DATA["programs"]],[3,1,1])
        self.assertEqual([len(x["appearances"]) for x in DATA["programs"]],[1,0,0])
    def test_fact_sources_and_no_winner_inference(self):
        for episode in DATA["programs"]:
            self.assertEqual(episode["show_id"],"aaa")
            for row in episode["matches"]+episode["appearances"]:
                self.assertEqual(row["status"],"REPORTED_UNVERIFIED")
                self.assertIn(row["source_name"],("411Mania","TPWW"))
                self.assertRegex(row["evidence_url"],
                  r"^https://(?:411mania\.com/wrestling/aaa-heroes-inmortales-2026-full-lineup/|www\.tpww\.net/2026/10/10-17-aaa-tv-notes-quick-match-results-[a-z0-9-]+/)$")
                self.assertNotIn("winner",row)
                self.assertNotIn("result",row)
    def test_authoritative_episode_mapping(self):
        future={x["airdate"]:x for x in DATA["programs"]}
        self.assertIn("El Grande Americano",future["2026-10-24"]["matches"][0]["text"])
        self.assertIn("Rey Fenix",future["2026-10-31"]["matches"][0]["text"])
        self.assertIn("El Fiscal",future["2026-11-07"]["matches"][0]["text"])
    def test_old_design_immutable(self):
        self.assertEqual(OLD.split("<style>",1)[1].split("</style>",1)[0],
                         NEW.split("<style>",1)[1].split("</style>",1)[0])
        self.assertIn("DISPLAY BUILD 4.30",OLD)
        self.assertIn("DISPLAY BUILD 4.31",NEW)
        self.assertNotIn("createElement('a')",NEW)
        self.assertIn("#board{width:min(100vw,56.25dvh)",NEW)
    def test_strict_airdate_and_publisher_gate(self):
        self.assertIn("record.airdate===show?.next?.date",NEW)
        self.assertIn("record.airdate<easternToday()",NEW)
        self.assertIn("provider.episode_withdrawn",NEW)
        self.assertIn("reviewedAaaFeed.reviewed_at_et>easternToday()",NEW)
        self.assertIn("DATED_AAA_TV_WEEK_CARD_REVIEW_UNVERIFIED",NEW)
        self.assertIn("reviewed-recaps.json",NEW)

if __name__=="__main__":unittest.main()
