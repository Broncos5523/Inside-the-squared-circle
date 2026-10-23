import unittest
from pathlib import Path
H=(Path(__file__).resolve().parents[1]/'web/preview-v4-26.html').read_text()
class AdditionalResultSource(unittest.TestCase):
    def test_syndicated_fact_source_is_date_matched_and_validated(self):
        for field in (
            'rss-excerpt-results.json',
            'RSS_SYNDICATED_EXCERPT_FACT',
            'POST_BROADCAST_RSS_SYNDICATED_EXCERPT_FACTS_UNVERIFIED',
            'excerptRecord?.airdate===latest',
            'collected.push({...x,origin:',
            'return collected.filter(x=>',
        ):self.assertIn(field,H)
    def test_previous_results_layout_and_safety_kept(self):
        self.assertIn('DISPLAY BUILD 4.26',H)
        self.assertIn('record.airdate!==newestCompleted(show,key)',H)
        self.assertIn("createRecapResult(rows[n],n)",H)
        self.assertIn("createRecapResult(results[n],n)",H)
        self.assertIn('justify-content:space-evenly;',H)
        self.assertNotIn("createElement('a')",H)
        self.assertIn('#board{width:min(100vw,56.25dvh)',H)
if __name__=='__main__':unittest.main()
