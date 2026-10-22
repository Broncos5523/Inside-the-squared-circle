import unittest
from pathlib import Path
H=(Path(__file__).resolve().parents[1]/'web/preview-v4-23.html').read_text()
class ResultFreshness(unittest.TestCase):
    def test_previous_broadcast_date_matches_before_results_screen_is_allowed(self):
        self.assertIn("const completed=[broadcast?.previous?.date,broadcast?.next?.date]",H)
        self.assertIn("record.airdate!==completed",H)
        self.assertIn("televisionBroadcastFinished({next:{date:day",H)
        self.assertIn("resultRows(k).length&&!hasReviewed",H)
    def test_prior_approved_look_and_clean_labels(self):
        self.assertIn('DISPLAY BUILD 4.23',H)
        self.assertIn('justify-content:space-evenly;',H)
        self.assertIn("createRecapResult(results[n],n)",H)
        self.assertIn('#board{width:min(100vw,56.25dvh)',H)
        self.assertNotIn("createElement('a')",H)
        self.assertIn('aspect-ratio:9/16',H)
if __name__=='__main__':unittest.main()
