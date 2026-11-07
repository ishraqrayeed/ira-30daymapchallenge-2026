const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/map.html','utf8'),data=JSON.parse(fs.readFileSync(__dirname+'/map-data.json'));
class El{constructor(dataset={}){this.dataset=dataset;this.style={};this.value='';this.children=[];this.attrs={};this.classes=new Set();this.classList={toggle:(k,v)=>v?this.classes.add(k):this.classes.delete(k)};this.clientWidth=1000;this.clientHeight=1250;this.offsetHeight=100;}append(...a){this.children.push(...a)}replaceChildren(){this.children=[]}setAttribute(k,v){this.attrs[k]=v}getBoundingClientRect(){return{x:100,y:100}}setPointerCapture(){}}
for(const width of [1200,390]){
const els=Object.fromEntries(['canvas','route','tip','plus','minus','reset','compare','existing'].map(k=>['#'+k,new El()])),svg=new El();els['#canvas'].querySelector=()=>svg;
const services=data.lines.map(f=>new El({route:f.properties.id})),stations=data.stations.map(s=>new El({station:s.id})),keys=data.lines.map(f=>new El({select:f.properties.id}));
const ctx={document:{querySelector:k=>els[k],querySelectorAll:k=>({'.service':services,'.station':stations,'[data-select]':keys}[k]),createElement:()=>new El(),createTextNode:t=>t},window:{innerWidth:width},innerWidth:width,innerHeight:900,console};vm.createContext(ctx);vm.runInContext(html.match(/<script>([\s\S]*)<\/script>/)[1],ctx);
assert.equal(els['#route'].children.length,10);els['#route'].value='A';els['#route'].onchange();assert.equal(services.filter(g=>g.classes.has('dim')).length,9);
els['#compare'].onchange({target:{checked:true}});assert.equal(els['#existing'].attrs.visibility,'visible');
const before=svg.style.transform;els['#plus'].onclick();assert.notEqual(svg.style.transform,before);els['#reset'].onclick();assert.equal(svg.style.transform,before);
stations[0].onclick({clientX:100,clientY:100});assert.equal(els['#tip'].style.display,'block');
els['#canvas'].onkeydown({key:'Escape',preventDefault(){}});assert.equal(els['#tip'].style.display,'none');assert(services.every(g=>!g.classes.has('dim')));
els['#canvas'].onpointerdown({clientX:0,clientY:0,pointerId:1,target:{closest:()=>null}});els['#canvas'].onpointermove({clientX:50,clientY:20});assert.notEqual(svg.style.transform,before);
console.log('PASS controls at width '+width+': route filtering, comparison, zoom/reset, station details, escape, pan');}
