"""Offline safety, historical date, and ordering tests for source-only staging."""
import importlib.util
from datetime import date
import pathlib
import sys
import unittest

FILE = pathlib.Path(__file__).resolve().parents[1] / "diagnostics/storylines/wwe_historical_source_compat.py"
spec = importlib.util.spec_from_file_location("wwe_historical_source_compat", FILE)
source = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = source
spec.loader.exec_module(source)


def page(body, title_date="Oct. 23, 2026", stamped=True):
    title = f"SmackDown results: {title_date} | WWE"
    h3 = "<h3>Published on October 23, 2026</h3>" if stamped else ""
    return (f"<html><head><title>{title}</title></head><body>{h3}"
            "<div class='field field--name-body field__item'>"
            f"{body}</div></body></html>" + " " * 400)


BODY = """
<p><strong>Sami Zayn and Trick Williams confronted each other.</strong></p>
<div class="embedded-entity"><p>Ghost def. Image Caption</p></div>
<p><strong>Chelsea Green def. Roxanne Perez in a WWE Women's Championship Match</strong></p>
<p>After IYO SKY stopped Raquel Rodriguez, Chelsea Green retained.</p>
<p>Seconds after the bell, Tiffany Stratton saved Green and nearly cashed in on Liv Morgan.</p>
<p><strong>Blake Monroe def. Giulia in a Street Fight</strong></p>
<p>The referee counted three.</p>
<p>There were chairs.<br><strong>Cody Rhodes confronted Randy Orton at Crown Jewel.</strong></p>
<p><strong>Michin &amp; B-Fab def. Alexa Bliss &amp; Tatum Paxley to capture the title</strong></p>
<p>Jade Cargill interfered.</p>
<p><strong>CM Punk and Kevin Owens traded words.</strong></p>
<p><strong>Trick Williams &amp; Rey Fenix def. Sami Zayn &amp; Johnny Gargano by disqualification</strong></p>
<p>Ricky Saints interfered and Penta demanded a six-man tag.</p>
<p><strong>Penta, Trick Williams &amp; Rey Fenix def. Sami Zayn, Johnny Gargano &amp; Ricky Saints</strong></p>
<p>Trick pinned Saints just one week before his WWE Title Match against Sami Zayn next week.</p>
"""


class SourceCompatibilityTests(unittest.TestCase):
    def test_current_article(self):
        doc = source.extract(page(BODY), "2026-10-23",
                             "https://www.wwe.com/shows/smackdown/2026-10-23/results")
        self.assertEqual(doc["match_count"], 5)
        self.assertEqual(len(doc["events"]), 11)
        self.assertEqual(doc["events"][-1]["follows"], doc["events"][-2]["order"])
        self.assertTrue(doc["events"][-2]["causes_next"])
        self.assertFalse(doc["safe_for_live_board"])
        self.assertEqual(doc["review_status"], "draft")
        self.assertEqual(doc["date_evidence"], "publication_and_title")
        self.assertIn("Tiffany", doc["events"][2]["details"][0])
        self.assertEqual(doc["events"][2]["kind"], "storyline")
        self.assertIn("Cody Rhodes", doc["events"][4]["source_headline"])

    def test_old_results_title_without_publication_heading(self):
        doc = source.extract(page(BODY, title_date="Oct. 16, 2026", stamped=False),
                             "2026-10-16",
                             "https://www.wwe.com/shows/smackdown/2026-10-16/results")
        self.assertEqual(doc["date_evidence"], "title_only")
        self.assertEqual(doc["match_count"], 5)

    def test_date_mismatch_or_preview_fails_closed(self):
        with self.assertRaises(source.SourceIntegrityError):
            source.extract(page(BODY), "2026-10-16",
                           "https://www.wwe.com/shows/smackdown/2026-10-16/results")
        with self.assertRaises(source.SourceIntegrityError):
            source.extract(page(BODY, stamped=False).replace("SmackDown results:", "SmackDown Preview:"),
                           "2026-10-23",
                           "https://www.wwe.com/shows/smackdown/2026-10-23/results")
        with self.assertRaises(source.SourceIntegrityError):
            source.extract(page(BODY), "2026-10-23", "https://example.com/results")

    def test_match_winners_headshots_only(self):
        doc = source.extract(page(BODY), "2026-10-23",
                             "https://www.wwe.com/shows/smackdown/2026-10-23/results")
        dq = next(e for e in doc["events"] if e["finish"] == "disqualification")
        self.assertEqual(dq["winners"], ["Trick Williams", "Rey Fenix"])
        self.assertEqual(dq["losers"], ["Sami Zayn", "Johnny Gargano"])
        self.assertEqual(dq["portrait_rule"], "winners_only")
        self.assertTrue(any(e["title_change"] for e in doc["events"]))
        self.assertFalse(any("Ghost" in e["source_headline"] for e in doc["events"]))

    def test_old_source_article_content_not_republished(self):
        doc = source.extract(page(BODY), "2026-10-23",
                             "https://www.wwe.com/shows/smackdown/2026-10-23/results")
        self.assertTrue(doc["events"])
        self.assertTrue(all(e["requires_editorial_review"] for e in doc["events"]))
        self.assertEqual(len(doc["digest_sha256"]), 64)

    def test_archive_previews_cannot_become_results(self):
        archive = ("<html><head><title>Archive | WWE</title></head><body>"
                   "<a href='/shows/smackdown/2026-10-30'>future</a>"
                   "<a href='/shows/smackdown/2026-10-23'>past</a>"
                   "<a href='/shows/smackdown/2026-10-16'>older</a>"
                   "<a href='/shows/raw/2026-10-28'>other brand</a>"
                   "</body></html>")
        found = source.discover(archive, date(2026, 10, 29))
        self.assertEqual(found["latest_eligible"], "2026-10-23")
        self.assertEqual(found["future_previews"], ["2026-10-30"])
        self.assertEqual(found["eligible"], ["2026-10-23", "2026-10-16"])


if __name__ == "__main__":
    unittest.main()
