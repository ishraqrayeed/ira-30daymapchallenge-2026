/* Static park atlas. All geographic detail is prepared ahead of time. */
'use strict';
const $ = id => document.getElementById(id);
const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
let refreshDetails=()=>{};
let map, qa, treeLibrary, treeLayer, interiorData, interiorIndex, staticSources, tourFrame, cameraPath, groundTexture, touring = false, popup;
const captions = ['Denver’s park system. Small green dots keep the smallest places discoverable.', 'Washington Park. Paths, lakes, play areas, and fields emerge as the city falls away.', 'One real mapped bench in Washington Park. A place to pause inside the larger map.'];
const fail = message => { $('error').hidden = false; $('error').textContent = message; };
const motion = duration => reduced() ? 0 : duration;
function cancelTour() { if(tourFrame){cancelAnimationFrame(tourFrame);tourFrame=null;} touring = false; }
function padding() { return innerWidth < 601 ? {top:225,bottom:60,left:30,right:30} : {top:100,bottom:80,left:440,right:90}; }
let dimensionState=null;
function syncDimension() { const tilted = map.getPitch() > 5;if(tilted===dimensionState)return;dimensionState=tilted; if(map.getLayer('amenities-3d')) {map.setLayoutProperty('amenities-3d','visibility',tilted?'visible':'none');} $('dimension').textContent = tilted ? '3D view' : '2D view'; $('dimension').title = tilted ? 'Switch to 2D view' : 'Switch to 3D view'; $('dimension').setAttribute('aria-pressed', String(tilted)); }
function announce(text){const target=$('caption');if(target&&target.textContent!==text)target.textContent=text;}
function activeStop(n){if(n>=0)announce(captions[n]);}

function showBenchCallout(feature){
  const p=feature.properties,coordinates=feature.geometry.coordinates;
  if(popup)popup.remove();
  const root=document.createElement('div'),h=document.createElement('h3');
  h.textContent=p.osm===qa.bench.osm?'The Bench':p.name||'Mapped bench';root.append(h);
  const source=document.createElement('a');source.href='https://www.openstreetmap.org/'+p.osm;source.textContent='View source ↗';source.target='_blank';source.rel='noopener';root.append(source);
  const screen=map.project(coordinates),width=map.getCanvas().clientWidth;
  const anchor=width<601?'bottom':width-screen.x>330?'left':screen.x>330?'right':'bottom';
  popup=new maplibregl.Popup({anchor,offset:anchor==='bottom'?74:64,maxWidth:'260px',className:'bench-callout',focusAfterOpen:false}).setLngLat(coordinates).setDOMContent(root).addTo(map);
}
function benchPopup(){showBenchCallout(interiorData.features.find(f=>f.properties.osm===qa.bench.osm));}

