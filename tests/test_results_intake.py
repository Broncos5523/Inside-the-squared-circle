import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from proof.results_intake import build_results, broadcast_complete, parse_result_lines, parse_explicit_description_results, eligible_episodes

ET=ZoneInfo("America/New_York")
def at(day=22,hour=17,minute=55): return datetime(2026,10,day,hour,minute,tzinfo=ET)
TNA={"idLeague":"4455","idEvent":"2618956","strEvent":"TNA iMPACT #1161",
     "dateEventLocal":"2026-10-22","dateEvent":"2026-10-23",
     "strResult":"Singles Match\nAvery Styles defeats Joe Alonzo\n\n"
                 "TNA X-Division Title Four Way #1 Contendership Match\n"
                 "Cedric Alexander defeats Fabian Aichner and KC Navarro and Rich Swann\n\n"
                 "TNA International Title Best Two Out Of Three Falls Match\nJason Hotch (c) vs. Mustafa Ali"}
SD={"idLeague":"4444","idEvent":"2599790","strEvent":"SmackDown #1418",
    "dateEventLocal":"2026-10-23","dateEvent":"2026-10-23",
    "strResult":"Street Fight\nGiulia vs. Blake Monroe"}
def snap():
    return {"shows":[
        {"id":"raw","previous":{"date":"2026-10-19"},"next":{"date":"2026-10-26"}},
        {"id":"smackdown","previous":{"date":"2026-10-16"},"next":{"date":"2026-10-23"}},
        {"id":"nxt","previous":{"date":"2026-10-20"},"next":{"date":"2026-10-27"}},
        {"id":"aaa","previous":{"date":"2026-10-17"},"next":{"date":"2026-10-24"}},
        {"id":"tna","previous":{"date":"2026-10-15"},"next":{"date":"2026-10-22"}},
        {"id":"evolve","previous":{"date":"2026-10-21"},"next":{"date":"2026-10-28"}}
    ]}
def requester(day,league):
    if league==4455 and day=="2026-10-23": return [TNA]
    if league==4444 and day=="2026-10-23":return [SD]
    return []

