const fs=require('fs'),assert=require('node:assert/strict');
const html=fs.readFileSync('web/preview-v4-37-smackdown-photo-showcase.html','utf8');
const a=html.indexOf("const sdPhotoOrder=['chelsea green'");
const b=html.indexOf("  function renderSdShowcase",a);
assert(a>0&&b>a);
const source=html.slice(a,b);
const matches=[
 {status:'REPORTED_UNVERIFIED',text:'Chelsea Green vs. Roxanne Perez'},
 {status:'REPORTED_UNVERIFIED',text:'Giulia vs. Blake Monroe'},
 {status:'REPORTED_UNVERIFIED',text:'Alexa Bliss & Tatum Paxley (c) vs. B-Fab & Michin (w/Jade Cargill)'},
 {status:'REPORTED_UNVERIFIED',text:'MFTs (Talla Tonga & Tama Tonga) (w/Haku) vs. Bakusai (Kyoki & Shinsuke Nakamura)'}
];
let gated=matches;
const roster=(new Function('reportedRows',source+'\nreturn sdNamedCompetitors;'))(()=>gated);
assert.deepEqual(roster({},'smackdown'),['chelsea green','roxanne perez','giulia','alexa bliss']);
assert.deepEqual(roster({},'raw'),[]);
gated=[{status:'REPORTED_UNVERIFIED',text:'Giulia vs. Chelsea Green (w/Alexa Bliss)'},
       {status:'REPORTED_UNVERIFIED',text:'Roxanne Perez vs. Blake Monroe'}];
assert.deepEqual(roster({},'smackdown'),['giulia','chelsea green','roxanne perez']);
gated=[{status:'UNREVIEWED',text:'Giulia vs. Roxanne Perez'}];
assert.deepEqual(roster({},'smackdown'),[]);
gated=[];assert.deepEqual(roster({},'smackdown'),[]);
const four=['chelsea green','roxanne perez','giulia','alexa bliss'];
const slides=Array.from({length:4},(_,i)=>[...four.slice(i),...four.slice(0,i)].slice(0,3));
assert.equal(new Set(slides.flat()).size,4);
console.log('V4.37 source-gated roster and rotations: PASS');
