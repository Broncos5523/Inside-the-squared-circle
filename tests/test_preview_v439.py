"""V4.39: actual broadcast layout backed by the existing vetted data."""
import unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
OLD=(R/'web/preview-v4-38-smackdown-broadcast-review.html').read_text()
NEW=(R/'web/preview-v4-39-reference-broadcast.html').read_text()
def css(s):return s.split('<style>',1)[1].split('</style>',1)[0]
class ReferenceBroadcast(unittest.TestCase):
 def test_existing_styles_and_version(self):
  self.assertTrue(css(NEW).startswith(css(OLD)))
  self.assertIn('DISPLAY BUILD 4.39',NEW)
  self.assertIn('#board{width:min(100vw,56.25dvh)',NEW)
  self.assertIn('#board.bc-active #bc{display:grid',NEW)
 def test_reference_layout_is_nontoken_dense(self):
  for p in [
    'MAN CAVE <span>SPORTS BOOK</span><em>PRESENTS</em>',
    'INSIDE THE<strong>SQUARED CIRCLE</strong>',
    'When the bell rings, it gets real.',
    'id="bc-people"','id="bc-now"','id="bc-venue"',
    'OTHER REPORTED MATCHES',"LAST WEEK'S FALLOUT",
    'UPCOMING WEEKLY WRESTLING','id="bc-schedule"','bc-ticker',
    'grid-template-rows:17cqh 27cqh 6.4cqh minmax(0,1fr) 9.2cqh 3.5cqh']:
   self.assertIn(p,NEW)
  self.assertNotIn('SMACKDOWN STANDINGS',NEW)
 def test_exact_source_integrations_not_fiction(self):
  for p in [
    "forceBroadcast=reviewParams.get('view')==='broadcast'&&requested==='smackdown'",
    "if(forceBroadcast&&keys.length===1)return [keys[0]]",
    "reportedRows(show,'smackdown','matches')",
    "reportedRows(show,'smackdown','appearances')",
    "editorialRecap(show,'smackdown')","REPORTED_UNVERIFIED",
    "sdApprovedPhoto(name)","renderBroadcast(show)",
    "const rest=rows.filter((_,i)=>i!==page).slice(0,3)"]:
   self.assertIn(p,NEW)
 def test_rights_and_logo_integrity(self):
  for p in ['src="./assets/vetted/smackdown-mark.png"','bc-person',
            'mask-image:radial-gradient','Diego Serrano / CC BY 2.0',
            'wcn-match-cards-private.json']:
   self.assertIn(p,NEW)
  self.assertNotIn("createElement('a')",NEW)
  self.assertNotIn('Roman Reigns vs. LA Knight',NEW)
  self.assertNotIn('Inside the Squared Circle Emblem.png',NEW)
if __name__=='__main__':unittest.main()
