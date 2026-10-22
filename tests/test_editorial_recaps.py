"""One-time, date-limited historical recaps from attributed published sources."""
import json,unittest
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
class EditorialRecapChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=json.loads((ROOT/'web/data/editorial-recaps-20261022.json').read_text())
    def test_attributed_and_not_fabricated_future_results(self):
        p=self.data
        self.assertEqual(p['mode'],'DATED_MULTI_SOURCE_RECAP_REVIEW_UNVERIFIED')
        self.assertEqual(p['reviewed_at_et'],'2026-10-22')
        self.assertEqual(len(p['programs']),4)
        self.assertEqual({s['show_id'] for s in p['programs']},{'raw','smackdown','nxt','tna'})
        self.assertEqual({s['show_id']:s['airdate'] for s in p['programs']},
            {'raw':'2026-10-19','smackdown':'2026-10-16','nxt':'2026-10-20','tna':'2026-10-15'})
        for show in p['programs']:
            self.assertTrue(show['results'] and show['developments'])
            for url in (show['source_url'],show.get('secondary_url')):
                if url:
                    self.assertEqual(urlparse(url).scheme,'https')
                    self.assertIn(urlparse(url).hostname,{'www.wwe.com','411mania.com','www.f4wonline.com'})
            for entry in show['results']+show['developments']:
                self.assertEqual(entry['status'],'REPORTED_UNVERIFIED')
                self.assertLessEqual(len(entry['text']),190)
    def test_specific_key_results_grounded_in_review(self):
        by={p['show_id']:p for p in self.data['programs']}
        self.assertEqual(len(by['raw']['results']),5)
        self.assertEqual(len(by['smackdown']['results']),5)
        self.assertEqual(len(by['nxt']['results']),4)
        self.assertEqual(len(by['tna']['results']),4)
        self.assertTrue(any('Roman Reigns' in e['text'] for e in by['raw']['developments']))
        self.assertTrue(any('double count-out' in e['text'] for e in by['nxt']['results']))
if __name__=='__main__':unittest.main()
