import {cp,mkdir,readFile,rm,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {basename,join,relative,resolve,sep} from 'node:path';
import playlist from '../../web/staging/playlist-engine.js';

const project=fileURLToPath(new URL('../../',import.meta.url));
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');

export async function buildRelease({output=join(project,'.pages-output'),now=new Date()}={}){
 output=resolve(output);
 if(basename(output)!=='.pages-output')throw Error('Release output must be a dedicated .pages-output directory');
 const web=join(project,'web'),originals=join(web,'staging/originals');
 const programming=JSON.parse(await readFile(join(web,'staging/data/programming.json'),'utf8'));
 const age=now.getTime()-Date.parse(programming.generated_at||'');
 if(!Number.isFinite(age)||age< -300000||age>6*3600000)throw Error('Production programming is stale');
 const active=playlist.select(programming.entries,now);
 if(!active.length)throw Error('No current source-backed boards are ready for production');
 await rm(output,{recursive:true,force:true});
 await cp(web,output,{recursive:true,filter(path){
  const nested=relative(originals,path);
  if(nested===''||nested.startsWith('..'+sep)||nested==='..')return true;
  return nested==='shared'||nested.startsWith('shared'+sep);
 }});
 const library=JSON.parse(await readFile(join(output,'staging/library.json'),'utf8'));
 const routes=JSON.parse(await readFile(join(output,'staging/asset-routes.json'),'utf8'));
 for(const record of library.records){
  if(!record.delivery)throw Error('Missing delivery source: '+record.id);
  const bytes=await readFile(join(output,'staging',record.delivery));
  if(hash(bytes)!==record.delivery_sha256)throw Error('Packaged board changed: '+record.id);
  const payload=await readFile(join(output,'staging/delivery/payloads',record.delivery_sha256+'.bin'));
  if(!payload.equals(bytes))throw Error('Packaged delivery payload changed: '+record.id);
 }
 for(const path of new Set(Object.values(routes))){
  const bytes=await readFile(join(output,'staging/originals'+path));
  if(hash(bytes)!==basename(path).split('.')[0])throw Error('Packaged artwork changed: '+path);
 }
 const release={schema_version:1,source_sha:execFileSync('git',['rev-parse','HEAD'],{cwd:project,encoding:'utf8'}).trim(),built_at:new Date().toISOString(),programming_generated_at:programming.generated_at,boards:library.records.length,shared_assets:new Set(Object.values(routes)).size,active_boards:active.map(x=>x.id)};
 await mkdir(join(output,'staging'),{recursive:true});
 await writeFile(join(output,'staging/release.json'),JSON.stringify(release,null,2)+'\n');
 await writeFile(join(output,'.nojekyll'),'');
 return {output,...release};
}

if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))console.log(JSON.stringify(await buildRelease()));
