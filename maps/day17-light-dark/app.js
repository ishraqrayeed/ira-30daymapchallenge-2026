import * as THREE from './vendor/three.module.js';
import {DURATION,HOLD,TRAVEL,distanceAt,positionAt,nearestDistance} from './core.js';
const $=id=>document.getElementById(id),params=new URLSearchParams(location.search),capture=params.has('capture');
if(capture)document.body.classList.add('capture');
const reduced=matchMedia('(prefers-reduced-motion: reduce)'),state={ready:false,time:reduced.matches?15:0,paused:true,data:null,panels:[],errors:[]};
window.Replay=state;
const ink={jfk:0x70d6c6,den:0xefb86f};
function planeGeometry(){const s=new THREE.Shape();const points=[[0,1350],[160,950],[190,330],[1080,-120],[1080,-350],[180,-130],[140,-750],[440,-970],[440,-1110],[0,-940],[-440,-1110],[-440,-970],[-140,-750],[-180,-130],[-1080,-350],[-1080,-120],[-190,330],[-160,950]];points.forEach(([x,y],i)=>i?s.lineTo(x,y):s.moveTo(x,y));s.closePath();return new THREE.ShapeGeometry(s);}
function ribbonGeometry(route,width){
 const verts=[];for(let i=0;i<route.length-1;i++){const a=route[i],b=route[i+1],dx=b[0]-a[0],dy=b[1]-a[1],len=Math.hypot(dx,dy)||1,nx=-dy/len*width/2,ny=dx/len*width/2;verts.push(a[0]+nx,a[1]+ny,1,a[0]-nx,a[1]-ny,1,b[0]+nx,b[1]+ny,1,b[0]+nx,b[1]+ny,1,a[0]-nx,a[1]-ny,1,b[0]-nx,b[1]-ny,1);}
 const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(verts,3));return geometry;
}
function seekDistance(miles){pause();const m=Math.max(0,Math.min(5,miles));seek(m>=5?DURATION:m<=0?0:HOLD+TRAVEL*m/5);}
function pointerWorld(panel,event){const rect=panel.renderer.domElement.getBoundingClientRect(),c=panel.camera;return {x:c.position.x+c.left+(event.clientX-rect.left)/rect.width*(c.right-c.left),y:c.position.y+c.top-(event.clientY-rect.top)/rect.height*(c.top-c.bottom),pixelsPerMeter:rect.width/(c.right-c.left)};}
function mapPlaneDrag(panel){
 const host=panel.host;
 const onPlane=e=>{const q=pointerWorld(panel,e);return Math.hypot(q.x-panel.plane.position.x,q.y-panel.plane.position.y)*q.pixelsPerMeter<=(e.pointerType==='touch'?44:34);};
 host.addEventListener('pointerdown',e=>{if(!state.ready||e.button!==0||!onPlane(e))return;pause();state.drag={kind:'map',panel,pointer:e.pointerId};host.setPointerCapture(e.pointerId);host.style.cursor='grabbing';e.preventDefault();});
 host.addEventListener('pointermove',e=>{if(state.drag?.panel===panel&&state.drag.pointer===e.pointerId){const q=pointerWorld(panel,e);seekDistance(nearestDistance(panel.p.route,q.x,q.y));e.preventDefault();}else if(state.ready&&!state.drag)host.style.cursor=onPlane(e)?'grab':'';});
 const end=e=>{if(state.drag?.panel===panel&&state.drag.pointer===e.pointerId){state.drag=null;host.style.cursor='grab';if(host.hasPointerCapture(e.pointerId))host.releasePointerCapture(e.pointerId);}};
 host.addEventListener('pointerup',end);host.addEventListener('pointercancel',end);
}
function makePanel(p){
 const host=$(p.id+'-map'),scene=new THREE.Scene();scene.background=new THREE.Color(0x050c19);
 const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,preserveDrawingBuffer:capture});renderer.setPixelRatio(capture?1:Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.setClearColor(0x050c19);host.appendChild(renderer.domElement);renderer.domElement.setAttribute('aria-label',p.id==='jfk'?'Night map and recorded path leaving JFK':'Night map and recorded path arriving at Denver');renderer.domElement.setAttribute('role','img');
 const camera=new THREE.OrthographicCamera(-16000,16000,12000,-12000,.1,100);camera.position.z=10;
 const panel={p,host,scene,renderer,camera,labels:[]};
 const texture=new THREE.TextureLoader().load('data/'+p.id+'-hybrid.png?v=warm5',()=>{panel.loaded=true;render();});texture.colorSpace=THREE.SRGBColorSpace;texture.minFilter=THREE.LinearFilter;texture.magFilter=THREE.LinearFilter;
 const ground=new THREE.Mesh(new THREE.PlaneGeometry(p.span_m,p.span_m),new THREE.MeshBasicMaterial({map:texture,depthTest:false}));scene.add(ground);
 const path=new THREE.Mesh(ribbonGeometry(p.route,30),new THREE.MeshBasicMaterial({color:p.id==='jfk'?0xa4f4df:0xffd596,transparent:true,opacity:.88,depthTest:false}));path.renderOrder=3;scene.add(path);panel.path=path;
 const glow=new THREE.Mesh(ribbonGeometry(p.route,110),new THREE.MeshBasicMaterial({color:ink[p.id],transparent:true,opacity:.15,depthTest:false}));glow.renderOrder=2;scene.add(glow);panel.glow=glow;
 panel.tail=[];for(let i=0;i<36;i++){const mesh=new THREE.Mesh(new THREE.PlaneGeometry(1,1),new THREE.MeshBasicMaterial({color:ink[p.id],transparent:true,opacity:.8*(i+1)/36,depthTest:false}));mesh.renderOrder=3;scene.add(mesh);panel.tail.push(mesh);}
 const plane=new THREE.Mesh(planeGeometry(),new THREE.MeshBasicMaterial({color:0xffffff,depthTest:false}));plane.scale.setScalar(.65);plane.position.z=3;plane.renderOrder=5;scene.add(plane);panel.plane=plane;
 const ring=new THREE.Mesh(new THREE.RingGeometry(140,185,32),new THREE.MeshBasicMaterial({color:0xf3f6fa,transparent:true,opacity:.7,depthTest:false}));ring.position.set(...p.airport_xy,2);ring.renderOrder=3;scene.add(ring);
 for(const {text:name,xy,kind} of p.labels){const el=document.createElement('span');el.className='map-label '+(kind||'');el.textContent=name;host.querySelector('.map-labels').appendChild(el);panel.labels.push({el,xy});}
 const airportEl=document.createElement('span');airportEl.className='map-label airport';airportEl.textContent=p.id.toUpperCase();host.querySelector('.map-labels').appendChild(airportEl);const labelAnchor=p.id==='den'?p.route.at(-1):p.airport_xy;panel.labels.push({el:airportEl,xy:[labelAnchor[0]+1500,labelAnchor[1]+700]});
 mapPlaneDrag(panel);host.querySelector('.fallback').style.visibility='hidden';new ResizeObserver(()=>render()).observe(host);return panel;
}
function updatePanel(panel,miles){const {p,host,renderer,camera,plane,path,tail}=panel,w=host.clientWidth,h=host.clientHeight,halfH=Math.max(6000,8000*h/w),halfW=halfH*w/h;
 if(renderer.domElement.width!==Math.round(w*renderer.getPixelRatio())||renderer.domElement.height!==Math.round(h*renderer.getPixelRatio()))renderer.setSize(w,h,false);
 const xs=p.route.map(v=>v[0]),ys=p.route.map(v=>v[1]),cx=(Math.min(...xs)+Math.max(...xs))/2,cy=(Math.min(...ys)+Math.max(...ys))/2;camera.position.x=cx;camera.position.y=cy;camera.left=-halfW;camera.right=halfW;camera.top=halfH;camera.bottom=-halfH;camera.updateProjectionMatrix();
 const pt=positionAt(p.route,miles);plane.visible=true;plane.position.set(pt.x,pt.y,3);plane.rotation.z=pt.angle;
 const coreWidth=(2*halfW/w)*2.0;if(panel.coreWidth!==coreWidth){panel.coreWidth=coreWidth;path.geometry.dispose();panel.glow.geometry.dispose();path.geometry=ribbonGeometry(p.route,coreWidth);panel.glow.geometry=ribbonGeometry(p.route,coreWidth*3);}
 const drawn=(miles>=5?p.route.length-1:pt.index)*6;path.geometry.setDrawRange(0,drawn);panel.glow.geometry.setDrawRange(0,drawn);
 tail.forEach((mesh,i)=>{const a=miles-1.2+(i/36)*1.2,b=miles-1.2+((i+1)/36)*1.2;if(a<0||state.time<1.3){mesh.visible=false;return;}mesh.visible=true;const pa=positionAt(p.route,a),pb=positionAt(p.route,b),dx=pb.x-pa.x,dy=pb.y-pa.y;mesh.position.set((pa.x+pb.x)/2,(pa.y+pb.y)/2,2);mesh.scale.set(Math.hypot(dx,dy)+25,100+50*i/36,1);mesh.rotation.z=Math.atan2(dy,dx);});
 for(const {el,xy} of panel.labels){const x=(xy[0]-cx+halfW)/(2*halfW)*w,y=(halfH-xy[1]+cy)/(2*halfH)*h;el.style.left=x+'px';el.style.top=y+'px';el.style.display=x>12&&x<w-12&&y>12&&y<h-12?'':'none';}
 host.querySelector('.scale i').style.width=(2*1609.344/(2*halfW)*w)+'px';renderer.render(panel.scene,camera);
}
function distanceLabel(miles){return miles>=5?'5.0':(Math.floor((miles+1e-8)*10)/10).toFixed(1);}
function render(){if(!state.data)return;if(capture)document.querySelector('.metric').style.opacity=Math.max(0,Math.min(1,(state.time-12.3)/.6));const miles=distanceAt(state.time);state.panels.forEach(p=>updatePanel(p,miles));updateChartPlanes(miles);$('jfk-mile').innerHTML=`${distanceLabel(miles)} <span>/ 5 mi</span>`;$('den-mile').innerHTML=`${distanceLabel(miles)} <span>/ 5 mi</span>`;$('play').textContent=state.paused?'▶':'Ⅱ';$('play').title=state.paused?'Play':'Pause';$('play').setAttribute('aria-label',state.paused?'Play distance comparison':'Pause distance comparison');}
function seek(t){state.time=Math.max(0,Math.min(DURATION,t));render();}function pause(){state.paused=true;render();}function play(){if(state.time>=15)state.time=0;state.paused=false;render();}
Object.assign(state,{seek,pause,play,render,distanceAt,seekDistance});

