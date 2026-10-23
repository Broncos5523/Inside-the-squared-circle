"""Graphics phase 1: SmackDown-only art and existing match data."""
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD=(ROOT/"web/preview-v4-34-private-wcn.html").read_text(encoding="utf-8")
NEW=(ROOT/"web/preview-v4-35-smackdown-graphics.html").read_text(encoding="utf-8")
SVG=(ROOT/"web/art/smackdown-arena-v1.svg").read_text(encoding="utf-8")
class GraphicsPhase1(unittest.TestCase):
 def test_self_contained_arena_vector(self):
  root=ET.fromstring(SVG)
  self.assertEqual(root.tag,"{http://www.w3.org/2000/svg}svg")
  self.assertEqual(root.attrib.get("viewBox"),"0 0 720 1280")
  self.assertIn("SMACK",SVG)
  self.assertIn("DOWN",SVG)
  self.assertNotIn("https://",SVG)
 def test_approved_css_is_preserved_as_prefix(self):
  old=OLD.split("<style>",1)[1].split("</style>",1)[0]
  new=NEW.split("<style>",1)[1].split("</style>",1)[0]
  self.assertTrue(new.startswith(old))
  self.assertIn("#board{width:min(100vw,56.25dvh)",NEW)
  self.assertIn("DISPLAY BUILD 4.35",NEW)
 def test_only_smackdown_receives_new_graphics(self):
  self.assertIn("classList.toggle('smackdown-graphics',key==='smackdown')",NEW)
  self.assertIn("#board.smackdown-graphics",NEW)
  self.assertIn("function sdMatchHero(text)",NEW)
  self.assertIn("function sdWinnerArt(text)",NEW)
  self.assertIn("textContent=sides[0].trim()",NEW)
  self.assertIn("textContent=sides[1].trim()",NEW)
  self.assertIn("textContent=match[1]",NEW)
  self.assertIn("./art/smackdown-arena-v1.svg",NEW)
 def test_data_and_output_safety_are_unchanged(self):
  self.assertNotIn("createElement('a')",NEW)
  self.assertIn("const rows=reportedRows(show,key,'matches')",NEW)
  self.assertIn("renderEditorialRecap(show,key)",NEW)
  self.assertIn("privateWcnRows(show,key,kind)",NEW)
  self.assertIn("recapRotationPage(key+'-recap',pages.length)",NEW)
  self.assertIn("rows.map((_,i)=>[i])",NEW)
  for name in ("reviewed-recaps.json","aaa-tv-week-cards-20261023.json",
               "wcn-match-cards-private.json","snapshot.json"):
   self.assertIn(name,NEW)
 def test_fallback_and_no_fake_photos(self):
  self.assertIn("masthead-img",NEW)
  self.assertIn("aria-hidden",NEW)
  self.assertNotIn("https://images.wwe.com",NEW)
if __name__=="__main__":unittest.main()
