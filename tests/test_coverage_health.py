import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from proof.coverage_health import build,SOURCES
NOW=datetime(2026,10,23,0,10,tzinfo=ZoneInfo("America/New_York"))
SNAP={"schema_version":1,"shows":[
 {"id":s,"schedule_status":"fresh",
  "previous":{"date":"2026-10-22"},"next":{"date":"2026-10-29"}}
 for s in ("raw","smackdown","nxt","aaa","tna","evolve")]}
def feed(which,air="2026-10-22",**data):
 return {"mode":SOURCES[which][0],"generated_at":NOW.isoformat(),
         "programs":[{"show_id":"tna","airdate":air,**data}]}
class SourceCoverageTests(unittest.TestCase):
 def test_article_links_never_become_match_results(self):
  sources={"recap_links":feed("recap_links",links=[{"headline":"News"}]*4)}
  out=build(SNAP,sources,{},NOW)
  self.assertEqual(out["totals"]["automatic_match_outcomes"],0)
  self.assertEqual(out["totals"]["publisher_headline_links"],4)
 def test_broadcast_date_and_freshness_gates(self):
  sources={"results":feed("results",results=[{"text":"A defeats B"}]*2)}
  out=build(SNAP,sources,{},NOW)
  self.assertEqual(out["totals"]["automatic_match_outcomes"],2)
  old=feed("results",results=[{"text":"A defeats B"}]*2)
  old["generated_at"]="2026-10-22T10:00:00-04:00"
  self.assertEqual(build(SNAP,{"results":old},{},NOW)["totals"]["automatic_match_outcomes"],0)
  self.assertEqual(build(SNAP,{"results":feed("results",air="2026-10-15",results=[{}])},{},NOW)["totals"]["automatic_match_outcomes"],0)
 def test_manual_and_automated_separate(self):
  e={"mode":"DATED_MULTI_SOURCE_RECAP_REVIEW_UNVERIFIED","programs":[
      {"show_id":"tna","airdate":"2026-10-22","results":[{},{}],"developments":[{}]}]}
  out=build(SNAP,{"fallout":feed("fallout",developments=[{}])},e,NOW)
  self.assertEqual(out["totals"]["manually_reviewed_outcomes"],2)
  self.assertEqual(out["totals"]["automatic_storylines"],1)
  self.assertEqual(out["totals"]["automatic_match_outcomes"],0)
 def test_evolve_source_review_not_lost_from_coverage(self):
  e={"mode":"DATED_EDITORIAL_EVOLVE_RECAP_UNVERIFIED","show_id":"evolve",
     "airdate":"2026-10-21","results":[{},{},{}],"developments":[{},{}]}
  schedule={"schema_version":1,"shows":[
     dict(s,previous={"date":"2026-10-21"}) if s["id"]=="evolve" else s for s in SNAP["shows"]]}
  out=build(schedule,{}, {},NOW,evolve=e)
  row=next(x for x in out["programs"] if x["show_id"]=="evolve")
  self.assertEqual(row["manually_reviewed_outcomes"],3)
  self.assertEqual(row["manually_reviewed_storylines"],2)
  self.assertEqual(out["totals"]["automatic_match_outcomes"],0)
 def test_synopsis_and_diagnostics_stay_separate(self):
  descriptions={"mode":SOURCES["rss_excerpts"][0],"generated_at":NOW.isoformat(),
    "source_diagnostics":{"https://approved.example/feed":{"with_defeated_word":10,"with_explicit_outcome_sentence":0}},
    "programs":[]}
  out=build(SNAP,{"rss_excerpts":descriptions},{},NOW)
  self.assertEqual(out["totals"]["rss_descriptions_with_defeated_word"],10)
  self.assertEqual(out["totals"]["automatic_match_outcomes"],0)
 def test_diagnostics_explain_missing_automated_results(self):
  def diagnostic(items,headlines,winner_mentions,exact):
   return {"status":"ok","items":items,"dated_broadcast_headlines":headlines,
           "with_defeated_word":winner_mentions,
           "with_explicit_outcome_sentence":0,
           "dated_descriptions_with_outcome":exact}
  src={"mode":SOURCES["rss_excerpts"][0],"generated_at":NOW.isoformat(),
       "source_diagnostics":{"https://411mania.com/wrestling/category/tv-report/feed/":
                  diagnostic(10,7,0,0),
                  "https://gerweck.net/category/results/feed/":diagnostic(50,4,10,0)},
       "programs":[]}
  out=build(SNAP,{"rss_excerpts":src},{},NOW)
  self.assertEqual(out["totals"]["rss_items_examined"],60)
  self.assertEqual(out["totals"]["rss_feeds_checked"],2)
  self.assertEqual(out["totals"]["rss_feeds_responding"],2)
  self.assertEqual(out["totals"]["rss_dated_episode_headlines"],11)
  self.assertEqual(out["totals"]["rss_descriptions_with_defeated_word"],10)
  self.assertEqual(out["totals"]["rss_dated_headlines_with_explicit_winner"],0)
  self.assertEqual(out["totals"]["rss_dated_descriptions_with_victory_word"],0)
  self.assertEqual(out["rss_bottleneck"],"no_dated_victory_language")
  self.assertEqual(out["totals"]["automatic_match_outcomes"],0)
  stale=dict(src,generated_at="2026-10-22T10:00:00-04:00")
  blocked=build(SNAP,{"rss_excerpts":stale},{},NOW)
  self.assertEqual(blocked["totals"]["rss_items_examined"],0)
  self.assertEqual(blocked["rss_bottleneck"],"feed_unavailable")
 def test_wrong_source_mode_does_not_count(self):
  x=feed("results",results=[{}]);x["mode"]="OTHER"
  self.assertEqual(build(SNAP,{"results":x},{},NOW)["totals"]["automatic_match_outcomes"],0)
 def test_reviewed_episode_counts_are_distinct_and_not_duplicated(self):
  reviewed={"schema_version":1,"mode":"REVIEWED_WEEKLY_EPISODE_FACTS_V1",
   "reviewed_at_et":"2026-10-22T23:45:00-04:00","programs":[{
    "show_id":"tna","airdate":"2026-10-22","review_method":"MANUAL_SOURCE_REVIEW",
    "reuse_basis":"FACT_ONLY_PARAPHRASE","source_name":"TNA Wrestling",
    "source_url":"https://tnawrestling.com/news/tna-impact-reviewed-episode",
    "results":[{"text":"Fixture Alpha defeated Fixture Bravo",
                "match_type":"Singles Match","status":"REPORTED_UNVERIFIED"}],
    "developments":[{"text":"Fixture Alpha confronted Fixture Gamma after the match",
                     "type":"Post-match rivalry","status":"REPORTED_UNVERIFIED"}]}]}
  old={"mode":"DATED_MULTI_SOURCE_RECAP_REVIEW_UNVERIFIED","programs":[{
   "show_id":"tna","airdate":"2026-10-22","results":[{},{}],"developments":[{},{}]}]}
  out=build(SNAP,{},old,NOW,reviewed=reviewed)
  row=next(x for x in out["programs"] if x["show_id"]=="tna")
  self.assertEqual(row["manually_reviewed_outcomes"],1)
  self.assertEqual(row["manually_reviewed_storylines"],1)
  self.assertEqual(out["totals"]["automatic_match_outcomes"],0)
  self.assertEqual(out["totals"]["automatic_storylines"],0)
 def test_invalid_reviewed_future_or_preview_cannot_count(self):
  reviewed={"schema_version":1,"mode":"REVIEWED_WEEKLY_EPISODE_FACTS_V1",
   "reviewed_at_et":"2026-10-23T12:00:00-04:00","programs":[{
    "show_id":"tna","airdate":"2026-10-29","review_method":"MANUAL_SOURCE_REVIEW",
    "reuse_basis":"FACT_ONLY_PARAPHRASE","source_name":"TNA Wrestling",
    "source_url":"https://tnawrestling.com/news/tna-impact-reviewed-episode",
    "results":[{"text":"Fixture A vs. Fixture B","match_type":"Singles Match",
                "status":"REPORTED_UNVERIFIED"}],"developments":[]}]}
  out=build(SNAP,{}, {},NOW,reviewed=reviewed)
  self.assertEqual(out["totals"]["manually_reviewed_outcomes"],0)
 def test_reviewed_advance_cards_count_without_claiming_automation(self):
  schedule={"schema_version":1,"shows":[
   dict(s,next={"date":"2026-10-26" if s["id"]=="raw" else "2026-10-24" if s["id"]=="aaa" else "2026-10-29"})
   for s in SNAP["shows"]]}
  research={"mode":"DATED_RESEARCH_SUPPLEMENT_UNVERIFIED","reviewed_at_et":"2026-10-22",
   "programs":[{"show_id":"raw","airdate":"2026-10-26",
     "matches":[{"text":"Bayley vs. Lyra Valkyria","status":"REPORTED_UNVERIFIED",
         "evidence_url":"https://www.f4wonline.com/news/wwe/bayley-no-dq/"}],
     "appearances":[]}]}
  aaa={"mode":"DATED_AAA_TV_WEEK_CARD_REVIEW_UNVERIFIED","reviewed_at_et":"2026-10-23",
    "programs":[{"show_id":"aaa","airdate":"2026-10-24",
       "matches":[{"text":"AAA Alpha vs. AAA Beta","status":"REPORTED_UNVERIFIED",
         "evidence_url":"https://411mania.com/wrestling/test/"},
        {"text":"AAA Gamma vs. AAA Delta","status":"REPORTED_UNVERIFIED",
         "evidence_url":"https://www.tpww.net/2026/10/source/"}],
       "appearances":[{"text":"Marisela Pena Hall of Fame ceremony",
         "type":"Hall of Fame","status":"REPORTED_UNVERIFIED",
         "evidence_url":"https://411mania.com/wrestling/test/"}]}]}
  out=build(schedule,{}, {},NOW,research=research,aaa_cards=aaa)
  self.assertEqual(out["totals"]["upcoming_reviewed_matches"],3)
  self.assertEqual(out["totals"]["upcoming_reviewed_appearances"],1)
  self.assertEqual(out["totals"]["upcoming_reported_matches"],0)
  self.assertEqual(out["totals"]["automatic_match_outcomes"],0)
  self.assertEqual(out["totals"]["automatic_storylines"],0)
  row=next(p for p in out["programs"] if p["show_id"]=="aaa")
  self.assertEqual(row["upcoming_reviewed_matches"],2)
  self.assertEqual(row["upcoming_reviewed_appearances"],1)
 def test_reviewed_advance_rejects_wrong_date_host_future_and_unattributed(self):
  fake={"mode":"DATED_RESEARCH_SUPPLEMENT_UNVERIFIED","reviewed_at_et":"2026-10-23",
   "programs":[{"show_id":"tna","airdate":"2026-10-29",
     "matches":[{"text":"Alice vs. Betty","status":"REPORTED_UNVERIFIED",
         "evidence_url":"https://malicious.invalid/match"},
        {"text":"Carl vs. Dana","status":"REPORTED_UNVERIFIED",
         "evidence_url":"https://www.wwe.com/shows/tna/"},
        {"text":"Eli vs. Fred","status":"UNVERIFIED",
         "evidence_url":"https://www.wwe.com/shows/tna/"},
        {"text":"Carl vs. Dana","status":"REPORTED_UNVERIFIED",
         "evidence_url":"https://www.wwe.com/shows/tna/"}],
     "appearances":[]}]}
  out=build(SNAP,{}, {},NOW,research=fake)
  self.assertEqual(out["totals"]["upcoming_reviewed_matches"],1)
  self.assertEqual(build(SNAP,{}, {},NOW,
    research=dict(fake,reviewed_at_et="2026-10-24"))["totals"]["upcoming_reviewed_matches"],0)
  wrongdate={"mode":fake["mode"],"reviewed_at_et":"2026-10-23","programs":[
    dict(fake["programs"][0],airdate="2026-10-22")]}
  self.assertEqual(build(SNAP,{}, {},NOW,research=wrongdate)["totals"]["upcoming_reviewed_matches"],0)
if __name__=="__main__":unittest.main()