function goToStop(n, fromTour=false, instant=false) {
  if(!fromTour) cancelTour();
  map.stop();if(popup)popup.remove();activeStop(n);
  if(n===0) {
    // fitBounds adds its inset to retained camera padding. Clear the previous
    // close-up inset so a mobile reset still has room to fit the whole city.
    map.setPadding({top:0,bottom:0,left:0,right:0});
    map.fitBounds(qa.bounds,{padding:padding(),pitch:0,bearing:0,duration:motion(instant?0:2100),maxZoom:11});
  }
  if(n===1) {
    const b=qa.washington_bounds;
    map.flyTo({center:[(b[0]+b[2])/2,(b[1]+b[3])/2],zoom:innerWidth<601?14.8:15.1,padding:innerWidth<601?{top:225,bottom:70,left:28,right:28}:{top:90,bottom:70,left:430,right:90},pitch:50,bearing:-20,duration:motion(3400),essential:false});
  }
  if(n===2) {
    map.flyTo({center:qa.bench.coordinates,zoom:20.2,pitch:52,bearing:-28,padding:innerWidth<601?{top:225,bottom:70,left:25,right:25}:{top:110,bottom:70,left:380,right:60},duration:motion(3200),essential:false});
    if(reduced()) benchPopup();else map.once('moveend',showBenchIfHere);
  }
}
function showBenchIfHere(){if(map.getZoom()>19 && map.getBounds().contains(qa.bench.coordinates))benchPopup();}
function add(id,type,source,paint,extra={}) {map.addLayer({id,type,source,paint,...extra});}
// Point-centred solids use recorded facing or a prepared nearest-trail inference.
function solids(features) {
  const output=[];
  function polygon(center,coords,props){
    const lat=center[1], sx=1/(111320*Math.cos(lat*Math.PI/180)),sy=1/111320;
    const ring=coords.map(([x,y])=>[center[0]+x*sx,lat+y*sy]);ring.push(ring[0]);
    output.push({type:'Feature',properties:props,geometry:{type:'Polygon',coordinates:[ring]}});
  }
  const compass={N:0,NNE:22.5,NE:45,ENE:67.5,E:90,ESE:112.5,SE:135,SSE:157.5,S:180,SSW:202.5,SW:225,WSW:247.5,W:270,WNW:292.5,NW:315,NNW:337.5};
  for(const f of features) {
    if(f.geometry.type!=='Point')continue;
    const p=f.properties,c=f.geometry.coordinates;
    const solid=(coords,color,base,height)=>polygon(c,coords,{...p,color,base,height});
    if(p.kind==='bench') {
      const d=String(p.direction??'').toUpperCase();const angle=d in compass?compass[d]:d!==''&&Number.isFinite(Number(d))?Number(d):null;
      const a=(angle??p.display_direction??0)*Math.PI/180, rotate=points=>points.map(([x,y])=>[x*Math.cos(a)+y*Math.sin(a),-x*Math.sin(a)+y*Math.cos(a)]);
      const benchScale=2.1;
      const rect=(x0,y0,x1,y1,col,z0,z1)=>solid(rotate([[x0,y0],[x1,y0],[x1,y1],[x0,y1]].map(([x,y])=>[x*benchScale,y*benchScale])),col,z0*benchScale,z1*benchScale);
      for(const x of [-.68,.60])for(const y of [-.18,.13])rect(x,y,x+.08,y+.06,'#545b54',0,.46);
      rect(-.76,-.18,.76,-.12,'#535d54',.28,.35);
      for(let j=0;j<4;j++)rect(-.9,-.24+j*.12,.9,-.14+j*.12,j%2?'#b48a53':'#9e7545',.44,.50);
      if(p.backrest!=='no') {
        rect(-.73,-.28,-.66,-.22,'#545b54',.38,1.0);rect(.66,-.28,.73,-.22,'#545b54',.38,1.0);
        for(let j=0;j<3;j++)rect(-.9,-.30,.9,-.24,j%2?'#b48a53':'#9e7545',.61+j*.13,.71+j*.13);
      }
    }
  }
  return {type:'FeatureCollection',features:output};
}
function init(style) {
  // Retain quiet road and place context; park interior detail comes from the static extract.
  style.layers = style.layers.filter(l=>!['park','landuse','landcover','poi'].includes(l['source-layer']) && !['waterway_line_label','water_name_point_label','water_name_line_label','highway-name-path'].includes(l.id));
  for(const l of style.layers) {
    if(l.type==='line' && l['source-layer']==='transportation') {if(l.paint)l.paint['line-opacity']=0.45;}
    if(l.id==='water')l.paint['fill-color']='#b7ced5';
  }
  style.sources.openmaptiles.attribution=''; // Persistent, linked credits are in the HTML footer.
  maplibregl.setWorkerCount(2);
  maplibregl.setWorkerUrl(new URL('vendor/maplibre-gl-csp-worker.js',location.href).href);
  map=new maplibregl.Map({container:'map',style,center:[-104.9,39.75],zoom:10,pitch:0,maxPitch:60,minZoom:8,maxZoom:21,scrollZoom:true,doubleClickZoom:true,boxZoom:true,touchZoomRotate:true,touchPitch:false,keyboard:true,attributionControl:false,renderWorldCopies:false});
  window.parkMap=map;
  map.addControl(new maplibregl.NavigationControl({showCompass:false}),'top-right');
  map.on('error', e=> {console.warn('Map resource:',e.error?.message);});
  map.on('pitch',syncDimension);map.on('pitchend',syncDimension);
  map.once('style.load',()=>{
    for(const name of ['boundary','parks','park-points','interiors']) map.addSource(name,{type:'geojson',data:name==='interiors'?{type:'FeatureCollection',features:[]}:staticSources[name],maxzoom:19,buffer:64});
    add('city-boundary','line','boundary',{'line-color':'#456954','line-width':1.5,'line-opacity':0.65,'line-dasharray':[3,2]});
    add('parkland','fill','parks',{'fill-color':'#3f8b56','fill-opacity':['interpolate',['linear'],['zoom'],10,0.86,15,0.63,18,0.40]});
    add('park-outline','line','parks',{'line-color':'#347349','line-width':['interpolate',['linear'],['zoom'],10,0.5,16,1.3],'line-opacity':0.65});
    add('park-dots','circle','park-points',{'circle-radius':['interpolate',['linear'],['zoom'],9,1.7,12,2.5],'circle-color':'#267343','circle-opacity':['interpolate',['linear'],['zoom'],11,0.8,13,0]}, {maxzoom:13});
    map.addImage('lawn-texture',groundTexture.grassPattern(),{pixelRatio:2});
    add('grass-detail','fill','parks',{'fill-pattern':'lawn-texture','fill-opacity':['interpolate',['linear'],['zoom'],15.5,0,17,.3,19,.65,20.2,.8]},{minzoom:15.5});
    const kind=k=>['==',['get','kind'],k];
    const geom=t=>['==',['geometry-type'],t];
    add('water-area','fill','interiors',{'fill-color':'#85b8ca','fill-opacity':0.95},{minzoom:12,filter:['all',kind('water'),geom('Polygon')]});
    add('water-lines','line','interiors',{'line-color':'#85b8ca','line-width':2},{minzoom:13,filter:['all',kind('water'),geom('LineString')]});
    add('pitch-area','fill','interiors',{'fill-color':'#acc97d','fill-outline-color':'#f3f4d9','fill-opacity':0.8},{minzoom:14,filter:['all',kind('pitch'),geom('Polygon')]});
    add('play-area','fill','interiors',{'fill-color':'#d5b26c','fill-opacity':0.8},{minzoom:14,filter:['all',kind('playground'),geom('Polygon')]});
    add('path-casing','line','interiors',{'line-color':'#7a8d6e','line-width':['interpolate',['linear'],['zoom'],13,2.4,18,7.5,20,10]}, {minzoom:13,filter:kind('path')});
    add('paths','line','interiors',{'line-color':'#f7f4d8','line-width':['interpolate',['linear'],['zoom'],13,1.2,18,5,20,7]}, {minzoom:13,filter:kind('path')});
    // OpenMapTiles building heights are metres. No invented floors or photorealism.
    map.addLayer({id:'buildings-3d',type:'fill-extrusion',source:'openmaptiles','source-layer':'building',minzoom:15,paint:{'fill-extrusion-color':'#d4d7cb','fill-extrusion-height':['number',['get','render_height'],3],'fill-extrusion-base':['number',['get','render_min_height'],0],'fill-extrusion-opacity':0.55}});
    add('tree-points','circle','interiors',{'circle-color':'#34714b','circle-radius':['interpolate',['linear'],['zoom'],17,2.5,20,7],'circle-stroke-color':'#c7dbab','circle-stroke-width':1}, {minzoom:17,filter:['all',kind('tree'),geom('Point')]});
    // Bench symbols use the actual OSM node, never a representative point.
    add('bench-points','circle','interiors',{'circle-color':'#8c5a30','circle-radius':['interpolate',['linear'],['zoom'],17,4,20,6],'circle-stroke-color':'#fff9e7','circle-stroke-width':1.5},{minzoom:17,filter:['all',kind('bench'),geom('Point')]});
    add('amenity-points','circle','interiors',{'circle-color':['match',['get','kind'],'playground','#c18d40','#81aa69'],'circle-radius':4,'circle-stroke-color':'#faf8e6','circle-stroke-width':1},{minzoom:15,filter:['all',['in',['get','kind'],['literal',['playground','pitch']]],geom('Point')]});
    map.addSource('point-solids',{type:'geojson',data:{type:'FeatureCollection',features:[]},maxzoom:20,tolerance:0});
    map.addLayer({id:'amenities-3d',type:'fill-extrusion',source:'point-solids',minzoom:17,layout:{visibility:'none'},paint:{'fill-extrusion-color':['get','color'],'fill-extrusion-base':['get','base'],'fill-extrusion-height':['get','height'],'fill-extrusion-opacity':0.95,'fill-extrusion-vertical-gradient':true}});
    let interiorSignature='',solidSignature='';
    const updateInteriors=()=>{
      if(map.getZoom()<12.5){if(interiorSignature){map.getSource('interiors').setData({type:'FeatureCollection',features:[]});interiorSignature='';}return;}
      const b=map.getBounds(),west=b.getWest(),south=b.getSouth(),east=b.getEast(),north=b.getNorth();
      const visible=interiorIndex.filter(i=>i.bounds[0]<=east&&i.bounds[2]>=west&&i.bounds[1]<=north&&i.bounds[3]>=south).map(i=>i.feature);
      const signature=visible.map(f=>f.properties.osm).join('|');
      if(signature!==interiorSignature){map.getSource('interiors').setData({type:'FeatureCollection',features:visible});interiorSignature=signature;}
    };
    map.on('moveend',()=>{if(!touring)updateInteriors();});
    const updateSolids=()=>{
      if(map.getZoom()<16.8){if(solidSignature){map.getSource('point-solids').setData({type:'FeatureCollection',features:[]});solidSignature='';}return;}
      const b=map.getBounds();const nearby=interiorData.features.filter(f=>f.geometry.type==='Point' && f.properties.kind==='bench' && b.contains(f.geometry.coordinates));
      const signature=nearby.map(f=>f.properties.osm).join('|');
      if(signature!==solidSignature){map.getSource('point-solids').setData(solids(nearby));solidSignature=signature;}
    };
    treeLayer=treeLibrary.createTreeLayer();window.parkTrees=treeLayer;map.addLayer(treeLayer);
    const updateTrees=()=>{
      const bounds=map.getBounds();
      treeLayer.update(map.getZoom()<17?[]:interiorData.features.filter(f=>f.properties.kind==='tree'&&f.geometry.type==='Point'&&bounds.contains(f.geometry.coordinates)));
    };
    map.on('moveend',()=>{if(!touring)updateTrees();});
    map.on('moveend',()=>{if(!touring)updateSolids();});
    refreshDetails=()=>{updateInteriors();updateSolids();updateTrees();};
    let lastDetails=0;
    map.on('move',()=>{
      if(performance.now()-lastDetails<450)return;
      lastDetails=performance.now();updateInteriors();updateSolids();updateTrees();
    });
    const textPaint={'text-color':'#254c32','text-halo-color':'#fbfcf3','text-halo-width':1.5};
    add('park-names','symbol','park-points',textPaint,{minzoom:12.5,layout:{'text-field':['get','name'],'text-font':['Noto Sans Regular'],'text-size':['interpolate',['linear'],['zoom'],12.5,11,16,15],'text-max-width':9,'text-padding':8}});
    add('interior-labels','symbol','interiors',textPaint,{minzoom:14.5,filter:['in',['get','kind'],['literal',['pitch','playground','water']]],layout:{'text-field':['case',['==',['get','kind'],'pitch'],['case',['==',['get','sport'],'soccer'],'Soccer pitch',['==',['get','sport'],'tennis'],'Tennis courts',['has','sport'],['concat',['get','sport'],' pitch'],'Sports pitch'],['==',['get','kind'],'playground'],'Playground',['coalesce',['get','name'],'Water']],'text-font':['Noto Sans Regular'],'text-size':11,'text-max-width':10,'text-padding':10}});
    map.on('click',e=>{
      const layers=['amenities-3d','bench-points','tree-points','amenity-points','play-area','pitch-area','water-area','water-lines','paths','parkland','park-dots'];
      const features=map.queryRenderedFeatures([[e.point.x-6,e.point.y-6],[e.point.x+6,e.point.y+6]],{layers});
      const treeHit=treeLayer.pick(e.point);const f=features[0]?.properties.kind==='bench'?features[0]:(treeHit||features[0]);
      if(!f)return;cancelTour();if(popup)popup.remove();const p=f.properties;
      if(p.kind==='bench'){const original=interiorData.features.find(item=>item.properties.osm===p.osm&&item.geometry.type==='Point');if(original){showBenchCallout(original);return;}}
      const root=document.createElement('div'), h=document.createElement('h3');h.textContent=p.name || ({bench:'Bench',tree:'Mapped tree',pitch:p.sport==='soccer'?'Soccer pitch':p.sport?p.sport+' pitch':'Sports pitch',playground:'Playground',path:'Park path',water:'Water'}[p.kind] || 'Parkland');root.append(h);
      const detail=document.createElement('p');detail.textContent=p.osm?['OpenStreetMap · '+p.osm,p.species||p.genus,p.kind==='tree'?'Illustrative '+treeLibrary.TREE_FORMS[treeLibrary.treeForm(p)].toLowerCase():null,p.surface,p.material,p.seats?p.seats+' seats':null].filter(Boolean).join(' · '):'Denver Parks & Recreation · '+p.class;root.append(detail);
      if(p.osm){const a=document.createElement('a');a.href='https://www.openstreetmap.org/'+p.osm;a.target='_blank';a.rel='noopener';a.textContent='View source feature ↗';root.append(a);}
      const at=f.geometry.type==='Point'?f.geometry.coordinates:e.lngLat;popup=new maplibregl.Popup({offset:10}).setLngLat(at).setDOMContent(root).addTo(map);
    });
    map.on('dragstart',()=>{cancelTour();activeStop(-1);announce('Explore Denver’s mapped details. Reload to replay the fly-through.');});
    map.on('zoomstart',e=>{if(e.originalEvent){cancelTour();activeStop(-1);}});
    map.on('rotatestart',e=>{if(e.originalEvent)cancelTour();});
    map.on('wheel',cancelTour);
    $('dimension').disabled=false;$('reset').disabled=false;
    map.fitBounds(qa.bounds,{padding:padding(),pitch:0,bearing:0,duration:0,maxZoom:11});activeStop(0);
    $('count').textContent=qa.parks_mapped+' parks mapped · City and County of Denver';
    map.once('idle',startTour);
    $('dates').textContent='Parkland updated '+qa.park_source_last_edit_utc.slice(0,10)+' · OSM snapshot '+qa.osm_timestamp.slice(0,10)+'.';
  });
}
$('dimension').onclick=()=>{cancelTour();map.stop();map.easeTo({pitch:map.getPitch()>5?0:50,duration:motion(850)});};
$('reset').onclick=()=>goToStop(0,false,true);
function startTour(){
  if(touring){cancelTour();map.stop();return;}
  goToStop(0,true,true);
  const start={center:map.getCenter().toArray(),zoom:map.getZoom(),padding:map.getPadding()};
  const inset=innerWidth<601?{top:225,bottom:70,left:25,right:25}:{top:110,bottom:70,left:380,right:60};
  const entry=qa.tour_entry||[(qa.washington_bounds[0]+qa.washington_bounds[2])/2,qa.washington_bounds[3]-.0007];
  if(reduced()){
    map.jumpTo(cameraPath.parkFlightCamera(1,start,qa.bench.coordinates,entry,inset,qa.tour_landmarks));
    activeStop(2);refreshDetails();benchPopup();return;
  }
  touring=true;const begin=performance.now(),duration=cameraPath.PARK_FLIGHT_DURATION_MS;
  const frame=now=>{
    if(!touring)return;
    const progress=cameraPath.parkFlightProgress(Math.min(duration,now-begin));
    const {label,phase,...camera}=cameraPath.parkFlightCamera(progress,start,qa.bench.coordinates,entry,inset,qa.tour_landmarks);
    map.jumpTo(camera);activeStop(phase==='city'?0:phase==='bench'?2:1);announce(label);
    if(progress<1){tourFrame=requestAnimationFrame(frame);return;}
    cancelTour();activeStop(2);refreshDetails();benchPopup();
  };
  tourFrame=requestAnimationFrame(frame);
}
window.parkPlayback={get running(){return touring;},play:startTour,stop(){cancelTour();if(map)map.stop();}};
function about(open){$('notes').hidden=!open;$('about').setAttribute('aria-expanded',String(open));if(open)$('close-about').focus();else $('about').focus();}
$('about').onclick=()=>about($('notes').hidden);$('close-about').onclick=()=>about(false);document.addEventListener('keydown',e=>{if(e.key==='Escape'){about(false);if(popup)popup.remove();}});
async function readJSON(path) {
  for(let attempt=0;attempt<3;attempt++) {
    try {const response=await fetch(path);if(!response.ok)throw Error(path+' ('+response.status+')');return await response.json();}
    catch(error){if(attempt===2)throw error;await new Promise(resolve=>setTimeout(resolve,250*(attempt+1)));}
  }
}
Promise.all([readJSON('data/qa.json'),readJSON('data/basemap.json'),readJSON('data/interiors.geojson'),Promise.all(['parks','boundary','park-points'].map(async name=>[name,await readJSON('data/'+name+'.geojson')])),import('./tree-layer.js?v=autumn-1'),import('./camera-path.js?v=park-roam-1'),import('./ground-texture.js?v=1')]).then(([q,s,i,staticLayers,trees,camera,ground])=>{groundTexture=ground;cameraPath=camera;treeLibrary=trees;staticSources=Object.fromEntries(staticLayers);qa=q;interiorData=i;interiorIndex=i.features.map(feature=>{
 const bounds=[Infinity,Infinity,-Infinity,-Infinity];
 function visit(c){if(typeof c[0]==='number'){bounds[0]=Math.min(bounds[0],c[0]);bounds[1]=Math.min(bounds[1],c[1]);bounds[2]=Math.max(bounds[2],c[0]);bounds[3]=Math.max(bounds[3],c[1]);}else c.forEach(visit);}
 if(feature.geometry.type==='GeometryCollection')feature.geometry.geometries.forEach(g=>visit(g.coordinates));else visit(feature.geometry.coordinates);
 return {feature,bounds};
});if(!qa.passed)throw Error('Data validation failed');init(s);}).catch(e=>fail('The map could not load. Serve this folder over HTTP and check your connection. '+e.message));
