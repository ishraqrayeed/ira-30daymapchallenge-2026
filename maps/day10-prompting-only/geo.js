/* Pure spherical geography; shared by browser and Node QA. */
(function(root){
const presets=[['Denver',39.7392,-104.9903],['Dhaka',23.8103,90.4125],['New York',40.7128,-74.006],['London',51.5074,-.1278],['Tokyo',35.6762,139.6503],['Sydney',-33.8688,151.2093]];
// Add 180 degrees, then normalize to [-180, 180). Handles wrapped inputs too.
function normalize(lon){return ((lon+180)%360+360)%360-180;}
function antipode(lat,lon){
 if(!Number.isFinite(lat)||Math.abs(lat)>90||!Number.isFinite(lon))throw new RangeError('Invalid latitude/longitude');
 return {lat:-lat,lon:normalize(lon+180)};
}
const presetLabels={Denver:'Denver, Colorado, USA',Dhaka:'Dhaka, Bangladesh','New York':'New York, New York, USA',London:'London, United Kingdom',Tokyo:'Tokyo, Japan',Sydney:'Sydney, New South Wales, Australia'};
// Orthographic side view of the selected diameter: project the actual ECEF
// tunnel into an origin-aligned section plane. No second globe coordinate system.
function sectionPoint(lat,lon,t){const axis=vector(lat,lon),p=tunnel(lat,lon,t);const along=p.reduce((sum,v,i)=>sum+v*axis[i],0)/6371000;const angle=-Math.PI*.77;return {x:along*Math.cos(angle),y:along*Math.sin(angle)};}
function vector(lat,lon){const a=lat*Math.PI/180,b=lon*Math.PI/180;return [Math.cos(a)*Math.cos(b),Math.cos(a)*Math.sin(b),Math.sin(a)];}
function tunnel(lat,lon,t){return vector(lat,lon).map(v=>6371000*v*(1-2*t));}
function ringContains(ring,x,y){let inside=false;for(let i=0,j=ring.length-1;i<ring.length;j=i++){const [a,b]=ring[i],[c,d]=ring[j];if((b>y)!=(d>y)&&x<(c-a)*(y-b)/(d-b)+a)inside=!inside;}return inside;}
function contains(g,lon,lat){const polys=g.type==='Polygon'?[g.coordinates]:g.coordinates;return polys.some(p=>ringContains(p[0],lon,lat)&&!p.slice(1).some(r=>ringContains(r,lon,lat)));}
function classify(lat,lon,countries,marine){lon=normalize(lon);const land=countries.features.find(f=>contains(f.geometry,lon,lat));if(land)return {name:land.properties.name,type:'Mapped land · Natural Earth 1:110m'};const sea=marine.features.filter(f=>contains(f.geometry,lon,lat)).at(-1);return {name:sea?.properties.name||'Unclassified waters / coastal area',type:sea?'Mapped water · Natural Earth 1:110m':'No country or named marine polygon found'};}
const api={presets,presetLabels,normalize,antipode,vector,tunnel,sectionPoint,contains,classify};if(typeof module!=='undefined')module.exports=api;else root.Geo=api;
})(globalThis);
