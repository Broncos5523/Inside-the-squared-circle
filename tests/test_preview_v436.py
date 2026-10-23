"""V4.36 only replaces vetted SmackDown assets: no fabricated talent photos."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD=(ROOT/'web/preview-v4-35-smackdown-graphics.html').read_text()
NEW=(ROOT/'web/preview-v4-36-authentic-smackdown.html').read_text()
class V436Tests(unittest.TestCase):
 def test_old_visual_style_preserved_plus_new_scoped_css(self):
  old=OLD.split('<style>',1)[1].split('</style>',1)[0]
  new=NEW.split('<style>',1)[1].split('</style>',1)[0]
  self.assertTrue(new.startswith(old))
  self.assertIn('DISPLAY BUILD 4.36',NEW)
  self.assertIn('#board{width:min(100vw,56.25dvh)',NEW)
 def test_official_logo_is_rendered_only_on_smackdown(self):
  self.assertIn("classList.toggle('smackdown-graphics',key==='smackdown')",NEW)
  self.assertIn("sdLogo.src='./assets/vetted/smackdown-mark.png'",NEW)
  self.assertIn('sd-logo-ready',NEW)
  self.assertIn("sdLogo.onerror=",NEW)
  self.assertNotIn("createElement('a')",NEW)
 def test_portraits_are_exact_real_wrestlers_no_image_guessing(self):
  for name in ['chelsea green','roxanne perez','giulia','alexa bliss']:
   self.assertIn("'"+name+"':",NEW)
  self.assertIn("const file=sdPortraits[name.trim().toLowerCase()]",NEW)
  self.assertIn("pic.src='./assets/vetted/'+file",NEW)
  self.assertIn("PHOTOS: DIEGO SERRANO · CC BY 2.0",NEW)
  self.assertIn("if(match.text.split(/",NEW)
  self.assertNotIn('https://upload.wikimedia.org/',NEW)
 def test_no_new_fake_matches_or_broken_sources(self):
  for term in ["privateWcnRows(show,key,kind)","reviewed-recaps.json",
       "aaa-tv-week-cards-20261023.json","recapRotationPage(key+'-recap',pages.length)"]:
   self.assertIn(term,NEW)
  self.assertIn('function sdWinnerArt(text)',NEW)
if __name__=='__main__':unittest.main()
