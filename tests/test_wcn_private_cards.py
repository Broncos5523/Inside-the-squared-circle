import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from proof.wcn_private_cards import BASE,FEED,MODE,approved,build,pairs,advertised,parse_page,feed_count

NOW=datetime(2026,10,23,0,30,tzinfo=ZoneInfo("America/New_York"))
SNAP={"schema_version":1,"shows":[
 {"id":s,"schedule_status":"fresh","next":{"date":day}} for s,day in [
 ("raw","2026-10-26"),("smackdown","2026-10-23"),("nxt","2026-10-27"),
 ("aaa","2026-10-24"),("tna","2026-10-29"),("evolve","2026-10-28")]]}
RSS=b'<rss><channel><item><title>SmackDown card update</title></item></channel></rss>'
PAGE=b'<h2>Card &amp; preview</h2><h3>Match card</h3><p>Giulia faces Blake Monroe in a street fight. Alexa Bliss and Tatum Paxley will make their first defense against Michin and B-Fab.</p><h2>Results</h2><p>Bob faces Ted. Dana defeated Zoe.</p><h2>More news from this show</h2><p>Joe faces Max.</p>'

class PrivateWcnTests(unittest.TestCase):
 def test_endpoint_allowlist(self):
  self.assertTrue(approved(FEED))
  self.assertTrue(approved(BASE+"/events/2026-10-23-wwe-smackdown/"))
  for url in [BASE+"/upcoming/",BASE+"/story/rumour.html",
              BASE+"/events/2026-10-24-aaa-heroes-inmortales/",
              "https://notwcn.example/events/2026-10-23-wwe-smackdown/",
              BASE+"/events/2026-10-23-wwe-smackdown/?edit=1"]:
   self.assertFalse(approved(url))
 def test_rss_is_not_outcome_feed(self):
  self.assertEqual(feed_count(RSS),1)
  self.assertEqual(feed_count(b"<rss><channel/></rss>"),0)
 def test_extract_two_clear_pairs_only(self):
  self.assertEqual(parse_page(PAGE)['matches'],[
    "Giulia vs. Blake Monroe",
    "Alexa Bliss & Tatum Paxley vs. Michin & B-Fab"])
 def test_ignore_results_sections_and_past_winners(self):
  self.assertEqual(parse_page(b"<h2>Results</h2><p>Alice faces Betty.</p>")['matches'],[])
  self.assertEqual(pairs("Cody Rhodes defeated Randy Orton on SmackDown."),[])
 def test_four_smackdown_bouts_and_explicit_appearances(self):
  para=("WWE has announced the card for SmackDown on October 23: "
        "Chelsea Green defends WWE Women's Title against Roxanne Perez; "
        "Giulia takes on Blake Monroe in a Street Fight; "
        "Michin & B-Fab challenge Alexa Bliss & Tatum Paxley for the title; "
        "and The MFTs once again collide with Bakusai. "
        "Also advertised: CM Punk, Cody Rhodes, Jade Cargill, Tiffany Stratton, "
        "Gunther, Trick Williams, Karl Anderson.")
  rows=parse_page(("<h2>Card &amp; preview</h2><p>"+para+"</p>").encode())
  self.assertEqual(rows["matches"],[
   "Chelsea Green vs. Roxanne Perez",
   "Giulia vs. Blake Monroe",
   "Michin & B-Fab vs. Alexa Bliss & Tatum Paxley",
   "The MFTs vs. Bakusai"])
  self.assertEqual(rows["appearances"],[
   "CM Punk","Cody Rhodes","Jade Cargill","Tiffany Stratton",
   "Gunther","Trick Williams","Karl Anderson"])
 def test_raw_dated_match_and_nxt_cancellation_safety(self):
  raw="WWE scheduled a No Disqualification match between Bayley and Lyra Valkyria on Raw."
  self.assertIn("Bayley vs. Lyra Valkyria",pairs(raw))
  nxt=("Jackson Drake will put the North American Championship on the line against EK Prosper. "
       "The six-man tag match was cancelled after Mini Vikingo was not medically cleared. "
       "Romeo Moreno and Noam Dar facing Ricky Smokes and Brad Baylor while "
       "Hank and Tank meet the Wagner Brothers. Saquon Shugars faces Sean Legacy.")
  rows=pairs(nxt)
  self.assertIn("Jackson Drake vs. EK Prosper",rows)
  self.assertIn("Romeo Moreno & Noam Dar vs. Ricky Smokes & Brad Baylor",rows)
  self.assertIn("Hank & Tank vs. The Wagner Brothers",rows)
  self.assertIn("Saquon Shugars vs. Sean Legacy",rows)
  self.assertFalse(any("Mini Vikingo" in r for r in rows))
 def test_unrelated_tna_ppv_cannot_be_the_weekly_impact_card(self):
  story=("TNA Destination X pay-per-view is scheduled for November 15. "
         "The Amazing Red faces Cedric Alexander at this separate event.")
  self.assertEqual(pairs(story),[])
  self.assertEqual(advertised(story),[])
 def test_roles_arenot_wrestler_names_and_no_implicit_appearances(self):
  para="New WWE Tag Team Champions Alexa Bliss and Tatum Paxley defend the titles against Michin and B-Fab."
  self.assertEqual(pairs(para),["Alexa Bliss & Tatum Paxley vs. Michin & B-Fab"])
  self.assertEqual(advertised("Giulia vs. Blake Monroe and Chelsea Green appears in the match."),[])
 def test_parser_does_not_read_results_news_or_mismatched_headings(self):
  body=b"<h2>Results</h2><p>Hank faces Tank.</p><h2>More news from this show</h2><p>Bob faces Jim.</p>"
  self.assertEqual(parse_page(body),{"matches":[],"appearances":[]})
 def test_date_scoped_nonpublic_output_and_no_aaa_event_assignment(self):
  calls=[]
  def get(url):
   calls.append(url)
   return RSS if url==FEED else PAGE
  data=build(SNAP,get,NOW)
  self.assertEqual(data["mode"],MODE)
  self.assertEqual(data["usage"],"PERSONAL_NONCOMMERCIAL_HOME_DISPLAY_ONLY")
  by={p["show_id"]:p for p in data["programs"]}
  self.assertEqual(len(by["smackdown"]["matches"]),2)
  self.assertEqual(by["smackdown"]["matches"][0]["status"],"REPORTED_UNVERIFIED")
  self.assertEqual(by["aaa"]["matches"],[])
  self.assertEqual(by["evolve"]["matches"],[])
  self.assertEqual(len(calls),5)
 def test_stale_or_previous_airdate_suppressed(self):
  snap={"schema_version":1,"shows":[dict(s) for s in SNAP["shows"]]}
  snap["shows"][1]={"id":"smackdown","schedule_status":"stale","next":{"date":"2026-10-23"}}
  snap["shows"][4]={"id":"tna","schedule_status":"fresh","next":{"date":"2026-10-22"}}
  d=build(snap,lambda url:RSS if url==FEED else PAGE,NOW)
  by={p["show_id"]:p for p in d["programs"]}
  self.assertEqual(by["smackdown"]["matches"],[])
  self.assertEqual(by["tna"]["matches"],[])
 def test_network_failure_fails_closed(self):
  def fail(url):raise OSError("offline")
  data=build(SNAP,fail,NOW)
  self.assertEqual(data["total_reported_matches"],0)
  self.assertEqual(data["rss_status"],"OSError")

if __name__=="__main__":unittest.main()
