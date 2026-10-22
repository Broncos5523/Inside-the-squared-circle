"""V4.8 static QA assertions; content comes from existing runtime feeds."""
from pathlib import Path
import unittest

PAGE=Path(__file__).resolve().parents[1]/'web/preview-v4-8.html'

class PortraitAppearanceReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=PAGE.read_text(encoding='utf-8')
    def test_separate_review_and_pristine_16_by_9_inverse(self):
        self.assertIn('DISPLAY BUILD 4.8',self.html)
        self.assertIn('#board{width:min(100vw,56.25dvh)',self.html)
        self.assertIn('aspect-ratio:9/16',self.html)
    def test_one_complete_appearance_per_frame(self):
        self.assertIn('const pages=rows.length;',self.html)
        self.assertIn('const x=rows[page];',self.html)
        self.assertNotIn("for(const x of rows.slice(0,2))",self.html)
        self.assertIn("put('segment-title','REPORTED APPEARANCE · '",self.html)
    def test_unverified_and_provenance_are_preserved(self):
        self.assertIn("REPORTED / UNVERIFIED",self.html)
        self.assertIn("x.evidence_url",self.html)
        self.assertIn('DATED_RESEARCH_SUPPLEMENT_UNVERIFIED',self.html)
    def test_single_match_does_not_promise_another_card(self):
        self.assertIn("CURRENT REPORTED CARD",self.html)
        self.assertIn("NEXT MATCH IN 14s",self.html)

if __name__=='__main__':
    unittest.main()