class ResultsIntakeTests(unittest.TestCase):
    def test_no_premature_tna_spoilers(self):
        self.assertFalse(broadcast_complete("tna","2026-10-22",at()))
        self.assertFalse(broadcast_complete("tna","2026-10-22",at(hour=23,minute=14)))
        self.assertTrue(broadcast_complete("tna","2026-10-22",at(hour=23,minute=15)))
        self.assertEqual(build_results(snap(),requester=requester,known={},now=at())["total_reported_results"],0)
    def test_results_after_broadcast_exact_match_day(self):
        r=build_results(snap(),requester=requester,known={},now=at(hour=23,minute=20))
        self.assertEqual(r["total_reported_results"],2)
        tna=next(x for x in r["programs"] if x["show_id"]=="tna")
        self.assertEqual(tna["airdate"],"2026-10-22")
        self.assertEqual(len(tna["results"]),2)
        self.assertEqual(tna["results"][0]["text"],"Avery Styles defeats Joe Alonzo")
        self.assertTrue(all(m["status"]=="REPORTED_UNVERIFIED" for m in tna["results"]))
        self.assertTrue(all(m["evidence_url"].endswith("id=2618956") for m in tna["results"]))
    def test_wrestling_result_grammar_defeated_and_def_dot(self):
        parsed=parse_result_lines(
            "Tag Team Match\nCody Rhodes & Jey Uso defeated Jimmy Uso & Solo Sikoa\n\n"
            "Singles Match\nSkylar Raye def. Sloane Jacobs")
        self.assertEqual(len(parsed),2)
        self.assertEqual(parsed[0]["text"],"Cody Rhodes & Jey Uso defeats Jimmy Uso & Solo Sikoa")
        self.assertEqual(parsed[1]["text"],"Skylar Raye defeats Sloane Jacobs")
    def test_only_explicit_results_section_of_description(self):
        desc=("Preview: Joe vs. Ali\n"
              "The challenger hopes to defeat the champion.\n\n"
              "Match Results:\n"
              "Singles Match\nAvery Styles defeated Joe Alonzo\n\n"
              "Next Week:\nJohn Cena defeated Randy Orton")
        actual=parse_explicit_description_results(desc)
        self.assertEqual(len(actual),1)
        self.assertEqual(actual[0]["text"],"Avery Styles defeats Joe Alonzo")
        self.assertEqual(parse_explicit_description_results("Storyline:\nRandy defeated Cody last week"),[])
        self.assertEqual(parse_explicit_description_results("Next Week:\nCody vs. Randy"),[])
    def test_description_result_used_only_after_air_and_matching_provider(self):
        described=dict(TNA,strResult=None,strDescriptionEN=
                       "Match Results:\nSingles Match\nAvery Styles defeated Joe Alonzo")
        feed=lambda d,l:[described] if d=="2026-10-23" and l==4455 else []
        before=build_results(snap(),requester=feed,known={},now=at(hour=22,minute=50))
        self.assertEqual(before["total_reported_results"],0)
        after=build_results(snap(),requester=feed,known={},now=at(hour=23,minute=20))
        tna=next(x for x in after["programs"] if x["show_id"]=="tna")
        self.assertEqual(len(tna["results"]),1)
        self.assertEqual(tna["results"][0]["provider_field"],"strDescriptionEN/results_section")
    def test_no_winner_from_advance_card(self):
        self.assertEqual(parse_result_lines(SD["strResult"]),[])
        self.assertEqual(parse_result_lines("Street Fight\nGiulia vs. Blake Monroe"),[])
    def test_no_fake_title_changes_or_unsourced_outcomes(self):
        self.assertEqual(len(parse_result_lines(TNA["strResult"])),2)
        self.assertEqual(parse_result_lines("Winner TBD\nA vs B"),[])
        self.assertEqual(parse_result_lines("Title Match\nPrediction: Joe defeats Cody"),[])
        self.assertEqual(parse_result_lines("<script>Joe defeats Cody</script>"),[])
    def test_past_league_endpoint_recovers_missing_exact_previous_event(self):
        previous=dict(TNA,idEvent="2618998",dateEventLocal="2026-10-15",dateEvent="2026-10-16",
                      strResult="Singles Match\nAvery Styles defeats Joe Alonzo")
        calls=[]
        def past(league):
            calls.append(league)
            return [previous] if league==4455 else []
        r=build_results(snap(),requester=lambda *_:[],past_lookup=past,known={},now=at())
        tna=next(x for x in r["programs"] if x["show_id"]=="tna")
        self.assertEqual(tna["airdate"],"2026-10-15")
        self.assertEqual(len(tna["results"]),1)
        self.assertEqual(calls.count(4455),1)
        self.assertEqual(tna["results"][0]["provider_event_id"],"2618998")
    def test_previous_week_result_is_not_recycled_after_new_broadcast(self):
        older=dict(TNA,idEvent="2618998",dateEventLocal="2026-10-15",
                   dateEvent="2026-10-16",
                   strResult="Singles Match\nAvery Styles defeated Joe Alonzo")
        # Current October 22 broadcast has finished, but the provider only
        # has October 15 results indexed.
        r=build_results(snap(),requester=lambda d,l:[older] if d=="2026-10-16" else [],
                        past_lookup=lambda l:[older] if l==4455 else [],
                        known={},now=at(hour=23,minute=20))
        tna=next(x for x in r["programs"] if x["show_id"]=="tna")
        self.assertEqual(tna["results"],[])
        self.assertIsNone(tna["airdate"])
        self.assertEqual(r["total_reported_results"],0)
    def test_past_league_wrong_show_or_date_rejected(self):
        wrong=dict(TNA,idEvent="2618998",dateEventLocal="2026-10-16")
        r=build_results(snap(),requester=lambda *_:[],past_lookup=lambda league:[wrong],
                        known={},now=at())
        self.assertEqual(r["total_reported_results"],0)
    def test_no_wrong_show_date_or_aaa_evolve_assignment(self):
        wrong=dict(TNA,dateEventLocal="2026-10-23")
        r=build_results(snap(),requester=lambda d,l:[wrong],known={},now=at(hour=23,minute=20))
        self.assertEqual(r["total_reported_results"],0)
        self.assertEqual(next(x for x in r["programs"] if x["show_id"]=="aaa")["results"],[])
        self.assertEqual(next(x for x in r["programs"] if x["show_id"]=="evolve")["results"],[])
    def test_incorrect_historic_event_identifier_ignored(self):
        known={"entries":[{"show_id":"tna","airdate":"2026-10-22","event_ids":["999999"]}]}
        r=build_results(snap(),requester=lambda d,l:[],event_lookup=lambda _: [TNA],known=known,now=at(hour=23,minute=20))
        self.assertEqual(r["total_reported_results"],0)
    def test_live_lookup_known_event_under_day_index_outage(self):
        known={"entries":[{"show_id":"tna","airdate":"2026-10-22","event_ids":["2618956"]}]}
        r=build_results(snap(),requester=lambda *_:[],event_lookup=lambda _: [TNA],known=known,now=at(hour=23,minute=20))
        self.assertEqual(r["total_reported_results"],2)
    def test_week_old_broadcast_and_preair_current(self):
        self.assertEqual(eligible_episodes(snap()["shows"][4],at()),["2026-10-15"])
        self.assertEqual(eligible_episodes(snap()["shows"][4],at(hour=23,minute=20)),["2026-10-22","2026-10-15"])
    def test_provider_failure_does_not_fabricate(self):
        def fail(*args):raise ConnectionError("offline")
        r=build_results(snap(),requester=fail,known={},now=at(hour=23,minute=20))
        self.assertEqual(r["total_reported_results"],0)
        self.assertTrue(next(x for x in r["programs"] if x["show_id"]=="tna")["partial_source_error"])
if __name__=="__main__":unittest.main()
