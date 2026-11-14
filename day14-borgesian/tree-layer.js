/* Leafy tree symbols at OSM points. Forms and dimensions are illustrative. */
import * as THREE from './vendor/three.module.js';

export const TREE_FORMS=['Spreading crown','Rounded crown','Upright crown','Weeping crown','Evergreen crown'];
export function treeForm(p) {
  const name=((p.genus||'')+' '+(p.species||'')).toLowerCase();
  if(p.leaf_type==='needleleaved'||/pinus|picea|abies|juniperus/.test(name))return 4;
  if(/salix/.test(name))return 3;
  if(/populus/.test(name))return 2;
  if(/quercus/.test(name))return 0;
  if(/acer/.test(name))return 1;
  return Number(p.osm.split('/')[1])%(p.leaf_type==='broadleaved'?4:5);
}
function random(seed){let x=seed|0;return()=>{x=(Math.imul(x,1664525)+1013904223)|0;return (x>>>0)/4294967296;};}
function foliageTexture(needles=false){
  const canvas=document.createElement('canvas');canvas.width=canvas.height=128;
  const ctx=canvas.getContext('2d');const rng=random(needles?72:36);
  ctx.strokeStyle='#a18c66';ctx.lineWidth=1.5;ctx.beginPath();ctx.moveTo(61,117);ctx.quadraticCurveTo(70,65,64,15);ctx.stroke();
  for(let i=0;i<(needles?22:9);i++){
    const y=17+i*(needles?4:10),side=i%2?1:-1;
    ctx.save();ctx.translate(64,y);ctx.rotate(side*(.5+rng()*.5));
    ctx.fillStyle=['#fff9e5','#ede3c8','#d0c5a6','#f0e4c4'][i%4];
    ctx.beginPath();
    if(needles){ctx.moveTo(0,0);ctx.lineTo(side*27,-5);ctx.lineTo(side*31,-8);ctx.lineTo(side*9,-8);}
    else {ctx.moveTo(0,0);ctx.bezierCurveTo(side*18,-19,side*35,-15,side*40,-26);ctx.bezierCurveTo(side*40,-2,side*19,9,0,0);}
    ctx.closePath();ctx.fill();
    if(!needles){ctx.strokeStyle='#a18f69';ctx.lineWidth=.7;ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(side*35,-20);ctx.stroke();}
    ctx.restore();
  }
  const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;texture.anisotropy=4;return texture;
}

