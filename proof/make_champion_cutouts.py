"""Prepare transparent wrestler cutouts from licensed photographs.

Only removes background from source photos, not a generative wrestler model.
All outputs are unapproved drafts until hair, hands, torso, attire and edge
quality are visually checked. No cutout is substituted for another wrestler.
Dependencies: Pillow and rembg[cpu] (model u2net_human_seg).
"""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path

HERO=(
 ("chelsea green","chelsea-green.jpg","chelsea-green-cutout-draft.png","left"),
 ("sami zayn","sami-zayn.jpg","sami-zayn-cutout-draft.png","center"),
 ("trick williams","trick-williams.png","trick-williams-cutout-draft.png","right"),
)
SOURCE_DIR=Path("web/assets/vetted")

def meaningful_transparency(rgba):
 from PIL import Image
 alpha=rgba.convert("RGBA").getchannel("A")
 hist=alpha.histogram(); n=rgba.width*rgba.height
 return sum(hist[:22])/n>=.08 and .11<=sum(hist[90:])/n<=.93 and sum(hist[235:])/n>=.09

def crop_alpha(rgba,padding=18):
 from PIL import Image
 rgba=rgba.convert("RGBA")
 box=rgba.getchannel("A").getbbox()
 if not box:raise ValueError("Empty transparency mask")
 l,t,r,b=box
 rgba=rgba.crop((max(0,l-padding),max(0,t-padding),
                 min(rgba.width,r+padding),min(rgba.height,b+padding)))
 if rgba.width<90 or rgba.height<140:raise ValueError("Subject mask too small")
 return rgba

def build(out_dir,segment=None,image_dir=SOURCE_DIR,clock=None):
 from PIL import Image,ImageOps,ImageFilter
 out_dir=Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True)
 image_dir=Path(image_dir)
 if segment is None:
  from rembg import remove,new_session
  session=new_session("u2net_human_seg")
  segment=lambda original:remove(original,session=session)
 records=[]
 for name,filename,cutout,position in HERO:
  input_path=image_dir/filename;target=out_dir/cutout
  base={"person":name,"position":position,
    "source":"./assets/vetted/"+filename,
    "cutout":"./assets/graphics/smackdown/hero/"+cutout,
    "visual_approval":"required","is_advertised_appearance":False}
  if not input_path.is_file():
   target.unlink(missing_ok=True)
   records.append({**base,"status":"source_missing"});continue
  try:
   with Image.open(input_path) as photo:
    rgb=ImageOps.exif_transpose(photo).convert("RGB")
   if max(rgb.size)>1350:rgb.thumbnail((1350,1350),Image.Resampling.LANCZOS)
   mask=segment(rgb).convert("RGBA")
   mask.putalpha(mask.getchannel("A").filter(ImageFilter.GaussianBlur(.48)))
   if not meaningful_transparency(mask):raise ValueError("Opaque or empty result")
   result=crop_alpha(mask)
   if not meaningful_transparency(result):raise ValueError("Mask lost transparency after crop")
   tmp=target.with_suffix(".part.png")
   result.save(tmp,"PNG",optimize=True);tmp.replace(target)
   records.append({**base,"status":"draft_ready","width":result.width,"height":result.height})
  except Exception as exc:
   target.unlink(missing_ok=True)
   records.append({**base,"status":"segmentation_failed","reason":type(exc).__name__})
 manifest={"schema_version":1,"mode":"REAL_PHOTO_BACKGROUND_REMOVAL_DRAFTS",
  "generated_at":(clock or datetime.now(timezone.utc)).isoformat(),
  "is_final_gold_master":False,"no_roman_reigns_in_smackdown_hero":True,
  "method":"rembg human foreground segmentation; no image generation",
  "source_credit":"Chelsea Green and Sami Zayn: Diego Serrano CC BY 2.0; Trick Williams: Front Office Sports CC BY 4.0",
  "license_url_by_person":{"chelsea green":"https://creativecommons.org/licenses/by/2.0/",
                           "sami zayn":"https://creativecommons.org/licenses/by/2.0/",
                           "trick williams":"https://creativecommons.org/licenses/by/4.0/"},
  "assets":records}
 (out_dir/"cutout-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
 print("CHAMPION CUTOUT DRAFT:",[(x["person"],x["status"]) for x in records])
 return manifest

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--out",default="web/assets/graphics/smackdown/hero")
 args=p.parse_args()
 if Path(args.out).as_posix() not in ("web/assets/graphics/smackdown/hero","/tmp/hero-cutout-test"):
  p.error("Cutouts can only be written to review folders")
 manifest=build(args.out)
 if not all(r["status"]=="draft_ready" for r in manifest["assets"]):
  raise SystemExit("At least one cutout is unavailable; no fake replacement.")
if __name__=="__main__":main()
