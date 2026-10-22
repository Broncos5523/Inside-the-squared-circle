import unittest
from datetime import date
from proof.known_events import build_known

class IdentifierCacheTests(unittest.TestCase):
    def test_merges_without_storing_old_match_text(self):
        old={"entries":[{"show_id":"smackdown","airdate":"2026-10-23","event_ids":["2599790"]},
                        {"show_id":"tna","airdate":"2026-10-15","event_ids":["123"]}]}
        feed={"mode":"REPORTED_MATCHES_UNVERIFIED","programs":[
            {"show_id":"smackdown","airdate":"2026-10-23","matches":[],"appearances":[]},
            {"show_id":"raw","airdate":"2026-10-26","matches":[{"provider_event_id":"3414141","text":"Fake text not cached"}],"appearances":[]},
            {"show_id":"aaa","airdate":"2026-10-24","matches":[{"provider_event_id":"999"}],"appearances":[]},
            {"show_id":"tna","airdate":"2026-10-15","matches":[],"appearances":[]}]}
        result=build_known(old,feed,date(2026,10,22))
        by={x["show_id"]:x for x in result["entries"]}
        self.assertEqual(by["smackdown"]["event_ids"],["2599790"])
        self.assertEqual(by["raw"]["event_ids"],["3414141"])
        self.assertNotIn("aaa",by)
        self.assertNotIn("tna",by)
        self.assertNotIn("Fake text",str(result))
    def test_rejects_bad_ids(self):
        d=build_known({},{"mode":"REPORTED_MATCHES_UNVERIFIED","programs":[
            {"show_id":"raw","airdate":"2026-10-26","matches":[{"provider_event_id":"javascript:void(0)"},
                {"provider_event_id":"1"},{"provider_event_id":None}],"appearances":[]}]},date(2026,10,22))
        self.assertEqual(d["entries"][0]["event_ids"],["1"])
if __name__=="__main__": unittest.main()
