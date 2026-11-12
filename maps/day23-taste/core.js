/* Shared filtering and shortest paths over the cached OSM pedestrian graph. */
(function(root){
 'use strict';
 function matches(p,s){return (s.category==='all'||p.category_ids.includes(s.category))&&(!s.dish||p.dish_tags.includes(s.dish))&&(!s.neighborhood||p.neighborhood===s.neighborhood)}
 class Heap{
  constructor(){this.a=[]}
  push(v){let i=this.a.length;this.a.push(v);while(i){let p=(i-1)>>1;if(this.a[p][0]<=v[0])break;this.a[i]=this.a[p];i=p}this.a[i]=v}
  pop(){const top=this.a[0],v=this.a.pop();if(this.a.length){let i=0;while(2*i+1<this.a.length){let c=2*i+1;if(c+1<this.a.length&&this.a[c+1][0]<this.a[c][0])c++;if(this.a[c][0]>=v[0])break;this.a[i]=this.a[c];i=c}this.a[i]=v}return top}
 }
 function path(graph,start,end){
  const n=graph.coordinates.length;if(!Number.isInteger(start)||!Number.isInteger(end)||start<0||end<0||start>=n||end>=n)throw Error('The street access point is unavailable.');
  const ds=new Float64Array(n);ds.fill(Infinity);const prev=new Int32Array(n);prev.fill(-1);ds[start]=0;const heap=new Heap();heap.push([0,start]);
  while(heap.a.length){const [d,u]=heap.pop();if(d!==ds[u])continue;if(u===end)break;for(const [v,w] of graph.adjacency[u])if(d+w<ds[v]){ds[v]=d+w;prev[v]=u;heap.push([ds[v],v])}}
  if(!Number.isFinite(ds[end]))throw Error('A walkable route between these stops cannot currently be calculated. Try different stops.');
  const ids=[];for(let u=end;u!==-1;u=prev[u]){ids.push(u);if(u===start)break}ids.reverse();return {nodes:ids,coordinates:ids.map(i=>graph.coordinates[i]),metres:ds[end]};
 }
 function route(graph,stops){
  if(stops.length<2||stops.length>5)throw Error('Choose between 2 and 5 stops.');
  if(new Set(stops.map(s=>s.id)).size!==stops.length)throw Error('Each stop may appear once.');
  if(stops.some(s=>s.walk_offset_m>100))throw Error('A reliable mapped street access point is unavailable.');
  const legs=stops.slice(1).map((s,i)=>path(graph,stops[i].walk_node,s.walk_node));const metres=legs.reduce((a,l)=>a+l.metres,0);
  return {legs,metres,minutes:metres/(graph.speed_kmh*1000/60),geometry:{type:'MultiLineString',coordinates:legs.filter(l=>l.coordinates.length>1).map(l=>l.coordinates)}};
 }
 const api={matches,path,route};if(typeof module!=='undefined')module.exports=api;root.FoodCore=api;
})(typeof self!=='undefined'?self:globalThis);
