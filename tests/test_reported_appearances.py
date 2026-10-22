"""Deterministic tests for explicit, UNVERIFIED appearance/segment detection."""
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from proof.reported_cards import build_reported, parse_reported_appearances

NOW = datetime(2026, 10, 22, 16, 0, tzinfo=ZoneInfo("America/New_York"))
EVENT = {
    "idLeague": "4444", "idEvent": "2599790", "strEvent": "SmackDown #1418",
    "dateEventLocal": "2026-10-23", "dateEvent": "2026-10-23",
    "strDescriptionEN": (
        "Street Fight\nGiulia vs. Blake Monroe\n\n"
        "In-Ring Segment\nCody Rhodes addresses the crowd\n\n"
        "Interview\nRandy Orton discusses his next challenger\n\n"
        "Result\nSomeone defeated someone else\n\n"
        "Promo\nWinner: Someone beat Someone\n\n"
        "Dark Match\nA vs. B"
    )
}
SNAP = {"shows": [{"id": "smackdown", "next": {"date": "2026-10-23"}}]}


def request(day, league):
    return [EVENT] if day == "2026-10-23" and league == 4444 else []


class ExplicitAppearanceTests(unittest.TestCase):
    def test_explicit_api_segments_only(self):
        result = build_reported(SNAP, requester=request, now=NOW)
        show = result["programs"][0]
        self.assertEqual(len(show["matches"]), 1)
        self.assertEqual(len(show["appearances"]), 2)
        self.assertEqual(result["total_reported_appearances"], 2)
        self.assertTrue(all(a["status"] == "REPORTED_UNVERIFIED" for a in show["appearances"]))
        self.assertTrue(all(a["evidence_url"].endswith("id=2599790") for a in show["appearances"]))

    def test_no_match_participants_inferred_as_appearances(self):
        self.assertEqual(parse_reported_appearances("Singles Match\nA vs. B"), [])
        self.assertEqual(parse_reported_appearances("Promo\nRandy Orton vs. Cody Rhodes"), [])

    def test_reject_html_results_and_unlabeled_prose(self):
        self.assertEqual(parse_reported_appearances("<p>Promo</p>\nCody Rhodes appears"), [])
        self.assertEqual(parse_reported_appearances("Winner\nCody Rhodes pinned a rival"), [])
        self.assertEqual(parse_reported_appearances("Segment\nCody Rhodes defeated Randy Orton"), [])

    def test_wrong_airdate_prevents_appearance(self):
        result = build_reported(
            {"shows": [{"id": "smackdown", "next": {"date": "2026-10-24"}}]},
            requester=request, now=NOW,
        )
        self.assertEqual(result["programs"][0]["appearances"], [])

    def test_failed_source_gives_no_appearance(self):
        def failure(*_):
            raise ConnectionError("offline")
        result = build_reported(SNAP, requester=failure, now=NOW)
        self.assertEqual(result["programs"][0]["appearances"], [])
        self.assertEqual(result["total_reported_appearances"], 0)


if __name__ == "__main__":
    unittest.main()
