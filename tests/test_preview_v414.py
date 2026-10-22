import unittest
from pathlib import Path

PAGE=(Path(__file__).resolve().parents[1]/'web/preview-v4-14.html').read_text()
class EvolveRecapPreviewTests(unittest.TestCase):
    def test_real_results_and_episode_synopsis_separately_labeled(self):
        self.assertIn("function renderEvolveRecap(show)",PAGE)
        self.assertIn("renderEvolveRecap(show);",PAGE)
        self.assertIn("DATED_EDITORIAL_EVOLVE_RECAP_UNVERIFIED",PAGE)
        self.assertIn("TVMAZE_EVOLVE_EPISODE_SYNOPSIS_ONLY",PAGE)
        self.assertIn("SYNOPSIS ONLY · DOES NOT IDENTIFY MATCH WINNERS",PAGE)
        self.assertIn("RESULTS COVERAGE INCOMPLETE · NO WINNERS INFERRED",PAGE)
    def test_prior_episode_only_date_limit_and_attribution(self):
        self.assertIn("evolveEditorial.airdate!==show.previous?.date",PAGE)
        self.assertIn("days>14",PAGE)
        self.assertIn("OCT 21 EPISODE REVIEW",PAGE)
        self.assertIn("REPORTED / UNVERIFIED",PAGE)
    def test_legacy_design_unchanged(self):
        self.assertIn("#board{width:min(100vw,56.25dvh)",PAGE)
        self.assertIn("aspect-ratio:9/16",PAGE)
        self.assertIn("DISPLAY BUILD 4.14",PAGE)
        self.assertIn("data/results.json",PAGE)
if __name__=='__main__':
    unittest.main()
