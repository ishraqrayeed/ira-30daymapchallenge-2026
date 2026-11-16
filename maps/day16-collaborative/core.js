(function(root){
'use strict';
const colors={approaching:'#35D7F2',receding:'#FFB65C','near-zero':'#E9F1F7'};
function direction(hz,threshold=100){return Math.abs(hz)<=threshold?'near-zero':hz>0?'approaching':'receding'}
function epoch(t,n=61){return Math.min(n-1,Math.max(0,Math.floor((t-9)/19*(n-1)+1e-9)))}
function seeded(seed){return()=>{seed=(Math.imul(1664525,seed)+1013904223)|0;return(seed>>>0)/4294967296}}
function stage(t){return t<4?'01 / The invisible sky':t<9?'02 / America starts listening':t<17?'03 / One satellite, one receiver':t<23?'04 / The frequency changes':'05 / The final symphony'}
function rgb(hex){return[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255)}
function recordsAt(station,gps){return station.records.filter(r=>r.gps_seconds===gps)}
function selectLinks(stations,gps,stationID,satellite,mobile=false){
 const limit=mobile?48:72,links=[],keys=new Set(),candidates=[];
 const add=link=>{const key=link.station.id+':'+link.record.prn;if(!keys.has(key)&&links.length<limit){links.push(link);keys.add(key)}};
 stations.forEach((station,i)=>{const rows=recordsAt(station,gps).slice().sort((a,b)=>a.prn.localeCompare(b.prn));
 const wrap=record=>({station,record,dimmed:satellite!=='all'&&record.prn!==satellite});
 if(station.id===stationID)for(const row of rows)add(wrap(row));
 if(rows.length)candidates.push(wrap((satellite!=='all'&&rows.find(r=>r.prn===satellite))||rows[(i*3)%rows.length]));
 });
 // Rendering sample only: state representation, then geographical maximin.
 const distance=link=>Math.min(...links.map(c=>{const dy=link.station.lat-c.station.lat,dx=(link.station.lon-c.station.lon)*Math.cos((link.station.lat+c.station.lat)*Math.PI/360);return dx*dx+dy*dy}),Infinity);
 const best=rows=>{let chosen,score=-Infinity;for(const row of rows){const d=distance(row);if(!chosen||d>score||(d===score&&row.station.id<chosen.station.id)){chosen=row;score=d}}return chosen};
 const represented=new Set(links.map(l=>l.station.state));
 for(const state of [...new Set(candidates.map(l=>l.station.state))].sort())if(!represented.has(state)){const row=best(candidates.filter(l=>l.station.state===state));if(row)add(row);represented.add(state)}
 while(links.length<limit){const remaining=candidates.filter(l=>!links.some(c=>c.station.id===l.station.id));if(!remaining.length)break;add(best(remaining))}
 return links;
}
const api={colors,direction,epoch,seeded,stage,rgb,recordsAt,selectLinks};root.SymphonyCore=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window==='undefined'?globalThis:window);
