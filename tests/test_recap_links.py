import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from proof.recap_links import parse_feed, filter_title, clean_link, eligible_dates, build_links

TZ=ZoneInfo("America/New_York")
NOW=datetime(2026,10,22,18,20,tzinfo=TZ)
SNAP={"shows":[
    {"id":"raw","previous":{"date":"2026-10-19"},"next":{"date":"2026-10-26"}},
    {"id":"smackdown","previous":{"date":"2026-10-16"},"next":{"date":"2026-10-23"}},
    {"id":"nxt","previous":{"date":"2026-10-20"},"next":{"date":"2026-10-27"}},
    {"id":"aaa","previous":{"date":"2026-10-17"},"next":{"date":"2026-10-24"}},
    {"id":"tna","previous":{"date":"2026-10-15"},"next":{"date":"2026-10-22"}},
    {"id":"evolve","previous":{"date":"2026-10-21"},"next":{"date":"2026-10-28"}},
]}
XML=b"""<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>WWE Evolve results: October 21 episode recap</title><link>https://www.f4wonline.com/news/wwe/evolve-results-10-21/?utm=tracking</link><pubDate>Wed, 21 Oct 2026 23:00:00 GMT</pubDate></item>
<item><title>WWE NXT results: October 20 highlights</title><link>https://www.f4wonline.com/news/nxt/results-10-20/</link><pubDate>Wed, 21 Oct 2026 02:00:00 GMT</pubDate></item>
<item><title>SmackDown preview and spoilers</title><link>https://www.f4wonline.com/news/wwe/smackdown-preview/</link><pubDate>Thu, 22 Oct 2026 20:00:00 GMT</pubDate></item>
<item><title>WWE RAW results October 12</title><link>https://www.f4wonline.com/news/wwe/raw-results-old/</link><pubDate>Tue, 20 Oct 2026 02:00:00 GMT</pubDate></item>
<item><title>TNA Impact results October 22</title><link>https://www.f4wonline.com/news/tna/impact-results-10-22/</link><pubDate>Thu, 22 Oct 2026 22:00:00 GMT</pubDate></item>
</channel></rss>"""

class RecapLinksTests(unittest.TestCase):
    def test_rss_title_and_link_only(self):
        parsed=parse_feed(XML)
        self.assertEqual(len(parsed),5)
        self.assertNotIn("utm",parsed[0]["url"])
        self.assertNotIn("body",parsed[0])
    def test_no_cross_show_or_future_or_spoiler_links(self):
        self.assertIsNone(filter_title("WWE SmackDown and NXT results","nxt","2026-10-20"))
        self.assertIsNone(filter_title("WWE Raw predictions and spoilers","raw","2026-10-19"))
        self.assertIsNone(filter_title("WWE RAW results October 12","raw","2026-10-19"))
        self.assertIsNone(clean_link("https://fake-f4wonline.com/news/evil"))
    def test_pre_air_tna_stays_hidden(self):
        data=build_links(SNAP,parse_feed(XML),NOW)
        by={x["show_id"]:x for x in data["programs"]}
        self.assertEqual(by["tna"]["links"],[])
        self.assertEqual(by["aaa"]["links"],[])
    def test_evolve_and_nxt_source_links_without_winners(self):
        data=build_links(SNAP,parse_feed(XML),NOW)
        by={x["show_id"]:x for x in data["programs"]}
        self.assertEqual(by["evolve"]["airdate"],"2026-10-21")
        self.assertEqual(len(by["evolve"]["links"]),1)
        self.assertEqual(by["nxt"]["airdate"],"2026-10-20")
        self.assertEqual(data["total_links"],2)
        self.assertEqual(by["evolve"]["links"][0]["status"],"PUBLISHER_HEADLINE_LINK_ONLY")
        self.assertNotIn("results",str(by["evolve"]["links"][0]).lower().replace("evolve results","x"))
    def test_after_broadcast_tna_can_show_article_link(self):
        after=datetime(2026,10,22,23,40,tzinfo=TZ)
        data=build_links(SNAP,parse_feed(XML),after)
        row=next(x for x in data["programs"] if x["show_id"]=="tna")
        self.assertEqual(len(row["links"]),1)
        self.assertEqual(row["airdate"],"2026-10-22")
    def test_empty_is_honest_and_no_result_inference(self):
        output=build_links(SNAP,[],NOW)
        self.assertEqual(output["total_links"],0)
        self.assertEqual(len(output["programs"]),6)

if __name__=="__main__":unittest.main()
