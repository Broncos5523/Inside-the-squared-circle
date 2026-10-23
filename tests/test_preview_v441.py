"""V4.41 exact Wikimedia archival trio, not advertised appearance claims."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
OLD=(ROOT/'web/preview-v4-40-smackdown-broadcast-recaps.html').read_text()
NEW=(ROOT/'web/preview-v4-41-licensed-stars-broadcast.html').read_text()
class LicensedArchiveTests(unittest.TestCase):
 def test_old_board_is_preserved(self):
  self.assertTrue(NEW.split('<style>',1)[1].split('</style>',1)[0].startswith(
   OLD.split('<style>',1)[1].split('</style>',1)[0]))
  self.assertIn('DISPLAY BUILD 4.41',NEW)
  for source in ('editorialRecap(show,key)','wcn-match-cards-private.json',
    'aaa-tv-week-cards-20261023.json',
    "reportedRows(show,key,'matches')","renderSdBroadcast(show,key)"):
   self.assertIn(source,NEW)
 def test_three_exact_identity_photos_and_disclaimer(self):
  for name,photo in (('la knight','la-knight.jpg'),
    ('roman reigns','roman-reigns.jpg'),('cody rhodes','cody-rhodes.jpg')):
   self.assertIn("'"+name+"':'"+photo+"'",NEW)
  for key in ('archiveFallback=!forceAfterBell&&matched.length<2',
    "archiveFallback?['la knight','roman reigns','cody rhodes']:matched",
    'NOT ADVERTISED APPEARANCES','id="bd-hero-note"',
    'WRESTLERS ON THIS REPORTED MATCH CARD',
    'FEATURED IN REVIEWED EPISODE COVERAGE'):
   self.assertIn(key,NEW)
  self.assertNotIn("createElement('a')",NEW)
 def test_factual_data_route_unchanged(self):
  self.assertIn('const matched=forceAfterBell?sdReviewedRecapTalent',NEW)
  self.assertIn("const rows=forceAfterBell?[]:reportedRows(show,key,'matches')",NEW)
if __name__=='__main__':unittest.main()
