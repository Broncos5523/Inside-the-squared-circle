import unittest
from pathlib import Path
H=(Path(__file__).resolve().parents[1]/'web/preview-v4-27.html').read_text()
class ExpandedSourcePreview(unittest.TestCase):
    def test_additional_provider_whitelist_date_safety(self):
        for term in ("Gerweck.net","TPWW",
                    "gerweck\\.net", "tpww\\.net",
                    "excerptRecord?.airdate===latest",
                    "rssRecord?.airdate===latest",
                    "RSS_SYNDICATED_EXCERPT_FACT"):
            self.assertIn(term,H)
    def test_previous_approved_design_unchanged(self):
        for term in ("DISPLAY BUILD 4.27","createRecapResult(rows[n],n)",
                     "createRecapResult(results[n],n)",
                     "justify-content:space-evenly;",
                     "#board{width:min(100vw,56.25dvh)","aspect-ratio:9/16"):
            self.assertIn(term,H)
        self.assertNotIn("createElement('a')",H)
if __name__=='__main__':unittest.main()
