import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from proof.evolve_intake import build_evolve,summary_text

NOW=datetime(2026,10,22,18,0,tzinfo=ZoneInfo("America/New_York"))
SNAP={"shows":[{"id":"evolve","previous":{"date":"2026-10-21"},
                "next":{"date":"2026-10-28"},"schedule_status":"fresh"}]}
RECORD={"id":3456789,"airdate":"2026-10-21",
        "summary":"<p>Aaron Rourke gets a rematch against Kale Dixon and looks for payback after Dixon's recent attack.</p>"}

class EvolveSynopsisTests(unittest.TestCase):
    def test_only_the_finished_and_exact_date_episode(self):
        result=build_evolve(SNAP,requester=lambda d:[RECORD],now=NOW)
        self.assertEqual(result["airdate"],"2026-10-21")
        self.assertEqual(result["episode_id"],3456789)
        self.assertEqual(result["source_name"],"TVmaze")
        self.assertEqual(result["license"],"CC BY-SA")
        self.assertNotIn("defeats",result["synopsis"])
        self.assertEqual(result["status"],"episode_synopsis_available")
    def test_wrong_date_does_not_get_attached(self):
        result=build_evolve(SNAP,requester=lambda d:[dict(RECORD,airdate="2026-10-28")],now=NOW)
        self.assertIsNone(result["synopsis"])
    def test_stale_show_is_not_inferred(self):
        future=datetime(2026,11,12,18,tzinfo=ZoneInfo("America/New_York"))
        self.assertEqual(build_evolve(SNAP,requester=lambda d:[RECORD],now=future)["status"],"outside_recap_window")
    def test_no_synthetic_results_from_synopsis(self):
        s=summary_text("<p>Cody vs. Randy is the week's main event.</p><script>alert(1)</script>")
        self.assertNotIn("alert",s)
        self.assertIn("vs.",s)
        result=build_evolve(SNAP,requester=lambda d:[],now=NOW)
        self.assertEqual(result["status"],"no_episode_synopsis")
    def test_failure_is_safe(self):
        def fail(_):raise ConnectionError("offline")
        result=build_evolve(SNAP,requester=fail,now=NOW)
        self.assertEqual(result["status"],"api_unavailable")
        self.assertIsNone(result["synopsis"])
if __name__=="__main__":
    unittest.main()
