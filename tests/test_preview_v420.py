import unittest,re
from pathlib import Path
H=(Path(__file__).resolve().parents[1]/"web/preview-v4-20.html").read_text()
class TelevisionCleanCopyTests(unittest.TestCase):
    def test_no_rendered_hyperlinks_on_any_board(self):
        self.assertNotRegex(H,r'<a\b')
        self.assertNotIn("createElement('a')",H)
        self.assertIn('TVmaze (CC BY-SA)',H)
    def test_requested_words_removed_from_visible_labels(self):
        for bad in (
            'REPORTED / UNVERIFIED · FINISHED SHOW',
            'REPORTED MATCHES · UNVERIFIED',
            'REPORTED APPEARANCES · UNVERIFIED',
            'FINISHED SHOW · MATCH RESULTS',
            'SCHEDULE CURRENT · REPORTED CARDS UNVERIFIED',
        ):
            self.assertNotIn(bad,H)
        for good in ('UPCOMING MATCHES','RESULTS & FALLOUT',
                     'MATCH CARDS SUBJECT TO CHANGE','APPEARANCES & SEGMENTS'):
            self.assertIn(good,H)
        # Status values in upstream data must not be rewritten or inflated.
        self.assertIn("x.status==='REPORTED_UNVERIFIED'",H)
        self.assertIn("record.airdate!==show.previous?.date",H)
        self.assertIn("televisionBroadcastFinished(past,key)",H)
    def test_original_geometry_and_all_five_show_recaps(self):
        self.assertIn('DISPLAY BUILD 4.20',H)
        self.assertIn('#board{width:min(100vw,56.25dvh)',H)
        self.assertIn('aspect-ratio:9/16',H)
        self.assertIn("renderEditorialRecap(show,key);",H)
        self.assertIn("renderEvolveRecap(show);",H)
        self.assertIn("showReportedCard(show,key,evolve);",H)
        self.assertIn("showReportedAppearances(show,key,evolve);",H)
if __name__=='__main__':unittest.main()
