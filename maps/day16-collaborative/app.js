import {createEarth} from './earth.js';
const $=id=>document.getElementById(id),C=SymphonyCore,mobile=()=>innerWidth<700,motion=matchMedia('(prefers-reduced-motion: reduce)');
const state=window.Symphony={ready:false,time:motion.matches?28:0,paused:motion.matches,ambientTime:0,playbackRate:5,index:0,selectedStation:null,selectedSatellite:'all',errors:[],frames:0};
let data,map,earth,particle,raf,last=0,lastSample=-1,lastPaint=-1,currentLinks=[],chartStation,chartSatellite,userMap=false;
function sync(){ $('play').textContent=state.paused?'Play':'Pause';$('play').setAttribute('aria-pressed',String(!state.paused));$('timeline').value=state.time;$('elapsed').textContent='0:'+String(Math.floor(state.time/state.playbackRate)).padStart(2,'0');}
function stop(){state.paused=true;cancelAnimationFrame(raf);last=0;sync()}
function play(){if(!state.ready)return;state.paused=false;last=0;sync();raf=requestAnimationFrame(frame)}
function seek(t){stop();state.time=Math.max(0,Math.min(28,t));state.ambientTime=0;update(true);if(state.time===28&&!motion.matches)play()}
function frame(now){if(state.paused)return;const dt=last?Math.min(.1,(now-last)/1000):0;last=now;if(state.time<28)state.time=Math.min(28,state.time+dt*state.playbackRate);else state.ambientTime+=dt;state.frames++;update();raf=requestAnimationFrame(frame)}
function fit(){
 const padding={left:18,right:18,top:18,bottom:55};
 map.fitBounds([[-124.8,24.5],[-66.9,49.5]],{padding,duration:0});
}
function stationFeatures(){return {type:'FeatureCollection',features:data.stations.map((s,i)=>({type:'Feature',properties:{id:s.id,birth:4+i/Math.max(1,data.stations.length-1)*4.5},geometry:{type:'Point',coordinates:[s.lon,s.lat]}}))}}
function makeRoute(link,i){
 const s=link.station,r=link.record,p=maplibregl.MercatorCoordinate.fromLngLat([s.lon,s.lat]),az=r.azimuth_deg*Math.PI/180;
 // Endpoints are local visual sky directions; no sub-satellite points on this map.
 const length=(.012+.025*(1-r.elevation_deg/90)),dx=Math.sin(az)*length,dy=-Math.cos(az)*length;
 const sky=[p.x+dx,p.y+dy],bend=(Number(r.prn.slice(1))%2?1:-1)*length*.23,control=[p.x+dx*.5-dy/length*bend,p.y+dy*.5+dx/length*bend];
 const samples=[],coords=[];for(let j=0;j<256;j++){const t=j/255,u=1-t,x=u*u*sky[0]+2*u*t*control[0]+t*t*p.x,y=u*u*sky[1]+2*u*t*control[1]+t*t*p.y;samples.push(x,y);const ll=new maplibregl.MercatorCoordinate(x,y).toLngLat();coords.push([ll.lng,ll.lat])}
 return {id:i,samples,length_km:length*40075,color:C.rgb(C.colors[r.direction]).map(v=>v*(link.dimmed?.12:1)),feature:{type:'Feature',properties:{color:C.colors[r.direction],opacity:link.dimmed?.08:1,selected:state.selectedStation===s.id?1:0},geometry:{type:'LineString',coordinates:coords}}};
}
function rebuild(){
 const gps=data.gps_seconds[state.index];currentLinks=C.selectLinks(data.stations,gps,state.selectedStation,state.selectedSatellite,mobile());
 const routes=currentLinks.map(makeRoute);
 map.getSource('links').setData({type:'FeatureCollection',features:routes.map(r=>r.feature)});
 if(particle){map.removeLayer('gnss-particles');particle=null}
 if(routes.length){try{particle=new SymphonyParticles(routes,state,mobile());map.addLayer(particle,'station-halo')}catch(e){state.errors.push(e.message);$('status').textContent='Particle effects unavailable; measured geographic links remain visible.'}}
 const shown=state.time>=9?currentLinks.length:0;state.illustratedLinks=shown;
 $('timestamp').textContent=data.times_utc[state.index].replace('T',' · ').replace('Z',' UTC');
 $('network').textContent=data.stations.length+' selected NOAA GNSS stations · '+new Set(data.stations.map(s=>s.state).filter(Boolean)).size+' states · '+shown+' links';
 const earthLinks=state.time<9?[]:currentLinks.filter(l=>!state.selectedStation||l.station.id===state.selectedStation).filter(l=>state.selectedSatellite==='all'||l.record.prn===state.selectedSatellite).slice(0,state.selectedStation?12:8);
 renderDetails();renderChart();
}
function update(force=false){
 const next=C.epoch(state.time,data.gps_seconds.length);state.index=next;
 if(force||next!==lastSample||(state.time>=9&&lastPaint<9)){lastSample=next;rebuild()}
 if(force||Math.abs(state.time-lastPaint)>.04){lastPaint=state.time;const t=state.time;
 const fade=['interpolate',['linear'],['-',t,['get','birth']],0,0,.6,1];
 for(const [id,op] of [['station-halo',.28],['station-glow',.7],['station-core',1]])map.setPaintProperty(id,'circle-opacity',['*',op,fade]);
 map.setPaintProperty('station-halo','circle-radius',motion.matches?20:20+Math.sin(t*2+state.ambientTime*.7)*(t>=28?.5:2));
 map.setPaintProperty('borders','line-opacity',Math.min(.55,t/4*.55));
 const arrival=Math.min(1,Math.max(0,(t-9)/2));map.setPaintProperty('link-bloom','line-opacity',['*',arrival*.17,['get','opacity']]);map.setPaintProperty('link-light','line-opacity',['*',arrival*.48,['get','opacity']]);
 $('chart-panel').style.opacity=String(t<9?0:Math.min(1,(t-9)/2));sync();
 }if(state.time<28&&!state.paused)renderChart();updateSelectedInset();map.triggerRepaint();
}
function chooseStation(id){state.selectedStation=id;const s=data.stations.find(s=>s.id===id);if(s){chartStation=s;const rows=C.recordsAt(s,data.gps_seconds[state.index]);if(!rows.some(r=>r.prn===chartSatellite))chartSatellite=rows[0]?.prn||chartSatellite}update(true)}
function updateSelectedInset(){
 const station=chartStation||data.stations[0],prn=state.selectedSatellite==='all'?chartSatellite:state.selectedSatellite;
 const record=station.records.find(r=>r.prn===prn&&r.gps_seconds===data.gps_seconds[state.index]);
 const fractional=Math.max(0,Math.min(60,(state.time-9)/19*60));
 state.selectedPair={station:station.id,prn,epoch:state.index,record:record||null};
 earth.update(fractional,state.time>=9?{station,prn,record}:null);
 $('earth-pair').textContent=station.id+' ↔ '+prn;
 const color=record?C.colors[record.direction]:'#a5b9cc';
 $('pass-state').textContent=record?(record.direction==='near-zero'?'NEAR ZERO DOPPLER':record.direction.toUpperCase()):'NO OBSERVATION';
 $('pass-state').style.color=color;
 $('pass-value').textContent=record?(record.physical_shift_hz>=0?'+':'')+record.physical_shift_hz.toFixed(0)+' Hz':'—';$('pass-value').style.color=color;
}
function renderDetails(){
 const s=data.stations.find(s=>s.id===state.selectedStation);$('details').style.display=s?'block':'none';if(!s)return;
 $('station-title').textContent=s.id+' / GPS L1';$('station-meta').textContent=s.lat.toFixed(4)+'°, '+s.lon.toFixed(4)+'° · '+s.height_m.toFixed(1)+' m\n'+data.times_utc[state.index];const rows=C.recordsAt(s,data.gps_seconds[state.index]);$('station-values').replaceChildren();
 for(const r of rows){const div=document.createElement('div');div.className='obs-row';div.style.color=C.colors[r.direction];const b=document.createElement('button');b.textContent=r.prn;b.onclick=()=>{chartSatellite=r.prn;state.selectedSatellite=r.prn;$('satellite').value=r.prn;update(true)};const v=document.createElement('span');v.textContent=(r.doppler_hz>=0?'+':'')+r.doppler_hz.toFixed(1)+' Hz · '+r.elevation_deg.toFixed(0)+'°';div.append(b,v);$('station-values').append(div)}
 if(!rows.length)$('station-values').textContent='No retained observations at this exact epoch.';
}
function renderChart(){
 const s=chartStation||data.stations[0],prn=state.selectedSatellite==='all'?chartSatellite:state.selectedSatellite;
 const rows=s.records.filter(r=>r.prn===prn).sort((a,b)=>a.gps_seconds-b.gps_seconds);$('chart-label').textContent=s.id+' × '+prn;const current=rows.find(r=>r.gps_seconds===data.gps_seconds[state.index]);
 $('chart-time').textContent='Measured: '+data.times_utc[state.index].replace('T',' · ').replace('Z',' UTC');
 const max=Math.max(1000,...rows.map(r=>Math.abs(r.doppler_hz))),x=t=>56+(t-data.gps_seconds[0])/3600*362,y=v=>68-v/max*49;
 let svg='<line x1="56" y1="68" x2="418" y2="68" stroke="#314a62" stroke-width=".7"/><line x1="56" y1="16" x2="56" y2="120" stroke="#314a62" stroke-width=".7"/>';
 for(const [v,label] of [[max,'+'+Math.round(max)], [0,'0'],[-max,String(-Math.round(max))]])svg+=`<text x="47" y="${y(v)+3}" fill="#7894ae" font-size="16" text-anchor="end">${label}</text>`;
 for(const r of rows)svg+=`<circle cx="${x(r.gps_seconds)}" cy="${y(r.doppler_hz)}" r="1.65" fill="${C.colors[r.direction]}"/>`;
 svg+=`<line x1="${x(data.gps_seconds[0]+Math.max(0,Math.min(1,(state.time-9)/19))*3600)}" y1="15" x2="${x(data.gps_seconds[0]+Math.max(0,Math.min(1,(state.time-9)/19))*3600)}" y2="121" stroke="#e9f1f7" stroke-width=".7" opacity=".65"/>`;
 if(current)svg+=`<circle cx="${x(current.gps_seconds)}" cy="${y(current.doppler_hz)}" r="4" fill="${C.colors[current.direction]}"/>`;
 for(const [t,label] of [[data.gps_seconds[0],'17:59:42'],[data.gps_seconds.at(-1),'18:59:42 UTC']])svg+=`<text x="${x(t)}" y="139" fill="#7894ae" font-size="16" text-anchor="${t===data.gps_seconds[0]?'start':'end'}">${label}</text>`;
 $('chart').innerHTML=svg;
}
async function init(){try{
 [data,state.states]=await Promise.all(['observations.json','states.geojson'].map(async name=>{const r=await fetch('data/'+name);if(!r.ok)throw Error('Missing '+name);return r.json()}));for(const s of data.stations)s.records=s.records.map(r=>({gps_seconds:data.gps_seconds[r[0]],prn:r[1],doppler_hz:r[2],physical_shift_hz:r[2]*s.rinex_doppler_to_received_shift_sign,azimuth_deg:r[3],elevation_deg:r[4],snr_dbhz:r[5],range_rate_mps:r[6],direction:C.direction(r[2]*s.rinex_doppler_to_received_shift_sign)}));state.data=data;data.stations.sort((a,b)=>a.lon-b.lon);
 // Pick a genuinely observed sign-changing pair with the longest measured series.
 const pairs=[];for(const s of data.stations)for(const prn of Object.keys(data.satellite_ecef_m)){const r=s.records.filter(r=>r.prn===prn);if(r.some(r=>r.doppler_hz>100)&&r.some(r=>r.doppler_hz< -100))pairs.push({s,prn,n:r.length})}pairs.sort((a,b)=>b.n-a.n);const preferred=pairs.find(p=>p.s.id==='LFLO'&&p.prn==='G04')||pairs[0];chartStation=preferred?.s||data.stations[0];chartSatellite=preferred?.prn||chartStation.records[0].prn;
 earth=createEarth($('earth'),data,state.states);
 for(const prn of Object.keys(data.satellite_ecef_m)){const o=document.createElement('option');o.value=prn;o.textContent=prn;$('satellite').append(o)}
 $('credit-details').textContent=' · '+data.date+' · GPS L1 · '+data.stations.length+' selected receivers';
 map=new maplibregl.Map({container:'map',center:[-98,38],zoom:3,renderWorldCopies:false,maxPitch:0,minZoom:1,maxZoom:9,attributionControl:false,preserveDrawingBuffer:true,canvasContextAttributes:{antialias:true,powerPreference:'high-performance'},style:{version:8,sources:{states:{type:'geojson',data:state.states},stations:{type:'geojson',data:stationFeatures()},links:{type:'geojson',data:{type:'FeatureCollection',features:[]}}},layers:[{id:'bg',type:'background',paint:{'background-color':'#07111F'}},{id:'land',type:'fill',source:'states',paint:{'fill-color':'#13283B'}},{id:'borders',type:'line',source:'states',paint:{'line-color':'#314A62','line-width':.65,'line-opacity':0}},{id:'link-bloom',type:'line',source:'links',paint:{'line-color':['get','color'],'line-width':5,'line-blur':3,'line-opacity':0}},{id:'link-light',type:'line',source:'links',paint:{'line-color':['get','color'],'line-width':.7,'line-blur':.3,'line-opacity':0}},{id:'station-halo',type:'circle',source:'stations',paint:{'circle-color':'#159dc8','circle-radius':20,'circle-blur':1,'circle-opacity':0}},{id:'station-glow',type:'circle',source:'stations',paint:{'circle-color':'#4DE1F4','circle-radius':6,'circle-blur':.7,'circle-opacity':0}},{id:'station-core',type:'circle',source:'stations',paint:{'circle-color':'#d0faff','circle-radius':2,'circle-opacity':0}}]}});state.map=map;
 map.on('error',e=>{state.errors.push(e.error?.message||'Map error');$('status').textContent='Some graphics could not load. See console.'});
 map.on('load',()=>{fit();state.ready=true;$('status').textContent='';update(true);if(!motion.matches)play()});map.on('resize',()=>{if(!userMap)fit();if(state.ready)updateSelectedInset()});map.on('dragstart',e=>{if(e.originalEvent)userMap=true});
 map.on('click','station-halo',e=>chooseStation(e.features[0].properties.id));map.on('mouseenter','station-core',()=>map.getCanvas().style.cursor='pointer');map.on('mouseleave','station-core',()=>map.getCanvas().style.cursor='');
 new ResizeObserver(()=>{if(state.ready){map.resize();if(!userMap)fit()}}).observe(document.querySelector('.map-stage'));
 state.seek=seek;state.pause=stop;state.play=play;state.chooseStation=chooseStation;state.render=()=>update(true);
 }catch(e){state.errors.push(e.message);$('status').textContent='Unable to load the measured dataset: '+e.message;console.error(e)}}
$('play').onclick=()=>state.paused?play():stop();$('replay').onclick=()=>{seek(0);play()};$('final').onclick=()=>seek(28);$('timeline').oninput=e=>seek(Number(e.target.value));$('satellite').onchange=e=>{state.selectedSatellite=e.target.value;update(true)};$('clear').onclick=()=>{state.selectedStation=null;update(true)};$('methods').onclick=()=>$('method-dialog').showModal();$('close-method').onclick=()=>$('method-dialog').close();document.addEventListener('visibilitychange',()=>{if(document.hidden)stop()});motion.addEventListener('change',()=>{if(motion.matches&&state.ready)seek(28)});init();
