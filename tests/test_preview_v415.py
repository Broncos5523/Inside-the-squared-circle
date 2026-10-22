"""Verify V4.15 RSS-derived publisher links don't masquerade as outcomes."""
import unittest
from pathlib import Path
PAGE=(Path(__file__).resolve().parents[1]/"web/preview-v4-15.html").read_text()
class PublisherCoverPreviewTests(unittest.TestCase):
    def test_link_only_rss_feed_and_optional_rotation(self):
        for text in ("PUBLISHER_RSS_POST_SHOW_LINKS_ONLY",
                     "recap-links.json","PUBLISHER_HEADLINE_LINK_ONLY",
                     "function renderCoverage(show,key)", "coverageRows(k).length",
                     "const coveragePage=slot.endsWith('-coverage')",
                     "const forceCoverage=reviewParams.get('view')==='coverage';"):
            self.assertIn(text,PAGE)
    def test_source_specific_footer_corrected(self):
        self.assertIn('id="source-footer"',PAGE)
        self.assertIn("function renderAttribution(evolve,resultsPage,coveragePage)",PAGE)
        self.assertIn("Evolve recap: independent episode review / TVmaze synopsis",PAGE)
        self.assertNotIn('Reported matches and appearances are UNVERIFIED · <a href="https://www.thesportsdb.com/">TheSportsDB</a>',PAGE)
    def test_existing_approved_geometry_and_spoiler_guard(self):
        self.assertIn("#board{width:min(100vw,56.25dvh)",PAGE)
        self.assertIn("aspect-ratio:9/16",PAGE)
        self.assertIn("televisionBroadcastFinished(finished,key)",PAGE)
        self.assertIn("renderEvolveRecap(show);",PAGE)
        self.assertIn("DISPLAY BUILD 4.15",PAGE)
if __name__=="__main__":unittest.main()
