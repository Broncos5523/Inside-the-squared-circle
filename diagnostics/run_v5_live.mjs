// Read-only, public-safe diagnostic: 9 limited WCN GET requests, counts only.
// Raw WCN source text is neither printed, uploaded nor committed.
import {readFileSync} from 'node:fs';
import {
  WCN_SHOW_INDEX, WCN_UPCOMING_URL, parseWcnShowIndex,
  parseWcnPageForEpisode, sourceAlignedShows
} from './wcn_parser_v5_staging.mjs';

const BASE = 'https://wrestlingcentralnews.com';
const SHOWS = ['raw', 'smackdown', 'nxt', 'tna'];
const now = new Date();
const nap = ms => new Promise(resolve => setTimeout(resolve, ms));
const report = (kind, value) => console.log('V5LIVE|' + kind + '|' + JSON.stringify(value));
const snapshot = JSON.parse(readFileSync('web/data/snapshot.json','utf8'));
let requestCount = 0;

async function readWcn(url) {
  if (++requestCount > 9) throw Error('WCN request safety limit');
  if (requestCount > 1) await nap(2000);
  if (!url.startsWith(BASE + '/')) throw Error('Not an authorized WCN URL');
  const abort = new AbortController();
  const timeout = setTimeout(() => abort.abort(), 15000);
  try {
    const res = await fetch(url, {
      redirect: 'error', signal: abort.signal,
      headers: {
        'User-Agent': 'InsideSquaredCirclePersonalHomeBoard/1.0 (diagnostic read-only)',
        'Accept': 'text/html'
      }
    });
    if (!res.ok) return {http: res.status, html: ''};
    if (Number(res.headers.get('content-length')||'0') > 1000000)
      return {http: 413, html: ''};
    const html = await res.text();
    return {http: html.length <= 1000000 ? res.status : 413,
      html: html.length <= 1000000 ? html : ''};
  } catch (err) {
    return {http: null, html: '', error: err?.name || 'NetworkError'};
  } finally {clearTimeout(timeout);}
}

report('run', {timestamp: now.toISOString(), mode: 'live-read-only',
  privacy: 'counts only; no publisher text logged'});
const upcoming = await readWcn(WCN_UPCOMING_URL);
report('upcoming', {http: upcoming.http, bytes: upcoming.html.length});
const rows = sourceAlignedShows(snapshot, upcoming.html, now);
let total = 0;
for (const show of SHOWS) {
  const row = rows.find(x => x.show_id === show);
  if (!row) {report('show', {show, error: 'no_fresh_schedule'}); continue;}
  const event = await readWcn(row.url);
  const eventCards = event.html ? parseWcnPageForEpisode(event.html,show,row.airdate) : {matches: [], appearances: []};
  const index = await readWcn(WCN_SHOW_INDEX[show]);
  const headlines = index.html ? parseWcnShowIndex(index.html,show,row.airdate,now) : [];
  total += eventCards.matches.length + headlines.length;
  report('show', {
    show, airdate: row.airdate,
    date_from_wcn_listing: row.schedule_source === 'wcn_upcoming_listing',
    snapshot_date_mismatch: row.date_mismatch,
    event_http: event.http,
    event_error: event.error || null,
    episode_event_matches: eventCards.matches.length,
    episode_event_appearances: eventCards.appearances.length,
    index_http: index.http,
    index_error: index.error || null,
    episode_headline_matches: headlines.length
  });
}
report('summary', {wcn_http_requests: requestCount, matches_extracted:total,
  data_was_collected_from_live_source: true,
  private_delivery_tested: false, fire_tv_tested: false,
  caution: 'candidate count, not a result or official confirmation'});
