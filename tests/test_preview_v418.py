import unittest
from pathlib import Path
H=(Path(__file__).resolve().parents[1]/'web/preview-v4-18.html').read_text()
class MultiArticleCoverage(unittest.TestCase):
    def test_compact_source_attributed_headlines_not_invented_results(self):
        self.assertIn('function coverageWindow(key)',H)
        self.assertIn('rows.slice(page*3,page*3+3)',H)
        self.assertIn('const group=coverageWindow(key)',H)
        self.assertIn("entry.source_name.toUpperCase()",H)
        self.assertIn('headline.textContent=entry.headline;',H)
        self.assertIn('link.href=entry.url;',H)
        self.assertIn('NO MATCH RESULTS INFERRED',H)
        self.assertIn("'LINKS'",H)
    def test_previous_editorial_and_evolve_remain_untouched(self):
        self.assertIn('renderEvolveRecap(show);',H)
        self.assertIn('renderEditorialRecap(show,key);',H)
        self.assertIn('REPORTED / UNVERIFIED',H)
        self.assertIn('DISPLAY BUILD 4.18',H)
        self.assertIn('#board{width:min(100vw,56.25dvh)',H)
        self.assertIn('aspect-ratio:9/16',H)
if __name__=='__main__':unittest.main()
