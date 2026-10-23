const fs=require('node:fs'),assert=require('node:assert/strict');
const html=fs.readFileSync('web/preview-v4-39-reference-broadcast.html','utf8');
const i=html.indexOf('function bcNames(rows)');
const j=html.indexOf('  function renderBroadcast(show)',i);
assert(i>0&&j>i);
const pick=new Function('sdPhotoOrder',html.slice(i,j)+'\nreturn bcNames;')(
 ['chelsea green','roxanne perez','giulia','alexa bliss']);
const cards=[
 {status:'REPORTED_UNVERIFIED',text:'Chelsea Green vs. Roxanne Perez'},
 {status:'REPORTED_UNVERIFIED',text:'Giulia vs. Blake Monroe'},
 {status:'REPORTED_UNVERIFIED',text:'Alexa Bliss & Tatum Paxley (c) vs. B-Fab & Michin (w/Jade Cargill)'}
];
assert.deepEqual(pick(cards),['chelsea green','roxanne perez','giulia','alexa bliss']);
assert.deepEqual(pick([{status:'REPORTED_UNVERIFIED',text:'Giulia vs. Roxanne Perez (w/Alexa Bliss)'}]),['giulia','roxanne perez']);
assert.deepEqual(pick([{status:'UNREVIEWED',text:'Giulia vs. Chelsea Green'}]),[]);
assert.deepEqual(pick([]),[]);
console.log('V4.39 date-gated correct wrestler selection PASS');
