/* Client-side directed highway routing, partial-edge snapping and game scoring. */
(function(root){'use strict';
 const CM_PER_MILE=160934.4;
 function hav(a,b){const r=Math.PI/180,p=a[1]*r,q=b[1]*r,v=Math.sin((q-p)/2)**2+Math.cos(p)*Math.cos(q)*Math.sin((b[0]-a[0])*r/2)**2;return 12742017.6*Math.asin(Math.min(1,Math.sqrt(v)))}
 function decode(s){let p=0,y=0,x=0,out=[];while(p<s.length){let a=[];for(let k=0;k<2;k++){let n=0,shift=0,b;do{b=s.charCodeAt(p++)-63;n|=(b&31)<<shift;shift+=5}while(b>=32);a.push(n&1?~(n>>1):n>>1)}y+=a[0];x+=a[1];out.push(x/1e6,y/1e6)}return Float64Array.from(out)}
 class Heap{constructor(){this.f=[];this.d=[];this.e=[]}get length(){return this.e.length}get minimum(){return this.f[0]??Infinity}push(f,d,e){let i=this.e.length;while(i){let p=(i-1)>>1;if(this.f[p]<=f)break;this.f[i]=this.f[p];this.d[i]=this.d[p];this.e[i]=this.e[p];i=p}this.f[i]=f;this.d[i]=d;this.e[i]=e}pop(){const answer=[this.f[0],this.d[0],this.e[0]],f=this.f.pop(),d=this.d.pop(),e=this.e.pop();if(this.e.length){let i=0;while(2*i+1<this.e.length){let c=2*i+1;if(c+1<this.e.length&&this.f[c+1]<this.f[c])c++;if(this.f[c]>=f)break;this.f[i]=this.f[c];this.d[i]=this.d[c];this.e[i]=this.e[c];i=c}this.f[i]=f;this.d[i]=d;this.e[i]=e}return answer}}
 class Graph{
  constructor(data){
   if(data.version!==1)throw Error('Unsupported highway dataset.');this.data=data;this.edges=data.edges;this.nodes=data.nodes;this.geo=data.geometries.map(s=>({xy:decode(s)}));this.byGeometry=Array.from({length:this.geo.length},()=>[]);this.grid=new Map();this.cell=.25;this.turns=new Map();
   const degree=new Uint32Array(this.nodes.length);this.edges.forEach((e,i)=>{degree[e[0]]++;this.byGeometry[e[3]].push(i)});this.offsets=new Uint32Array(this.nodes.length+1);for(let i=0;i<degree.length;i++)this.offsets[i+1]=this.offsets[i]+degree[i];this.out=new Uint32Array(this.edges.length);const cursor=this.offsets.slice();this.edges.forEach((e,i)=>this.out[cursor[e[0]]++]=i);
   for(const [a,b] of data.turns){if(!this.turns.has(a))this.turns.set(a,new Set());this.turns.get(a).add(b)}
   this.geo.forEach((g,id)=>{const xy=g.xy,cum=new Float64Array(xy.length/2);let xmin=Infinity,ymin=Infinity,xmax=-Infinity,ymax=-Infinity;for(let i=0;i<xy.length;i+=2){xmin=Math.min(xmin,xy[i]);xmax=Math.max(xmax,xy[i]);ymin=Math.min(ymin,xy[i+1]);ymax=Math.max(ymax,xy[i+1]);if(i)cum[i/2]=cum[i/2-1]+hav([xy[i-2],xy[i-1]],[xy[i],xy[i+1]])}g.cum=cum;g.length=cum.at(-1);g.bounds=[xmin,ymin,xmax,ymax];for(let x=Math.floor(xmin/this.cell);x<=Math.floor(xmax/this.cell);x++)for(let y=Math.floor(ymin/this.cell);y<=Math.floor(ymax/this.cell);y++){const key=x+','+y;if(!this.grid.has(key))this.grid.set(key,[]);this.grid.get(key).push(id)}});
   this.dist=new Float64Array(this.edges.length);this.parent=new Int32Array(this.edges.length);
  }
  node(id){return [this.nodes[id][0]/1e6,this.nodes[id][1]/1e6]}
  snap(coordinate,maxMetres=40000,preferredGeometry=null,ref=null){
   const x=Math.floor(coordinate[0]/this.cell),y=Math.floor(coordinate[1]/this.cell),candidates=new Set();
   if(preferredGeometry!==null&&this.geo[preferredGeometry])candidates.add(preferredGeometry);
   else for(let dx=-2;dx<=2;dx++)for(let dy=-2;dy<=2;dy++)for(const id of this.grid.get((x+dx)+','+(y+dy))||[])candidates.add(id);
   const scale=Math.cos(coordinate[1]*Math.PI/180);let best=null;
   for(const id of candidates){if(ref!==null&&!this.byGeometry[id].some(i=>this.data.refs[this.edges[i][5]]===ref))continue;const g=this.geo[id],v=g.xy;for(let i=2;i<v.length;i+=2){const ax=(v[i-2]-coordinate[0])*scale,ay=v[i-1]-coordinate[1],bx=(v[i]-v[i-2])*scale,by=v[i+1]-v[i-1],den=bx*bx+by*by,t=den?Math.max(0,Math.min(1,-(ax*bx+ay*by)/den)):0,dx=ax+t*bx,dy=ay+t*by,d=dx*dx+dy*dy;if(!best||d<best.d){const position=[v[i-2]+(v[i]-v[i-2])*t,v[i-1]+(v[i+1]-v[i-1])*t];best={d,gid:id,position,fraction:g.length?(g.cum[i/2-1]+(g.cum[i/2]-g.cum[i/2-1])*t)/g.length:0}}}}
   if(!best||hav(coordinate,best.position)>maxMetres)throw Error('Choose a mapped highway. Zoom in to place your stop more precisely.');
   const ids=this.byGeometry[best.gid],base=this.edges[ids[0]],options=ids.filter(i=>{const e=this.edges[i];return (e[0]===base[0]&&e[1]===base[1])||(e[0]===base[1]&&e[1]===base[0])}).map(i=>({edge:i,offset:Math.round(this.edges[i][2]*(this.edges[i][4]===1?best.fraction:1-best.fraction))}));
   return {coordinate:best.position,geometry:best.gid,options,label:this.data.refs[base[5]]||'Major highway',snap_metres:hav(coordinate,best.position)};
  }
  allowed(a,b){return !this.turns.get(a)?.has(b)}
  shortest(start,targets,coordinate){
   const ds=this.dist,prev=this.parent;ds.fill(Infinity);prev.fill(-1);const heap=new Heap(),result=targets.map(()=>null),byEdge=new Map();targets.forEach((t,i)=>{if(!byEdge.has(t.edge))byEdge.set(t.edge,[]);byEdge.get(t.edge).push(i)});
   targets.forEach((t,i)=>{if(t.edge===start.edge&&t.offset>=start.offset)result[i]={cost:t.offset-start.offset,direct:true}});
   const heuristic=node=>this.dijkstra?0:Math.max(0,hav(this.node(node),coordinate)*98-500); // cm; 0.98 × spherical distance is a conservative WGS84 lower bound.
   const first=this.edges[start.edge];ds[start.edge]=first[2]-start.offset;prev[start.edge]=-2;heap.push(ds[start.edge]+heuristic(first[1]),ds[start.edge],start.edge);
   while(heap.length){if(result.every(Boolean)&&heap.minimum>=Math.max(...result.map(r=>r.cost)))break;const [,cost,incoming]=heap.pop();if(cost!==ds[incoming])continue;const node=this.edges[incoming][1];for(let p=this.offsets[node];p<this.offsets[node+1];p++){const edge=this.out[p];if(!this.allowed(incoming,edge))continue;for(const i of byEdge.get(edge)||[]){const total=cost+targets[i].offset;if(!result[i]||total<result[i].cost)result[i]={cost:total,last:incoming,direct:false}}const next=cost+this.edges[edge][2];if(next<ds[edge]){ds[edge]=next;prev[edge]=incoming;heap.push(next+heuristic(this.edges[edge][1]),next,edge)}}}
   return result.map((r,i)=>{if(!r)return null;if(r.direct)return {cost:r.cost,segments:[[start.edge,start.offset,targets[i].offset]]};const chain=[];for(let e=r.last;e>=0;e=prev[e]){chain.push(e);if(prev[e]===-2)break}chain.reverse();const segments=chain.map((e,j)=>[e,j===0?start.offset:0,this.edges[e][2]]);segments.push([targets[i].edge,0,targets[i].offset]);return {cost:r.cost,segments}});
  }
  route(stops){
   if(stops.length<2)return {centimetres:0,seconds:0,states:[],segments:[],geometry:{type:'MultiLineString',coordinates:[]}};
   let choices=stops[0].options.map(option=>({option,cost:0,segments:[]}));
   for(let i=1;i<stops.length;i++){const next=stops[i].options.map(()=>null);for(const prior of choices){if(!prior)continue;const legs=this.shortest(prior.option,stops[i].options,stops[i].coordinate);legs.forEach((leg,j)=>{if(leg&&(!next[j]||prior.cost+leg.cost<next[j].cost))next[j]={option:stops[i].options[j],cost:prior.cost+leg.cost,segments:[...prior.segments,...leg.segments]}})}choices=next;if(!choices.some(Boolean))throw Error(`No permitted highway path connects stops ${i} and ${i+1}. Try a different carriageway or interchange. No straight-line substitute is shown.`)}
   const best=choices.filter(Boolean).sort((a,b)=>a.cost-b.cost)[0],segments=[];for(const [id,a,b] of best.segments){if(b<=a)continue;const last=segments.at(-1);if(last&&last[0]===id&&last[2]===a)last[2]=b;else segments.push([id,a,b])}
   const states=new Set();let centimetres=0,seconds=0;const lines=[];
   for(const [id,a,b] of segments){const e=this.edges[id];centimetres+=b-a;seconds+=e[8]*(b-a)/e[2];const intervals=e[9];let before=0;for(let i=0;i<intervals.length;i+=2){const end=intervals[i],state=intervals[i+1],overlap=Math.min(b,end)-Math.max(a,before);if(overlap>=this.data.state_minimum_interval_cm&&state>=0&&this.data.states[state]!=='DC')states.add(this.data.states[state]);before=end}const xy=this.slice(id,a,b);if(xy.length<2)continue;const last=lines.at(-1);if(last&&Math.abs(last.at(-1)[0]-xy[0][0])<1e-6&&Math.abs(last.at(-1)[1]-xy[0][1])<1e-6)last.push(...xy.slice(1));else lines.push(xy)}
   return {centimetres,seconds,states:[...states].sort(),segments,geometry:{type:'MultiLineString',coordinates:lines}};
  }
  slice(id,a,b){const e=this.edges[id],g=this.geo[e[3]],total=e[2],start=(e[4]===1?a/total:1-b/total)*g.length,end=(e[4]===1?b/total:1-a/total)*g.length,v=g.xy,c=g.cum;const pointAt=d=>{let lo=0,hi=c.length-1;while(lo+1<hi){const mid=(lo+hi)>>1;if(c[mid]<=d)lo=mid;else hi=mid}const f=c[hi]>c[lo]?(d-c[lo])/(c[hi]-c[lo]):0;return [v[lo*2]+(v[hi*2]-v[lo*2])*f,v[lo*2+1]+(v[hi*2+1]-v[lo*2+1])*f]};const out=[pointAt(start)];for(let i=1;i<c.length-1;i++)if(c[i]>start&&c[i]<end)out.push([v[i*2],v[i*2+1]]);out.push(pointAt(end));if(e[4]===-1)out.reverse();return out}
 }
 const MAX_DISTANCE_METERS=1609344,MAX_DISTANCE_CM=MAX_DISTANCE_METERS*100;
 function withinBudget(cm){return Number.isFinite(cm)&&cm>=0&&cm<=MAX_DISTANCE_CM+1e-7}
 function score(result){const centimetres=result.centimetres,miles=centimetres/CM_PER_MILE,states=new Set(result.states).size;return {centimetres,miles,states,eligible:states>0&&centimetres>0&&withinBudget(centimetres),remainingMiles:Math.max(0,(MAX_DISTANCE_CM-centimetres)/CM_PER_MILE)}}
 function better(candidate,previous){if(!candidate.eligible)return false;if(!previous)return true;if(candidate.states!==previous.states)return candidate.states>previous.states;return candidate.centimetres<(previous.centimetres??previous.miles*CM_PER_MILE)-1e-7}
 function compatibleBest(record,version){return !!record&&record.version===version&&Number.isInteger(record.states)&&record.states>0&&record.states<=48&&withinBudget(record.centimetres??record.miles*CM_PER_MILE)&&(record.centimetres??record.miles*CM_PER_MILE)>0}
 function migrateBest(legacy,version){const old=legacy?.thousand;if((old?.mode&&old.mode!=='thousand')||!compatibleBest(old,version))return null;return {states:old.states,centimetres:old.centimetres??Math.round(old.miles*CM_PER_MILE),miles:old.miles,date:old.date,version,waypoints:old.waypoints||[]}}
 const api={Graph,Heap,hav,decode,score,better,withinBudget,migrateBest,compatibleBest,MAX_DISTANCE_METERS,MAX_DISTANCE_CM,CM_PER_MILE};root.RoadTripCore=api;if(typeof module!=='undefined')module.exports=api;
})(typeof self!=='undefined'?self:globalThis);
