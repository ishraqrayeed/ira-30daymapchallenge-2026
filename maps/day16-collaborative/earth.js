import * as THREE from './vendor/three.module.js';
export function createEarth(canvas,data,states){
 const renderer=new THREE.WebGLRenderer({canvas,alpha:true,antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,1.5));
 const scene=new THREE.Scene(),camera=new THREE.OrthographicCamera(-3,3,2,-2,.1,100);camera.position.set(-2.2,11,15.8);camera.lookAt(0,0,0);
 const radius=6371000;
 const ecef=p=>new THREE.Vector3(p[0]/radius,p[2]/radius,-p[1]/radius);
 const geo=(lon,lat)=>{let a=lon*Math.PI/180,b=lat*Math.PI/180;return new THREE.Vector3(Math.cos(b)*Math.cos(a),Math.sin(b),-Math.cos(b)*Math.sin(a))};
 const earthBody=new THREE.Mesh(new THREE.SphereGeometry(1,64,40),new THREE.MeshBasicMaterial({color:0x12283b}));earthBody.scale.set(6378137/radius,6356752.314245/radius,6378137/radius);scene.add(earthBody);const wires=[];
 for(let lat=-60;lat<=60;lat+=30)for(let lon=-180;lon<180;lon+=3)wires.push(...geo(lon,lat).multiplyScalar(1.003).toArray(),...geo(lon+3,lat).multiplyScalar(1.003).toArray());
 for(let lon=-180;lon<180;lon+=30)for(let lat=-90;lat<90;lat+=3)wires.push(...geo(lon,lat).multiplyScalar(1.003).toArray(),...geo(lon,lat+3).multiplyScalar(1.003).toArray());
 let geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(wires,3));scene.add(new THREE.LineSegments(geometry,new THREE.LineBasicMaterial({color:0x34556f,transparent:true,opacity:.38})));
 const border=[];for(const feature of states.features){const polygons=feature.geometry.type==='Polygon'?[feature.geometry.coordinates]:feature.geometry.coordinates;for(const polygon of polygons)for(const ring of polygon)for(let i=1;i<ring.length;i++)border.push(...geo(...ring[i-1]).multiplyScalar(1.005).toArray(),...geo(...ring[i]).multiplyScalar(1.005).toArray())}
 geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(border,3));scene.add(new THREE.LineSegments(geometry,new THREE.LineBasicMaterial({color:0x6d91ac,transparent:true,opacity:.7})));
 const satMeshes={};for(const prn of Object.keys(data.satellite_ecef_m)){const mesh=new THREE.Mesh(new THREE.SphereGeometry(.035,10,8),new THREE.MeshBasicMaterial({color:0xb0c5d8}));scene.add(mesh);satMeshes[prn]=mesh}
 const receiverMarker=new THREE.Mesh(new THREE.SphereGeometry(.035,14,10),new THREE.MeshBasicMaterial({color:0xffffff}));scene.add(receiverMarker);
 const losGeometry=new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(),new THREE.Vector3()]);
 const los=new THREE.Line(losGeometry,new THREE.LineBasicMaterial({color:0xffffff,transparent:true,opacity:.9}));scene.add(los);
 const motionArrow=new THREE.ArrowHelper(new THREE.Vector3(1,0,0),new THREE.Vector3(),.4,0xffffff,.1,.06);scene.add(motionArrow);
 let trail=null,previousPRN=null,frameKey='';
 const icon=new THREE.Group();const body=new THREE.Mesh(new THREE.BoxGeometry(.07,.07,.07),new THREE.MeshBasicMaterial({color:0xe9f1f7}));icon.add(body);for(const sign of [-1,1]){const wing=new THREE.Mesh(new THREE.BoxGeometry(.13,.065,.012),new THREE.MeshBasicMaterial({color:0x35a9c7}));wing.position.x=sign*.115;icon.add(wing)}scene.add(icon);
 const dense=data.satellite_orbit_ecef_m||data.satellite_ecef_m,step=data.orbit_sample_interval_s||60;
 function position(prn,epoch){const v=epoch*60/step,i=Math.min(dense[prn].length-1,Math.floor(v)),j=Math.min(i+1,dense[prn].length-1);return ecef(dense[prn][i]).lerp(ecef(dense[prn][j]),v-i)}
 function update(epoch,selection){
  const rect=canvas.getBoundingClientRect();if(!rect.width||!rect.height)return;if(canvas.width!==Math.round(rect.width*renderer.getPixelRatio())||canvas.height!==Math.round(rect.height*renderer.getPixelRatio()))renderer.setSize(rect.width,rect.height,false);
 const key=selection?selection.station.id+selection.prn+rect.width+':'+rect.height:'';
 if(selection&&key!==frameKey){
 const ground=ecef(selection.station.ecef_m),up=ground.clone().normalize(),path=dense[selection.prn].map(ecef),velocity=path.at(-1).clone().sub(path[0]),normal=up.clone().cross(velocity).normalize(),right=up.clone().cross(normal).normalize();
 const xs=path.map(p=>p.clone().sub(ground).dot(right)),ys=path.map(p=>p.clone().sub(ground).dot(up));let minX=Math.min(-1.1,...xs)-.28,maxX=Math.max(1.1,...xs)+.28,minY=-.65,maxY=Math.max(.8,...ys)+.42;
 const center=ground.clone().addScaledVector(right,(minX+maxX)/2).addScaledVector(up,(minY+maxY)/2),aspect=rect.width/rect.height;let halfH=(maxY-minY)/2,halfW=(maxX-minX)/2;if(halfW/halfH>aspect)halfH=halfW/aspect;else halfW=halfH*aspect;
 camera.left=-halfW;camera.right=halfW;camera.top=halfH;camera.bottom=-halfH;camera.up.copy(up);camera.position.copy(center).addScaledVector(normal,20);camera.lookAt(center);camera.updateProjectionMatrix();camera.updateMatrixWorld();frameKey=key;
 }
  for(const [prn,mesh] of Object.entries(satMeshes)){mesh.visible=false;mesh.position.copy(position(prn,epoch));mesh.scale.setScalar(selection?.prn===prn?2.5:1);mesh.material.color.set(selection?.prn===prn?0xffffff:0x7691a8)}
  const selected=selection&&selection.record;
  receiverMarker.visible=los.visible=motionArrow.visible=icon.visible=!!selected;
  if(selection&&selection.prn!==previousPRN){
   if(trail){scene.remove(trail);trail.geometry.dispose();trail.material.dispose()}
   const points=dense[selection.prn].map(ecef);trail=new THREE.Line(new THREE.BufferGeometry().setFromPoints(points),new THREE.LineBasicMaterial({color:0x7c9db7,transparent:true,opacity:.55}));scene.add(trail);previousPRN=selection.prn;
  }
  if(trail)trail.visible=!!selection;
  if(selected){
   const ground=ecef(selection.station.ecef_m),sat=position(selection.prn,epoch),color=SymphonyCore.colors[selected.direction];
   receiverMarker.position.copy(ground);icon.position.copy(sat);icon.quaternion.copy(camera.quaternion);body.material.color.set(color);satMeshes[selection.prn].material.color.set(color);
   los.geometry.setFromPoints([ground,sat]);los.material.color.set(color);
   // Projected relative motion: direction is physical; arrow length is deliberately enlarged.
   const direction=position(selection.prn,Math.min(60,epoch+.1)).sub(position(selection.prn,Math.max(0,epoch-.1))).normalize();
   motionArrow.position.copy(sat);motionArrow.setDirection(direction);motionArrow.setColor(new THREE.Color('#e9f1f7'));motionArrow.setLength(.35,.09,.055);
 function label(id,point,text,dy){const node=document.getElementById(id);node.textContent=text;const p=point.clone().project(camera);node.style.left=Math.max(4,Math.min(rect.width-node.offsetWidth-4,(p.x+1)*rect.width/2+9))+'px';node.style.top=Math.max(4,Math.min(rect.height-node.offsetHeight-4,(1-p.y)*rect.height/2+dy))+'px';node.style.display='block'}
 label('satellite-label',sat,'GPS '+selection.prn+' · moving',-28);label('receiver-label',ground,selection.station.id+' · fixed receiver',10);
  }
  if(!selected){document.getElementById('satellite-label').style.display='none';document.getElementById('receiver-label').style.display='none'}
  renderer.render(scene,camera);
 }
 return {update,dispose(){renderer.dispose()}};
}
