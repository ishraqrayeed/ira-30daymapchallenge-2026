import * as THREE from './vendor/three.module.js';
import { OrbitControls } from './vendor/OrbitControls.js';
const canvas=document.querySelector('#road'),stage=document.querySelector('#stage'),loading=document.querySelector('#loading');
let renderer;
try{renderer=new THREE.WebGLRenderer({canvas,antialias:true});}
catch(error){loading.innerHTML='3D is unavailable. <a href="map.png">Open the poster.</a>';throw error;}
renderer.setClearColor(0x1b2225);renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(44,1,.001,100);camera.up.set(0,0,1);
scene.add(new THREE.HemisphereLight(0xffefdb,0x637080,2.2));
scene.add(new THREE.AmbientLight(0xffffff,.7));
for(const [position,power] of [[[-10,-4,20],1.6],[[8,12,10],1.4]]){const light=new THREE.DirectionalLight(0xffffff,power);light.position.set(...position);scene.add(light);}
const top=new THREE.MeshStandardMaterial({color:0xe8a348,roughness:.9,metalness:.02,emissive:0x5e3410,emissiveIntensity:.32});
const edge=new THREE.MeshStandardMaterial({color:0x70401d,roughness:.8});
let route,mesh,points=[],fitPoints=[],heightFactor=6,azimuth=Math.PI/4,elevation=28*Math.PI/180,roll=-25*Math.PI/180;
let distance=1,zoom=1,scheduled=false,controls;
const target=new THREE.Vector3();const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function geometry(){
 const p=route.points,origin=[(Math.min(...p.map(p=>p[0]))+Math.max(...p.map(p=>p[0])))/2,(Math.min(...p.map(p=>p[1]))+Math.max(...p.map(p=>p[1])))/2,Math.min(...p.map(p=>p[2]))];
 const raw=p.map(p=>new THREE.Vector3((p[0]-origin[0])/1000,(p[1]-origin[1])/1000,(p[2]-origin[2])/1000));
 points=raw.map(p=>new THREE.Vector3(p.x,p.y,p.z*heightFactor));
 fitPoints=[...points];
 const vertices=[],tops=[],edges=[],g=new THREE.BufferGeometry(),width=route.selection.ribbon_width_m/1000,thickness=route.selection.ribbon_thickness_m/1000;
 for(let i=0;i<points.length;i++){
  const tangent=points[Math.min(points.length-1,i+1)].clone().sub(points[Math.max(0,i-1)]);tangent.z=0;tangent.normalize();const normal=new THREE.Vector3(-tangent.y,tangent.x,0);
  for(const [side,z] of [[-1,0],[1,0],[-1,-thickness],[1,-thickness]]){const v=points[i].clone().addScaledVector(normal,side*width/2);v.z+=z;vertices.push(v.x,v.y,v.z);}
 }
 function face(a,b,c,d,m){(m===0?tops:edges).push(d,c,b,d,b,a);}
 for(let i=0;i<points.length-1;i++){const a=i*4,b=a+4;face(a,a+1,b+1,b,0);face(a+2,b+2,b+3,a+3,1);face(a,b,b+2,a+2,1);face(a+1,a+3,b+3,b+1,1);}
 face(0,2,3,1,1);let a=vertices.length/3-4;face(a,a+1,a+3,a+2,1);
 g.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));g.setIndex([...tops,...edges]);g.addGroup(0,tops.length,0);g.addGroup(tops.length,edges.length,1);
 if(mesh){scene.remove(mesh);mesh.geometry.dispose();}const flat=g.toNonIndexed();g.dispose();flat.computeVertexNormals();mesh=new THREE.Mesh(flat,[top,edge]);mesh.name="US 550";scene.add(mesh);
 fitPoints=[];for(let i=0;i<vertices.length;i+=3)fitPoints.push(new THREE.Vector3(vertices[i],vertices[i+1],vertices[i+2]));
 target.set((Math.min(...fitPoints.map(p=>p.x))+Math.max(...fitPoints.map(p=>p.x)))/2,(Math.min(...fitPoints.map(p=>p.y))+Math.max(...fitPoints.map(p=>p.y)))/2,(Math.min(...fitPoints.map(p=>p.z))+Math.max(...fitPoints.map(p=>p.z)))/2);
 fitView();setupControls();render();
}
function updateCamera(){
 const w=stage.clientWidth||390,h=stage.clientHeight||480;camera.aspect=w/h;
 camera.position.set(Math.cos(azimuth)*Math.cos(elevation),Math.sin(azimuth)*Math.cos(elevation),Math.sin(elevation)).multiplyScalar(distance/zoom).add(target);
 camera.lookAt(target);camera.clearViewOffset();camera.updateProjectionMatrix();camera.updateMatrixWorld();
}
function fitView(){
 if(!fitPoints.length)return;const previous=zoom;zoom=1;let lo=.03,hi=5;
 function extent(){let x0=Infinity,x1=-Infinity,y0=Infinity,y1=-Infinity,z=Infinity;for(const p of fitPoints){const q=p.clone().project(camera);x0=Math.min(x0,q.x);x1=Math.max(x1,q.x);y0=Math.min(y0,q.y);y1=Math.max(y1,q.y);z=Math.min(z,q.z);}return {x0,x1,y0,y1,z};}
 for(let i=0;i<35;i++){distance=(lo+hi)/2;updateCamera();const b=extent();if(b.z< -1||b.x1-b.x0>1.72||b.y1-b.y0>1.72)lo=distance;else hi=distance;}
 distance=hi;updateCamera();const b=extent(),w=stage.clientWidth||390,h=stage.clientHeight||480;
 camera.setViewOffset(w,h,(b.x0+b.x1)*w/4,(-(b.y0+b.y1)/2)*h/2,w,h);camera.updateProjectionMatrix();camera.updateMatrixWorld();zoom=previous;
}
function setupControls(){
 if(controls)controls.dispose();controls=new OrbitControls(camera,canvas);controls.target=target;
 controls.enableDamping=true;controls.dampingFactor=.12;controls.rotateSpeed=.32;controls.zoomSpeed=.65;controls.panSpeed=.65;
 controls.minPolarAngle=.005;controls.maxPolarAngle=Math.PI-.005;
 controls.minDistance=distance*.3;controls.maxDistance=distance*4;
 controls.screenSpacePanning=true;controls.addEventListener('change',render);controls.update();
}
function draw(){scheduled=false;const moving=controls?.update();camera.updateMatrixWorld();renderer.render(scene,camera);if(moving)render();}
function render(){if(!scheduled){scheduled=true;requestAnimationFrame(draw);}}
function resize(){
 if(!stage.clientWidth||!stage.clientHeight)return;renderer.setSize(stage.clientWidth,stage.clientHeight,false);
 if(route){if(controls){const v=camera.position.clone().sub(target);azimuth=Math.atan2(v.y,v.x);elevation=Math.atan2(v.z,Math.hypot(v.x,v.y));}fitView();setupControls();}render();
}
new ResizeObserver(resize).observe(stage);
function reset(){if(!route)return;const c=route.selection.camera;azimuth=c.azimuth*Math.PI/180;elevation=c.elevation*Math.PI/180;zoom=1;geometry();}
function overhead(){elevation=89.5*Math.PI/180;azimuth=Math.PI/2;zoom=1;fitView();setupControls();render();}
function stopMotion(){if(controls){controls.enableDamping=false;controls.update();controls.enableDamping=true;}}
function nudge(horizontal,vertical){
 if(!controls)return;stopMotion();const v=camera.position.clone().sub(target),r=v.length(),a=Math.atan2(v.y,v.x)+horizontal,e=clamp(Math.atan2(v.z,Math.hypot(v.x,v.y))+vertical,-Math.PI/2+.005,Math.PI/2-.005);
 camera.position.set(Math.cos(a)*Math.cos(e),Math.sin(a)*Math.cos(e),Math.sin(e)).multiplyScalar(r).add(target);controls.update();render();
}
function dolly(delta){if(!controls)return;stopMotion();const v=camera.position.clone().sub(target),r=clamp(v.length()*Math.exp(delta),controls.minDistance,controls.maxDistance);camera.position.copy(v.normalize().multiplyScalar(r).add(target));controls.update();render();}
canvas.addEventListener('pointerdown',()=>canvas.focus({preventScroll:true}));
canvas.addEventListener('dblclick',reset);
canvas.addEventListener('keydown',e=>{const actions={ArrowLeft:()=>nudge(.12,0),ArrowRight:()=>nudge(-.12,0),ArrowUp:()=>nudge(0,.10),ArrowDown:()=>nudge(0,-.10),'+':()=>dolly(-.1),'=':()=>dolly(-.1),'-':()=>dolly(.1),r:reset,R:reset};if(actions[e.key]){e.preventDefault();actions[e.key]();}});
canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();loading.hidden=false;loading.innerHTML='3D was interrupted. Reload, or <a href="map.png">open the poster.</a>';});
document.querySelector('#reset').addEventListener('click',reset);document.querySelector('#top').addEventListener('click',overhead);
function buildGIS(){
 const p=route.points,xmin=Math.min(...p.map(p=>p[0])),xmax=Math.max(...p.map(p=>p[0])),ymin=Math.min(...p.map(p=>p[1])),ymax=Math.max(...p.map(p=>p[1])),pad=35;
 document.querySelector('#gis-map').setAttribute('viewBox',`${-xmax-pad} ${ymin-pad} ${xmax-xmin+2*pad} ${ymax-ymin+2*pad}`);
 document.querySelector('#gis-path').setAttribute('d',p.map((p,i)=>`${i?'L':'M'}${-p[0]} ${p[1]}`).join(' '));
 const length=route.length_m>=1000?`${Number((route.length_m/1000).toFixed(2))} km`:`${Math.round(route.length_m)} m`;
 document.querySelector('#gis-stats').textContent=`${length} of US 550 · South up · NAD83 / UTM 13N`;
}
fetch('./data/route.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error(`Route HTTP ${r.status}`);return r.json();}).then(data=>{route=data;heightFactor=data.selection.default_vertical_scale;loading.hidden=true;buildGIS();reset();resize();}).catch(error=>{loading.hidden=false;loading.innerHTML='Could not load the road. <a href="map.png">Open the poster.</a>';console.error(error);});
