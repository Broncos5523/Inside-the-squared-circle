"""Import the recovered, hash-locked library without editing original board bytes."""
from pathlib import Path
import argparse, hashlib, json, shutil

def build(recovery: Path, destination: Path):
    source=recovery/'restored/private_public'
    original=json.loads((source/'review/manifest.json').read_text())
    routes=json.loads((recovery/'asset-routes.json').read_text())
    out=destination/'originals'
    records=[]
    for row in original['records']:
        r=dict(row)
        r['source_available']=bool(r.get('href') and r.get('original_sha256'))
        r['design_approved']=r.get('status')=='LOCKED'
        if r['source_available']:
            path=r['href'].split('?')[0]
            src=source/path.lstrip('/')
            assert hashlib.sha256(src.read_bytes()).hexdigest()==r['original_sha256'],r['id']
            target=out/path.lstrip('/');target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(src,target)
        if r.get('thumbnail'):
            target=destination/r['thumbnail'].lstrip('/');target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source/r['thumbnail'].lstrip('/'),target)
        records.append(r)
    for path in set(routes.values()):
        src=source/path.lstrip('/');target=out/path.lstrip('/')
        assert src.is_file(),path
        assert hashlib.sha256(src.read_bytes()).hexdigest()==src.stem,path
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target)
    destination.mkdir(parents=True,exist_ok=True)
    (destination/'asset-routes.json').write_text(json.dumps(routes,separators=(',',':'))+'\n')
    result={'project':original['project'],'source_date':original['date'],'slots':68,
            'source_slots':sum(r['source_available'] for r in records),
            'mapped_asset_routes':len(routes),'distinct_mapped_files':len(set(routes.values())),
            'records':records,'content_policy':'Archive review is separate from the source-verified active playlist. Final Evolve source is held.'}
    (destination/'library.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['slots','source_slots','mapped_asset_routes','distinct_mapped_files']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--recovery',type=Path,required=True);p.add_argument('--destination',type=Path,default=Path('web/staging'))
    a=p.parse_args();build(a.recovery,a.destination)
