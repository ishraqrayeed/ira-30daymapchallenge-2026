'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'../maps/day06-vintage'),T=require(path.join(root,'web/map-controls.js')),data=JSON.parse(fs.readFileSync(path.join(root,'web/map-data.json')));
assert.deepEqual(T.validateData(data),{historic_rating:293,other_or_unrated:813,legacy:25});
assert.equal(T.visible(data.buildings.features,new Set(['historic_rating'])).length,293);
assert.equal(T.visible(data.buildings.features,new Set()).length,0);
assert.equal(T.styleFor({group:'historic_rating'}).fillColor,'#8f382a');assert.equal(T.styleFor({group:'legacy'}).fillOpacity,0);
const malicious=T.details({id:1,name:'<img src=x onerror=alert(1)>',rating:'<script>bad()</script>',source:'javascript:alert(1)'});assert(!malicious.includes('<img'));assert(!malicious.includes('<script>'));assert(!malicious.includes('href='));assert(malicious.includes('&lt;img'));
assert.equal(T.sourceURL('https://evil.example/?www.telluride.gov'),null);assert.equal(T.sourceURL('http://www.telluride.gov/'),null);assert.equal(T.sourceURL('https://www.telluride.gov/DocumentCenter/View/2131'),'https://www.telluride.gov/DocumentCenter/View/2131');
const corrupt=structuredClone(data);corrupt.buildings.features[1].properties.id=corrupt.buildings.features[0].properties.id;assert.throws(()=>T.validateData(corrupt),/Duplicate/);
const wrongDate=structuredClone(data);wrongDate.summary.pre1900_count=293;assert.throws(()=>T.validateData(wrongDate),/scope/);
function element(dataset={}){return{dataset,hidden:false,attributes:{},style:{},textContent:'',setAttribute(k,v){this.attributes[k]=v;},addEventListener(k,v){this['on'+k]=v;},getBoundingClientRect(){return{left:0,right:400,top:0,bottom:400};},showModal(){this.open=true;},close(){this.open=false;}};}
async function integration(ok=true){
 const nodes=Object.fromEntries(['#map-status','#downtown','#full-town','#terrain','#ratings-dialog','#about-ratings','.close-dialog'].map(k=>[k,element()]));nodes['#ratings-dialog'].querySelector=()=>nodes['.close-dialog'];
 const groupButtons=T.groups.map(group=>element({group})),landmarkButtons=[1,2,3].map(landmark=>element({landmark:String(landmark)}));
 const doc={documentElement:{dataset:{}},querySelector(q){if(q==='[data-group=historic_rating]')return groupButtons[0];return nodes[q];},querySelectorAll(q){return q==='[data-group]'?groupButtons:landmarkButtons;}};
 const map={layers:new Set(),zoom:16,panes:{},attributionControl:{setPrefix(){},addAttribution(){}},createPane(k){this.panes[k]={style:{}};},getPane(k){return this.panes[k];},closePopup(){},fitBounds(b,o){this.lastBounds=b;},setView(c,z){this.center=c;this.zoom=z;},getZoom(){return this.zoom;},hasLayer(l){return this.layers.has(l);},removeLayer(l){this.layers.delete(l);},on(k,v){this['on'+k]=v;},latLngToLayerPoint(c){return{x:c[1]*1000,y:-c[0]*1000};}};
 function featureLayer(feature){return{feature,events:{},on(k,v){this.events[k]=v;return this;},setStyle(s){this.style=s;return this;},bindPopup(html){this.popup=html;return this;},openPopup(){this.opened=true;return this;},fire(k){this.events[k]?.();return this;},getBounds(){return[[37,-108],[38,-107]];}};}
 function geoJSON(initial,options={}){const layer={features:[],addTo(m){m.layers.add(this);return this;},clearLayers(){this.features=[];},addData(features){for(const f of features){const item=featureLayer(f);options.onEachFeature?.(f,item);this.features.push(item);}}};if(initial)layer.addData(initial.features);return layer;}
 const L={map(){return map;},geoJSON,control:{scale(){return{addTo(){}};}},marker(c,options){return{events:{},addTo(m){m.layers.add(this);return this;},on(k,v){this.events[k]=v;return this;}};},divIcon(options){return options;}};
 const context={window:{Telluride:T,L},L,document:doc,fetch:async()=>({ok,json:async()=>structuredClone(data)}),matchMedia:()=>({matches:true}),history:{replaceState(...args){this.hash=args[2];}},location:{hash:''},console:{error(){}},URL,Set,Map,Number};vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'web/app.js'),'utf8'),context);await new Promise(resolve=>setImmediate(resolve));
 if(!ok){assert.equal(nodes['#map-status'].attributes.role,'alert');assert(!doc.documentElement.dataset.mapReady);return;}
 const app=context.window.TELLURIDE_MAP;assert.equal(doc.documentElement.dataset.mapReady,'true');assert(nodes['#map-status'].hidden);assert.equal(app.byId.size,1131);
 groupButtons[1].onclick();assert.equal(app.byId.size,318);assert.equal(groupButtons[1].attributes['aria-pressed'],'false');
 groupButtons[0].onclick();assert.equal(app.byId.size,25);
 landmarkButtons[2].onclick();assert(app.enabled.has('historic_rating'));assert.equal(app.byId.size,318);assert.equal(map.zoom,19);assert(app.byId.get(831).opened);assert.equal(context.history.hash,'#structure-831');
 nodes['#full-town'].onclick();assert.equal(nodes['#full-town'].attributes['aria-pressed'],'true');assert.equal(JSON.stringify(map.lastBounds),JSON.stringify(data.summary.town_bounds));
 nodes['#downtown'].onclick();assert.equal(nodes['#downtown'].attributes['aria-pressed'],'true');assert.equal(JSON.stringify(map.lastBounds),JSON.stringify(data.summary.downtown_bounds));
 const terrainEvent={currentTarget:nodes['#terrain']};nodes['#terrain'].onclick(terrainEvent);assert.equal(nodes['#terrain'].attributes['aria-pressed'],'false');nodes['#terrain'].onclick(terrainEvent);assert.equal(nodes['#terrain'].attributes['aria-pressed'],'true');
 nodes['#about-ratings'].onclick();assert(nodes['#ratings-dialog'].open);nodes['.close-dialog'].onclick();assert(!nodes['#ratings-dialog'].open);
}
(async()=>{await integration();await integration(false);const html=fs.readFileSync(path.join(root,'map.html'),'utf8');assert(!html.includes('<img id="poster"'));for(const match of html.matchAll(/(?:src|href)="((?:web|exports)\/[^"#]+)"/g))assert(fs.existsSync(path.join(root,match[1])),match[1]);console.log('Telluride: source counts, filters, landmark selection, views, contours, rating dialog, popup safety and load-error behavior passed.');})();
