'use strict';
const $=id=>document.getElementById(id),motion=matchMedia('(prefers-reduced-motion: reduce)'),mobile=()=>innerWidth<700;
const state=window.Pulse={ready:false,time:motion.matches?10:0,paused:motion.matches,cinematic:!motion.matches,particlesAvailable:false,errors:[],frames:0};
let map,layer,finalCamera,hoover,dam,raf,last=0,lastPaint=-1,labels=[],disposed=false,userCamera=false;
const cities=[
 {name:'Las Vegas',coordinates:[-115.1398,36.1699],size:18,birth:2},
 {name:'Los Angeles',coordinates:[-118.2437,34.0522],size:22,birth:2.4},
 {name:'Phoenix',coordinates:[-112.074,33.4484],size:20,birth:2.6},
 {name:'Boulder City',coordinates:[-114.8325,35.9786],size:9,birth:2.1},
 {name:'Kingman',coordinates:[-114.053,35.1894],size:12,birth:2.2},
 {name:'Palm Springs',coordinates:[-116.5453,33.8303],size:14,birth:2.4}
];
function sync(){
 $('pause').textContent=state.paused?'Play':'Pause';$('pause').setAttribute('aria-pressed',String(state.paused));
 if(motion.matches){$('pause').textContent='Reduced motion';$('pause').disabled=true;$('replay').disabled=true}
 else{$('pause').disabled=false;$('replay').disabled=false}
}
function stop(){state.paused=true;last=0;cancelAnimationFrame(raf);sync()}
function start(){if(!state.ready||motion.matches)return;state.paused=false;last=0;sync();raf=requestAnimationFrame(frame)}
function fit(){
 const padding=mobile()?{top:225,bottom:145,left:22,right:22}:{top:60,bottom:90,left:Math.min(440,Math.max(300,innerWidth*.31)),right:45};
 const result=map.cameraForBounds([[-119.25,32.3],[-110.75,37.75]],{padding});
 // cameraForBounds already offsets its center for padding. Use the geographic
 // midpoint with retained camera padding so the editorial offset is applied once.
 const mercatorY=lat=>Math.asinh(Math.tan(lat*Math.PI/180));
 const latitude=Math.atan(Math.sinh((mercatorY(32.3)+mercatorY(37.75))/2))*180/Math.PI;
 finalCamera={center:[-115,latitude],zoom:result.zoom,padding};
}
function marker(text,coordinates,kind,birth,offset=[0,0],anchor='center'){
 const element=document.createElement('div');element.className='place';
 const content=document.createElement('div');content.className=kind;element.append(content);
 // Labels are fixed local text, not remote dataset HTML.
 if(kind==='source-label'){content.textContent='HOOVER DAM';const small=document.createElement('small');small.textContent='Colorado River';content.append(small)}else content.textContent=text;
 content.style.opacity='0';const marker=new maplibregl.Marker({element,offset,anchor}).setLngLat(coordinates).addTo(map);labels.push({element:content,marker,kind,birth});
}
function updatePaint(force=false){
 const t=state.time;
 if(!force&&Math.abs(t-lastPaint)<.05)return;lastPaint=t;
 const source=PulseCore.smooth((t-.5)/.5),pulse=motion.matches?1:1+Math.sin(t*.9)*.045;
 for(const [id,radius,opacity] of [['dam-halo',58,.24],['dam-glow',27,.62],['dam-core',4.2,1]]){map.setPaintProperty(id,'circle-radius',radius*pulse);map.setPaintProperty(id,'circle-opacity',source*opacity)}
 map.setPaintProperty('corridor-bloom','line-opacity',PulseCore.opacityExpression(t,.13));
 map.setPaintProperty('corridor-light','line-opacity',PulseCore.opacityExpression(t,.2596));
 const cityFade=['interpolate',['linear'],['-',t,['get','birth']],0,0,.8,1];
 map.setPaintProperty('city-halo','circle-opacity',['*',.25,cityFade]);map.setPaintProperty('city-core','circle-opacity',['*',.8,cityFade]);
 for(const l of labels){const opacity=PulseCore.smooth((t-l.birth)/.5);l.element.style.opacity=String(opacity*(l.kind==='state-label'?.7:1))}
 $('chapter').textContent=motion.matches?'The regional grid':PulseCore.stage(state.time);
}
function frame(now){
 if(disposed||state.paused)return;
 const dt=last?Math.max(0,(now-last)/1000):0;last=now;state.time+=dt;state.frames++;
 if(state.cinematic){map.jumpTo(PulseCore.camera(state.time,finalCamera,hoover,mobile()));if(state.time>=10)state.cinematic=false}
 updatePaint();map.triggerRepaint();raf=requestAnimationFrame(frame);
}
function replay(){if(!state.ready||motion.matches)return;stop();userCamera=false;state.time=0;state.cinematic=true;map.jumpTo(PulseCore.camera(0,finalCamera,hoover,mobile()));updatePaint(true);start()}
async function init(){
 try{
  const [lines,context,routes,source,world]=await Promise.all(['transmission.geojson','context.geojson','routes.json','sources.json','world.geojson'].map(async file=>{const response=await fetch('data/'+file);if(!response.ok)throw Error('Geographic data unavailable: '+file);return response.json()}));
  hoover=source.camera_anchor_coordinates||source.hoover_coordinates;dam=source.hoover_coordinates;
  const activeRoutes=new Set(routes.routes.map(r=>r.id));
  for(const f of lines.features){f.properties.active=Number(activeRoutes.has(f.properties.id));f.properties.start=PulseCore.revealTime(f.properties.reveal)}
  if(!window.maplibregl)throw Error('MapLibre could not load.');
  map=new maplibregl.Map({container:'map',center:hoover,zoom:5.8,maxZoom:10,minZoom:0,renderWorldCopies:false,maxPitch:45,pixelRatio:Math.min(devicePixelRatio||1,1.6),attributionControl:false,canvasContextAttributes:{antialias:true,powerPreference:'high-performance'},style:{version:8,sources:{world:{type:'geojson',data:world},context:{type:'geojson',data:context,attribution:'<a href="https://www.naturalearthdata.com/about/terms-of-use/">Natural Earth</a>'},lines:{type:'geojson',data:lines,attribution:'<a href="https://www.arcgis.com/home/item.html?id=d4090758322c4d32a4cd002ffaa0aa12">HIFLD / EIA · 2024 archive</a>'},dam:{type:'geojson',data:{type:'Feature',properties:{},geometry:{type:'Point',coordinates:dam}}},cities:{type:'geojson',data:{type:'FeatureCollection',features:cities.map(c=>({type:'Feature',properties:{size:c.size,birth:c.birth},geometry:{type:'Point',coordinates:c.coordinates}}))}}},layers:[
   {id:'night',type:'background',paint:{'background-color':'#03080e'}},
   {id:'land',type:'fill',source:'world',paint:{'fill-color':'#080f17','fill-opacity':1}},
   {id:'world-borders',type:'line',source:'world',paint:{'line-color':'#273d4b','line-opacity':['interpolate',['linear'],['zoom'],1,.5,4,.15,6,0],'line-width':.6}},
   {id:'borders',type:'line',source:'context',filter:['==',['get','kind'],'boundary'],paint:{'line-color':'#2a3e4a','line-opacity':.4,'line-width':.65}},
   {id:'water',type:'fill',source:'context',filter:['==',['get','kind'],'water'],paint:{'fill-color':['case',['==',['get','name'],'Lake Mead'],'#0e2a39','#0b202b'],'fill-opacity':['case',['==',['get','name'],'Lake Mead'],.78,.7]}},
   {id:'water-edge',type:'line',source:'context',filter:['==',['get','kind'],'water'],paint:{'line-color':'#234451','line-width':.6,'line-opacity':.4}},
   {id:'colorado-river',type:'line',source:'context',filter:['==',['get','kind'],'river'],paint:{'line-color':'#234451','line-width':['interpolate',['linear'],['zoom'],4,1.1,7,1.7,10,2.2],'line-opacity':.5}},
   {id:'quiet-grid',type:'line',source:'lines',paint:{'line-color':'#40708a','line-opacity':['interpolate',['linear'],['zoom'],2,0,4,.13,7,.23],'line-width':.6}},
   {id:'city-halo',type:'circle',source:'cities',paint:{'circle-color':'#dfae63','circle-radius':['get','size'],'circle-blur':1,'circle-opacity':0}},
   {id:'city-core',type:'circle',source:'cities',paint:{'circle-color':'#e0b56c','circle-radius':2.1,'circle-blur':.65,'circle-opacity':0}},
   {id:'corridor-bloom',type:'line',source:'lines',paint:{'line-color':'#087eaa','line-width':5,'line-blur':3,'line-opacity':0}},
   {id:'corridor-light',type:'line',source:'lines',paint:{'line-color':'#25b9e8','line-width':.8,'line-blur':.45,'line-opacity':0}},
   {id:'dam-halo',type:'circle',source:'dam',paint:{'circle-color':'#098dff','circle-radius':43,'circle-blur':1,'circle-opacity':0}},
   {id:'dam-glow',type:'circle',source:'dam',paint:{'circle-color':'#1ebeff','circle-radius':22,'circle-blur':1,'circle-opacity':0}},
   {id:'dam-core',type:'circle',source:'dam',paint:{'circle-color':'#d8f9ff','circle-radius':3.5,'circle-blur':.3,'circle-opacity':0}}
  ]}});
  state.map=map;state.source=source;fit();map.jumpTo(PulseCore.camera(state.time,finalCamera,hoover,mobile()));
  map.addControl(new maplibregl.AttributionControl({compact:true}));
  map.on('error',event=>{const message=event.error?.message||'Map error';state.errors.push(message);$('status').textContent='Some geography could not render. Reload to try again.'});
  map.on('load',()=>{
   try{layer=new PulseParticles(routes,lines,state,mobile());map.addLayer(layer,'dam-halo');state.particlesAvailable=layer.available;state.particleCount=layer.count}
   catch(error){state.errors.push(error.message);$('status').textContent='Particle effects unavailable · Geographic line animation remains available.'}
   marker('',dam,'source-label',-.5,[18,0],'left');marker('Lake Mead',[-114.58,36.17],'water-label',-.5,[30,-17]);
   for(const c of cities)if(['Las Vegas','Los Angeles','Phoenix'].includes(c.name))marker(c.name,c.coordinates,'city-label',-.5,c.name==='Las Vegas'?[-12,-9]:[0,12],c.name==='Las Vegas'?'bottom-right':'top');
   for(const [name,point] of [['N E V A D A',[-116.8,37.1]],['C A L I F O R N I A',[-118.15,35.7]],['A R I Z O N A',[-112.3,35.5]]])marker(name,point,'state-label',-.5);
   state.ready=true;updatePaint(true);sync();if(!state.errors.length)$('status').textContent='';map.triggerRepaint();if(!state.paused)start();
  });
  for(const event of ['dragstart','zoomstart','rotatestart','pitchstart'])map.on(event,e=>{if(e.originalEvent){state.cinematic=false;userCamera=true}});
  map.on('resize',()=>{fit();if(!userCamera)map.jumpTo(PulseCore.camera(state.time,finalCamera,hoover,mobile()))});
  map.getCanvas().addEventListener('webglcontextlost',()=>{stop();$('status').textContent='Graphics paused · Reload to restore the visualization.'});
 }catch(error){state.errors.push(error.message);$('status').textContent='Unable to prepare the map. Please use a WebGL-capable browser and local HTTP preview.';$('pause').disabled=true;$('replay').disabled=true}
}
$('pause').onclick=()=>state.paused?start():stop();$('replay').onclick=replay;
document.addEventListener('visibilitychange',()=>{if(document.hidden)stop()});
motion.addEventListener('change',()=>{if(motion.matches&&state.ready){stop();state.time=10;state.cinematic=false;if(!userCamera)map.jumpTo(PulseCore.camera(10,finalCamera,hoover,mobile()));updatePaint(true);map.triggerRepaint()}sync()});
window.addEventListener('pagehide',event=>{stop();if(event.persisted)return;disposed=true;labels.forEach(l=>l.marker.remove());map?.remove()},{once:true});
state.replay=replay;state.pause=stop;state.seek=t=>{stop();state.time=t;state.cinematic=!userCamera&&!motion.matches&&t<10;if(!userCamera)map.jumpTo(PulseCore.camera(t,finalCamera,hoover,mobile()));updatePaint(true);map.triggerRepaint()};
init();
