import copy
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from proof.reviewed_recaps import MODE, ReviewError, validate_feed

NOW = datetime(2026, 10, 23, 12, tzinfo=ZoneInfo("America/New_York"))
SOURCE = "https://www.f4wonline.com/news/wwe/results/synthetic-test-episode/"
def fixture():
    return {"schema_version":1,"mode":MODE,"reviewed_at_et":"2026-10-23T05:00:00-04:00",
        "programs":[{"show_id":"nxt","airdate":"2026-10-20",
            "review_method":"MANUAL_SOURCE_REVIEW","reuse_basis":"FACT_ONLY_PARAPHRASE",
            "source_name":"Synthetic test source","source_url":SOURCE,
            "results":[{"text":"Fixture Wrestler A defeated Fixture Wrestler B",
                        "match_type":"Singles Match","status":"REPORTED_UNVERIFIED"}],
            "developments":[{"text":"Fixture Team A confronted Fixture Team B after the show",
                             "type":"Post-match storyline","status":"REPORTED_UNVERIFIED"}]}]}

class OptInReviewTests(unittest.TestCase):
    def test_empty_opt_in(self):
        self.assertEqual(validate_feed({"schema_version":1,"mode":MODE,
            "reviewed_at_et":None,"programs":[]},NOW)["programs"],[])
    def test_valid_fixture(self):
        self.assertEqual(len(validate_feed(fixture(),NOW)["programs"]),1)
    def test_no_source(self):
        d=fixture();d["programs"][0]["source_url"]=""
        with self.assertRaises(ReviewError):validate_feed(d,NOW)
    def test_unapproved_host(self):
        d=fixture();d["programs"][0]["source_url"]="https://example.com/anything"
        with self.assertRaises(ReviewError):validate_feed(d,NOW)
    def test_preview_not_result(self):
        d=fixture();d["programs"][0]["results"][0]["text"]="Fixture A vs. Fixture B"
        with self.assertRaises(ReviewError):validate_feed(d,NOW)
    def test_future_airdate(self):
        d=fixture();d["programs"][0]["airdate"]="2026-10-27"
        with self.assertRaises(ReviewError):validate_feed(d,NOW)
    def test_pre_broadcast_same_day(self):
        d=fixture();d["programs"][0]["show_id"]="smackdown";d["programs"][0]["airdate"]="2026-10-23"
        with self.assertRaises(ReviewError):validate_feed(d,NOW)
    def test_no_missing_confidence(self):
        d=fixture();d["programs"][0]["results"][0]["status"]="CONFIRMED"
        with self.assertRaises(ReviewError):validate_feed(d,NOW)
    def test_no_duplicate(self):
        d=fixture();d["programs"][0]["results"].append(copy.deepcopy(d["programs"][0]["results"][0]))
        with self.assertRaises(ReviewError):validate_feed(d,NOW)
    def test_storyline_only(self):
        d=fixture();d["programs"][0]["results"]=[]
        self.assertEqual(validate_feed(d,NOW)["programs"][0]["results"],[])
    def test_evolve_recap(self):
        d=fixture();d["programs"][0]["show_id"]="evolve"
        self.assertEqual(len(validate_feed(d,NOW)["programs"]),1)
    def test_no_empty_recap(self):
        d=fixture();d["programs"][0]["results"]=[];d["programs"][0]["developments"]=[]
        with self.assertRaises(ReviewError):validate_feed(d,NOW)

if __name__=="__main__":unittest.main()
