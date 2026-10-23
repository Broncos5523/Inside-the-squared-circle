import unittest
from pathlib import Path
from proof.recap_links import FEED_URLS,PUBLISHERS,clean_link
from proof.rss_facts import APPROVED
PAGE=(Path(__file__).resolve().parents[1]/"web/preview-v4-28.html").read_text()
class FeedProvenance(unittest.TestCase):
    def test_source_identity_and_https(self):
        for source,host,feed in (
            ("Ringside News","www.ringsidenews.com","https://www.ringsidenews.com/feed/"),
            ("Wrestling Headlines","wrestlingheadlines.com","https://wrestlingheadlines.com/feed/"),
        ):
            self.assertIn(feed,FEED_URLS)
            self.assertEqual(PUBLISHERS[host],source)
            self.assertIn(host,APPROVED[source])
            self.assertIn(source,PAGE)
            self.assertEqual(clean_link("https://"+host+"/results/?tracking=x"),
                             "https://"+host+"/results/")
        self.assertIsNone(clean_link("https://ringsidenews.com.evil.test/results"))
    def test_display_only_date_matched_results(self):
        self.assertIn("excerptRecord?.airdate===latest",PAGE)
        self.assertIn("RSS_SYNDICATED_EXCERPT_FACT",PAGE)
        self.assertIn("record.airdate!==newestCompleted(show,key)",PAGE)
        self.assertNotIn("createElement('a')",PAGE)
        self.assertIn("justify-content:space-evenly;",PAGE)
if __name__=="__main__":unittest.main()
