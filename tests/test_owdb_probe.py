import unittest
from proof.owdb_probe import probe
class PublicApiProbe(unittest.TestCase):
    def test_only_json_schema_no_fabricated_match_claims(self):
        self.assertEqual(probe(lambda:{"matches":37,"links":{"matches":"/api/matches/"}}),
          {"status":"json_schema_discovered","top_level_keys":["links","matches"],
           "declared_routes":["matches"],"matches_shape":{"type":"int","count":37}})
        self.assertEqual(probe(lambda:[]),{"status":"unexpected_schema"})
        self.assertNotIn("results",str(probe(lambda:{"wrestlers":[]})))
    def test_fails_closed_on_provider_outage(self):
        def bad():raise TimeoutError("offline")
        self.assertEqual(probe(bad)["status"],"unavailable")
if __name__=="__main__":unittest.main()
