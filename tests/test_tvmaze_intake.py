import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from proof.tvmaze_intake import candidates_from_summary, build_tvmaze

ET=ZoneInfo("America/New_York")
NOW=datetime(2026,10,22,16,0,tzinfo=ET)
SD={"id":993421,"airdate":"2026-10-23","summary":"<p>Street Fight: Giulia vs. Blake Monroe</p><p>WWE Women's Championship Match: Chelsea Green vs. Roxanne Perez</p>"}
UNSAFE={"id":993422,"airdate":"2026-10-23","summary":"<p>Dark Match: Fake Wrestler vs. Other Wrestler</p><p>Yesterday Giulia vs Blake Monroe ended with a pinfall.</p>"}
SNAP={"shows":[{"id":"raw","next":{"date":"2026-10-26"},"schedule_status":"fresh"},
               {"id":"smackdown","next":{"date":"2026-10-23"},"schedule_status":"fresh"},
               {"id":"nxt","next":{"date":"2026-10-27"},"schedule_status":"fresh"},
               {"id":"aaa","next":{"date":"2026-10-24"},"schedule_status":"fresh"},
               {"id":"tna","next":{"date":"2026-10-22"},"schedule_status":"fresh"},
               {"id":"evolve","next":{"date":"2026-10-28"},"schedule_status":"fresh"}]}
def get_episodes(show,day):
    return [SD] if show==803 else []

class TVmazeTests(unittest.TestCase):
    def test_parse_two_explicit_bouts(self):
        matches=candidates_from_summary(SD["summary"])
        self.assertEqual(len(matches),2)
        self.assertEqual(matches[1]["text"],"Chelsea Green vs Roxanne Perez")
        self.assertEqual(matches[1]["stipulation"],"WWE Women's Championship Match")
    def test_narrative_future_title_defense_extracts_only_explicit_pair(self):
        summary=("<p>Chelsea Green is set to put her WWE Women's Championship on "
                 "the line against The Judgment Day's Roxanne Perez this Friday "
                 "on SmackDown, even as her potential Champion vs. Champion "
                 "Match looms.</p>")
        self.assertEqual(candidates_from_summary(summary), [
            {"text":"Chelsea Green vs. Roxanne Perez",
             "stipulation":"WWE Women's Championship Match"}
        ])
    def test_long_tvm_synopsis_first_clause_match(self):
        live=("<p>Chelsea Green is set to put her WWE Women's Championship on the "
              "line against The Judgment Day's Roxanne Perez this Friday on SmackDown, "
              "even as her potential Champion vs. Champion Match against Women's World "
              "Champion Liv Morgan at WWE Crown Jewel looms on the horizon.</p>")
        self.assertEqual(len(candidates_from_summary(live)),1)
        self.assertEqual(candidates_from_summary(live)[0]["text"],"Chelsea Green vs. Roxanne Perez")
    def test_no_past_result_or_speculative_title_match(self):
        self.assertEqual(candidates_from_summary(
            "<p>Yesterday Chelsea Green put the WWE Women's Championship "
            "on the line against Roxanne Perez.</p>"), [])
        self.assertEqual(candidates_from_summary(
            "<p>Chelsea Green may put her WWE Women's Championship "
            "on the line against Roxanne Perez this Friday.</p>"), [])
    def test_not_match_unrelated_storylines_outcomes_or_dark_matches(self):
        self.assertEqual(candidates_from_summary(UNSAFE["summary"]),[])
        self.assertEqual(candidates_from_summary("<p>Cody Rhodes and Randy Orton will appear</p>"),[])
        self.assertEqual(candidates_from_summary("<p>Last week: A vs B</p>"),[])
        self.assertEqual(candidates_from_summary("<p>Prediction Match: A vs B</p>"),[])
        self.assertEqual(candidates_from_summary("<p>Giulia vs Blake Monroe is a rivalry from last week</p>"),[])
        self.assertEqual(candidates_from_summary("<script>XX</script>"),[])
    def test_show_and_date_and_source(self):
        d=build_tvmaze(SNAP,requester=get_episodes,now=NOW)
        self.assertEqual(len(d["programs"]),6)
        sm=next(x for x in d["programs"] if x["show_id"]=="smackdown")
        self.assertEqual(len(sm["matches"]),2)
        self.assertTrue(all(x["status"]=="REPORTED_UNVERIFIED" for x in sm["matches"]))
        self.assertTrue(all(x["evidence_url"]=="https://api.tvmaze.com/episodes/993421" for x in sm["matches"]))
        self.assertEqual(d["total_reported_matches"],2)
        self.assertEqual(next(x for x in d["programs"] if x["show_id"]=="aaa")["matches"],[])
        self.assertEqual(next(x for x in d["programs"] if x["show_id"]=="evolve")["matches"],[])
    def test_wrong_episode_date_rejected(self):
        def wrong(*args):return [dict(SD,airdate="2026-10-30")]
        d=build_tvmaze(SNAP,requester=wrong,now=NOW)
        self.assertEqual(d["total_reported_matches"],0)
    def test_stale_schedule_skipped(self):
        clone={"shows":[{**s, "schedule_status":"stale"} for s in SNAP["shows"]]}
        def fail(*args):raise AssertionError("stale schedule should not call TVmaze")
        self.assertEqual(build_tvmaze(clone,requester=fail,now=NOW)["total_reported_matches"],0)
    def test_ended_broadcast_rejected(self):
        future=datetime(2026,10,30,16,tzinfo=ET)
        self.assertEqual(build_tvmaze(SNAP,requester=get_episodes,now=future)["total_reported_matches"],0)
    def test_api_failure_never_fabricates(self):
        def fail(*_):raise ConnectionError("unavailable")
        d=build_tvmaze(SNAP,requester=fail,now=NOW)
        self.assertEqual(d["total_reported_matches"],0)
        self.assertEqual(next(x for x in d["programs"] if x["show_id"]=="smackdown")["collection_status"],"api_unavailable")

if __name__=="__main__":unittest.main()
