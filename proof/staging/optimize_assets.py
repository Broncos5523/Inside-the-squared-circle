"""Decode embedded asset bytes for cached delivery; preserve locked source HTML."""
from pathlib import Path
import base64, hashlib, json, re

root=Path(__file__).resolve().parents[2]/'web/staging'
library=json.loads((root/'library.json').read_text())
pattern=re.compile(r'data:([\w.+-]+/[\w.+-]+);base64,([A-Za-z0-9+/=]{256,})')
extensions={'image/png':'png','image/jpeg':'jpg','image/webp':'webp','image/gif':'gif','image/svg+xml':'svg','font/woff2':'woff2','font/woff':'woff','font/ttf':'ttf','application/font-woff':'woff','application/x-font-ttf':'ttf'}
assets={};done={};original_bytes=0;delivery_bytes=0
for row in library['records']:
    if not row['source_available']:continue
    logical=row['href'].split('?')[0].lstrip('/')
    if logical not in done:
        original=(root/'originals'/logical).read_bytes()
        assert hashlib.sha256(original).hexdigest()==row['original_sha256']
        def replace(match):
            mime=match.group(1)
            if mime not in extensions:return match.group(0)
            try:raw=base64.b64decode(match.group(2),validate=True)
            except ValueError:return match.group(0)
            digest=hashlib.sha256(raw).hexdigest();filename=digest+'.'+extensions[mime]
            shared=root/'originals/shared'/filename
            relative='originals/shared/'+filename if shared.exists() else 'originals/embedded/'+filename
            path=root/relative
            if not path.exists():path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
            assets.setdefault(relative,{'path':relative,'sha256':digest,'size':len(raw),'mime_type':mime,'occurrences':0})['occurrences']+=1
            return '__ISC_BASE__'+relative
        text=pattern.sub(replace,original.decode('utf8'))
        target=root/'delivery'/logical;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
        result={'path':'delivery/'+logical,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'size':target.stat().st_size}
        done[logical]=result;original_bytes+=len(original);delivery_bytes+=result['size']
    row['delivery']=done[logical]['path'];row['delivery_sha256']=done[logical]['sha256']
library['delivery_policy']='Only embedded asset URL delivery changes. Every decoded image/font byte matches its hash; original locked HTML remains unchanged.'
(root/'library.json').write_text(json.dumps(library,indent=2)+'\n')
manifest={'original_unique_html_bytes':original_bytes,'delivery_html_bytes':delivery_bytes,'assets':list(assets.values())}
(root/'delivery-assets.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'original_html_bytes':original_bytes,'delivery_html_bytes':delivery_bytes,'unique_embedded_assets':len(assets),'asset_bytes':sum(x['size'] for x in assets.values()),'new_asset_bytes':sum(x['size'] for x in assets.values() if '/embedded/' in x['path'])}))
