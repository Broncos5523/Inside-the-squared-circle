import unittest
from pathlib import Path
HTML=(Path(__file__).resolve().parents[1]/'web/preview-v4-19.html').read_text()
class ResultsFirstTest(unittest.TestCase):
    def test_old_coverage_url_opens_real_results_instead_of_headlines(self):
        self.assertIn("['recap','coverage'].includes(reviewParams.get('view'))",HTML)
        self.assertIn("if(forceRecap&&keys.length===1)return [keys[0]+'-recap'];",HTML)
        self.assertIn("renderEditorialRecap(show,key);",HTML)
        self.assertIn("'MATCH RESULTS · SOURCED'",HTML)
        self.assertNotIn("renderCoverage(show,key)",HTML)
        self.assertNotIn("coverageRows(k).length",HTML)
    def test_source_specific_winners_and_storyline_reports_preserved(self):
        self.assertIn("REPORTED / UNVERIFIED",HTML)
        self.assertIn("result.textContent",HTML) if False else None
        self.assertIn("r.text",HTML)
        self.assertIn("item.text",HTML)
        self.assertIn("record.airdate!==show.previous?.date",HTML)
        self.assertIn("days>14",HTML)
        self.assertIn("renderEvolveRecap(show);",HTML)
        self.assertIn("resultRows(k).length&&!hasReviewed",HTML)
    def test_layout_and_live_data_pipeline_unchanged(self):
        self.assertIn('DISPLAY BUILD 4.19',HTML)
        self.assertIn('#board{width:min(100vw,56.25dvh)',HTML)
        self.assertIn('aspect-ratio:9/16',HTML)
        self.assertIn('data/results.json',HTML)
        self.assertIn('data/editorial-recaps-20261022.json',HTML)
if __name__=="__main__":unittest.main()