$('play').onclick=()=>state.paused?play():pause();
let last=performance.now();function tick(now){const dt=Math.min((now-last)/1000,.1);last=now;if(state.ready&&!state.paused){state.time=Math.min(15,state.time+dt);if(state.time===15)state.paused=true;render();}requestAnimationFrame(tick);}requestAnimationFrame(tick);
document.addEventListener('visibilitychange',()=>{if(document.hidden)pause();});reduced.addEventListener('change',()=>{if(reduced.matches){pause();seek(15);}});
function chart(data){const W=$('chart').clientWidth,H=$('chart').clientHeight,left=40,top=19,bottom=H-33,max=40;const X=m=>left+m/5*(W-left-14),Y=v=>bottom-v/max*(bottom-top),font=W<600?9:10;let s=`<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg"><title>2024 VIIRS relative brightness by distance flown within each segment. DEN runs from five miles out to the last recorded position.</title>`;
 for(const v of [0,20,40])s+=`<line x1="${left}" x2="${W-14}" y1="${Y(v)}" y2="${Y(v)}" stroke="#253141"/><text x="31" y="${Y(v)+3}" text-anchor="end" fill="#9eacbb" font-size="${font}">${v}</text>`;
 for(const p of data.panels){const col=p.id==='jfk'?'#70d6c6':'#efb86f';s+=`<path d="${p.profile.map((r,i)=>(i?'L':'M')+X(r.mile)+','+Y(r.median_stored_value)).join(' ')}" fill="none" stroke="${col}" stroke-width="1.8"/>`;}
 for(const m of [0,1,2,3,4,5])s+=`<text x="${X(m)}" y="${H-19}" text-anchor="middle" fill="#9eacbb" font-size="${font}">${m} mi</text>`;

 for(const p of data.panels){const color=p.id==='jfk'?'#70d6c6':'#efb86f';s+=`<g id="chart-plane-${p.id}" role="slider" tabindex="0" aria-valuemin="0" aria-valuemax="5" aria-label="${p.id.toUpperCase()} replay position; drag or use arrow keys"><circle r="11" fill="${color}" opacity=".16"/><path d="M0 -8 L1 -5 L1 -2 L7 1 L7 3 L1 1 L1 6 L3 8 L3 9 L0 7 L-3 9 L-3 8 L-1 6 L-1 1 L-7 3 L-7 1 L-1 -2 L-1 -5 Z" transform="rotate(90) scale(1.3)" fill="#fff" stroke="${color}" stroke-width=".7" stroke-linejoin="round"/></g>`;}
 s+=`<text x="${(W+left)/2}" y="${H-4}" text-anchor="middle" fill="#b0bdca" font-size="${font}">Distance flown within each segment</text><text x="11" y="${(top+bottom)/2}" transform="rotate(-90 11 ${(top+bottom)/2})" text-anchor="middle" fill="#a5b2c1" font-size="${font}">Relative brightness</text><text x="40" y="10" fill="#8b9caf" font-size="${font}">2024 VIIRS</text><text x="${W-153}" y="10" fill="#70d6c6" font-size="${font}">JFK · leaving</text><text x="${W-77}" y="10" fill="#efb86f" font-size="${font}">DEN · arriving</text></svg>`;$('chart').innerHTML=s;state.chartScale={left,top,bottom,width:W,max};updateChartPlanes(distanceAt(state.time));}
