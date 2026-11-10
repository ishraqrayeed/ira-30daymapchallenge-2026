'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const G=require('./geo.js');
const close=(a,b,tol=1e-9)=>assert(Math.abs(a-b)<tol,`${a} != ${b}`);
const fixtures=[['Dhaka',24.0057,90.3911,-24.0057,-89.6089],['Denver',39.7392,-104.9903,-39.7392,75.0097],['London',51.5074,-.1278,-51.5074,179.8722],['Equator',0,0,0,-180],['East dateline',12,179.999,-12,-.001],['West dateline',-12,-179.999,12,.001],['North pole',90,45,-90,-135],['South pole',-90,-180,90,0]];
for(const [name,lat,lon,a,b]of fixtures){const actual=G.antipode(lat,lon);close(actual.lat,a);close(actual.lon,b);console.log(`PASS ${name}: ${actual.lat}, ${actual.lon}`);}
let count=0;
for(let lat=-90;lat<=90;lat+=5)for(let lon=-540;lon<=540;lon+=5){const a=G.antipode(lat,lon),twice=G.antipode(a.lat,a.lon);close(twice.lat,lat);close(G.normalize(twice.lon-lon),0);assert(a.lon>=-180&&a.lon<180);const v=G.vector(lat,lon),w=G.vector(a.lat,a.lon);close(v.reduce((s,x,i)=>s+x*w[i],0),-1);const start=G.tunnel(lat,lon,0),end=G.tunnel(lat,lon,1),expected=G.vector(a.lat,a.lon).map(v=>6371000*v);for(let i=0;i<3;i++){close(end[i],expected[i],1e-7);close(G.tunnel(lat,lon,.5)[i],0);}close(Math.hypot(...start.map((x,i)=>x-end[i])),12742000,1e-7);const p=G.sectionPoint(lat,lon,.5);close(p.x,0);close(p.y,0);const p0=G.sectionPoint(lat,lon,0),p1=G.sectionPoint(lat,lon,1);close(p0.x,-p1.x);close(p0.y,-p1.y);count++;}
const read=n=>JSON.parse(fs.readFileSync(path.join(__dirname,'data',n+'.geojson'))),countries=read('admin_0_countries'),marine=read('geography_marine_polys');
for(const [lat,lon,name]of [[24.0057,90.3911,'South Pacific Ocean'],[39.7392,-104.9903,'INDIAN OCEAN']]){const a=G.antipode(lat,lon);assert.equal(G.classify(a.lat,a.lon,countries,marine).name,name);}
assert.equal(G.classify(39,-105,countries,marine).name,'United States of America');
assert.deepEqual(G.classify(0,181,countries,marine),G.classify(0,-179,countries,marine));
for(const [,lat,lon]of G.presets){const a=G.antipode(lat,lon);assert.notEqual(G.classify(a.lat,a.lon,countries,marine).name,'Unclassified waters / coastal area');}
assert.throws(()=>G.antipode(91,0),RangeError);assert.throws(()=>G.antipode(0,NaN),RangeError);
console.log(`PASS ${count} global / wrapped-coordinate cases: involution, 180° separation, diameter, center and rendered section projection. Country/ocean and five preset checks passed.`);
