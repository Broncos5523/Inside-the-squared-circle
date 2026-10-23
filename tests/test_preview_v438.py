"""V4.38 screenshot response: reclaim wasted top margin, increase talent area."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD=(ROOT/'web/preview-v4-37-smackdown-photo-showcase.html').read_text(encoding='utf-8')
NEW=(ROOT/'web/preview-v4-38-smackdown-broadcast-review.html').read_text(encoding='utf-8')
def css(src):return src.split('<style>',1)[1].split('</style>',1)[0]
class SmackdownScreenshotReview(unittest.TestCase):
 def test_data_and_older_css_preserved(self):
  self.assertTrue(css(NEW).startswith(css(OLD)))
  for s in ("privateWcnRows(show,key,kind)", "reportedRows(show,key,'matches')",
            "sdNamedCompetitors(show,key)","recapRotationPage(key,names.length)",
            "sdApprovedPhoto(name)","renderEditorialRecap(show,key)",
            "wcn-match-cards-private.json","aaa-tv-week-cards-20261023.json"):
   self.assertIn(s,NEW)
 def test_compact_deadspace_and_larger_hero(self):
  self.assertIn('#board.smackdown-showcase header{',NEW)
  self.assertIn('min-height:15.0cqh;height:15.0cqh;flex:0 0 15.0cqh',NEW)
  self.assertIn('margin-top:1.15cqw;min-height:5.1cqh',NEW)
  self.assertIn('height:31.5cqh;flex:0 0 31.5cqh',NEW)
  self.assertIn('height:21cqh;left:1.8cqw;right:1.8cqw',NEW)
  self.assertIn('.sd-talent-panel:nth-child(2)',NEW)
  self.assertIn('object-position:center 14%;transform:scale(1.06)',NEW)
  self.assertIn("if(!forceShowcase||key!=='smackdown')return;",NEW)
 def test_visible_build_label_corrected(self):
  self.assertIn('DISPLAY BUILD 4.38<br>Awaiting first update',NEW)
  self.assertIn("put('timestamp',\x60DISPLAY BUILD 4.38 ·",NEW)
  self.assertNotIn("put('timestamp',\x60DISPLAY BUILD 4.31 ·",NEW)
 def test_not_marked_as_approved_brand_or_replaced_logo(self):
  self.assertIn('class="brand-over">MAN CAVE SPORTS BOOK PRESENTS',NEW)
  self.assertIn("src='./assets/vetted/'+file",NEW)
  self.assertIn('smackdown-mark.png',NEW)
  self.assertNotIn("createElement('a')",NEW)
if __name__=='__main__':unittest.main()
