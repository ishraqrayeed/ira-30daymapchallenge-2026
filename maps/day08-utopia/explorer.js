/* Standalone geographic explorer: generated HTML embeds this file, with no runtime dependencies. */
const canvas=document.querySelector('#canvas'),svg=canvas.querySelector('svg'),sel=document.querySelector('#route'),tip=document.querySelector('#tip'),legend=document.querySelector('#legend');
const allButton=document.querySelector('#all-services'),statusText=document.querySelector('#selection-status'),railNote=document.querySelector('#rail-note');
const W=1200,H=1200*940/1130,NS='http://www.w3.org/2000/svg';
let scale=1,fitScale=1,level=1,tx=0,ty=0,drag=null,moved=false,popupStation=null,pinchDistance=null,selected='',mode='utopia';
const pointers=new Map(),stationById=Object.fromEntries(MAP_DATA.stations.map(s=>[s.id,s])),routes=Object.fromEntries(MAP_DATA.lines.map(f=>[f.properties.id,f.properties]));
const memberships=Object.fromEntries(MAP_DATA.stations.map(s=>[s.id,new Set()]));
for(const line of MAP_DATA.lines)for(const id of line.properties.stations)memberships[id].add(line.properties.id);
const majorIds=new Set(['dallas','fw','arlington','dfw','denton','frisco','plano','mckinney']);
const terminalIds=new Set(MAP_DATA.lines.flatMap(f=>[f.properties.stations[0],f.properties.stations.at(-1)]));
const stationNodes=[...document.querySelectorAll('.station')];
const stationPoints=stationNodes.map(node=>{const circle=node.querySelector('circle:last-of-type');return{id:node.dataset.station,x:Number(circle.getAttribute('cx')),y:Number(circle.getAttribute('cy')),radius:Number(circle.getAttribute('r'))}});
const labelsGroup=document.createElementNS(NS,'g');labelsGroup.id='dynamic-labels';svg.append(labelsGroup);
const measureContext=document.createElement('canvas').getContext('2d');
function measure(text,size,weight){measureContext.font=`${weight} ${size}px Helvetica,Arial,sans-serif`;return measureContext.measureText(text).width;}
function overlaps(a,b){return a[0]<b[2]&&a[2]>b[0]&&a[1]<b[3]&&a[3]>b[1];}
function screenPoint(point){const ratio=scale*W/1130;return{x:tx+(point.x-35)*ratio,y:ty+(point.y-305)*ratio,radius:Math.max(3,point.radius*ratio)}}
function popupInfo(id){const s=stationById[id],services=[...memberships[id]].map(key=>routes[key]);return{id,name:s.name,services,transfer:services.length>=2,conceptual:true,anchor:s.anchor};}
/* Pure placement in screen pixels makes collision checks independent of zoom scale. */
function computeLabels(points,zoomLevel,chosen,width,height,measureText){
 const visible=points.map(point=>({...point,...screenPoint(point)})).filter(p=>p.x>-50&&p.x<width+50&&p.y>-50&&p.y<height+50);
 const obstacles=visible.map(p=>[p.x-p.radius-3,p.y-p.radius-3,p.x+p.radius+3,p.y+p.radius+3]);
 const candidates=visible.filter(p=>{
  if(majorIds.has(p.id))return true;
  if(terminalIds.has(p.id))return zoomLevel>=1.4;
  if(chosen&&memberships[p.id].has(chosen))return zoomLevel>=1.65;
  if(memberships[p.id].size>=2)return zoomLevel>=1.9;
  return zoomLevel>=2.8;
 }).sort((a,b)=>{
  const priority=p=>(majorIds.has(p.id)?1000:0)+(chosen&&memberships[p.id].has(chosen)?500:0)+(terminalIds.has(p.id)?180:0)+memberships[p.id].size*10;
  return priority(b)-priority(a)||a.id.localeCompare(b.id);
 });
 const placed=[],boxes=[];
 for(const p of candidates){
  const major=majorIds.has(p.id),size=major?13:12,weight=major?750:600,text=stationById[p.id].name,tw=measureText(text,size,weight),gap=p.radius+7;
  const choices=[[gap,-8,'start'],[gap,size+5,'start'],[-gap,-8,'end'],[-gap,size+5,'end'],[0,-gap-3,'middle'],[0,gap+size,'middle'],[gap+10,4,'start'],[-gap-10,4,'end'],[0,-gap-20,'middle'],[0,gap+size+16,'middle']];
  for(const [dx,dy,anchor] of choices){const x=p.x+dx,y=p.y+dy,left=x-(anchor==='end'?tw:anchor==='middle'?tw/2:0),box=[left-5,y-size-4,left+tw+5,y+6];
   if(box[0]<10||box[2]>width-10||box[1]<10||box[3]>height-10)continue;
   if(boxes.some(b=>overlaps(box,b))||obstacles.some(b=>overlaps(box,b)))continue;
   placed.push({id:p.id,text,x,y,anchor,size,weight,box,muted:!!chosen&&!memberships[p.id].has(chosen)});boxes.push(box);break;
  }
 }
 return placed;
}
let currentLabels=[];
function drawLabels(){
 currentLabels=computeLabels(stationPoints,level,selected,canvas.clientWidth,canvas.clientHeight,measure);labelsGroup.replaceChildren();const ratio=scale*W/1130;
 for(const l of currentLabels){const text=document.createElementNS(NS,'text');text.textContent=l.text;text.setAttribute('data-label',l.id);text.setAttribute('class','map-label');text.setAttribute('x',35+(l.x-tx)/ratio);text.setAttribute('y',305+(l.y-ty)/ratio);text.setAttribute('text-anchor',l.anchor);text.style.fontSize=(l.size/ratio)+'px';text.style.fontWeight=String(l.weight);text.style.fill='#172326';text.style.paintOrder='stroke';text.style.stroke='#f4f1e8';text.style.strokeWidth=String(3/ratio);text.style.strokeLinejoin='round';text.style.opacity=l.muted?'.4':'1';labelsGroup.append(text)}
}
function routeBadge(id,popup=false){const p=routes[id],button=document.createElement('button');button.type='button';button.dataset.select=id;button.setAttribute('aria-label',`Highlight ${id} · ${p.name}`);button.setAttribute('aria-pressed',String(selected===id));
 if(popup){button.className='popup-route';button.textContent=id;button.style.background=p.color}else{button.className='route-choice';const badge=document.createElement('span'),name=document.createElement('span');badge.className='badge';badge.textContent=id;badge.style.background=p.color;name.textContent=p.name;button.append(badge,name)}
 button.onclick=()=>highlight(selected===id?'':id);return button;
}
for(const f of MAP_DATA.lines){const p=f.properties,option=document.createElement('option');option.value=p.id;option.textContent=p.id+' · '+p.name;sel.append(option);legend.append(routeBadge(p.id));}
function highlight(id){if(mode==='reality'&&id)return;selected=routes[id]?id:'';sel.value=selected;
 document.querySelectorAll('.service').forEach(g=>{g.classList.toggle('dim',!!selected&&g.dataset.route!==selected);g.classList.toggle('selected',g.dataset.route===selected)});
 stationNodes.forEach(g=>g.classList.toggle('dim',!!selected&&!memberships[g.dataset.station].has(selected)));
 document.querySelectorAll('[data-select]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.select===selected)));
 statusText.textContent=selected?`${selected} · ${routes[selected].name}`:'Explore all 10 services';drawLabels();
 if(selected){const button=[...legend.children].find(b=>b.dataset.select===selected);button?.scrollIntoView({block:'nearest',inline:'nearest',behavior:window.matchMedia?.('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});}
}
allButton.onclick=()=>highlight('');sel.onchange=()=>highlight(sel.value);
function positionPopup(){if(!popupStation)return;const point=stationPoints.find(p=>p.id===popupStation),pos=screenPoint(point),width=tip.offsetWidth||270,height=tip.offsetHeight||160;tip.style.left=Math.max(8,Math.min(canvas.clientWidth-width-8,pos.x+14))+'px';tip.style.top=Math.max(8,Math.min(canvas.clientHeight-height-8,pos.y+14))+'px';}
function closePopup(){popupStation=null;tip.style.display='none';}
function openStation(id){if(mode==='reality')return;const info=popupInfo(id);popupStation=id;tip.replaceChildren();const close=document.createElement('button'),heading=document.createElement('h2'),badges=document.createElement('div'),transfer=document.createElement('p'),note=document.createElement('p');
 close.type='button';close.className='popup-close';close.textContent='×';close.setAttribute('aria-label','Close station details');close.onclick=closePopup;heading.textContent=info.name;badges.className='popup-services';badges.setAttribute('aria-label','Services stopping here');for(const p of info.services)badges.append(routeBadge(p.id,true));transfer.className='transfer-note';transfer.textContent=info.transfer?`Transfer station · ${info.services.length} services`:'Single-service station';note.className='concept-note';note.textContent='Conceptual station in a fictional subway network.';tip.append(close,heading,badges,transfer,note);
 if(info.anchor==='Existing rail station'){const anchor=document.createElement('p');anchor.className='popup-anchor';anchor.textContent='An existing rail station provides this geographic anchor.';tip.append(anchor)}
 tip.style.display='block';positionPopup();
}
function draw(){const sw=W*scale,sh=H*scale;tx=sw<=canvas.clientWidth?(canvas.clientWidth-sw)/2:Math.min(0,Math.max(canvas.clientWidth-sw,tx));ty=sh<=canvas.clientHeight?(canvas.clientHeight-sh)/2:Math.min(0,Math.max(canvas.clientHeight-sh,ty));svg.style.transform=`translate(${tx}px,${ty}px) scale(${scale})`;canvas.classList.toggle('can-pan',level>1.001);drawLabels();positionPopup();}
function reset(){fitScale=Math.min(canvas.clientWidth/W,canvas.clientHeight/H);level=1;scale=fitScale;tx=0;ty=0;pointers.clear();drag=null;moved=false;closePopup();draw();}
function zoom(f,cx=canvas.clientWidth/2,cy=canvas.clientHeight/2){const old=scale;level=Math.max(1,Math.min(8,level*f));scale=fitScale*level;tx=cx-(cx-tx)*scale/old;ty=cy-(cy-ty)*scale/old;draw();}
document.querySelector('#plus').onclick=()=>zoom(1.35);document.querySelector('#minus').onclick=()=>zoom(1/1.35);document.querySelector('#reset').onclick=reset;
function setMode(next){
 mode=next;closePopup();highlight('');
 document.querySelector('.explorer').classList.toggle('reality',mode==='reality');
 for(const key of ['reality','utopia'])document.querySelector('#'+key).setAttribute('aria-pressed',String(mode===key));
 sel.disabled=mode==='reality';allButton.disabled=mode==='reality';
 for(const button of legend.children)button.disabled=mode==='reality';
 document.querySelectorAll('.service').forEach(node=>node.setAttribute('aria-hidden',String(mode==='reality')));
 stationNodes.forEach(node=>{node.setAttribute('tabindex',mode==='reality'?'-1':'0');node.setAttribute('aria-hidden',String(mode==='reality'))});
 const compare=document.querySelector('#compare');compare.disabled=mode==='reality';
 updateRail();statusText.textContent=mode==='reality'?'Existing rail · source snapshots':'Explore all 10 services';
}
function updateRail(){const show=mode==='reality'||document.querySelector('#compare').checked;document.querySelector('#existing').setAttribute('visibility',show?'visible':'hidden');railNote.hidden=!show;}
document.querySelector('#reality').onclick=()=>setMode('reality');document.querySelector('#utopia').onclick=()=>setMode('utopia');
document.querySelector('#compare').onchange=()=>{updateRail();reset();};
canvas.addEventListener('wheel',e=>{e.preventDefault();const rect=canvas.getBoundingClientRect();zoom(Math.exp(-e.deltaY*.002),e.clientX-rect.left,e.clientY-rect.top)},{passive:false});
for(const node of stationNodes){node.setAttribute('role','button');node.setAttribute('aria-label',`${stationById[node.dataset.station].name}, ${memberships[node.dataset.station].size} conceptual services`);node.onclick=()=>{if(!moved)openStation(node.dataset.station)};node.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();openStation(node.dataset.station)}};}
canvas.onpointerdown=e=>{pointers.set(e.pointerId,[e.clientX,e.clientY]);if(pointers.size===1){drag={x:e.clientX,y:e.clientY,tx,ty};moved=false}if(pointers.size===2){const[a,b]=[...pointers.values()];pinchDistance=Math.hypot(a[0]-b[0],a[1]-b[1]);drag=null;moved=true}if(!e.target.closest('.station'))canvas.setPointerCapture(e.pointerId);};
canvas.onpointermove=e=>{if(!pointers.has(e.pointerId))return;pointers.set(e.pointerId,[e.clientX,e.clientY]);if(pointers.size===2){const[a,b]=[...pointers.values()],distance=Math.hypot(a[0]-b[0],a[1]-b[1]),rect=canvas.getBoundingClientRect();if(pinchDistance>0)zoom(distance/pinchDistance,(a[0]+b[0])/2-rect.left,(a[1]+b[1])/2-rect.top);pinchDistance=distance;moved=true}else if(drag&&level>1.001){const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.hypot(dx,dy)>4)moved=true;tx=drag.tx+dx;ty=drag.ty+dy;draw()}};
canvas.onpointerup=e=>{pointers.delete(e.pointerId);pinchDistance=null;drag=null;if(!e.target.closest('.station')&&!moved)closePopup();};canvas.onpointercancel=e=>{pointers.delete(e.pointerId);drag=null;pinchDistance=null;};
canvas.onkeydown=e=>{if(['+','=','-','Escape','Home','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.key))e.preventDefault();if(e.key==='+'||e.key==='=')zoom(1.35);if(e.key==='-')zoom(1/1.35);if(e.key==='Home')reset();if(e.key==='Escape'){closePopup();highlight('')}if(level>1.001){if(e.key==='ArrowLeft')tx+=50;if(e.key==='ArrowRight')tx-=50;if(e.key==='ArrowUp')ty+=50;if(e.key==='ArrowDown')ty-=50}draw();};
window.addEventListener('resize',reset);if(typeof ResizeObserver!=='undefined')new ResizeObserver(reset).observe(canvas);reset();
/* Read-only state supports reproducible interaction and screen-space label QA. */
function explorerState(){return{mode,selected,level,scale,tx,ty,popupStation,labels:currentLabels.map(l=>({...l})),markerCount:stationNodes.length};}
