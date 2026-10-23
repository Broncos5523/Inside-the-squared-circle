"""V4.42 screenshot QA corrections: real photos, no fabricated claims."""
from pathlib import Path
import unittest,re
ROOT=Path(__file__).resolve().parents[1]
OLD=(ROOT/"web/preview-v4-41-licensed-stars-broadcast.html").read_text()
NEW=(ROOT/"web/preview-v4-42-smackdown-reference-qa.html").read_text()
class ScreenshotQA(unittest.TestCase):
 def test_visual_changes_are_only_scoped_overrides(self):
  previous=OLD.split('<style>',1)[1].split('</style>',1)[0]
  current=NEW.split('<style>',1)[1].split('</style>',1)[0]
  self.assertTrue(current.startswith(previous))
  self.assertIn('grid-template-rows:18.5% 25.5% 2.4% 5.8% 26% 12% 3% 6% .8%',NEW)
  self.assertIn('#sd-broadcast .bd-ring{',NEW)
  self.assertIn('z-index:1;bottom:3%;height:.45cqw;',NEW)
  self.assertIn('#sd-broadcast .bd-photo .bd-name{',NEW)
  self.assertIn('z-index:6;bottom:10%;font-size:2.85cqw;',NEW)
  self.assertIn('#sd-broadcast .bd-tag{',NEW)
  self.assertIn('margin-top:.85cqw;margin-bottom:1.05cqw;',NEW)
 def test_show_cover_is_editorial_not_an_appearance(self):
  self.assertIn('const archiveFallback=!forceAfterBell;',NEW)
  self.assertIn("archiveFallback?['la knight','roman reigns','cody rhodes']:matched",NEW)
  self.assertIn('EDITORIAL HERO · ARCHIVAL PHOTOS · NOT ADVERTISED APPEARANCES',NEW)
  self.assertIn("const first=archiveFallback?0:position%talent.length",NEW)
  self.assertIn("const rows=forceAfterBell?[]:reportedRows(show,key,'matches')",NEW)
  self.assertIn('renderSdRecapBoxes(record,verifiedResults,developments',NEW)
 def test_version_and_original_working_board_intact(self):
  self.assertIn('DISPLAY BUILD 4.42',NEW)
  self.assertIn('id="bd-build">DISPLAY 4.42',NEW)
  self.assertIn("bd('build').textContent='DISPLAY 4.42'",NEW)
  self.assertNotIn('id="bd-build">DISPLAY 4.40',NEW)
  self.assertIn('wcn-match-cards-private.json',NEW)
  self.assertIn('aaa-tv-week-cards-20261023.json',NEW)
  self.assertNotIn("createElement('a')",NEW)
if __name__=="__main__": unittest.main()
