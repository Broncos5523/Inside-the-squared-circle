"""Review-only enriched Results & Fallout while preserving v4.15 and the production default."""
import unittest
from pathlib import Path
PAGE=(Path(__file__).resolve().parents[1]/'web/preview-v4-16.html').read_text()
class RecapSourceTests(unittest.TestCase):
    def test_date_scoped_sourced_details_not_just_rss_headlines(self):
        for x in ("DATED_MULTI_SOURCE_RECAP_REVIEW_UNVERIFIED",
                  "editorial-recaps-20261022.json",
                  "record.airdate!==show.previous?.date",
                  "days>14","televisionBroadcastFinished(past,key)",
                  "renderEditorialRecap(show,key);",
                  "const editorialPage=slot.endsWith('-recap');",
                  "const forceRecap=reviewParams.get('view')==='recap';"):
            self.assertIn(x,PAGE)
    def test_source_specific_footer_not_the_sportsdb_for_all(self):
        self.assertIn("renderAttribution(show,evolve,resultsPage,coveragePage,editorialPage)",PAGE)
        self.assertIn("sourceLink(reviewed.source_url,reviewed.source_name)",PAGE)
        self.assertIn("SOURCE · '+record.source_name.toUpperCase()",PAGE)
        self.assertIn("REPORTED / UNVERIFIED",PAGE)
    def test_long_evolve_result_qa_correction(self):
        self.assertIn("is-recap",PAGE)
        self.assertIn("#board.is-recap #card{justify-content:flex-start",PAGE)
        self.assertIn("#board.is-recap #card .long-result .reported-text",PAGE)
        self.assertIn("#board.is-recap #report-status",PAGE)
        self.assertIn("renderEvolveRecap(show);",PAGE)
    def test_portrait_source_and_old_preview_preserved(self):
        self.assertIn("#board{width:min(100vw,56.25dvh)",PAGE)
        self.assertIn("aspect-ratio:9/16",PAGE)
        self.assertIn("recap-links.json",PAGE)
        self.assertIn("DISPLAY BUILD 4.16",PAGE)
if __name__=='__main__':unittest.main()