function updateChartPlanes(miles){
 const scale=state.chartScale;if(!scale||!state.data)return;const x=scale.left+miles/5*(scale.width-scale.left-14),cursor=$('chart-progress');cursor?.setAttribute('x1',x);cursor?.setAttribute('x2',x);
 for(const p of state.data.panels){const lo=Math.min(4,Math.floor(miles)),f=Math.min(1,miles-lo),value=p.profile[lo].median_stored_value*(1-f)+p.profile[lo+1].median_stored_value*f,y=scale.bottom-value/scale.max*(scale.bottom-scale.top),plane=$('chart-plane-'+p.id);plane?.setAttribute('transform',`translate(${x} ${y})`);plane?.setAttribute('data-mile',miles.toFixed(4));plane?.setAttribute('aria-valuenow',miles.toFixed(2));plane?.setAttribute('aria-label',`${p.id.toUpperCase()} at ${miles.toFixed(1)} miles flown, relative brightness ${value.toFixed(1)}`);}
}
const chartHost=$('chart');
chartHost.addEventListener('pointerdown',e=>{if(!state.ready||e.button!==0||!e.target.closest('[id^="chart-plane-"]'))return;pause();state.drag={kind:'chart',pointer:e.pointerId};chartHost.setPointerCapture(e.pointerId);chartHost.style.cursor='grabbing';e.preventDefault();});
chartHost.addEventListener('pointermove',e=>{if(state.drag?.kind!=='chart'||state.drag.pointer!==e.pointerId)return;const rect=chartHost.getBoundingClientRect(),c=state.chartScale;seekDistance((e.clientX-rect.left-c.left)/(c.width-c.left-14)*5);e.preventDefault();});
for(const event of ['pointerup','pointercancel'])chartHost.addEventListener(event,e=>{if(state.drag?.kind==='chart'&&state.drag.pointer===e.pointerId){state.drag=null;chartHost.style.cursor='';if(chartHost.hasPointerCapture(e.pointerId))chartHost.releasePointerCapture(e.pointerId);}});
chartHost.addEventListener('keydown',e=>{if(!e.target.closest('[id^="chart-plane-"]'))return;const keys={ArrowLeft:-.05,ArrowRight:.05,Home:-5,End:5};if(e.key in keys){seekDistance(distanceAt(state.time)+keys[e.key]);e.preventDefault();}});
new ResizeObserver(()=>{if(state.data)chart(state.data)}).observe($('chart'));
(async()=>{try{const response=await fetch('data/replay.json');if(!response.ok)throw Error('Flight data unavailable');state.data=await response.json();const d=state.data;$('ratio').textContent=d.ratio.toFixed(1)+'×';if($('finding'))$('finding').textContent=`Along this flight’s two segments, the median of the JFK profile is ${d.ratio.toFixed(1)} times the median of the Denver profile (${d.panels[0].profile_median} versus ${d.panels[1].profile_median} stored brightness units). This compares typical ground brightness, not light seen by a passenger.`;
 for(const p of d.panels){const format=t=>new Intl.DateTimeFormat('en-US',{timeZone:p.id==='jfk'?'America/New_York':'America/Denver',hour:'numeric',minute:'2-digit'}).format(new Date(t));$(p.id+'-time').textContent=format(p.start_utc)+' – '+format(p.end_utc)+(p.id==='jfk'?' EDT':' MDT');}
 if($('track-note'))$('track-note').textContent=`Verified DAL424, N533DT, a6bbef; KJFK → KDEN. The API returns ${d.flight.point_count} simplified positions from ${d.flight.raw_point_count.toLocaleString()} raw positions. One ${d.gaps[0].seconds.toFixed(1)}-second coverage break occurs at 03:11–03:12 UTC, outside both selected windows. Simplified vertices are joined along geodesic legs; these are reconstructed paths between reports.`;
 chart(d);state.panels=d.panels.map(makePanel);await Promise.all(state.panels.map(panel=>new Promise((resolve,reject)=>{let n=0;const check=()=>panel.loaded?resolve():++n>200?reject(Error('Night texture did not load')):setTimeout(check,50);check();})));state.ready=true;$('status').textContent='';$('play').disabled=false;render();
 }catch(error){state.errors.push(error.message);$('status').textContent='The replay could not start: '+error.message+'. The night maps and brightness profiles remain available below.';console.error(error);}})();
