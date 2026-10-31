import {readFile,stat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const root=new URL('../../web/staging/',import.meta.url);
const library=JSON.parse(await readFile(new URL('library.json',root),'utf8'));
const routes=JSON.parse(await readFile(new URL('asset-routes.json',root),'utf8'));
let html=0,assets=0;
for(const row of library.records){
 if(!row.source_available)continue;
 const path='originals'+row.href.split('?')[0];
 const bytes=await readFile(new URL(path,root));
 if(createHash('sha256').update(bytes).digest('hex')!==row.original_sha256)throw Error('Original HTML hash mismatch: '+row.id);
 if(row.delivery){const delivered=await readFile(new URL(row.delivery,root));if(createHash('sha256').update(delivered).digest('hex')!==row.delivery_sha256)throw Error('Delivery HTML hash mismatch: '+row.id);}
 html++;
}
const embedded=JSON.parse(await readFile(new URL('delivery-assets.json',root),'utf8'));
for(const item of embedded.assets){const bytes=await readFile(new URL(item.path,root));if(createHash('sha256').update(bytes).digest('hex')!==item.sha256)throw Error('Decoded asset bytes changed: '+item.path);}
for(const path of new Set(Object.values(routes))){
 const bytes=await readFile(new URL('originals'+path,root));
 const expected=path.split('/').pop().split('.')[0];
 if(createHash('sha256').update(bytes).digest('hex')!==expected)throw Error('Original artwork hash mismatch: '+path);
 assets++;
}
if(library.records.length!==68||html!==67||assets!==530||Object.keys(routes).length!==1585)throw Error('Source inventory changed unexpectedly');
console.log(JSON.stringify({planned_slots:68,source_backed_slots:html,unchanged_shared_files:assets,asset_routes:Object.keys(routes).length,final_evolve_held:true}));
