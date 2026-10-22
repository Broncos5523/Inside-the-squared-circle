"""V4.9 keeps the existing portrait presentation while adding fresh API card reports."""
import unittest
from pathlib import Path
HTML=(Path(__file__).resolve().parents[1]/'web/preview-v4-9.html').read_text()
class V49PageTests(unittest.TestCase):
    def test_new_source_fetched_and_dated(self):
        self.assertIn("tvmaze-reported.json",HTML)
        self.assertIn("TVMAZE_EPISODE_SUMMARY_REPORTED_UNVERIFIED",HTML)
        self.assertIn("entry.airdate!==show.next?.date",HTML)
        self.assertIn("entry.airdate<easternToday()",HTML)
        self.assertIn("age>480",HTML)
    def test_not_source_confirmed_and_prev_versions_untouched(self):
        self.assertIn("REPORTED / UNVERIFIED",HTML)
        self.assertIn("TVMAZE EPISODE SUMMARY · UNVERIFIED",HTML)
        self.assertIn("uniqueRows(uniqueRows(api,tvmazeRows(show,key,kind)),datedRows(show,key,kind))",HTML)
        self.assertIn("const perPage=1",HTML)
        self.assertIn("#board{width:min(100vw,56.25dvh)",HTML)
        self.assertIn("DISPLAY BUILD 4.9",HTML)
if __name__=='__main__':unittest.main()
