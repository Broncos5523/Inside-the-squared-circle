import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

export const PUBLISHED_FEED_ROOT='https://broncos5523.github.io/Inside-the-squared-circle/data/';

// During the Pages job, use the schedules just collected by that same job.
// An absent local feed stays absent; fetching the previous deployment would
// silently replace a fresh collection with older data.
export async function localPublishedFeed(url,directory){
 if(!directory||!String(url).startsWith(PUBLISHED_FEED_ROOT))return null;
 const filename=String(url).slice(PUBLISHED_FEED_ROOT.length);
 if(!/^[a-z0-9-]+\.json$/.test(filename))return new Response('{}',{status:404});
 try{
  const bytes=await readFile(resolve(directory,filename));
  return new Response(bytes,{headers:{'Content-Type':'application/json'}});
 }catch(error){
  if(error.code!=='ENOENT')throw error;
  return new Response('{}',{status:404});
 }
}
