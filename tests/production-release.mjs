import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,rm,stat,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {runInNewContext} from 'node:vm';
import {buildRelease} from '../proof/staging/build-release.mjs';
import {localPublishedFeed,PUBLISHED_FEED_ROOT} from '../proof/staging/local-published-feeds.mjs';

test('same-run local feeds take precedence and absent feeds cannot fall back to the old deployment',async()=>{
 const dir=await mkdtemp(join(tmpdir(),'isc-local-feeds-'));
 try{
  const snapshot={generated_at:'2026-10-31T21:00:00Z',shows:[{id:'tna',previous:{date:'2026-10-29'}}]};
  await writeFile(join(dir,'snapshot.json'),JSON.stringify(snapshot));
  assert.deepEqual(await (await localPublishedFeed(PUBLISHED_FEED_ROOT+'snapshot.json',dir)).json(),snapshot);
  assert.equal((await localPublishedFeed(PUBLISHED_FEED_ROOT+'tna-verified-results.json',dir)).status,404);
  assert.equal((await localPublishedFeed(PUBLISHED_FEED_ROOT+'../snapshot.json',dir)).status,404);
  assert.equal(await localPublishedFeed('https://www.wwe.com/shows/raw/results',dir),null);
 }finally{await rm(dir,{recursive:true,force:true});}
});

test('the main entry starts live playback under the GitHub project subpath',async()=>{
 const html=await readFile(new URL('../web/index.html',import.meta.url),'utf8');
 const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
 let destination;
 runInNewContext(script,{URL,URLSearchParams,location:{href:'https://broncos5523.github.io/Inside-the-squared-circle/?id=weekly-results-tna',search:'?id=weekly-results-tna',replace:value=>{destination=value;}}});
 assert.equal(destination,'https://broncos5523.github.io/Inside-the-squared-circle/staging/?view=tv&mode=active&id=weekly-results-tna');
 runInNewContext(script,{URL,URLSearchParams,location:{href:'https://broncos5523.github.io/Inside-the-squared-circle/?rotate=right',search:'?rotate=right',replace:value=>{destination=value;}}});
 assert.equal(new URL(destination).searchParams.get('rotate'),'right');
});

test('production result cards resolve the new artwork within the GitHub Pages subpath',async()=>{
 const root=new URL('../web/staging/',import.meta.url);
 const library=JSON.parse(await readFile(new URL('library.json',root),'utf8'));
 const routes=JSON.parse(await readFile(new URL('asset-routes.json',root),'utf8'));
 const data=JSON.parse(await readFile(new URL('fixtures/staging-programming-20261031.json',import.meta.url),'utf8'));
 const host={};
 runInNewContext(await readFile(new URL('board-adapter.js',root),'utf8'),{window:host,URL});
 const base='https://broncos5523.github.io/Inside-the-squared-circle/staging/';
 for(const [show,slug] of [['nxt','chantel-monroe'],['tna','agent-zero'],['aaa','big-mami']]){
  const row=library.records.find(r=>r.id==='weekly-results-'+show);
  const html=host.ISCBoardAdapter.build(await readFile(new URL(row.delivery,root),'utf8'),row,routes,base,'active',data.feeds);
  const config=JSON.parse(html.match(/<base[^>]*><script>[\s\S]*?\)\((\{"weeklyResults":[\s\S]*?)\);<\/script>/)[1]);
  assert.equal(config.base,base);
  assert.ok(config.resultPortraits[slug].startsWith(base+'originals/shared/'));
  assert.ok(!config.resultPortraits[slug].includes('raw.githubusercontent.com'));
 }
});

test('the Pages artifact contains all approved delivery boards and exact artwork without embedded source copies',async()=>{
 const temporary=await mkdtemp(join(tmpdir(),'isc-release-'));
 try{
  const data=JSON.parse(await readFile(new URL('../web/staging/data/programming.json',import.meta.url),'utf8'));
  const release=await buildRelease({output:join(temporary,'.pages-output'),now:new Date(data.generated_at)});
  assert.equal(release.boards,68);
  assert.equal(release.shared_assets,543);
  const library=JSON.parse(await readFile(new URL('../web/staging/library.json',import.meta.url),'utf8'));
  for(const record of library.records){
   const payload=await readFile(join(release.output,'staging/delivery/payloads',record.delivery_sha256+'.bin'));
   assert.deepEqual(payload,await readFile(join(release.output,'staging',record.delivery)));
  }
  assert.ok(release.active_boards.includes('weekly-results-tna'));
  for(const dir of ['boards','screens'])await assert.rejects(stat(join(release.output,'staging/originals',dir)),{code:'ENOENT'});
  assert.deepEqual(await readFile(join(release.output,'previous-display.html')),await readFile(new URL('../web/previous-display.html',import.meta.url)));
  await assert.rejects(buildRelease({output:join(temporary,'.pages-output'),now:new Date(Date.parse(data.generated_at)+7*3600000)}),/stale/);
 }finally{await rm(temporary,{recursive:true,force:true});}
});
