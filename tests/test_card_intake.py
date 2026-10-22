import unittest
from datetime import date, timedelta

from proof.card_intake import (
    broadcast_date, build_report, parse_bouts, relevant_events, valid_upcoming, unusable_upcoming_event
)

TODAY = date(2026, 10, 22)

SMACKDOWN = {
    "idLeague": "4444", "idEvent": "2599790", "strEvent": "SmackDown #1418",
    "dateEventLocal": "2026-10-23", "dateEvent": "2026-10-23",
    "strDescriptionEN": (
        "Street Fight\nGiulia vs. Blake Monroe\n\n"
        "WWE Women's Tag Team Title Match\n"
        "Alexa Bliss & Tatum Paxley (c) vs. B-Fab & Michin\n\n"
        "Non Title Tag Team Match\n"
        "MFTs vs. Bakusai"
    )
}
RAW = {
    "idLeague": "4444", "idEvent": "2599791", "strEvent": "RAW #1744",
    "dateEventLocal": "2026-10-26", "dateEvent": "2026-10-26",
    "strDescriptionEN": ""
}
TNA = {
    "idLeague": "4455", "idEvent": "2618956", "strEvent": "TNA iMPACT #1161",
    "dateEvent": "2026-10-23", "dateEventLocal": "2026-10-22",
    "strDescriptionEN": "Singles Match\nJoe Alonzo vs. Avery Styles"
}
AAA = {
    "idLeague": "4593", "idEvent": "2618990",
    "strEvent": "Heroes Inmortales", "dateEventLocal": "2026-10-24",
    "strDescriptionEN": "Singles Match\nA vs. B"
}


def sample_snapshot():
    dates = {
        "smackdown": "2026-10-23",
        "raw": "2026-10-26",
        "nxt": "2026-10-27",
        "aaa": "2026-10-24",
        "tna": "2026-10-22",
        "evolve": "2026-10-28",
    }
    return {
        "shows": [
            {"id": key, "next": {"date": day}, "schedule_status": "fresh"}
            for key, day in dates.items()
        ]
    }


def fake_request(day, league):
    if league == 4444 and day == "2026-10-23":
        return [SMACKDOWN]
    if league == 4444 and day == "2026-10-26":
        return [RAW]
    if league == 4455 and day == "2026-10-23":
        return [TNA]
    if league == 4593 and day == "2026-10-24":
        return [AAA]
    return []


