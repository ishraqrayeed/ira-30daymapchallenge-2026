/* Day 23: an entirely local, buildless culinary atlas. No tile or routing API keys. */
'use strict';
const $=id=>document.getElementById(id),reduceMotion=matchMedia('(prefers-reduced-motion: reduce)');
const categories=[['all','All Food','সব খাবার'],['biryani','Biryani & Kacchi','বিরিয়ানি ও কাচ্চি'],['morog','Morog Polao','মোরগ পোলাও'],['khichuri','Khichuri','খিচুড়ি'],['bhaat','Bhaat & Bhorta','ভাত ও ভর্তা'],['kebab','Kebab & Grill','কাবাব ও গ্রিল'],['drinks','Lacchi & Drinks','লাচ্ছি ও শরবত'],['desserts','Mishti & Desserts','মিষ্টি ও মিষ্টান্ন'],['snacks','Bakarkhani & Snacks','বাখরখানি ও নাস্তা']];
const paths={all:'M4 5v7m3-7v7M3 9h5m-3 3v7M15 5c-3 3-3 7 0 8v6m1-14v14',biryani:'M3 11h18M5 11a7 7 0 0 0 14 0M8 7l1-2m3 2V4m3 3 1-2M7 19h10',morog:'M4 12h16M5 12a7 7 0 0 0 14 0M8 8c-1-3 2-3 1-6m4 6c-1-3 2-3 1-6M7 20h10',khichuri:'M4 10h16v4a6 6 0 0 1-6 5h-4a6 6 0 0 1-6-5zm3-3 1-2m4 2V3m4 4 1-2',bhaat:'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18m-4 7a4 4 0 0 1 8 0m-8 3h8m-7 3h6',kebab:'M5 3l14 18M4 8l6-4 3 4-6 4zm5 7 6-4 3 4-6 4z',drinks:'M6 6h12l-2 14H8zM7 10h10m-5-4 3-4h4',desserts:'M5 11h14l-2 8H7zm2 0c-2-5 2-7 5-5 3-2 7 0 5 5m-5-6V3',snacks:'M4 12a8 7 0 1 0 16 0 8 7 0 1 0-16 0m3-3 10 6M7 15l10-6M8 6l8 12M8 18l8-12'};
const state={category:'all',dish:'',neighborhood:'',selected:null,trail:[],panel:null,route:null,routeError:'',routing:false,ready:false,errors:[]};
window.addEventListener('error',e=>{if(e.message)state.errors.push(e.message)});
window.addEventListener('unhandledrejection',e=>state.errors.push(String(e.reason?.message||e.reason)));
let neighborhoodsData, map,places=[],byId=new Map(),worker,requestId=0,toastTimer,hoverId,routeFrame,routeToken=0;
const empty=()=>({type:'FeatureCollection',features:[]});
function el(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n}
function notify(text){$('toast').textContent=text;$('toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.remove('show'),3200)}
function duration(ms){return reduceMotion.matches?0:ms}
function iconMarkup(id){return `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[id]}"/></svg>`}
function canvasImage(text,color,size=12,weight=400){
 const canvas=document.createElement('canvas'),ctx=canvas.getContext('2d'),font=`${weight} ${size}px Arial`;ctx.font=font;canvas.width=Math.ceil(ctx.measureText(text).width+10)*2;canvas.height=(size+12)*2;ctx.scale(2,2);ctx.font=font;ctx.textBaseline='middle';ctx.lineWidth=4;ctx.strokeStyle='#F4F5F3';ctx.strokeText(text,5,(size+12)/2);ctx.fillStyle=color;ctx.fillText(text,5,(size+12)/2);return {width:canvas.width,height:canvas.height,data:ctx.getImageData(0,0,canvas.width,canvas.height).data};
}
async function categoryImage(id,light=false){
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24"><path d="${paths[id]}" fill="none" stroke="${light?'#FFFFFF':'#202523'}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
 const img=new Image();img.src=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml'}));await img.decode();map.addImage((light?'food-light-':'food-')+id,img,{pixelRatio:2});URL.revokeObjectURL(img.src);
}
async function loadJSON(url){const r=await fetch(url);if(!r.ok)throw Error(`Unable to load ${url} (${r.status}).`);return r.json()}
function padding(){return innerWidth<=700?{top:245,bottom:252,left:35,right:35}:{top:105,bottom:224,left:innerWidth>1100?430:335,right:state.panel?380:65}}
function fit(features,ms=550){if(!features.length)return;const box=turf.bbox(turf.featureCollection(features));map.setPadding({top:0,bottom:0,left:0,right:0});map.fitBounds([[box[0],box[1]],[box[2],box[3]]],{padding:padding(),maxZoom:16.4,retainPadding:false,duration:duration(ms)})}
function source(id,data,opts={}){map.addSource(id,{type:'geojson',data,...opts})}
function symbol(id,sourceId,image,extra={}){map.addLayer({id,type:'symbol',source:sourceId,layout:{'icon-image':image,...extra},paint:{'icon-opacity':1}})}
function setPanel(mode){state.panel=mode;$('panel').hidden=!mode;$('trail-toggle').setAttribute('aria-expanded',String(mode==='trail'));if(mode==='trail'){renderTrail();const h=$('panel-content').querySelector('h2');h.tabIndex=-1;h.focus({preventScroll:true})}}
function matching(){return places.filter(f=>FoodCore.matches(f.properties,state))}
function applyFilters(adjust=true){
 const matches=matching(),ids=new Set(matches.map(f=>f.id));for(const f of places)map.setFeatureState({source:'restaurants',id:f.id},{match:ids.has(f.id)});
 for(const b of $('categories').children)b.setAttribute('aria-pressed',String(b.dataset.category===state.category));
 $('dish').value=state.dish;$('neighborhood').value=state.neighborhood;
 let message=`${matches.length} ${matches.length===1?'destination':'destinations'}`;if(state.neighborhood)message+=' in '+state.neighborhood;else if(state.dish)message+=' · '+state.dish;else if(state.category==='all')message+=' · one extraordinary old city';else message+=' · '+categories.find(c=>c[0]===state.category)[1];$('result-count').textContent=message;
 for(const option of $('place').options)if(option.value)option.disabled=!ids.has(option.value);
 if(state.neighborhood&&matches.length)message+=' · '+[...new Set(matches.map(f=>f.properties.signature_food))].slice(0,2).join(' / ');$('result-count').textContent=message;
 if(adjust&&matches.length)fit(matches);if(adjust&&!matches.length&&state.neighborhood){const center=neighborhoodsData.features.find(f=>f.properties.name===state.neighborhood);if(center)fit([center]);}if(!matches.length)notify('No places match this combination. Choose another dish or neighborhood.');
}
function chooseCategory(id){state.category=id;state.dish='';applyFilters()}
function choosePlace(id){
 const f=byId.get(id);if(!f)return;state.selected=id;$('place').value=id;setPanel('place');renderCard(f);const heading=$('panel-content').querySelector('h2');heading.tabIndex=-1;heading.focus({preventScroll:true});
 
 for(const p of places)map.setFeatureState({source:'restaurants',id:p.id},{selected:p.id===id});
 map.setPadding({top:0,bottom:0,left:0,right:0});map.easeTo({retainPadding:false,center:f.geometry.coordinates,zoom:Math.max(map.getZoom(),15.7),padding:innerWidth<=700?{top:210,bottom:Math.min(innerHeight*.43+239,innerHeight-265),left:35,right:35}:{top:140,bottom:215,left:120,right:380},duration:duration(550)});
}
function renderCard(f){
 const p=f.properties,c=$('panel-content');c.replaceChildren();c.append(el('p','kicker',p.neighborhood),el('h2','',p.name));if(p.name_bn)c.append(el('p','name-bn',p.name_bn));c.append(el('p','signature',p.signature_food),el('p','story',p.story),el('p','address',p.address));
 const tags=el('div','tag-list');for(const dish of p.dish_tags){const b=el('button','',dish);b.onclick=()=>{state.dish=dish;state.category='all';state.neighborhood='';applyFilters()};tags.append(b)}c.append(tags);
 const add=el('button','primary',state.trail.includes(p.id)?'Added to your trail ✓':'+ Add to food trail');add.disabled=state.trail.includes(p.id);add.onclick=()=>addStop(p.id);c.append(add);
 const sources=el('p','sources');p.source_urls.forEach((url,i)=>{const a=el('a','',i===p.source_urls.length-1?'Location ↗':`Reference ${i+1} ↗`);a.href=url;a.target='_blank';a.rel='noopener';sources.append(a)});c.append(sources);
 const note=el('p','verification',p.operating_status);if(p.operating_status.includes('uncertain'))note.classList.add('uncertain');c.append(note);if(p.menu_note)c.append(el('p','route-note',p.menu_note));if(p.id==='makhan')c.append(el('p','route-note',p.coordinate_precision));
}
function addStop(id){if(state.trail.includes(id))return;if(state.trail.length>=5){notify('Your trail can include up to five stops. Remove one to add another.');return}state.trail.push(id);updateTrail();if(state.panel==='place')renderCard(byId.get(state.selected));notify(`Added ${byId.get(id).properties.name} · ${state.trail.length}/5 stops`)}
function updateStops(){
 if(!state.ready)return;const stops=state.trail.map((id,i)=>({type:'Feature',geometry:byId.get(id).geometry,properties:{number:String(i+1),id},id}));map.getSource('stops').setData(turf.featureCollection(stops));for(const f of places)map.setFeatureState({source:'restaurants',id:f.id},{'trail-dim':state.trail.length>=2&&!state.trail.includes(f.id)});$('trail-count').textContent=state.trail.length;
}
function clearRoute(){routeToken++;cancelAnimationFrame(routeFrame);map.getSource('trail').setData(empty());state.route=null;state.routeError='';state.routing=false}
function updateTrail(){
 requestId++;clearRoute();updateStops();if(state.trail.length>=2)calculateRoute();if(state.panel==='trail')renderTrail();
}
function calculateRoute(){
 const id=++requestId;state.routing=true;state.routeError='';
 if(!worker){state.routing=false;state.routeError='Walking routing is unavailable in this browser. Your stops are saved; no straight-line route is shown.';return}
 worker.postMessage({id,stops:state.trail.map(id=>byId.get(id).properties)});
}
function drawRoute(result){
 const features=result.geometry.coordinates.map(c=>turf.lineString(c));map.getSource('trail').setData(turf.featureCollection(features));
 const token=++routeToken,start=performance.now();function reveal(now){if(token!==routeToken)return;const t=reduceMotion.matches?1:Math.min(1,(now-start)/700);map.setPaintProperty('trail-core','line-gradient',['step',['line-progress'],'#486C6800',0,'#486C68',Math.max(.001,t),'#486C6800']);if(t<1)routeFrame=requestAnimationFrame(reveal)}routeFrame=requestAnimationFrame(reveal);
 // Turf independently measures the returned street geometry for the UI.
 state.route.geometry_km=features.reduce((sum,f)=>sum+turf.length(f),0);
}
function renderTrail(){
 const c=$('panel-content');c.replaceChildren();c.append(el('p','kicker','A walk, one bite at a time'),el('h2','','Your food trail'));
 c.append(el('p','empty',state.trail.length?'Choose 2–5 stops. Change the order to shape your walk.':'Start with a restaurant. Add two to five places and we’ll follow the mapped walking streets between them.'));
 const list=el('ol','trail-list');state.trail.forEach((id,i)=>{const li=el('li');li.append(el('span','stop-number',String(i+1)),el('span','stop-name',byId.get(id).properties.name));const actions=el('div','stop-actions');for(const [text,label,delta] of [['↑','Move earlier',-1],['↓','Move later',1],['×','Remove stop',0]]){const b=el('button','',text);b.setAttribute('aria-label',label+' '+byId.get(id).properties.name);b.disabled=(delta===-1&&i===0)||(delta===1&&i===state.trail.length-1);b.onclick=()=>{if(!delta)state.trail.splice(i,1);else [state.trail[i],state.trail[i+delta]]=[state.trail[i+delta],state.trail[i]];updateTrail();renderTrail()};actions.append(b)}li.append(actions);list.append(li)});c.append(list);
 if(state.routing)c.append(el('p','route-note','Finding your walk through the mapped streets…'));
 if(state.route){const r=state.route,p=el('p','route-summary',r.metres<1?'Shared street access':`${(r.metres/1000).toFixed(2)} km`);p.append(el('small','',r.metres<1?' · neighboring stops':` · ≈ ${Math.max(1,Math.round(r.minutes))} min walking`));c.append(p,el('p','route-note',`Street route at 4 km/h; stops and waiting time excluded. Access points are up to ${Math.ceil(Math.max(...state.trail.map(id=>byId.get(id).properties.walk_offset_m)))} m from mapped places. Entrances, temporary closures and street conditions are not surveyed.`));const walk=el('button','primary','See the whole walk ↗');walk.onclick=()=>fit(state.trail.map(id=>byId.get(id)),550);c.append(walk)}
 if(state.routeError)c.append(el('p','verification uncertain',state.routeError));
 if(state.trail.length){const clear=el('button','text-button','Clear food trail');clear.onclick=()=>{state.trail=[];updateTrail();fit(places);renderTrail()};c.append(clear)}
}
function bindControls(){
 for(const [id,name,bn] of categories){const b=el('button','category');b.dataset.category=id;b.setAttribute('aria-pressed',String(id==='all'));const icon=el('span','icon');icon.innerHTML=iconMarkup(id);const bengali=el('span','bn',bn);bengali.lang='bn';b.append(icon,el('strong','',name),bengali);b.onclick=()=>chooseCategory(id);$('categories').append(b)}
 const dishes=[...new Set(places.flatMap(f=>f.properties.dish_tags))].sort();for(const dish of dishes){const option=el('option','',dish);option.value=dish;$('dish').append(option)}
 const hood=[...new Set([...places.map(f=>f.properties.neighborhood),...neighborhoodsData.features.map(f=>f.properties.name)])].sort();for(const name of hood){const o=el('option','',name);o.value=name;$('neighborhood').append(o)}
 for(const f of [...places].sort((a,b)=>a.properties.name.localeCompare(b.properties.name))){const o=el('option','',f.properties.name);o.value=f.id;$('place').append(o)}
 $('place').onchange=e=>{if(e.target.value)choosePlace(e.target.value)};$('dish').onchange=e=>{state.dish=e.target.value;state.category='all';applyFilters()};$('neighborhood').onchange=e=>{state.neighborhood=e.target.value;applyFilters()};
 $('trail-toggle').onclick=()=>setPanel(state.panel==='trail'?null:'trail');$('close-panel').onclick=()=>{setPanel(null);$('trail-toggle').focus()};
 $('reset').onclick=()=>{state.category='all';state.dish='';state.neighborhood='';state.selected=null;state.trail=[];setPanel(null);$('place').value='';for(const f of places)map.setFeatureState({source:'restaurants',id:f.id},{selected:false});updateTrail();applyFilters(false);fit(places)};
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&state.panel){setPanel(null);$('place').focus()}});
}
async function main(){
 try{
  const [restaurants,streets,context,neighborhoods,landmarks]=await Promise.all(['restaurants','streets','context','neighborhoods','landmarks'].map(n=>loadJSON(`data/${n}.geojson`)));
  neighborhoodsData=neighborhoods;places=restaurants.features;byId=new Map(places.map(f=>[f.id,f]));
  map=new maplibregl.Map({container:'map',style:{version:8,sources:{},layers:[{id:'background',type:'background',paint:{'background-color':'#F4F5F3'}}]},center:[90.403,23.714],zoom:14.5,minZoom:12,maxZoom:19,attributionControl:false,renderWorldCopies:false,pitchWithRotate:false,dragRotate:false,touchPitch:false});
  map.addControl(new maplibregl.NavigationControl({showCompass:false}),'bottom-right');
  map.on('error',e=>{state.errors.push(e.error?.message||'Map asset error');notify('A map asset could not load. Try reloading the local HTTP page.')});
  await new Promise(resolve=>map.on('load',resolve));
  source('water',context);map.addLayer({id:'water',type:'fill',source:'water',paint:{'fill-color':'#E3EAED','fill-opacity':.86}});map.addLayer({id:'shore',type:'line',source:'water',paint:{'line-color':'#CAD5D7','line-width':.7,'line-opacity':.55}});
  source('streets',streets);map.addLayer({id:'street-shadow',type:'line',source:'streets',paint:{'line-color':'#CFD3D0','line-opacity':.1,'line-width':['interpolate',['linear'],['zoom'],13,2,17,6]},layout:{'line-cap':'round'}});
  map.addLayer({id:'street-lines',type:'line',source:'streets',layout:{'line-cap':'round','line-join':'round'},paint:{'line-color':['match',['get','highway'],['primary','secondary'],'#ADB4B0','#CFD3D0'],'line-width':['interpolate',['linear'],['zoom'],13,.45,15,['match',['get','highway'],['primary','secondary'],1.65,.8],18,['match',['get','highway'],['primary','secondary'],4,2]],'line-opacity':.54}});
  // Label sprites keep the atlas self-contained: no third-party glyph API or basemap requests.
  for(const f of neighborhoods.features){const name=f.properties.name;map.addImage('hood-'+name,canvasImage(name.toUpperCase(),'#626A67',10),{pixelRatio:2});f.properties.sprite='hood-'+name}source('neighborhoods',neighborhoods);symbol('neighborhood-labels','neighborhoods',['get','sprite'],{'icon-padding':35});map.setPaintProperty('neighborhood-labels','icon-opacity',.6);
  for(const f of landmarks.features){map.addImage('landmark-'+f.properties.name,canvasImage('◇ '+f.properties.name,'#626A67',11),{pixelRatio:2});f.properties.sprite='landmark-'+f.properties.name}source('landmarks',landmarks);symbol('landmark-labels','landmarks',['get','sprite'],{'icon-padding':12});
  map.addImage('river-label',canvasImage('B U R I G A N G A','#879A9F',12),{pixelRatio:2});
  const riverParts=context.features.filter(f=>f.geometry.type.includes('Polygon'));const riverPoint=turf.pointOnFeature(turf.featureCollection(riverParts));source('river-name',turf.featureCollection([riverPoint]));symbol('river-label','river-name','river-label',{'icon-padding':20});
  // Named streets are selected from real geometries, never drawn from invented centerlines.
  const names=streets.features.filter(f=>/Johnson|Nazimuddin|Alauddin|Islampur/i.test(f.properties.name));for(const f of names){const name=f.properties.name;if(!map.hasImage('road-'+name))map.addImage('road-'+name,canvasImage(name,'#89928D',9),{pixelRatio:2});f.properties.sprite='road-'+name}source('named-streets',turf.featureCollection(names));symbol('road-labels','named-streets',['get','sprite'],{'symbol-placement':'line','symbol-spacing':350,'icon-padding':20});map.setLayerZoomRange('road-labels',15.4,24);
  source('trail',empty(),{lineMetrics:true});map.addLayer({id:'trail-glow',type:'line',source:'trail',layout:{'line-cap':'round','line-join':'round'},paint:{'line-color':'#486C68','line-width':7,'line-blur':1,'line-opacity':.08}});map.addLayer({id:'trail-core',type:'line',source:'trail',layout:{'line-cap':'round','line-join':'round'},paint:{'line-color':'#486C68','line-width':4.5,'line-opacity':.95}});
  await Promise.all(categories.filter(c=>c[0]!=='all').flatMap(c=>[categoryImage(c[0]),categoryImage(c[0],true)]));
  for(const f of places){const p=f.properties;p.icon='food-'+p.category_ids[0];p.selected_icon='food-light-'+p.category_ids[0];p.sprite='place-'+p.id;map.addImage(p.sprite,canvasImage(p.name,p.flagship?'#202523':'#626A67',p.flagship?12:10,p.flagship?500:400),{pixelRatio:2})}
  source('restaurants',restaurants,{promoteId:'id'});
  const opacity=['case',['boolean',['feature-state','match'],true],['case',['boolean',['feature-state','trail-dim'],false],.2,1],.17],radius=['case',['boolean',['feature-state','hover'],false],15,['boolean',['feature-state','selected'],false],14,['get','flagship'],12,9];
  map.addLayer({id:'place-glow',type:'circle',source:'restaurants',paint:{'circle-radius':['case',['get','flagship'],27,18],'circle-color':'#486C68','circle-blur':.85,'circle-opacity':['case',['boolean',['feature-state','hover'],false],.1,0]}});
  map.addLayer({id:'place-rings',type:'circle',source:'restaurants',paint:{'circle-radius':['+',radius,4],'circle-color':'#486C68','circle-opacity':0,'circle-stroke-color':'#486C68','circle-stroke-width':['case',['boolean',['feature-state','selected'],false],1.4,0],'circle-stroke-opacity':opacity}});
  map.addLayer({id:'places',type:'circle',source:'restaurants',paint:{'circle-radius':radius,'circle-color':['case',['boolean',['feature-state','selected'],false],'#202523','#FFFFFF'],'circle-opacity':opacity,'circle-stroke-color':['case',['boolean',['feature-state','hover'],false],'#486C68','#202523'],'circle-stroke-width':1.35,'circle-radius-transition':{duration:180},'circle-stroke-color-transition':{duration:180}}});
  symbol('place-icons','restaurants',['get','icon'],{'icon-size':['case',['get','flagship'],.7,.52],'icon-allow-overlap':true,'icon-ignore-placement':true});map.setPaintProperty('place-icons','icon-opacity',['case',['boolean',['feature-state','selected'],false],0,opacity]);
  symbol('selected-icons','restaurants',['get','selected_icon'],{'icon-size':['case',['get','flagship'],.7,.52],'icon-allow-overlap':true,'icon-ignore-placement':true});map.setPaintProperty('selected-icons','icon-opacity',['case',['boolean',['feature-state','selected'],false],1,0]);
  symbol('place-labels','restaurants',['get','sprite'],{'icon-anchor':['case',['>',['get','longitude'],90.410],'right','left'],'icon-offset':['case',['>',['get','longitude'],90.410],['literal',[-16,0]],['literal',[16,0]]],'icon-padding':5,'symbol-sort-key':['case',['get','flagship'],0,1]});map.setPaintProperty('place-labels','icon-opacity',opacity);
  for(let i=1;i<=5;i++)map.addImage('stop-'+i,canvasImage(String(i),'#FFFFFF',15,600),{pixelRatio:2});source('stops',empty(),{promoteId:'id'});map.addLayer({id:'stop-circles',type:'circle',source:'stops',paint:{'circle-radius':14,'circle-color':'#202523','circle-stroke-color':'#FFFFFF','circle-stroke-width':2}});symbol('stop-numbers','stops',['concat','stop-',['get','number']],{'icon-allow-overlap':true,'icon-ignore-placement':true});
  const popup=new maplibregl.Popup({closeButton:false,closeOnClick:false,offset:18});
  map.on('mousemove','places',e=>{const id=e.features[0].id;map.getCanvas().style.cursor='pointer';if(hoverId!==undefined)map.setFeatureState({source:'restaurants',id:hoverId},{hover:false});hoverId=id;map.setFeatureState({source:'restaurants',id},{hover:true});const p=byId.get(id).properties,content=el('div');content.append(el('div','hover-name',p.name),el('div','hover-food',p.signature_food));popup.setLngLat(e.features[0].geometry.coordinates).setDOMContent(content).addTo(map)});
  map.on('mouseleave','places',()=>{map.getCanvas().style.cursor='';if(hoverId!==undefined)map.setFeatureState({source:'restaurants',id:hoverId},{hover:false});hoverId=undefined;popup.remove()});
  map.on('click','places',e=>{popup.remove();choosePlace(e.features[0].id)});
  map.on('click','stop-circles',e=>choosePlace(e.features[0].id));
  try{worker=new Worker('routing-worker.js');worker.onmessage=({data})=>{if(data.id!==requestId)return;state.routing=false;if(data.error)state.routeError=data.error;else{state.route=data.result;drawRoute(data.result)}if(state.panel==='trail')renderTrail()};worker.onerror=()=>{state.routing=false;state.routeError='Walking data could not be loaded. No straight-line substitute is shown.';if(state.panel==='trail')renderTrail()}}catch(e){state.errors.push(e.message)}
  state.ready=true;bindControls();applyFilters(false);fit(places,0);window.addEventListener('resize',()=>{map.resize()});
  window.Day23={state,map,places,get matching(){return matching()}};
 }catch(error){state.errors.push(error.message);$('map-error').hidden=false;$('map-error').textContent=error.message+' Open this page over local HTTP in a WebGL-capable browser, then reload.';$('result-count').textContent='The food map could not be loaded.';console.error(error)}
}
main();
