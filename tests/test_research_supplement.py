"""Ensure the one-time reviewed facts remain dated, attributed and separated by show."""
import json
import unittest
from pathlib import Path
from datetime import date
from urllib.parse import urlparse

PATH=Path(__file__).resolve().parents[1]/'web/data/research-20261022.json'
DATES={'raw':'2026-10-26','smackdown':'2026-10-23','nxt':'2026-10-27','aaa':'2026-10-24','tna':'2026-10-22','evolve':'2026-10-28'}

class ResearchSupplementTests(unittest.TestCase):
    def test_sources_dates_and_labels(self):
        d=json.loads(PATH.read_text())
        self.assertEqual(d['mode'],'DATED_RESEARCH_SUPPLEMENT_UNVERIFIED')
        self.assertIn('ONE_TIME',d['method'])
        self.assertEqual(d['reviewed_at_et'],'2026-10-22')
        rows={x['show_id']:x for x in d['programs']}
        self.assertEqual(set(rows),set(DATES))
        for k,v in rows.items():
            self.assertEqual(v['airdate'],DATES[k])
            self.assertGreaterEqual(date.fromisoformat(v['airdate']),date.fromisoformat(d['reviewed_at_et']))
            for x in v['matches']+v['appearances']:
                self.assertEqual(x['status'],'REPORTED_UNVERIFIED')
                self.assertEqual(urlparse(x['evidence_url']).scheme,'https')
                self.assertIn(urlparse(x['evidence_url']).netloc,{'www.wwe.com','www.f4wonline.com','tnawrestling.com','www.thesportsdb.com'})
                self.assertTrue(x['source_name'])
        self.assertEqual(len(rows['raw']['matches']),1)
        self.assertEqual(len(rows['smackdown']['matches']),1)
        self.assertEqual(len(rows['nxt']['matches']),5)
        self.assertFalse(rows['aaa']['matches'])
        self.assertFalse(rows['evolve']['matches'])
        self.assertEqual(len(rows['tna']['appearances']),2)
if __name__=='__main__':unittest.main()
