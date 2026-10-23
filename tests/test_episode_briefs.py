import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from proof.episode_briefs import build_briefs,most_recent_completed
NOW=datetime(2026,10,23,8,0,tzinfo=ZoneInfo("America/New_York"))
ET=ZoneInfo("America/New_York")
def snap(prev="2026-10-22",nxt="2026-10-29"):
 return {"shows":[{"id":"tna","schedule_status":"fresh",
                   "previous":{"date":prev},"next":{"date":nxt}}]}
EP={"id":7380001,"airdate":"2026-10-22",
    "summary":"<p>Daria Rae opens iMPACT! to discuss the future of the Knockouts division.</p>"}
class LicensedEpisodeGuideTest(unittest.TestCase):
    def test_exact_date_and_provider_attribution_not_result(self):
        d=build_briefs(snap(),lambda sid,day:[EP],NOW)
        x=d["programs"][0]
        self.assertEqual(d["synopses_available"],1)
        self.assertEqual(x["airdate"],"2026-10-22")
        self.assertEqual(x["license"],"CC BY-SA")
        self.assertNotIn("results",x)
        self.assertEqual(x["evidence_url"],"https://api.tvmaze.com/episodes/7380001")
    def test_future_broadcast_excluded(self):
        before=datetime(2026,10,22,22,50,tzinfo=ET)
        self.assertNotEqual(most_recent_completed(snap()["shows"][0],before),"2026-10-22")
        d=build_briefs(snap(),lambda sid,day:[EP],before)
        self.assertIsNone(d["programs"][0]["synopsis"])
    def test_wrong_episode_and_stale_schedule(self):
        d=build_briefs(snap(),lambda sid,day:[dict(EP,airdate="2026-10-29")],NOW)
        self.assertEqual(d["synopses_available"],0)
        st=snap();st["shows"][0]["schedule_status"]="stale"
        self.assertEqual(build_briefs(st,lambda sid,day:[EP],NOW)["synopses_available"],0)
    def test_last_good_exact_date_only(self):
        old=build_briefs(snap(),lambda sid,day:[EP],NOW)
        def fail(sid,day):raise ConnectionError()
        new=build_briefs(snap(),fail,NOW,old)
        self.assertEqual(new["programs"][0]["status"],"retained_same_episode")
        nextshow=snap("2026-10-29","2026-11-05")
        nexttime=datetime(2026,10,30,8,tzinfo=ET)
        self.assertEqual(build_briefs(nextshow,fail,nexttime,old)["synopses_available"],0)
if __name__=="__main__":unittest.main()
