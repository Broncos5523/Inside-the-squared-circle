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
        self.assertEqual(by["tna"]["event_ids"],["123"])
        self.assertNotIn("Fake text",str(result))
    def test_retains_crossed_broadcast_event_ids_for_result_refresh(self):
        previous={"entries":[
            {"show_id":"tna","airdate":"2026-10-22","event_ids":["2618956"]},
            {"show_id":"smackdown","airdate":"2026-10-23","event_ids":["2599790"]}]}
        no_card={"mode":"REPORTED_MATCHES_UNVERIFIED","programs":[]}
        after=build_known(previous,no_card,date(2026,10,23))
        self.assertEqual({(x["show_id"],x["airdate"]) for x in after["entries"]},
                         {("tna","2026-10-22"),("smackdown","2026-10-23")})
        self.assertEqual(after["entries"][1]["event_ids"],["2618956"])
        stale=build_known(previous,no_card,date(2026,11,7))
        self.assertFalse(any(x["show_id"]=="tna" for x in stale["entries"]))
        self.assertNotIn("2618956",str(stale))
    def test_does_not_reuse_old_ids_on_future_new_episode(self):
        prev={"entries":[{"show_id":"raw","airdate":"2026-10-19","event_ids":["1234567"]}]}
        report={"mode":"REPORTED_MATCHES_UNVERIFIED","programs":[
            {"show_id":"raw","airdate":"2026-10-26","matches":[],"appearances":[]}]}
        got=build_known(prev,report,date(2026,10,26))
        self.assertEqual(len(got["entries"]),1)
        self.assertEqual(got["entries"][0]["airdate"],"2026-10-19")
    def test_rejects_bad_ids(self):
        d=build_known({},{"mode":"REPORTED_MATCHES_UNVERIFIED","programs":[
            {"show_id":"raw","airdate":"2026-10-26","matches":[{"provider_event_id":"javascript:void(0)"},
                {"provider_event_id":"1"},{"provider_event_id":None}],"appearances":[]}]},date(2026,10,22))
        self.assertEqual(d["entries"][0]["event_ids"],["1"])
if __name__=="__main__": unittest.main()
