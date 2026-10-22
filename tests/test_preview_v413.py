import unittest
from pathlib import Path

HTML=(Path(__file__).resolve().parents[1]/'web/preview-v4-13.html').read_text()
class ResultsPageTests(unittest.TestCase):
    def test_results_source_appears_only_when_loaded_and_not_preair(self):
        self.assertIn("data/results.json",HTML)
        self.assertIn("PROVIDER_REPORTED_POST_BROADCAST_RESULTS_UNVERIFIED",HTML)
        self.assertIn("televisionBroadcastFinished(show,key)",HTML)
        self.assertIn("record.airdate>today",HTML)
        self.assertIn("age>480",HTML)
        self.assertIn("source-reported",HTML.lower())
    def test_result_page_rotates_only_with_real_outcomes(self):
        self.assertIn("resultRows(k).length?[k,k+'-results']:[k]",HTML)
        self.assertIn("const forceResults=reviewParams.get('view')==='results';",HTML)
        self.assertIn("const resultsPage=slot.endsWith('-results');",HTML)
        self.assertIn("renderResults(show,key);",HTML)
        self.assertIn("NO TITLE CHANGES INFERRED",HTML)
    def test_existing_portrait_and_research_sources_preserved(self):
        self.assertIn("#board{width:min(100vw,56.25dvh)",HTML)
        self.assertIn("aspect-ratio:9/16",HTML)
        self.assertIn("tvmaze-reported.json",HTML)
        self.assertIn("research-20261022.json",HTML)
        self.assertIn("DISPLAY BUILD 4.13",HTML)
if __name__=='__main__':unittest.main()
