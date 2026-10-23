import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from proof.rss_facts import build_facts,explicit_outcome_from_headline,current_completed_airdate

TZ=ZoneInfo("America/New_York")
NOW=datetime(2026,10,23,7,30,tzinfo=TZ)
SHOWS={"shows":[
 {"id":"raw","previous":{"date":"2026-10-19"},"next":{"date":"2026-10-26"}},
 {"id":"smackdown","previous":{"date":"2026-10-16"},"next":{"date":"2026-10-23"}},
 {"id":"nxt","previous":{"date":"2026-10-20"},"next":{"date":"2026-10-27"}},
 {"id":"aaa","previous":{"date":"2026-10-17"},"next":{"date":"2026-10-24"}},
 {"id":"tna","previous":{"date":"2026-10-15"},"next":{"date":"2026-10-22"}},
 {"id":"evolve","previous":{"date":"2026-10-21"},"next":{"date":"2026-10-28"}},
]}
def link(title, published="2026-10-23T05:30:00-04:00", name="411Mania"):
  return {"headline":title,"url":"https://411mania.com/wrestling/wwe-results-post-show/",
          "source_name":name,"published_at":published,
          "status":"PUBLISHER_HEADLINE_LINK_ONLY"}
def feed(items,air="2026-10-22"):
  return {"mode":"PUBLISHER_RSS_POST_SHOW_LINKS_ONLY",
          "programs":[{"show_id":"tna","airdate":air,"links":items}]}

class StrictRssOutcomeTests(unittest.TestCase):
    def test_exact_episode_and_explicit_winner(self):
        r=build_facts(SHOWS,feed([link("TNA Impact Results 10/22/2026: Avery Styles defeated Joe Alonzo")]),NOW)
        t=next(s for s in r["programs"] if s["show_id"]=="tna")
        self.assertEqual(len(t["results"]),1)
        self.assertEqual(t["results"][0]["text"],"Avery Styles defeated Joe Alonzo")
        self.assertEqual(t["results"][0]["source_name"],"411Mania")
        self.assertEqual(t["results"][0]["status"],"REPORTED_UNVERIFIED")
        self.assertEqual(r["total_reported_results"],1)
    def test_live_results_advance_title_not_an_outcome(self):
        for h in [
            "TNA Impact Live Results 10/22/2026: Joe Alonzo vs Avery Styles",
            "TNA Impact Results 10/22/2026: Joe Alonzo vs. Avery Styles",
            "TNA Impact Results 10/22/2026: Joe Alonzo may defeat Avery Styles",
            "TNA Impact Results 10/22/2026: Joe Alonzo defeated Avery Styles next week",
            "NXT & TNA Impact Results 10/22/2026: Avery Styles defeated Joe Alonzo",
            "TNA Impact Review: Avery Styles defeated Joe Alonzo", # no date
            "TNA Impact Results 10/15/2026: Avery Styles defeated Joe Alonzo",
            "TNA Impact Results 10/22/2026: Joe Alonzo expected to defeat Avery Styles",
        ]:
            self.assertIsNone(explicit_outcome_from_headline(h,"tna","2026-10-22"),h)
    def test_pre_air_time_never_qualifies_even_if_suggestive(self):
        claims=feed([link("TNA Impact Results 10/22/2026: Avery Styles defeated Joe Alonzo",
                          published="2026-10-22T20:50:00-04:00")])
        self.assertEqual(build_facts(SHOWS,claims,NOW)["total_reported_results"],0)
    def test_after_air_window_and_wrong_source_rejected(self):
        valid="TNA Impact Results 10/22/2026: Avery Styles defeated Joe Alonzo"
        wrong=link(valid,name="Fightful")
        invalid=link(valid,published="2026-10-28T22:00:00-04:00")
        result=build_facts(SHOWS,feed([wrong,invalid]),NOW)
        self.assertEqual(result["total_reported_results"],0)
    def test_only_current_completed_episode_not_last_week(self):
        snap={"shows":[dict(s,previous={"date":"2026-10-22"},next={"date":"2026-10-29"})
                       if s["id"]=="tna" else s for s in SHOWS["shows"]]}
        old=feed([link("TNA Impact Results 10/15/2026: Avery Styles defeated Joe Alonzo")],
                 air="2026-10-15")
        self.assertEqual(build_facts(snap,old,NOW)["total_reported_results"],0)
    def test_aaa_not_auto_matched_to_taping(self):
        result=build_facts(SHOWS,feed([link("AAA Impact Results 10/22/2026: A defeated B")]),NOW)
        self.assertEqual(next(s for s in result["programs"] if s["show_id"]=="aaa")["results"],[])
    def test_broadcast_date_gate_before_air(self):
        before=datetime(2026,10,22,22,15,tzinfo=TZ)
        self.assertEqual(current_completed_airdate(SHOWS["shows"][4],"tna",before),"2026-10-15")
        self.assertEqual(current_completed_airdate(SHOWS["shows"][4],"tna",NOW),"2026-10-22")
if __name__=="__main__":unittest.main()
