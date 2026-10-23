import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from proof.rss_excerpt_results import build_results,parse_syndicated_feed,parse_excerpt_sentences,diagnose_syndicated_feed,diagnose_syndicated_feed
ET=ZoneInfo("America/New_York")
NOW=datetime(2026,10,23,8,0,tzinfo=ET)
SNAP={"shows":[
{"id":"raw","previous":{"date":"2026-10-19"},"next":{"date":"2026-10-26"}},
{"id":"smackdown","previous":{"date":"2026-10-16"},"next":{"date":"2026-10-23"}},
{"id":"nxt","previous":{"date":"2026-10-20"},"next":{"date":"2026-10-27"}},
{"id":"aaa","previous":{"date":"2026-10-17"},"next":{"date":"2026-10-24"}},
{"id":"tna","previous":{"date":"2026-10-15"},"next":{"date":"2026-10-22"}},
{"id":"evolve","previous":{"date":"2026-10-21"},"next":{"date":"2026-10-28"}}]}
def entry(title,excerpt,stamp="2026-10-23T00:10:00-04:00"):
 return {"title":title,"excerpt":excerpt,"published_at":datetime.fromisoformat(stamp),
         "url":"https://411mania.com/wrestling/episode-review/",
         "source_name":"411Mania"}
class SyndicatedFacts(unittest.TestCase):
    def test_extracts_only_direct_publisher_syndicated_results(self):
        e=entry("TNA iMPACT! Results 10/22/2026",
                "<p>Avery Styles defeated Joe Alonzo.</p><p>Rich Swann defeated KC Navarro by pinfall.</p>")
        d=build_results(SNAP,[e],NOW)
        t=next(x for x in d["programs"] if x["show_id"]=="tna")
        self.assertEqual(len(t["results"]),2)
        self.assertEqual(t["results"][0]["text"],"Avery Styles defeated Joe Alonzo")
        self.assertEqual(t["results"][1]["evidence_type"],"RSS_SYNDICATED_EXCERPT_FACT")
        self.assertNotIn("excerpt",str(d))
        self.assertEqual(d["total_reported_results"],2)
    def test_recaps_with_narrow_explicit_context_phrases(self):
        rss=entry("10/21/26 WWE Evolve Recap",
                  "<p>In the opening contest, Chazz Starboy Hall and Cappuccino Jones "
                  "defeated Jacari Ball and Santi Rivera in a great match.</p>",
                  "2026-10-22T10:10:00-04:00")
        rss["url"]="https://gerweck.net/2026/10/22/10-21-26-wwe-evolve-recap/"
        rss["source_name"]="Gerweck.net"
        data=build_results(SNAP,[rss],NOW)
        row=next(x for x in data["programs"] if x["show_id"]=="evolve")
        self.assertEqual(len(row["results"]),1)
        self.assertEqual(row["results"][0]["text"],
                         "Chazz Starboy Hall and Cappuccino Jones defeated Jacari Ball and Santi Rivera")
        self.assertEqual(row["results"][0]["source_name"],"Gerweck.net")
        self.assertEqual(build_results(SNAP,[dict(rss,title="10/14/26 WWE Evolve Recap")],NOW)["total_reported_results"],0)
        self.assertEqual(parse_excerpt_sentences("<p>Last week Chazz Starboy Hall defeated Santi Rivera.</p>"),[])
    def test_rejects_prebroadcast_and_wrong_date_claims(self):
        good="TNA iMPACT! Results 10/22/2026"
        a=entry(good,"<p>Avery Styles defeated Joe Alonzo.</p>","2026-10-22T20:15:00-04:00")
        b=entry("TNA iMPACT! Results 10/15/2026","<p>Avery Styles defeated Joe Alonzo.</p>")
        c=entry(good,"<p>Avery Styles might defeat Joe Alonzo.</p>")
        self.assertEqual(build_results(SNAP,[a,b,c],NOW)["total_reported_results"],0)
    def test_no_previews_or_cross_show_or_methods_guessed(self):
        d=build_results(SNAP,[entry("WWE NXT and TNA iMPACT! Results 10/22/2026",
            "<p>Avery Styles defeated Joe Alonzo.</p>")],NOW)
        self.assertEqual(d["total_reported_results"],0)
        self.assertEqual(parse_excerpt_sentences("<p>Joe Alonzo vs. Avery Styles</p>"),[])
        self.assertEqual(parse_excerpt_sentences("<p>Joe Alonzo may defeat Avery Styles</p>"),[])
        self.assertEqual(parse_excerpt_sentences("<p>Joe Alonzo defeated Avery Styles last week</p>"),[])
    def test_diagnostic_identifies_winner_language_in_same_show_same_date(self):
        articles=[entry("TNA iMPACT! Results 10/22/2026",
                         "<p>Avery Styles defeated Joe Alonzo.</p>"),
                  entry("WWE RAW Results 10/19/2026",
                         "<p>Chelsea Green defeated Roxanne Perez.</p>"),
                  entry("TNA iMPACT! Results 10/15/2026",
                         "<p>Avery Styles defeated Joe Alonzo.</p>")]
        counts=diagnose_syndicated_feed(articles,SNAP,NOW)
        self.assertEqual(counts["dated_broadcast_headlines"],1)
        self.assertEqual(counts["dated_descriptions_with_victory_word"],1)
        self.assertEqual(counts["dated_descriptions_with_outcome"],1)
    def test_approved_syndicated_description_not_full_content(self):
        rss=(b"<rss><channel><item><title>TNA iMPACT! Results 10/22/2026</title>"
          b"<link>https://411mania.com/wrestling/episode-review/</link>"
          b"<pubDate>Fri, 23 Oct 2026 04:10:00 +0000</pubDate>"
          b"<description>&lt;p&gt;Avery Styles defeated Joe Alonzo.&lt;/p&gt;</description>"
          b"<content:encoded xmlns:content='http://purl.org/rss/1.0/modules/content/'>"
          b"Unwanted full article goes here</content:encoded></item></channel></rss>")
        rows=parse_syndicated_feed(rss)
        self.assertEqual(len(rows),1)
        self.assertNotIn("Unwanted full article",str(rows))
        self.assertEqual(build_results(SNAP,rows,NOW)["total_reported_results"],1)
    def test_safe_diagnostics_report_counts_never_syndicated_excerpts(self):
        entries=[
            entry("TNA iMPACT! Results 10/22/2026",
                  "<p>Avery Styles defeated Joe Alonzo.</p>"),
            entry("RAW results 10/19/2026",
                  "<p>See complete results on publisher website.</p>"),
        ]
        result=diagnose_syndicated_feed(entries,SNAP,NOW)
        self.assertEqual(result["items"],2)
        self.assertEqual(result["with_description"],2)
        self.assertEqual(result["with_defeated_word"],1)
        self.assertEqual(result["with_explicit_outcome_sentence"],1)
        self.assertEqual(result["dated_descriptions_with_outcome"],1)
        self.assertNotIn("Avery Styles",str(result))
        self.assertNotIn("excerpt",result)
    def test_future_show_and_aaa_never_fabricated(self):
        d=build_results(SNAP,[entry("AAA Results 10/24/2026","<p>Avery Styles defeated Joe Alonzo.</p>")],NOW)
        self.assertEqual(d["total_reported_results"],0)
if __name__=='__main__':unittest.main()
