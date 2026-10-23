"""Wikimedia exact-file intake: image licenses, redirects, size and safe fallback."""
from datetime import datetime,timezone
from pathlib import Path
import json,tempfile,unittest
from proof.approved_graphics import ASSETS, API, build, image_info, valid_image, fetch

PNG=b'\x89PNG\r\n\x1a\n'+b'\x00'*130
JPEG=b'\xff\xd8\xff'+b'\x00'*130+b'\xff\xd9'

def mockfetch(url):
 if url.startswith(API):
  from urllib.parse import urlsplit, parse_qs
  name=parse_qs(urlsplit(url).query)['titles'][0]
  entry=next(x for x in ASSETS if 'File:'+x['title']==name)
  fmt='png' if entry['file'].endswith('.png') else 'jpg'
  return json.dumps({'query':{'pages':[{'title':name,'imageinfo':[{
      'thumburl':'https://upload.wikimedia.org/test/'+entry['file'],
      'mime':'image/svg+xml' if entry['type']=='logo' else 'image/jpeg',
      'extmetadata':{'LicenseShortName':{'value':entry['license']}}}]}]}}).encode()
 if url.startswith('https://upload.wikimedia.org/test/'):
  return PNG if url.endswith('.png') else JPEG
 raise AssertionError('Unexpected mock fetch: '+url)

class ApprovedGraphicsTests(unittest.TestCase):
 def test_real_people_and_credit_are_exactly_mapped(self):
  self.assertEqual([x['id'] for x in ASSETS],
       ['smackdown','chelsea green','roxanne perez','giulia','alexa bliss','la knight','roman reigns','cody rhodes','sami zayn','trick williams'])
  self.assertTrue(all(x['source'].startswith('https://commons.wikimedia.org/wiki/File:') for x in ASSETS))
  self.assertTrue(all(x['license'] in {'CC BY 2.0','CC BY 4.0'} for x in ASSETS if x['type']=='portrait'))
 def test_exact_commons_license_verified_per_file(self):
  for entry in ASSETS:
   self.assertEqual(image_info(entry,mockfetch),'https://upload.wikimedia.org/test/'+entry['file'])
   valid_image(entry,PNG if entry['file'].endswith('.png') else JPEG)
 def test_reject_invalid_or_malicious_image_data(self):
  for item in ASSETS:
   with self.assertRaises(ValueError):valid_image(item,b'<html>wrong image</html>'*10)
  with self.assertRaises(ValueError):fetch('https://example.com/logo.png')
 def test_license_gate_fails_closed(self):
  def revoked(url):
   if url.startswith(API):
    val=json.loads(mockfetch(url))
    val['query']['pages'][0]['imageinfo'][0]['extmetadata']['LicenseShortName']['value']='All rights reserved'
    return json.dumps(val).encode()
   return mockfetch(url)
  with self.assertRaises(ValueError):image_info(ASSETS[1],revoked)
 def test_ingest_creates_ten_local_images_and_attribution_manifest(self):
  with tempfile.TemporaryDirectory() as temp:
   output=build(temp,mockfetch,datetime(2026,10,23,tzinfo=timezone.utc))
   self.assertEqual([r['status'] for r in output['assets']],['ready']*10)
   self.assertEqual(len(output['issues']),0)
   for r in output['assets']:
    self.assertTrue((Path(temp)/r['file']).exists())
    self.assertEqual(r['path'],'./assets/vetted/'+r['file'])
   self.assertEqual(json.loads((Path(temp)/'asset-manifest.json').read_text())['schema_version'],1)
 def test_missing_asset_never_gets_substituted_for_a_real_person(self):
  with tempfile.TemporaryDirectory() as temp:
   def outage(url):
    if 'Chelsea_Green' in url or 'chelsea-green.jpg' in url:raise OSError('blocked')
    return mockfetch(url)
   obj=build(temp,outage)
   chelsea=next(r for r in obj['assets'] if r['id']=='chelsea green')
   self.assertEqual(chelsea['status'],'unavailable')
   self.assertFalse((Path(temp)/'chelsea-green.jpg').exists())
   self.assertEqual(sum(a['status']=='ready' for a in obj['assets']),9)
if __name__=="__main__":unittest.main()
