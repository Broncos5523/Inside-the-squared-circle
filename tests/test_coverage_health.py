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
 def test_wrong_source_mode_does_not_count(self):
  x=feed("results",results=[{}]);x["mode"]="OTHER"
  self.assertEqual(build(SNAP,{"results":x},{},NOW)["totals"]["automatic_match_outcomes"],0)
if __name__=="__main__":unittest.main()
