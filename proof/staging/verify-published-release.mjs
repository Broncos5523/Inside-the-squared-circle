import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';

const output=new URL('../../.pages-output/',import.meta.url);
const base='https://broncos5523.github.io/Inside-the-squared-circle/';
const paths=['index.html','staging/release.json','staging/data/programming.json','staging/review.js','staging/board-adapter.js',
 'staging/originals/shared/38d20c88e02da1204f899dfed6d311dff8a7579d9e6f830127dfca6ce089f4ad.webp',
 'staging/originals/shared/a85eafc5364a482e2e18e3681f6910f157c3c9d3a3073baae37c96e279102186.png'];
const hash=value=>createHash('sha256').update(value).digest('hex');
const expected=new Map(await Promise.all(paths.map(async path=>[path,hash(await readFile(new URL(path,output)))])));
let lastError;
for(let attempt=0;attempt<8;attempt++){
 try{
  for(const path of paths){
   const url=new URL(path,base);url.searchParams.set('release',String(process.env.GITHUB_RUN_ID||Date.now()));
   const response=await fetch(url,{cache:'no-store',signal:AbortSignal.timeout(12000)});
   if(!response.ok||hash(Buffer.from(await response.arrayBuffer()))!==expected.get(path))throw Error('Published bytes do not match release: '+path);
  }
  console.log('Production entry, programming, playback code, and both new portraits match the verified artifact.');
  process.exit(0);
 }catch(error){lastError=error;if(attempt<7)await new Promise(resolve=>setTimeout(resolve,3000));}
}
throw lastError;