export function createTreeLayer(){
  const layer={
    id:'leafy-trees-3d',type:'custom',renderingMode:'3d',
    onAdd(map,gl){
      this.map=map;this.scene=new THREE.Scene();this.camera=new THREE.Camera();
      this.scene.add(new THREE.HemisphereLight(0xf2f6db,0x667354,2.0));
      const sun=new THREE.DirectionalLight(0xfff6dc,2.2);sun.position.set(-4,-6,11);this.scene.add(sun);
      this.renderer=new THREE.WebGLRenderer({canvas:map.getCanvas(),context:gl,antialias:true});
      this.renderer.autoClear=false;this.renderer.outputColorSpace=THREE.SRGBColorSpace;
      this.geometry={wood:new THREE.CylinderGeometry(.65,1,1,9),crown:new THREE.SphereGeometry(1,16,12),leaf:new THREE.PlaneGeometry(1,1)};
      this.textures=[foliageTexture(),foliageTexture(true),foliageTexture()];
      this.textures[2].wrapS=this.textures[2].wrapT=THREE.RepeatWrapping;this.textures[2].repeat.set(5,3);
      this.material={wood:new THREE.MeshLambertMaterial({color:0x846a4c}),crown:new THREE.MeshLambertMaterial({map:this.textures[2],alphaTest:.38,side:THREE.DoubleSide,color:0xffffff}),leaf:new THREE.MeshLambertMaterial({map:this.textures[0],alphaTest:.38,side:THREE.DoubleSide,color:0xffffff}),needle:new THREE.MeshLambertMaterial({map:this.textures[1],alphaTest:.35,side:THREE.DoubleSide,color:0xffffff})};
      this.meshes=[];this.trees=[];this.inverse=new THREE.Matrix4();this.ready=true;
    },
    update(features){
      if(!this.ready)return;
      const middle=this.map.getCenter(),dense=this.map.getZoom()>=19;
      const selected=this.map.getZoom()<17?[]:[...features].sort((a,b)=>middle.distanceTo(a.geometry.coordinates)-middle.distanceTo(b.geometry.coordinates)).slice(0,this.map.getCanvas().clientWidth<601?100:250);
      const signature=selected.map(f=>f.properties.osm).sort().join('|')+(dense?':detail':':simple');
      if(signature===this.signature)return;this.signature=signature;
      for(const mesh of this.meshes){this.scene.remove(mesh);mesh.dispose();}this.meshes=[];this.trees=[];
      if(this.map.getZoom()<17||!features.length){this.map.triggerRepaint();return;}
      this.origin=maplibregl.MercatorCoordinate.fromLngLat(middle,0);this.unit=this.origin.meterInMercatorCoordinateUnits();
      const entries={wood:[],crown:[],leaf:[],needle:[]};
      const matrix=new THREE.Matrix4(),quaternion=new THREE.Quaternion(),position=new THREE.Vector3(),size=new THREE.Vector3();
      const append=(kind,pos,scale,color,rotation)=>{
        position.set(...pos);size.set(...scale);quaternion.copy(rotation||new THREE.Quaternion());matrix.compose(position,quaternion,size);
        entries[kind].push({matrix:matrix.clone(),color:new THREE.Color(color)});
      };
      const segment=(a,b,r)=>{
        const from=new THREE.Vector3(...a),to=new THREE.Vector3(...b),delta=to.clone().sub(from);
        const q=new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,1,0),delta.clone().normalize());
        append('wood',from.add(to).multiplyScalar(.5).toArray(),[r,delta.length(),r],0x8b7150,q);
      };
      // Limit expensive leaf meshes to the closest trees; all other OSM points remain discoverable.
      for(const f of selected){
        const p=f.properties,form=treeForm(p),rng=random(Number(p.osm.split('/')[1]));
        const coordinate=maplibregl.MercatorCoordinate.fromLngLat(f.geometry.coordinates,0);
        const x=(coordinate.x-this.origin.x)/this.unit,y=-(coordinate.y-this.origin.y)/this.unit;
        const variation=.82+rng()*.35;
        const measured=/^\d+(\.\d+)?\s*m?$/.test(String(p.height||''))?Number.parseFloat(p.height):NaN,height=Number.isFinite(measured)&&measured>=2&&measured<=35?measured:((form===2?10:form===4?9:8)*variation);
        const spread=height*(form===2?.15:form===4?.23:form===0?.39:.31);
        const trunkTop=height*(form===4?.75:.63),base=[x,y,0];
        segment(base,[x+.05,y,trunkTop],height*.023);
        const lobes=[];
        if(form===4){
          for(let j=0;j<9;j++){const t=(j+.5)/9,a=j*2.4;lobes.push({x:x+Math.cos(a)*spread*(1-t)*.4,y:y+Math.sin(a)*spread*(1-t)*.4,z:height*(.28+t*.64),rx:spread*(1-t)*.8+.12,ry:spread*(1-t)*.8+.12,rz:height*.17});}
        }else{
          const count=form===2?5:7;
          for(let j=0;j<count;j++){
            const a=j*Math.PI*2/count+rng()*.6,r=spread*(j===0?0:.40+rng()*.24);
            lobes.push({x:x+Math.cos(a)*r,y:y+Math.sin(a)*r,z:height*(form===3?.54:.65)+(rng()-.4)*height*.17,rx:spread*(.55+rng()*.22),ry:spread*(.55+rng()*.22),rz:height*(form===2?.29:form===3?.29:.22)});
          }
        }
        const palette=[['#c5912c','#e4b74d'],['#b8472d','#df7340'],['#c3a333','#ebcc65'],['#b97834','#d6a64e'],['#3b6249','#64835b']][form];
        for(let j=0;j<lobes.length;j++){
          const l=lobes[j];
          segment([x,y,trunkTop*.64],[l.x,l.y,l.z],height*.007);
          // Smooth inner foliage supports the leaf sprays without terraced silhouettes.
          append('crown',[l.x,l.y,l.z],[l.rx*.74,l.ry*.74,l.rz*.75],palette[0]);
          const sprays=dense?72:22;
          for(let k=0;k<sprays;k++){
            const u=rng()*2-1,a=rng()*Math.PI*2,ring=Math.sqrt(1-u*u),radius=.8+rng()*.28;
            const pos=[l.x+l.rx*ring*Math.cos(a)*radius,l.y+l.ry*ring*Math.sin(a)*radius,l.z+l.rz*u*radius];
            const q=new THREE.Quaternion().setFromEuler(new THREE.Euler(rng()*Math.PI,rng()*Math.PI,rng()*Math.PI));
            const leafSize=(form===4?.75:.85)*(height/8)*(.7+rng()*.5);
            append(form===4?'needle':'leaf',pos,[leafSize,leafSize*(form===3?1.8:1.1),1],palette[k%2],q);
            if(form===3&&k%12===0)segment([l.x,l.y,l.z],pos,height*.002);
          }
        }
        this.trees.push({feature:f,sphere:new THREE.Sphere(new THREE.Vector3(x,y,height*.62),Math.max(spread,height*.28)),form:TREE_FORMS[form]});
      }
      for(const [kind,instances] of Object.entries(entries)){
        if(!instances.length)continue;
        const mesh=new THREE.InstancedMesh(this.geometry[kind==='needle'?'leaf':kind],this.material[kind],instances.length);
        instances.forEach((item,i)=>{mesh.setMatrixAt(i,item.matrix);mesh.setColorAt(i,item.color);});
        mesh.instanceMatrix.needsUpdate=true;mesh.instanceColor.needsUpdate=true;mesh.frustumCulled=false;this.meshes.push(mesh);this.scene.add(mesh);
      }
      this.map.triggerRepaint();
    },
    render(gl,args){
      if(!this.origin||this.map.getZoom()<17||this.map.getPitch()<=5||!this.trees.length)return;
      const projection=new THREE.Matrix4().fromArray(args.defaultProjectionData.mainMatrix);
      const local=new THREE.Matrix4().makeTranslation(this.origin.x,this.origin.y,0).scale(new THREE.Vector3(this.unit,-this.unit,this.unit));
      this.camera.projectionMatrix.copy(projection.multiply(local));this.camera.projectionMatrixInverse.copy(this.camera.projectionMatrix).invert();this.inverse.copy(this.camera.projectionMatrixInverse);
      this.renderer.resetState();this.renderer.render(this.scene,this.camera);this.renderer.resetState();
    },
    pick(point){
      if(this.map.getZoom()<17||this.map.getPitch()<=5)return null;
      const x=point.x/this.map.getCanvas().clientWidth*2-1,y=1-point.y/this.map.getCanvas().clientHeight*2;
      const near=new THREE.Vector3(x,y,-1).applyMatrix4(this.inverse),far=new THREE.Vector3(x,y,1).applyMatrix4(this.inverse);
      const ray=new THREE.Ray(near,far.sub(near).normalize());let best=null,distance=Infinity;
      for(const tree of this.trees){const hit=ray.intersectSphere(tree.sphere,new THREE.Vector3());if(hit&&hit.distanceTo(near)<distance){distance=hit.distanceTo(near);best=tree.feature;}}
      return best;
    },
    onRemove(){for(const mesh of this.meshes)mesh.dispose();Object.values(this.geometry).forEach(g=>g.dispose());Object.values(this.material).forEach(m=>m.dispose());this.textures.forEach(t=>t.dispose());this.renderer.dispose();}
  };
  return layer;
}
