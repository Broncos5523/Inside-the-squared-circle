import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from proof.reported_cards import build_reported


ET = ZoneInfo("America/New_York")
NOW = datetime(2026, 10, 22, 16, 0, tzinfo=ET)

EVENT_SD = {
    "idLeague": "4444", "idEvent": "2599790", "strEvent": "SmackDown #1418",
    "dateEventLocal": "2026-10-23", "dateEvent": "2026-10-23",
    "strDescriptionEN": "Street Fight\nGiulia vs. Blake Monroe\n\n"
                        "WWE Women's Tag Team Title Match\n"
                        "Alexa Bliss & Tatum Paxley vs. B-Fab & Michin\n\n"
                        "Non Title Match\nMFTs vs. Bakusai",
}
EVENT_TNA = {
    "idLeague": "4455", "idEvent": "2618956", "strEvent": "TNA iMPACT #1161",
    "dateEventLocal": "2026-10-22", "dateEvent": "2026-10-23",
    "strDescriptionEN": "Singles Match\nJoe Alonzo vs. Avery Styles",
}
EVENT_AAA = {
    "idLeague": "4593", "idEvent": "2618990", "strEvent": "Heroes Inmortales",
    "dateEventLocal": "2026-10-24", "dateEvent": "2026-10-24",
    "strDescriptionEN": "Singles Match\nA vs. B",
}


def snapshot():
    return {"shows": [
        {"id": "raw", "next": {"date": "2026-10-26"}},
        {"id": "smackdown", "next": {"date": "2026-10-23"}},
        {"id": "nxt", "next": {"date": "2026-10-27"}},
        {"id": "aaa", "next": {"date": "2026-10-24"}},
        {"id": "tna", "next": {"date": "2026-10-22"}},
        {"id": "evolve", "next": {"date": "2026-10-28"}},
    ]}


def provider(day, league):
    if day == "2026-10-23" and league == 4444:
        return [EVENT_SD, EVENT_SD]
    if day == "2026-10-23" and league == 4455:
        return [EVENT_TNA]
    if day == "2026-10-24" and league == 4593:
        return [EVENT_AAA]
    return []


