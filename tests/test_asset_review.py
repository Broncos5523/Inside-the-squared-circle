import unittest
from pathlib import Path
DOC=(Path(__file__).resolve().parents[1]/'web/asset-review.html').read_text()
class AssetReviewTest(unittest.TestCase):
 def test_real_exact_photo_and_logo_inventory(self):
  self.assertIn('Authentic Asset Review',DOC)
  for f in ['smackdown-mark.png','chelsea-green.jpg','roxanne-perez.jpg','giulia.jpg','alexa-bliss.jpg']:
   self.assertIn(f,DOC)
  self.assertIn('2025 Royal Rumble · CC BY 2.0',DOC)
  self.assertIn('Source image not cached yet',DOC)
  self.assertIn('standalone checkerboard master emblem was rejected',DOC)
  self.assertNotIn('https://images.wwe.com',DOC)
 def test_logo_review_no_invented_rest_of_league_graphics(self):
  for x in ['RAW','NXT','TNA iMPACT!','AAA','Evolve']:
   self.assertIn(x,DOC)
  self.assertIn('not installed',DOC)
if __name__=='__main__':unittest.main()
