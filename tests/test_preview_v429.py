import unittest
from pathlib import Path
H=(Path(__file__).resolve().parents[1]/'web/preview-v4-29.html').read_text()
class AutomaticStorylineUI(unittest.TestCase):
    def test_after_air_storyline_provenance(self):
        for q in ("rss-fallout.json","function falloutRows(key)",
                  "row.airdate!==newestCompleted(show,key)",
                  "RSS_SYNDICATED_FALLOUT_FACT",
                  "STORYLINES & FALLOUT","falloutRows(k).length"):
            self.assertIn(q,H)
    def test_previous_clean_portrait_design_unchanged(self):
        self.assertIn("DISPLAY BUILD 4.29",H)
        self.assertIn("createRecapResult(rows[n],n)",H)
        self.assertIn("createRecapResult(results[n],n)",H)
        self.assertIn("justify-content:space-evenly;",H)
        self.assertNotIn("createElement('a')",H)
        self.assertIn("#board{width:min(100vw,56.25dvh)",H)
if __name__=="__main__":unittest.main()
