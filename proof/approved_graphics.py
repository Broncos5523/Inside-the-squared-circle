"""Retrieve an exact, license-checked Wikimedia logo and wrestler-photo starter pack.

No guessing: only named Commons files with independently inspected license pages.
Output is local/same-origin web assets. If a source fails, do not substitute
another photo or auto-promote an unknown image. No hotlinked Wikimedia content.

Usage: python -m proof.approved_graphics --out web/assets/vetted
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from datetime import datetime, timezone

API="https://commons.wikimedia.org/w/api.php"
USER_AGENT="ManCaveInsideSquaredCirclePersonalBoard/1.0 (license-reviewed image cache)"
ASSETS=(
 {"id":"smackdown","type":"logo","title":"WWE SmackDown (2024) Logo.svg",
  "file":"smackdown-mark.png","license":"Public domain","artist":"AJKelley / WWE logo design",
  "credit":"SmackDown identifying mark (trademark of WWE)",
  "source":"https://commons.wikimedia.org/wiki/File:WWE_SmackDown_(2024)_Logo.svg"},
 {"id":"chelsea green","type":"portrait","title":"Chelsea Green RR25 (2).jpg",
  "file":"chelsea-green.jpg","license":"CC BY 2.0","artist":"Diego Serrano",
  "credit":"Diego Serrano / CC BY 2.0",
  "source":"https://commons.wikimedia.org/wiki/File:Chelsea_Green_RR25_(2).jpg"},
 {"id":"roxanne perez","type":"portrait","title":"Roxanne Perez RR25.jpg",
  "file":"roxanne-perez.jpg","license":"CC BY 2.0","artist":"Diego Serrano",
  "credit":"Diego Serrano / CC BY 2.0",
  "source":"https://commons.wikimedia.org/wiki/File:Roxanne_Perez_RR25.jpg"},
 {"id":"giulia","type":"portrait","title":"Giulia RR25.jpg",
  "file":"giulia.jpg","license":"CC BY 2.0","artist":"Diego Serrano",
  "credit":"Diego Serrano / CC BY 2.0",
  "source":"https://commons.wikimedia.org/wiki/File:Giulia_RR25.jpg"},
 {"id":"alexa bliss","type":"portrait","title":"Alexa Bliss RR25 (1).jpg",
  "file":"alexa-bliss.jpg","license":"CC BY 2.0","artist":"Diego Serrano",
  "credit":"Diego Serrano / CC BY 2.0",
  "source":"https://commons.wikimedia.org/wiki/File:Alexa_Bliss_RR25_(1).jpg"},
)
LIMIT_BYTES=2_100_000

def fetch(url):
 p=urlsplit(url)
 if p.scheme!="https" or p.hostname not in {"commons.wikimedia.org","upload.wikimedia.org"}:
  raise ValueError("Host outside the Wikimedia Commons / upload allowlist")
 req=Request(url,headers={"User-Agent":USER_AGENT,"Accept":"application/json,image/*"})
 with urlopen(req,timeout=22) as response:
  final=urlsplit(response.geturl())
  if final.scheme!="https" or final.hostname not in {"commons.wikimedia.org","upload.wikimedia.org"}:
   raise ValueError("Wikimedia redirect outside host allowlist")
  b=response.read(LIMIT_BYTES+1)
 if len(b)>LIMIT_BYTES:raise ValueError("Image exceeds 2.1 MB download cap")
 return b

def image_info(asset,fetcher=fetch):
 query=urlencode({"action":"query","format":"json","formatversion":"2",
  "prop":"imageinfo","titles":"File:"+asset["title"],
  "iiprop":"url|mime|size|extmetadata","iiurlwidth":"620"})
 obj=json.loads(fetcher(API+"?"+query))
 pages=obj.get("query",{}).get("pages",[])
 if len(pages)!=1 or pages[0].get("missing") or not pages[0].get("imageinfo"):
  raise ValueError("Wikimedia exact file not found")
 page=pages[0]
 if page.get("title","").replace("_"," ").casefold()!=("File:"+asset["title"]).casefold():
  raise ValueError("Different file returned from Commons")
 info=page["imageinfo"][0]
 license_name=re.sub(r"<[^>]*>","",info.get("extmetadata",{}).get("LicenseShortName",{}).get("value",""))
 if license_name.casefold()!=asset["license"].casefold():
  raise ValueError("Wikimedia license mismatch for "+asset["id"]+": "+license_name)
 url=info.get("thumburl","")
 if urlsplit(url).hostname!="upload.wikimedia.org" or urlsplit(url).scheme!="https":
  raise ValueError("Missing trusted Wikimedia thumbnail for "+asset["id"])
 suffix=urlsplit(url).path.lower()
 expected=".png" if asset["type"]=="logo" else ".jpg"
 if not suffix.endswith(expected):raise ValueError("Unexpected image extension for "+asset["id"])
 return url

def valid_image(asset,data):
 if len(data)<100 or len(data)>LIMIT_BYTES:raise ValueError("Downloaded asset size invalid")
 if asset["type"]=="logo":
  if not data.startswith(b"\x89PNG\r\n\x1a\n"):raise ValueError("Expected PNG logo thumbnail")
 else:
  if not (data.startswith(b"\xff\xd8\xff") and data.endswith(b"\xff\xd9")):
   raise ValueError("Expected JPEG wrestler portrait")
 return True

def build(out_dir,fetcher=fetch,clock=None):
 dest=Path(out_dir)
 dest.mkdir(parents=True,exist_ok=True)
 saved=[];issues=[]
 for entry in ASSETS:
  path=dest/entry["file"]
  if path.exists():
   try:
    valid_image(entry,path.read_bytes())
    saved.append({**entry,"path":"./assets/vetted/"+entry["file"],"status":"ready"})
    continue
   except (OSError,ValueError):path.unlink(missing_ok=True)
  try:
   url=image_info(entry,fetcher)
   payload=fetcher(url)
   valid_image(entry,payload)
   tmp=path.with_name(path.name+".part")
   tmp.write_bytes(payload);tmp.replace(path)
   saved.append({**entry,"path":"./assets/vetted/"+entry["file"],"status":"ready"})
  except Exception as exc:
   # No substitute, no image misinformation, and no build outage due to
   # a rate-limited external thumbnail service.
   issues.append({"id":entry["id"],"reason":type(exc).__name__})
   saved.append({**entry,"status":"unavailable"})
 manifest={"schema_version":1,"mode":"COMMONS_REVIEWED_WRESTLING_VISUAL_ASSETS",
   "collected_at":(clock or datetime.now(timezone.utc)).isoformat(),
   "usage":"attributed_wrestling_broadcast_identification",
   "assets":saved,"issues":issues}
 (dest/"asset-manifest.json").write_text(
  json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("VETTED ASSET INGEST",len([x for x in saved if x["status"]=="ready"]),
       "ready",len(issues),"missing; fallbacks stay intact")
 return manifest

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--out",default="web/assets/vetted")
 args=p.parse_args()
 if Path(args.out).as_posix() not in {"web/assets/vetted","/tmp/vetted-assets"}:
  p.error("Approved graphics must stay in the vetted asset folder")
 build(args.out)

if __name__=="__main__":main()
