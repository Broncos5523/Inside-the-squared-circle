"""Private WCN real-card expansion without changing approved portrait styles."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD=(ROOT/"web/preview-v4-33-private-wcn.html").read_text(encoding="utf-8")
NEW=(ROOT/"web/preview-v4-34-private-wcn.html").read_text(encoding="utf-8")

class CardsAndAppearances(unittest.TestCase):
 def test_all_old_visuals_identical(self):
  self.assertEqual(OLD.split("<style>",1)[1].split("</style>",1)[0],
                   NEW.split("<style>",1)[1].split("</style>",1)[0])
  self.assertIn("DISPLAY BUILD 4.34",NEW)
  self.assertIn("#board{width:min(100vw,56.25dvh)",NEW)
 def test_wcn_source_is_local_only_and_attributed(self):
  for term in ("wcn-match-cards-private.json","PERSONAL_NONCOMMERCIAL_HOME_DISPLAY_ONLY",
               "Wrestling Central News (wrestlingcentralnews.com)",
               "m.evidence_url===url","m.status==='REPORTED_UNVERIFIED'",
               "kind==='matches'","m.type==='Advertised appearance'"):
   self.assertIn(term,NEW)
  self.assertNotIn("createElement('a')",NEW)
 def test_advance_card_appearances_and_fallback_results_rotate_every_item(self):
  self.assertIn("const page=recapRotationPage(key,pages)",NEW)
  self.assertIn("const page=recapRotationPage(key,rows.length)",NEW)
  self.assertIn("const page=recapRotationPage(key+'-results',rows.length)",NEW)
  for slots,want in ((["smackdown","smackdown-recap"],"smackdown"),
                     (["raw","raw-recap","nxt","nxt-recap","raw","raw-recap"],"raw"),
                     (["tna","tna-results"],"tna-results")):
   for count in (2,3,4,6,7):
    shown=[]
    for position in range(len(slots)*count):
     if slots[position%len(slots)]!=want:continue
     page=(position//len(slots)*slots.count(want)+slots[:position%len(slots)].count(want))%count
     shown.append(page)
    self.assertEqual(set(shown),set(range(count)),(slots,want,count))
if __name__=="__main__":unittest.main()
