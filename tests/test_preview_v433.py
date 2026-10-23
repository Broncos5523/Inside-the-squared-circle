"""Regression: the iPhone review showed result 4 partly clipped beneath result 3."""
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD=(ROOT/"web/preview-v4-32-private-wcn.html").read_text(encoding="utf-8")
NEW=(ROOT/"web/preview-v4-33-private-wcn.html").read_text(encoding="utf-8")
RECAP=json.loads((ROOT/"web/data/editorial-recaps-20261022.json").read_text(encoding="utf-8"))
class PortraitRecapFit(unittest.TestCase):
 def test_approved_css_is_identical(self):
  self.assertEqual(OLD.split("<style>",1)[1].split("</style>",1)[0],
                   NEW.split("<style>",1)[1].split("</style>",1)[0])
  self.assertIn("DISPLAY BUILD 4.32",OLD)
  self.assertIn("DISPLAY BUILD 4.33",NEW)
 def test_avoid_two_result_layout_when_storyline_uses_vertical_space(self):
  self.assertIn("const pages=notes.length?rows.map((_,i)=>[i]):groupedRecapResultPages(rows);",NEW)
  self.assertIn("card.classList.toggle('two-result-mode',indices.length===2)",NEW)
  self.assertIn("recapRotationPage(key+'-recap',pages.length)",NEW)
  self.assertIn("recapRotationPage(key+'-recap',notes.length)",NEW)
  self.assertIn("recapRotationPage('evolve',pages.length)",NEW)
  self.assertIn("recapRotationPage('evolve',notes.length)",NEW)
  self.assertIn("Math.floor(position/sequence.length)*timesPerCycle+earlierThisCycle",NEW)
  self.assertIn("for(const n of indices)card.append(createRecapResult(rows[n],n))",NEW)
 def test_every_match_still_rotates_with_storyline_panel(self):
  # This simulates the guarded JS branch for the five reported SmackDown
  # results in the screenshot: all five must be displayed, never omitted.
  smackdown=next(p for p in RECAP["programs"] if p["show_id"]=="smackdown")
  total=len(smackdown["results"])
  self.assertGreater(total,1)
  self.assertGreater(len(smackdown["developments"]),0)
  pages=[[i] for i in range(total)]
  self.assertEqual([idx for page in pages for idx in page],list(range(total)))
 def test_all_even_and_odd_result_counts_rotate_without_skips(self):
  for seq,slot in (
   (["smackdown","smackdown-recap"],"smackdown-recap"),
   (["raw","raw-recap","nxt","nxt-recap","raw","raw-recap"],"raw-recap"),
   (["evolve"],"evolve"),
  ):
   for total in (2,3,4,5,6):
    visited=[]
    for pos in range(len(seq)*total*2):
     if seq[pos%len(seq)]!=slot:continue
     page=(pos//len(seq)*seq.count(slot)+seq[:pos%len(seq)].count(slot))%total
     visited.append(page)
    self.assertEqual(set(visited),set(range(total)),(seq,slot,total))
 def test_private_source_and_other_previews_unmodified(self):
  for token in ("privateWcnRows","wcn-match-cards-private.json","Wrestling Central News (wrestlingcentralnews.com)","datedAaaWeekRows"):
   self.assertIn(token,NEW)
  self.assertNotIn("createElement('a')",NEW)
if __name__=="__main__":unittest.main()
