import unittest
from pathlib import Path

HTML=(Path(__file__).resolve().parents[1]/'web/preview-v4-17.html').read_text()
class ThreePublisherFrontendTests(unittest.TestCase):
    def test_exact_url_to_source_consistency(self):
        self.assertIn("'411Mania':/^https:\\/\\/(?:www\\.)?411mania\\.com\\/",HTML)
        self.assertIn("'Fightful':/^https:\\/\\/(?:www\\.)?fightful\\.com\\/",HTML)
        self.assertIn("'F4W / Wrestling Observer':/^https:",HTML)
        self.assertIn("allowed[link.source_name].test(link.url||'')",HTML)
        self.assertIn("link.textContent='READ ARTICLE · '+selected.source_name.toUpperCase()",HTML)
    def test_source_specific_footer_and_no_winner_claim(self):
        self.assertIn("chosen.source_name+' RSS'",HTML)
        self.assertIn("no results inferred",HTML)
        self.assertIn('PUBLISHER_HEADLINE_LINK_ONLY',HTML)
        self.assertIn('COVERAGE LINK ',HTML)
    def test_review_only_preserves_sizing_and_past_versions(self):
        self.assertIn('DISPLAY BUILD 4.17',HTML)
        self.assertIn('#board{width:min(100vw,56.25dvh)',HTML)
        self.assertIn('aspect-ratio:9/16',HTML)
        self.assertIn('renderEvolveRecap(show);',HTML)
        self.assertIn('renderEditorialRecap(show,key);',HTML)
if __name__=="__main__":unittest.main()
