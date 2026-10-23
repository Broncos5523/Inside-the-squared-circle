import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD=(ROOT/"web/preview-v4-29.html").read_text(encoding="utf-8")
NEW=(ROOT/"web/preview-v4-30.html").read_text(encoding="utf-8")

class ReviewedRecapPreviewTests(unittest.TestCase):
    def test_baseline_locked(self):
        self.assertIn("DISPLAY BUILD 4.29",OLD)
        self.assertIn("DISPLAY BUILD 4.30",NEW)
        self.assertIn("#board{width:min(100vw,56.25dvh)",NEW)
        self.assertIn("groupedRecapResultPages(rows)",NEW)
        self.assertIn("STORYLINES & FALLOUT",NEW)
        self.assertNotIn("createElement('a')",NEW)
    def test_opt_in_and_fallback(self):
        self.assertIn("reviewed-recaps.json",NEW)
        self.assertIn("REVIEWED_WEEKLY_EPISODE_FACTS_V1",NEW)
        self.assertIn("const imported=optInReviewedRecap(show,key);",NEW)
        self.assertIn("editorial-recaps-20261022.json",NEW)
        self.assertIn("const imported=optInReviewedRecap(show,'evolve');",NEW)
    def test_airdate_and_spoiler_checks(self):
        self.assertIn("record.airdate!==newestCompleted(show,key)",NEW)
        self.assertIn("record.airdate!==show.previous?.date",NEW)
        self.assertIn("televisionBroadcastFinished",NEW)
        self.assertIn("reviewedAt>Date.now()",NEW)
    def test_no_source_links(self):
        self.assertNotIn("createElement('a')",NEW)
        self.assertIn("text.textContent=row.text",NEW)

if __name__=="__main__":unittest.main()
