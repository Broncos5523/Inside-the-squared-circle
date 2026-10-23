"""Never display stale results or turn RSS review headlines into fabricated match outcomes."""
import unittest
from pathlib import Path
H=(Path(__file__).resolve().parents[1]/'web/preview-v4-24.html').read_text()
class MultiSourceUI(unittest.TestCase):
    def test_aggregate_source_validated_exact_broadcast_date(self):
        for x in (
          "function newestCompleted(show,key)",
          "function resultRows(key)",
          "rss-facts.json",
          "POST_BROADCAST_RSS_EXPLICIT_FACTS_UNVERIFIED",
          "rssRecord?.airdate===latest",
          "provider?.airdate===latest",
          "x.evidence_type!=='RSS_EXPLICIT_HEADLINE'",
          "collected.filter(x=>",
        ):self.assertIn(x,H)
    def test_expire_old_manual_recaps_after_next_episode_airs(self):
        self.assertIn("record.airdate!==newestCompleted(show,key)",H)
        self.assertIn("evolveEditorial.airdate!==newestCompleted(show,'evolve')",H)
        self.assertIn("televisionBroadcastFinished({next:{date:day",H)
    def test_no_visual_changes(self):
        self.assertIn('DISPLAY BUILD 4.24',H)
        self.assertIn("createRecapResult(rows[n],n)",H)
        self.assertIn("createRecapResult(results[n],n)",H)
        self.assertIn("justify-content:space-evenly;",H)
        self.assertIn("#board{width:min(100vw,56.25dvh)",H)
        self.assertNotIn("createElement('a')",H)
        self.assertIn("aspect-ratio:9/16",H)
if __name__=='__main__':unittest.main()
