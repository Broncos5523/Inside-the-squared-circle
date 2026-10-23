import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from proof.rss_fallout import parse_developments,build_fallout
ET=ZoneInfo("America/New_York")
NOW=datetime(2026,10,23,8,tzinfo=ET)
SNAP={"shows":[{"id":"raw","previous":{"date":"2026-10-19"},
    "next":{"date":"2026-10-26"}},
    {"id":"tna","previous":{"date":"2026-10-15"},"next":{"date":"2026-10-22"}},
    {"id":"aaa","previous":{"date":"2026-10-17"},"next":{"date":"2026-10-24"}}]}
def source(description,day="2026-10-19",pub="2026-10-20T08:00:00-04:00"):
    return {"title":"WWE RAW Results "+day[5:7]+"/"+day[8:10]+"/"+day[:4],
            "url":"https://411mania.com/wrestling/raw-results-2026/",
            "source_name":"411Mania","published_at":datetime.fromisoformat(pub),
            "excerpt":description}

class Fallout(unittest.TestCase):
    def test_structured_developments_without_article_or_original_excerpt(self):
        r=build_fallout(SNAP,[source("<p>Bron Breakker attacked Roman Reigns.</p><p>Bayley challenged Lyra Valkyria.</p>")],NOW)
        a=r["programs"][0]
        self.assertEqual(len(a["developments"]),2)
        self.assertEqual(a["developments"][0]["type"],"POST-MATCH FALLOUT")
        self.assertEqual(a["developments"][1]["text"],"Bayley challenged Lyra Valkyria")
        self.assertEqual(a["developments"][1]["evidence_type"],"RSS_SYNDICATED_FALLOUT_FACT")
        self.assertFalse(any("excerpt" in fact or "description" in fact
                             for row in r["programs"] for fact in row["developments"]))
        self.assertEqual(r["total_developments"],2)
    def test_return_and_speculation(self):
        self.assertEqual(parse_developments("<p>Roman Reigns returned to WWE Raw.</p>")[0]["type"],"RETURN")
        for text in ("Roman Reigns may return to Raw.","Bayley might challenge Lyra Valkyria.",
                     "Bayley challenged Lyra Valkyria next week.","Bron Breakker attacked Roman Reigns last week.",
                     "Roman Reigns vs. Bron Breakker","Roman Reigns defeated Bron Breakker."):
            self.assertEqual(parse_developments("<p>"+text+"</p>"),[],text)
    def test_wrong_episode_or_earlier_feed_never_promoted(self):
        self.assertEqual(build_fallout(SNAP,[source("<p>Bron Breakker attacked Roman Reigns.</p>",
            day="2026-10-12")],NOW)["total_developments"],0)
        self.assertEqual(build_fallout(SNAP,[source("<p>Bron Breakker attacked Roman Reigns.</p>",
            pub="2026-10-19T19:00:00-04:00")],NOW)["total_developments"],0)
    def test_cross_show_and_invalid_host(self):
        e=source("<p>Bron Breakker attacked Roman Reigns.</p>")
        self.assertEqual(build_fallout(SNAP,[dict(e,title="WWE Raw and NXT results 10/19/2026")],NOW)["total_developments"],0)
        self.assertEqual(build_fallout(SNAP,[dict(e,url="https://evil.invalid/result/")],NOW)["total_developments"],0)
    def test_aaa_not_fabricated_from_taping(self):
        d=build_fallout(SNAP,[source("<p>Bron Breakker attacked Roman Reigns.</p>")],NOW)
        self.assertFalse(next(x for x in d["programs"] if x["show_id"]=="aaa")["developments"])
if __name__=="__main__":unittest.main()