class MatchIntakeTests(unittest.TestCase):
    def test_parse_candidates_not_truth(self):
        c = parse_bouts(SMACKDOWN["strDescriptionEN"])
        self.assertEqual(len(c), 3)
        self.assertTrue(all(x["status"] == "UNVERIFIED_SOURCE_MENTION" for x in c))
        self.assertTrue(all(x["kind"] == "possible_match" for x in c))

    def test_skip_editorial_unrelated_text(self):
        self.assertEqual(parse_bouts("Promo segment\nCM Punk returns"), [])
        self.assertEqual(parse_bouts("Fantasy booking\nA vs. B"), [])
        self.assertEqual(parse_bouts("<script>alert(1)</script>"), [])

    def test_no_result_spoilers_in_reported_match_lines(self):
        self.assertEqual(
            parse_bouts("Singles Match\nJohn Cena vs. CM Punk — Winner: John Cena"), []
        )
        self.assertEqual(
            parse_bouts("Title Match\nJohn Cena vs. CM Punk; CM Punk retained"), []
        )
        self.assertEqual(
            parse_bouts("Street Fight\nGiulia vs. Blake Monroe"), [
                {"kind": "possible_match", "status": "UNVERIFIED_SOURCE_MENTION",
                 "description": "Giulia vs. Blake Monroe", "stipulation": "Street Fight"}
            ]
        )

    def test_utc_day_differs_from_local_airdate(self):
        self.assertEqual(broadcast_date(TNA), "2026-10-22")
        self.assertEqual(len(relevant_events("tna", "2026-10-22", [TNA])), 1)
        self.assertEqual(relevant_events("tna", "2026-10-23", [TNA]), [])

    def test_show_identity_before_episode_number(self):
        self.assertEqual(len(relevant_events("smackdown", "2026-10-23", [SMACKDOWN])), 1)
        self.assertEqual(relevant_events("raw", "2026-10-23", [SMACKDOWN]), [])
        self.assertEqual(relevant_events("smackdown", "2026-10-26", [RAW]), [])

    def test_reject_league_date_mismatch(self):
        wrong = dict(SMACKDOWN, idLeague="4455")
        self.assertEqual(relevant_events("smackdown", "2026-10-23", [wrong]), [])
        wrong = dict(SMACKDOWN, dateEventLocal="2026-10-24")
        self.assertEqual(relevant_events("smackdown", "2026-10-23", [wrong]), [])

    def test_cancelled_postponed_and_aired_records_rejected(self):
        for field, val in [
            ("strStatus", "Match Finished"), ("strStatus", "Postponed"),
            ("strStatus", "Cancelled"), ("strPostponed", "yes"),
            ("strPostponed", 1), ("strResult", "Joe Alonzo won"),
        ]:
            event = dict(SMACKDOWN, **{field: val})
            with self.subTest(field=field, val=val):
                self.assertTrue(unusable_upcoming_event(event))
                self.assertEqual(relevant_events("smackdown", "2026-10-23", [event]), [])
        self.assertFalse(unusable_upcoming_event(dict(SMACKDOWN, strStatus="Scheduled")))

    def test_provider_pre_event_strresult_contains_card_without_outcomes(self):
        event = dict(SMACKDOWN, strStatus="", strPostponed="no",
                     strResult=SMACKDOWN["strDescriptionEN"])
        self.assertFalse(unusable_upcoming_event(event))
        self.assertEqual(len(relevant_events("smackdown", "2026-10-23", [event])), 1)
        finished = dict(event, strResult="Singles Match\nGiulia defeats Blake Monroe")
        self.assertEqual(relevant_events("smackdown", "2026-10-23", [finished]), [])

    def test_optional_next_league_rows_strict_and_deduplicated(self):
        calls = []
        def league_fetch(league):
            calls.append(league)
            return [SMACKDOWN, RAW, dict(SMACKDOWN, strResult="Result available"), AAA]
        def day_fetch(day, league):
            return [SMACKDOWN] if (day, league) == ("2026-10-23", 4444) else []
        d = build_report(sample_snapshot(), requester=day_fetch, clock=TODAY, next_lookup=league_fetch)
        by = {e["show_id"]: e for e in d["programs"]}
        self.assertEqual(by["smackdown"]["candidate_count"], 3)
        self.assertEqual(by["raw"]["candidate_count"], 0)
        self.assertEqual(by["aaa"]["candidate_count"], 0)
        self.assertEqual(calls.count(4444), 1)
        self.assertEqual(calls.count(4455), 1)

    def test_aaa_segmented_tv_event_never_autolinked(self):
        self.assertEqual(relevant_events("aaa", "2026-10-24", [AAA]), [])

    def test_evolve_is_results_only(self):
        self.assertEqual(relevant_events("evolve", "2026-10-28", [SMACKDOWN]), [])

    def test_validate_airdate_horizon(self):
        self.assertTrue(valid_upcoming("2026-10-22", TODAY))
        self.assertTrue(valid_upcoming("2026-11-11", TODAY))
        self.assertFalse(valid_upcoming("2026-10-21", TODAY))
        self.assertFalse(valid_upcoming("2026-11-12", TODAY))
        self.assertFalse(valid_upcoming("2026-99-99", TODAY))
        self.assertFalse(valid_upcoming(None, TODAY))

    def test_report_counts_only_with_no_verified_fabrications(self):
        result = build_report(sample_snapshot(), fake_request, TODAY)
        self.assertEqual(result["mode"], "RESEARCH_LEADS_ONLY")
        by = {e["show_id"]: e for e in result["programs"]}
        self.assertEqual(by["smackdown"]["candidate_count"], 3)
        self.assertEqual(by["tna"]["candidate_count"], 1)
        self.assertEqual(by["aaa"]["candidate_count"], 0)
        self.assertEqual(by["evolve"]["candidate_count"], 0)
        self.assertEqual(by["raw"]["candidate_count"], 0)
        self.assertEqual(result["total_unverified_possible_match_mentions"], 4)
        self.assertEqual(result["verified_matches"], [])
        self.assertEqual(result["verified_appearances"], [])
        self.assertEqual(by["smackdown"]["events_considered"][0]["verification"], "NOT_CONFIRMED")

    def test_duplicate_event_not_double_counted(self):
        def duplicate(day, league):
            if day == "2026-10-23" and league == 4455:
                return [TNA, TNA]
            return []
        result = build_report(sample_snapshot(), duplicate, TODAY)
        tna = next(x for x in result["programs"] if x["show_id"] == "tna")
        self.assertEqual(tna["candidate_count"], 1)

    def test_source_failure_never_promotes_anything(self):
        def failure(day, league):
            raise ConnectionError("upstream outage")
        result = build_report(sample_snapshot(), failure, TODAY)
        self.assertEqual(result["verified_matches"], [])
        self.assertEqual(result["verified_appearances"], [])
        self.assertEqual(result["total_unverified_possible_match_mentions"], 0)
        smackdown = next(x for x in result["programs"] if x["show_id"] == "smackdown")
        self.assertEqual(smackdown["intake_status"], "partial_source_error")

    def test_no_candidate_description_in_published_report(self):
        result = build_report(sample_snapshot(), fake_request, TODAY)
        payload = str(result)
        self.assertNotIn("Giulia vs.", payload)
        self.assertNotIn("Joe Alonzo vs.", payload)
        self.assertIn("lookupevent.php?id=2599790", payload)


if __name__ == "__main__":
    unittest.main()
