"""V4.37 source-gated SmackDown photo-showcase structural checks."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD=(ROOT/"web/preview-v4-36-authentic-smackdown.html").read_text()
NEW=(ROOT/"web/preview-v4-37-smackdown-photo-showcase.html").read_text()
class ShowcaseTests(unittest.TestCase):
 def test_old_approved_css_is_prefix(self):
  self.assertTrue(NEW.split("<style>",1)[1].split("</style>",1)[0].startswith(
    OLD.split("<style>",1)[1].split("</style>",1)[0]))
  self.assertIn("DISPLAY BUILD 4.37",NEW)
 def test_opt_in_and_only_exact_reviewed_wrestlers(self):
  for text in ("forceShowcase=reviewParams.get('view')==='showcase'&&requested==='smackdown'",
     "if(forceShowcase&&keys.length===1)return [keys[0]]",
     "if(!forceShowcase||key!=='smackdown')return;",
     "reportedRows(show,key,'matches')","REPORTED_UNVERIFIED",
     "const sdPhotoOrder=['chelsea green','roxanne perez','giulia','alexa bliss']",
     "side=item.replace(/\\(w\\/[^)]*\\)/gi,' ')",
     "sdApprovedPhoto(name)","ON REPORTED CARD","if(names.length<2)return;"):
   self.assertIn(text,NEW)
  self.assertIn("PHOTOS: DIEGO SERRANO · CC BY 2.0 · CROPPED FOR LAYOUT",NEW)
  self.assertIn("recapRotationPage(key,names.length)",NEW)
 def test_no_wrong_article_links_fake_matches_or_show_changes(self):
  self.assertNotIn("createElement('a')",NEW)
  self.assertIn("wcn-match-cards-private.json",NEW)
  self.assertIn("aaa-tv-week-cards-20261023.json",NEW)
  self.assertIn("renderEditorialRecap(show,key)",NEW)
  self.assertIn("#board.smackdown-showcase",NEW)
  self.assertIn("#board{width:min(100vw,56.25dvh)",NEW)
if __name__=="__main__":unittest.main()
