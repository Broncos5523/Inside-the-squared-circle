import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
class EvolveEditorialFacts(unittest.TestCase):
    def test_sourced_one_time_previous_episode_only(self):
        data=json.loads((ROOT/'web/data/evolve-recap-20261021.json').read_text())
        self.assertEqual(data["mode"],"DATED_EDITORIAL_EVOLVE_RECAP_UNVERIFIED")
        self.assertEqual(data["airdate"],"2026-10-21")
        self.assertEqual(data["reviewed_at_et"],"2026-10-22")
        self.assertEqual(data["show_id"],"evolve")
        self.assertTrue(data["source_url"].startswith("https://www.blogofdoom.com/2026/10/21/"))
        self.assertEqual(len(data["results"]),3)
        self.assertGreaterEqual(len(data["developments"]),2)
        for record in data["results"]+data["developments"]:
            self.assertEqual(record["status"],"REPORTED_UNVERIFIED")
            self.assertLessEqual(len(record["text"]),210)
if __name__=="__main__":
    unittest.main()
