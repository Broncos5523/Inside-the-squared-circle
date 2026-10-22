import unittest,re
from pathlib import Path
PAGE=(Path(__file__).resolve().parents[1]/"web/preview-v4-21.html").read_text()
class PreviewV421(unittest.TestCase):
    def test_shows_two_short_wrestling_results_and_not_clipped_long_results(self):
        self.assertIn("function groupedRecapResultPages(rows)",PAGE)
        self.assertIn("a.text.length+b.text.length<=155",PAGE)
        self.assertIn("a.match_type.length<=56 && b.match_type.length<=56",PAGE)
        self.assertIn("pages.push(pair?[i,i+1]:[i])",PAGE)
        self.assertIn("card.classList.toggle('two-result-mode',indices.length===2)",PAGE)
        self.assertIn("createRecapResult(rows[n],n)",PAGE)
        self.assertIn("createRecapResult(results[n],n)",PAGE)
        self.assertIn("String(results.length).padStart(2,'0')+' RESULTS'",PAGE)
        self.assertIn("recap-result-item+.recap-result-item",PAGE)
    def test_link_free_clean_labels_and_existing_filters(self):
        self.assertNotRegex(PAGE,r'<a\b')
        self.assertNotIn("createElement('a')",PAGE)
        self.assertNotIn("REPORTED / UNVERIFIED · FINISHED SHOW",PAGE)
        self.assertNotIn("REPORTED MATCHES · UNVERIFIED",PAGE)
        self.assertIn("x.status==='REPORTED_UNVERIFIED'",PAGE)
        self.assertIn("record.airdate!==show.previous?.date",PAGE)
        self.assertIn("televisionBroadcastFinished(past,key)",PAGE)
        self.assertIn("renderEvolveRecap(show);",PAGE)
    def test_portrait_and_existing_rotation(self):
        self.assertIn("DISPLAY BUILD 4.21",PAGE)
        self.assertIn("#board{width:min(100vw,56.25dvh)",PAGE)
        self.assertIn("aspect-ratio:9/16",PAGE)
        self.assertIn("renderEditorialRecap(show,key);",PAGE)
        self.assertIn("showReportedAppearances(show,key,evolve);",PAGE)
if __name__=="__main__":unittest.main()
