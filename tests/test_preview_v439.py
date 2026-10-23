"""V4.39 broadcast-layout is new, real-content-driven and non-destructive."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD=(ROOT/"web/preview-v4-38-smackdown-broadcast-review.html").read_text()
NEW=(ROOT/"web/preview-v4-39-smackdown-full-broadcast.html").read_text()
class BroadcastProof(unittest.TestCase):
 def test_existing_layout_code_preserved(self):
  self.assertTrue(NEW.split("<style>",1)[1].split("</style>",1)[0].startswith(
                  OLD.split("<style>",1)[1].split("</style>",1)[0]))
  for marker in ("function renderSdShowcase(show,key)","function renderEditorialRecap(show,key)",
                 "function showReportedCard(show,key,evolve)","function privateWcnRows(show,key,kind)",
                 "aaa-tv-week-cards-20261023.json","wcn-match-cards-private.json"):
   self.assertIn(marker,NEW)
  self.assertIn("DISPLAY BUILD 4.39",NEW)
 def test_full_broadcast_structure_not_four_text_cards(self):
  for marker in ('id="sd-broadcast" hidden','bd-brand-plate','bd-logo-side left',
      'bd-logo-side right','id="bd-hero"','id="bd-primary"','id="bd-side"',
      'id="bd-others"','id="bd-notes"','id="bd-ticker"','id="bd-dates"',
      'grid-template-rows:17.5% 25.5% 5.8% 27.5% 12.5% 3% 6.3% 1.9%',
      'grid-template-columns:58% 42%','bd-photo.center',
      'bd-ring','bd-main-logo bd-gold'):
   self.assertIn(marker,NEW)
  # Standings is present only in historic CSS comments at most, never in the
  # newly added broadcast composition.
  markup=NEW.split('<section id="sd-broadcast"',1)[1].split("</section>\n</div>\n<script>",1)[0]
  self.assertNotIn("STANDINGS",markup.upper())
  self.assertNotIn("WIN–LOSS",markup.upper())
 def test_real_data_and_correct_photo_allowlist(self):
  for marker in ("const rows=reportedRows(show,key,'matches')",
                 "const appearances=reportedRows(show,key,'appearances')",
                 "const talent=sdNamedCompetitors(show,key)",
                 "const photo=sdApprovedPhoto(name)",
                 "const type=(featured.stipulation||'MATCH')",
                 "if(!rows.length)","if(appearances.length)",
                 "if(!forceBroadcast||key!=='smackdown')",):
   if marker=="if(!forceBroadcast||key!=='smackdown')":
    self.assertIn("const active=forceBroadcast&&key==='smackdown'",NEW)
   else:self.assertIn(marker,NEW)
  self.assertIn("SCHEDULE: TVMAZE · WRESTLER PHOTOS: DIEGO SERRANO / CC BY 2.0",NEW)
  self.assertNotIn("createElement('a')",NEW)
 def test_preserve_separate_review_and_old_pages(self):
  self.assertIn("const forceBroadcast=reviewParams.get('view')==='broadcast'&&requested==='smackdown'",NEW)
  self.assertIn("stage.hidden=!active",NEW)
  self.assertIn("renderSdBroadcast(show,key)",NEW)
  self.assertIn("sd-broadcast[hidden]",NEW)
  self.assertIn("url('./art/smackdown-arena-v1.svg')",NEW)
  self.assertIn("./assets/vetted/smackdown-mark.png",NEW)
 def test_runtime_build_version_not_stale(self):
  self.assertIn("put('timestamp',\x60DISPLAY BUILD 4.39 ·",NEW)
  self.assertNotIn("put('timestamp',\x60DISPLAY BUILD 4.31 ·",NEW)
if __name__=="__main__":unittest.main()
