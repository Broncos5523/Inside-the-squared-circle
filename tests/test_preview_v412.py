import unittest
from pathlib import Path

PAGE=(Path(__file__).resolve().parents[1]/'web/preview-v4-12.html').read_text()

class PreAirBoardTests(unittest.TestCase):
    def test_tna_prior_to_11_15_et_shows_reported_card(self):
        self.assertIn("function televisionBroadcastFinished(show,key)",PAGE)
        self.assertIn("show.next?.time==='21:00'",PAGE)
        self.assertIn(">=1395",PAGE)
        self.assertIn("record.episode_outcome_detected && televisionBroadcastFinished(show,key)",PAGE)
        self.assertIn("provider.episode_outcome_detected && televisionBroadcastFinished(show,key)",PAGE)
    def test_source_labels_and_portrait(self):
        self.assertIn("9 PM ET · AMC",PAGE)
        self.assertIn("REPORTED / UNVERIFIED",PAGE)
        self.assertIn("research-20261022.json",PAGE)
        self.assertIn("DISPLAY BUILD 4.12",PAGE)
        self.assertIn("#board{width:min(100vw,56.25dvh)",PAGE)
if __name__=='__main__':
    unittest.main()
