(async()=>{'use strict';
const $=id=>document.getElementById(id),M=CinematicCore,C=Cesium,q=window.day09={ready:false,running:false,paused:false,errors:[],index:0,progress:0,buffering:false};
if(innerWidth<=650)document.querySelector('.panel>details').open=false;
const status=t=>$('status').textContent=t;
window.addEventListener('error',e=>q.errors.push(e.message));window.addEventListener('unhandledrejection',e=>q.errors.push(String(e.reason)));
try{
 C.Ion.defaultAccessToken='';
 const r=await fetch('data/history.json?v=refine1');if(!r.ok)throw Error('Historical layers unavailable');const data=await r.json();q.data=data;$('epoch').max=data.series.length-1;
 const viewer=q.viewer=new C.Viewer('map',{baseLayer:false,baseLayerPicker:false,geocoder:false,homeButton:false,sceneModePicker:false,navigationHelpButton:false,animation:false,timeline:false,fullscreenButton:false,selectionIndicator:false,infoBox:false,requestRenderMode:true,maximumRenderTimeChange:Infinity,shouldAnimate:false,contextOptions:{webgl:{alpha:false,antialias:true}}});
 const scene=viewer.scene,request=()=>scene.requestRender();viewer.resolutionScale=Math.min(devicePixelRatio||1,1.5)/(devicePixelRatio||1);
 scene.globe.enableLighting=true;scene.globe.showWaterEffect=false;scene.globe.depthTestAgainstTerrain=true;scene.globe.baseColor=C.Color.fromCssColorString('#152936');scene.globe.tileCacheSize=180;scene.sun.show=false;scene.moon.show=false;scene.sunBloom=false;viewer.clock.currentTime=C.JulianDate.fromIso8601('2025-05-15T23:00:00Z');
 const ctl=scene.screenSpaceCameraController;ctl.enableCollisionDetection=true;ctl.minimumZoomDistance=30;ctl.maximumZoomDistance=30000000;ctl.tiltEventTypes=[C.CameraEventType.RIGHT_DRAG,C.CameraEventType.PINCH];ctl.zoomEventTypes=[C.CameraEventType.WHEEL,C.CameraEventType.PINCH];ctl.lookEventTypes=[];
 scene.renderError.addEventListener((_,e)=>{q.errors.push(String(e));status('Rendering error — check WebGL and reload.');});
 const globe=viewer.imageryLayers.addImageryProvider(await C.SingleTileImageryProvider.fromUrl('data/nasa-blue-marble.jpg',{rectangle:C.Rectangle.MAX_VALUE,credit:new C.Credit('NASA GIBS Blue Marble satellite composite')}));
 const satellite=viewer.imageryLayers.addImageryProvider(new C.UrlTemplateImageryProvider({url:'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',maximumLevel:19,credit:new C.Credit('Esri World Imagery © Esri, Vantor, Earthstar Geographics & contributors')}));
 const terrain=await C.ArcGISTiledElevationTerrainProvider.fromUrl('https://elevation3d.arcgis.com/arcgis/rest/services/WorldElevation3D/Terrain3D/ImageServer'),ellipsoid=new C.EllipsoidTerrainProvider();
 function lod(){const h=viewer.camera.positionCartographic.height,p=$('terrain').checked&&h<2000000?terrain:ellipsoid;if(viewer.terrainProvider!==p)viewer.terrainProvider=p;satellite.alpha=M.smooth((12000000-h)/8000000);globe.show=satellite.alpha<1;request();}
 viewer.camera.percentageChanged=.01;viewer.camera.changed.addEventListener(lod);
 let comparing=false;let elapsed=0,last=0,raf=0,preparing=false,complete=false;const warmed=new Set();
 const world={...data.display.world,ground:0},overview={...data.display.overview,ground:0};
 const sample=await C.sampleTerrain(terrain,12,[C.Cartographic.fromDegrees(overview.lon,overview.lat)]);if(!Number.isFinite(sample[0].height))throw Error('Terrain elevation sample unavailable');overview.ground=sample[0].height;
 function camera(p){viewer.camera.lookAt(C.Cartesian3.fromDegrees(p.lon,p.lat,p.ground||0),new C.HeadingPitchRange(0,C.Math.toRadians(p.pitch),p.range*Math.max(1,Math.min(1.6,scene.canvas.clientHeight/scene.canvas.clientWidth))));viewer.camera.lookAtTransform(C.Matrix4.IDENTITY);lod();}
 camera(overview);
 const layers=[];const rectangle=C.Rectangle.fromDegrees(...data.texture_bounds);
 // Presentation only: recolor classified texture RGB; preserve its exact geographic alpha mask.
 async function historicalProvider(path,key){
  let url=path;
  if(key!=='new'){const image=new Image();image.src=path;await image.decode();const canvas=document.createElement('canvas');canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;const context=canvas.getContext('2d');context.drawImage(image,0,0);context.globalCompositeOperation='source-in';context.fillStyle='#304F63';context.fillRect(0,0,canvas.width,canvas.height);url=canvas.toDataURL('image/png');}
  return C.SingleTileImageryProvider.fromUrl(url,{rectangle,credit:new C.Credit('GHSL R2023A © European Commission JRC')});
 }
 for(const row of data.series){const item={};for(const key of ['footprint','stable','gain','new','loss']){const provider=await historicalProvider(row.texture[key==='new'?'highlight':key],key);item[key]=viewer.imageryLayers.addImageryProvider(provider);item[key].show=false;}layers.push(item);}
 q.layers=layers;
 function ui(){for(const id of ['comparison','growth','play','replay','reset'])$(id).disabled=preparing;$('pause').disabled=!q.running&&!q.paused;$('pause').textContent=q.paused?'Resume':'Pause';$('comparison').setAttribute('aria-pressed',String(comparing));$('growth').setAttribute('aria-pressed',String(!comparing));}
 function statistics(row,comparison=false){const first=data.series[0],last=data.series.at(-1),selected=comparison?last:row,multiplier=selected.developed_km2/first.developed_km2;$('area').textContent=`${multiplier.toFixed(1)}× GROWTH`;$('metric-label').textContent=`Developed-cell footprint · ${first.year}–${selected.year}`;$('change').textContent=`${first.developed_km2.toFixed(1)} km² → ${selected.developed_km2.toFixed(1)} km²`;$('miles').textContent='GHSL estimates · ≥10% built-up surface per cell';q.multiplier=multiplier;}
 function apply(states){for(const item of layers)for(const layer of Object.values(item)){const alpha=states.get(layer)||0;if(alpha>0){layer.alpha=alpha;if(!layer.show)layer.show=true;}else if(layer.show)layer.show=false;}request();}
 function display(index,phase=1,animate=false){if(comparing)return;q.index=index;const row=data.series[index];$('year').textContent=row.year;$('selected').textContent=row.year;$('epoch').value=index;statistics(row);$('temporal').textContent=row.temporal_definition;
  const item=layers[index],show=$('footprint').checked,highlight=$('new').checked,states=new Map();
  function layer(key,alpha,on=show){if(on&&alpha>0)states.set(item[key],alpha);}
  if(!animate||index===0){layer('footprint',.45);layer('new',.25,highlight&&show&&index>0&&!animate);}
  else{const fade=M.smooth(phase/.5),settle=M.smooth((phase-.5)/.5);layer('stable',.45);layer('loss',.45*(1-fade),show&&row.loss_km2>0);layer('gain',.45*fade);layer('new',.30*fade*(1-settle),highlight&&show);}
  apply(states);
 }
 function leaveComparison(){comparing=false;q.comparing=false;document.body.classList.remove('comparing');$('swipe').hidden=true;$('growth-year').hidden=false;for(const item of layers)for(const layer of Object.values(item))if(layer.splitDirection!==C.SplitDirection.NONE)layer.splitDirection=C.SplitDirection.NONE;}
 function compare(){if(preparing)return;pause();q.paused=false;comparing=true;q.comparing=true;document.body.classList.add('comparing');$('swipe').hidden=false;$('growth-year').hidden=true;const states=new Map();for(const [index,side] of [[0,C.SplitDirection.LEFT],[layers.length-1,C.SplitDirection.RIGHT]]){layers[index].footprint.splitDirection=side;if($('footprint').checked)states.set(layers[index].footprint,.45);}scene.splitPosition=Number($('compare').value)/100;statistics(null,true);apply(states);status(`Drag the divider · ${data.epochs[0]} / ${data.epochs.at(-1)} · same classification`);ui();}
 function growth(){if(preparing)return;pause();leaveComparison();q.paused=false;elapsed=0;q.progress=0;complete=false;display(0);ui();status('Growth mode · ten source epochs · camera stays in place');}
 $('compare').oninput=()=>{const value=Number($('compare').value);scene.splitPosition=value/100;$('divider').style.left=value+'%';request();};
 $('comparison').onclick=compare;$('growth').onclick=growth;
 // Readiness is checked before playback; the basemap and camera never animate in Growth mode.
 scene.postRender.addEventListener(()=>{if(q.disposed)return;const canvas=scene.canvas,ray=canvas.clientWidth&&canvas.clientHeight?viewer.camera.getPickRay(new C.Cartesian2(canvas.clientWidth/2,canvas.clientHeight/2)):null;q.surfaceReady=!!ray&&!!scene.globe.pick(ray,scene)&&scene.globe.tilesLoaded;});
 const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
 async function waitTiles(){const start=performance.now();let stable=0;while(performance.now()-start<45000){request();await sleep(125);stable=q.surfaceReady?stable+1:0;if(stable>=4)return;}throw Error('Map tiles still loading. Check connection and retry.');}
 async function prepare(){if(preparing)return false;if(warmed.size===data.series.length&&q.surfaceReady)return true;preparing=true;$('loading').hidden=false;ui();ctl.enableInputs=false;try{for(let i=0;i<data.series.length;i++){if(warmed.has(i))continue;$('loading-text').textContent=`Preparing historical layers · ${i+1}/${data.series.length}`;display(i,.3,true);await waitTiles();display(i);await waitTiles();warmed.add(i);}display(0);await waitTiles();return true;}catch(e){status(e.message);q.errors.push(e.message);return false;}finally{preparing=false;ctl.enableInputs=true;$('loading').hidden=true;ui();}}
 function pause(){if(!q.running)return;q.running=false;q.paused=true;cancelAnimationFrame(raf);ui();status('Paused · navigate freely or resume');}
 function tick(now){if(!q.running)return;elapsed+=(now-last)/1000;last=now;const progress=M.clamp(elapsed/Number($('duration').value));q.progress=progress;const f=M.frame(progress,data.series.length);display(f.index,f.phase,true);if(progress>=1){q.running=false;q.paused=false;complete=true;display(data.series.length-1);layers.at(-1).new.show=false;ui();status(`${data.epochs[0]}–${data.epochs.at(-1)} · explore the valley or replay`);return;}raf=requestAnimationFrame(tick);}
 async function start(){if(preparing)return;leaveComparison();pause();elapsed=0;q.progress=0;q.paused=false;complete=false;display(0);if(!await prepare())return;q.running=true;last=performance.now();ui();status(`${data.epochs[0]}–${data.epochs.at(-1)} · ${data.epochs.length} GHSL estimates`);raf=requestAnimationFrame(tick);}
 function resume(){if(!q.paused)return;q.paused=false;q.running=true;last=performance.now();ui();raf=requestAnimationFrame(tick);}
 function playPause(){if(q.running)pause();else if(q.paused)resume();else start(false);}
 $('play').onclick=()=>start();$('pause').onclick=()=>q.running?pause():resume();$('replay').onclick=()=>start();$('reset').onclick=()=>{growth();status('1975 · ready to play');};$('reset-camera').onclick=()=>{pause();camera(overview);};
 $('epoch').oninput=()=>{leaveComparison();pause();q.paused=false;elapsed=Number($('epoch').value)/data.series.length*Number($('duration').value);display(Number($('epoch').value));ui();};
 $('duration').onchange=()=>{pause();q.paused=false;ui();$('play').textContent=`Play Growth · ${$('duration').value}s`;};
 for(const id of ['footprint','new'])$(id).onchange=()=>comparing?compare():display(q.index);
 $('terrain').onchange=lod;$('record').onclick=()=>{document.body.classList.toggle('recording');$('record').blur();};
 document.addEventListener('keydown',e=>{if(!document.body.classList.contains('recording')&&/INPUT|SELECT|TEXTAREA/.test(e.target.tagName))return;if(e.code==='Space'){e.preventDefault();playPause();}if(e.code==='KeyR'){e.preventDefault();start();}if(e.code==='Escape')document.body.classList.remove('recording');});
 scene.canvas.addEventListener('pointerdown',pause);scene.canvas.addEventListener('wheel',pause,{passive:true});
 window.addEventListener('pagehide',()=>{q.disposed=true;cancelAnimationFrame(raf);viewer.destroy();});window.addEventListener('pageshow',e=>{if(e.persisted)location.reload();});
 window.addEventListener('resize',()=>{if(innerWidth<=650)document.querySelector('.panel>details').open=false;request();});
 q.actions={start,pause,resume,display,camera,prepare,compare,growth,leaveComparison};q.views={world,overview};display(0);if(!await prepare())throw Error('Historical layers could not be prepared');q.ready=true;compare();ui();
}catch(e){q.errors.push(String(e));$('fatal').hidden=false;$('fatal').textContent=`The map could not initialize: ${e.message}. Check internet and WebGL access, then reload.`;console.error(e);}
})();
