"""V4.40 full SmackDown broadcast with source-gated completed show facts."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD=(ROOT/'web/preview-v4-39-smackdown-full-broadcast.html').read_text()
NEW=(ROOT/'web/preview-v4-40-smackdown-broadcast-recaps.html').read_text()
class BoardV440Tests(unittest.TestCase):
 def test_older_graphics_remain_intact_and_independent(self):
  self.assertTrue(NEW.split('<style>',1)[1].split('</style>',1)[0].startswith(
    OLD.split('<style>',1)[1].split('</style>',1)[0]))
  self.assertIn('DISPLAY BUILD 4.40',NEW)
  self.assertIn("const forceAfterBell=reviewParams.get('view')==='afterbell'&&requested==='smackdown';",NEW)
  self.assertIn("if((forceBroadcast||forceAfterBell)&&keys.length===1)return [keys[0]];",NEW)
  self.assertIn("const active=(forceBroadcast||forceAfterBell)&&key==='smackdown';",NEW)
 def test_post_air_facts_cannot_use_future_card(self):
  for phrase in ('editorialRecap(show,key)','verifiedResults=forceAfterBell',
    'developments=forceAfterBell','sdReviewedRecapTalent(verifiedResults,developments)',
    'renderSdRecapBoxes(record,verifiedResults,developments,primary,side,other,notes)',
    'record?.airdate||show.previous?.date',
    'NEXT COMPLETED-SHOW RECAP UPDATING'):
   self.assertIn(phrase,NEW)
  self.assertIn("const appearances=forceAfterBell?[]:reportedRows(show,key,'appearances')",NEW)
  self.assertIn('if(!record||!hasResults)',NEW)
  self.assertNotIn("createElement('a')",NEW)
 def test_full_board_components_and_attribution(self):
  for phrase in ('id="sd-broadcast" hidden','bd-logo-side left',
    'bd-logo-side right','bd-photo.center',
    'id="bd-hero"','id="bd-primary"','id="bd-side"',
    'id="bd-others"','id="bd-notes"','id="bd-air-label"',
    'id="bd-others-title"','id="bd-ticker"','id="bd-dates"',
    'DIEGO SERRANO / CC BY 2.0'):
   self.assertIn(phrase,NEW)
  self.assertIn("wcn-match-cards-private.json",NEW)
  self.assertIn("aaa-tv-week-cards-20261023.json",NEW)
  self.assertIn("renderEditorialRecap(show,key)",NEW)
  self.assertNotIn("DISPLAY BUILD 4.31",NEW)
if __name__=='__main__':unittest.main()
