const assert=require('node:assert/strict'),fs=require('fs'),C=require('../core.js');
assert.equal(C.direction(101),'approaching');assert.equal(C.direction(-101),'receding');assert.equal(C.direction(100),'near-zero');assert.equal(C.direction(-100),'near-zero');
assert.equal(C.epoch(0),0);assert.equal(C.epoch(9),0);assert.equal(C.epoch(28),60);assert.equal(C.epoch(18.5),30);
const d=JSON.parse(fs.readFileSync(require('path').join(__dirname,'../data/observations.json')));
for(const s of d.stations)s.records=s.records.map(r=>({gps_seconds:d.gps_seconds[r[0]],prn:r[1],doppler_hz:r[2],direction:C.direction(r[2])}));
const epochs=[];
for(let i=0;i<61;i++){
 const links=C.selectLinks(d.stations,d.gps_seconds[i],null,'all');const unique=new Set();assert(links.length<=72);
 const availableStates=new Set(d.stations.filter(s=>C.recordsAt(s,d.gps_seconds[i]).length).map(s=>s.state));const renderedStates=new Set(links.map(l=>l.station.state));for(const state of availableStates)assert(renderedStates.has(state));epochs.push({epoch:i,links:links.length,states:renderedStates.size});
 assert(C.selectLinks(d.stations,d.gps_seconds[i],null,'all',true).length<=48);
 for(const l of links){assert.equal(l.record.gps_seconds,d.gps_seconds[i]);assert.equal(l.record.direction,C.direction(l.record.doppler_hz));const key=l.station.id+':'+l.record.prn;assert(!unique.has(key));unique.add(key)}
 const selected=C.selectLinks(d.stations,d.gps_seconds[i],null,'G01');assert(selected.length<=72);for(const l of selected)assert.equal(l.dimmed,l.record.prn!=='G01');
}
const s=d.stations[0],links=C.selectLinks(d.stations,d.gps_seconds[0],s.id,'all');assert.equal(links.filter(l=>l.station.id===s.id).length,C.recordsAt(s,d.gps_seconds[0]).length);
console.log('Passed: 61 synchronized epochs, measured sign colors, unique links, selection and timeline.');

fs.writeFileSync(require('path').join(__dirname,'../data/render-selection-qa.json'),JSON.stringify({passed:true,desktopLimit:72,mobileLimit:48,epochs},null,2)+'\n');