class ReportedCardTests(unittest.TestCase):
    def test_reported_not_confirmed_and_source_traced(self):
        result = build_reported(snapshot(), requester=provider, now=NOW)
        self.assertEqual(result["mode"], "REPORTED_MATCHES_UNVERIFIED")
        sd = next(x for x in result["programs"] if x["show_id"] == "smackdown")
        self.assertEqual(len(sd["matches"]), 3)
        self.assertTrue(all(m["status"] == "REPORTED_UNVERIFIED" for m in sd["matches"]))
        self.assertTrue(all(m["source_name"] == "TheSportsDB" for m in sd["matches"]))
        self.assertTrue(all(m["evidence_url"].endswith("?id=2599790") for m in sd["matches"]))

    def test_tna_uses_local_airdate_even_utc_next_day(self):
        result = build_reported(snapshot(), requester=provider, now=NOW)
        tna = next(x for x in result["programs"] if x["show_id"] == "tna")
        self.assertEqual(len(tna["matches"]), 1)
        self.assertEqual(tna["matches"][0]["text"], "Joe Alonzo vs. Avery Styles")

    def test_aaa_evolve_not_misassigned(self):
        result = build_reported(snapshot(), requester=provider, now=NOW)
        for name in ("aaa", "evolve"):
            item = next(x for x in result["programs"] if x["show_id"] == name)
            self.assertEqual(item["matches"], [])

    def test_expired_airdate_displays_nothing(self):
        old = snapshot()
        old["shows"][1]["next"]["date"] = "2026-10-21"
        result = build_reported(old, requester=provider, now=NOW)
        self.assertEqual(result["programs"][1]["matches"], [])

    def test_no_invented_matches_if_provider_fails(self):
        def fail(day, league):
            raise RuntimeError("API unavailable")
        result = build_reported(snapshot(), requester=fail, now=NOW)
        self.assertEqual(result["total_reported_matches"], 0)
        self.assertEqual(next(x for x in result["programs"] if x["show_id"] == "smackdown")["error"], "PROVIDER_PARTIAL_OR_UNAVAILABLE")

    def test_no_unverified_appearances_in_feed(self):
        result = build_reported(snapshot(), requester=provider, now=NOW)
        self.assertNotIn("confirmed", str(result).lower())
        self.assertNotIn("advertised_appearances", str(result))

    def test_result_tombstone_survives_upstream_blackout_only_same_airdate(self):
        prior={"programs":[{"show_id":"tna","airdate":"2026-10-22",
                            "episode_outcome_detected":True,"episode_withdrawn":False},
                           {"show_id":"smackdown","airdate":"2026-10-16",
                            "episode_outcome_detected":True}]}
        d=build_reported(snapshot(),requester=lambda *_:[],now=NOW,previous=prior)
        by={p["show_id"]:p for p in d["programs"]}
        self.assertTrue(by["tna"]["episode_outcome_detected"])
        self.assertEqual(by["tna"]["matches"],[])
        self.assertFalse(by["smackdown"]["episode_outcome_detected"])

    def test_result_detection_suppresses_stale_advertised_cards(self):
        recorded=dict(EVENT_TNA, strResult="Singles Match\nAvery Styles defeats Joe Alonzo")
        d=build_reported(snapshot(),requester=lambda day,league:[recorded] if league==4455 else [],
                         now=NOW)
        tna=next(x for x in d["programs"] if x["show_id"]=="tna")
        self.assertTrue(tna["episode_outcome_detected"])
        self.assertEqual(tna["matches"],[])
        self.assertFalse(next(x for x in d["programs"] if x["show_id"]=="smackdown")["episode_outcome_detected"])

    def test_cancelled_episode_sets_withdrawn_flag_and_no_card(self):
        cancelled=dict(EVENT_SD,strStatus="Cancelled")
        d=build_reported(snapshot(),requester=lambda day,league:[cancelled] if league==4444 else [],
                         now=NOW)
        sd=next(x for x in d["programs"] if x["show_id"]=="smackdown")
        self.assertTrue(sd["episode_withdrawn"])
        self.assertEqual(sd["matches"],[])

    def test_known_event_identifier_requeries_live_and_recovers_index_gap(self):
        known = {"entries": [
            {"show_id":"smackdown","airdate":"2026-10-23","event_ids":["2599790"]},
            {"show_id":"tna","airdate":"2026-10-22","event_ids":["2618956"]},
        ]}
        calls=[]
        def lookup(event_id):
            calls.append(event_id)
            return [EVENT_SD] if event_id=="2599790" else [EVENT_TNA]
        result=build_reported(snapshot(),requester=lambda *_: [],now=NOW,
                              known_events=known,event_lookup=lookup)
        self.assertEqual(result["total_reported_matches"],4)
        self.assertEqual(calls,["2599790","2618956"])
        self.assertEqual(next(x for x in result["programs"] if x["show_id"]=="smackdown")["matches"][0]["status"],"REPORTED_UNVERIFIED")

    def test_known_id_rejects_expired_mismatch_cancelled_and_finished(self):
        known={"entries":[{"show_id":"smackdown","airdate":"2026-10-23","event_ids":["2599790"]}]}
        for altered in [
            dict(EVENT_SD,strStatus="Cancelled"),
            dict(EVENT_SD,strResult="Match winner published"),
            dict(EVENT_SD,dateEventLocal="2026-10-30"),
            dict(EVENT_SD,strEvent="RAW #1700"),
        ]:
            with self.subTest(event=altered):
                result=build_reported(snapshot(),requester=lambda *_:[],now=NOW,
                                      known_events=known,event_lookup=lambda _: [altered])
                self.assertEqual(result["total_reported_matches"],0)

    def test_known_id_is_ignored_for_other_airdate_or_wrong_provider_id(self):
        known={"entries":[{"show_id":"smackdown","airdate":"2026-10-30","event_ids":["2599790"]},
                          {"show_id":"smackdown","airdate":"2026-10-23","event_ids":["9999999"]}]}
        result=build_reported(snapshot(),requester=lambda *_: [],now=NOW,
                              known_events=known,event_lookup=lambda _: [EVENT_SD])
        self.assertEqual(result["total_reported_matches"],0)

    def test_next_league_enriches_but_never_cross_assigns(self):
        episode = dict(EVENT_SD, idEvent="2777111", strEvent="RAW #1744",
                       dateEventLocal="2026-10-26", dateEvent="2026-10-26",
                       strDescriptionEN="Singles Match\nBayley vs. Lyra Valkyria")
        calls = []
        def fetch_next(league):
            calls.append(league)
            return [episode, EVENT_SD] if league == 4444 else []
        empty=lambda day,league: []
        result = build_reported(snapshot(), requester=empty, now=NOW, next_lookup=fetch_next)
        by = {p["show_id"]: p for p in result["programs"]}
        self.assertEqual(len(by["raw"]["matches"]), 1)
        self.assertEqual(by["raw"]["matches"][0]["text"], "Bayley vs. Lyra Valkyria")
        self.assertEqual(len(by["smackdown"]["matches"]), 3)
        self.assertEqual(by["nxt"]["matches"], [])
        self.assertEqual(by["aaa"]["matches"], [])
        self.assertEqual(calls.count(4444), 1)

    def test_expired_or_cancelled_next_league_records_ignored(self):
        cancelled = dict(EVENT_SD, strStatus="Cancelled")
        dated = dict(EVENT_SD, dateEventLocal="2026-10-30")
        result=build_reported(snapshot(), requester=lambda *args: [], now=NOW,
                              next_lookup=lambda league: [cancelled, dated])
        self.assertEqual(result["total_reported_matches"], 0)

    def test_next_league_failure_is_partial_but_day_source_survives(self):
        def fail(*args):raise ConnectionError("provider offline")
        result=build_reported(snapshot(), requester=provider, now=NOW, next_lookup=fail)
        sm=next(x for x in result["programs"] if x["show_id"]=="smackdown")
        self.assertEqual(len(sm["matches"]),3)
        self.assertEqual(sm["error"], "PROVIDER_PARTIAL_OR_UNAVAILABLE")

    def test_no_match_after_program_changes(self):
        snap = snapshot()
        snap["shows"][1]["next"]["date"] = "2026-10-30"
        result = build_reported(snap, requester=provider, now=NOW)
        self.assertEqual(result["programs"][1]["matches"], [])


if __name__ == "__main__":
    unittest.main()
