import unittest
from proof.owdb_probe import probe,probe_matches_root,probe_recent_coverage
class PublicApiProbe(unittest.TestCase):
    def test_only_json_schema_no_fabricated_match_claims(self):
        self.assertEqual(probe(lambda:{"matches":37,"links":{"matches":"/api/matches/"}}),
          {"status":"json_schema_discovered","top_level_keys":["links","matches"],
           "declared_routes":["matches"],"matches_shape":{"type":"int","count":37}})
        self.assertEqual(probe(lambda:[]),{"status":"unexpected_schema"})
        self.assertNotIn("results",str(probe(lambda:{"wrestlers":[]})))
    def test_matches_json_schema_is_metadata_only(self):
        r=probe_matches_root(lambda:{"count":27,"results":[{
            "id":1,"event_name":"WWE RAW","winner":"First Wrestler"}]})
        self.assertEqual(r["status"],"matches_json_discovered")
        self.assertEqual(r["schema"]["declared_count"],27)
        self.assertEqual(r["schema"]["example_winner"],"First Wrestler")
    def test_four_page_audit_is_restricted_to_declared_api_urls(self):
        def request(url):
            if url.endswith('/api/matches/'):
                return {"results":[{"event":{"date":"2026-10-20","name":"WWE NXT"}}],
                        "next":"https://www.attacker.invalid/api/matches/"}
            raise AssertionError("Unapproved URL")
        s=probe_recent_coverage(request)
        self.assertEqual(s["pages_scanned"],1)
        self.assertEqual(s["since_sep2026_count"],1)
        self.assertEqual(s["since_sep2026_events"],["WWE NXT"])
    def test_fails_closed_on_provider_outage(self):
        def bad():raise TimeoutError("offline")
        self.assertEqual(probe(bad)["status"],"unavailable")
if __name__=="__main__":unittest.main()
