import tempfile, unittest
from pathlib import Path
from PIL import Image, ImageDraw
from proof.make_champion_cutouts import HERO, build, crop_alpha, meaningful_transparency

def fake_foreground(img):
 out=img.convert("RGBA"); alpha=Image.new("L",img.size,0)
 ImageDraw.Draw(alpha).ellipse((img.width//6,14,img.width*5//6,img.height-8),fill=255)
 out.putalpha(alpha);return out

class ChampionCutoutTests(unittest.TestCase):
 def test_names_and_positions(self):
  self.assertEqual([r[0] for r in HERO],["chelsea green","sami zayn","trick williams"])
  self.assertEqual([r[3] for r in HERO],["left","center","right"])
 def test_alpha_must_be_meaningful(self):
  photo=Image.new("RGB",(260,390),"#335485")
  mask=fake_foreground(photo)
  self.assertTrue(meaningful_transparency(mask))
  self.assertTrue(meaningful_transparency(crop_alpha(mask)))
  self.assertFalse(meaningful_transparency(Image.new("RGBA",(260,390),"red")))
 def test_missing_source_is_not_replaced(self):
  with tempfile.TemporaryDirectory() as temp:
   out=build(Path(temp)/"out",segment=fake_foreground,image_dir=Path(temp)/"missing")
   self.assertTrue(all(a["status"]=="source_missing" for a in out["assets"]))
   self.assertFalse(list((Path(temp)/"out").glob("*.png")))
   self.assertTrue(out["no_roman_reigns_in_smackdown_hero"])
 def test_three_rgba_drafts_pending_quality_review(self):
  with tempfile.TemporaryDirectory() as temp:
   source=Path(temp)/"src";source.mkdir()
   for _,fname,_,_ in HERO:Image.new("RGB",(260,390),"#325685").save(source/fname)
   dest=Path(temp)/"out";out=build(dest,segment=fake_foreground,image_dir=source)
   self.assertEqual([x["status"] for x in out["assets"]],["draft_ready"]*3)
   self.assertFalse(out["is_final_gold_master"])
   for person,fname,cutout,pos in HERO:
    with Image.open(dest/cutout) as img:
     self.assertEqual(img.mode,"RGBA")
     self.assertTrue(meaningful_transparency(img))
   self.assertTrue(all(x["visual_approval"]=="required" for x in out["assets"]))
if __name__=="__main__":unittest.main()
