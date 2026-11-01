import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';

const root=new URL('../../web/staging/',import.meta.url);
const library=JSON.parse(await readFile(new URL('library.json',root),'utf8'));
const payloads=new Map();
for(const record of library.records){
 if(!record.source_available||!record.delivery)continue;
 const bytes=await readFile(new URL(record.delivery,root));
 const digest=createHash('sha256').update(bytes).digest('hex');
 if(digest!==record.delivery_sha256)throw Error('Delivery source changed: '+record.id);
 payloads.set(digest,bytes);
}
await mkdir(new URL('delivery/payloads/',root),{recursive:true});
for(const [digest,bytes] of payloads)await writeFile(new URL('delivery/payloads/'+digest+'.bin',root),bytes);
console.log(JSON.stringify({verified_payloads:payloads.size,format:'Exact approved delivery bytes; immutable URL; binary transport'}));
