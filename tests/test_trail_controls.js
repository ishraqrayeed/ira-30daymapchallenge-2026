// Exercise the real generated script with a minimal canvas/DOM host. Browser
// appearance still requires visual review; these checks cover control behavior.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('maps/day02-lines/map.html','utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
const nodes=new Map(),queue=[],strokes=[];
function element(id){if(!nodes.has(id))nodes.set(id,{hidden:false,textContent:'',innerHTML:'',style:{},listeners:{},children:[],addEventListener(k,f){this.listeners[k]=f;},setAttribute(k,v){this[k]=v;},replaceChildren(){this.children=[];},append(...v){this.children.push(...v);},getBoundingClientRect(){return {width:600,left:0,top:0};},setPointerCapture(){}});return nodes.get(id);}
const ctx=new Proxy({}, {get(o,k){return o[k]??((...args)=>{if(k==='stroke')strokes.push(o.strokeStyle);});},set(o,k,v){o[k]=v;return true;}});
element('map').getContext=()=>ctx;
const sandbox={console,document:{getElementById:element,createElement:()=>element(Math.random()),querySelector:()=>element('circle')},window:{devicePixelRatio:1,innerWidth:1280},Image:class{complete=true;naturalWidth=2400;},ResizeObserver:class{constructor(f){this.f=f;}observe(){this.f();}},requestAnimationFrame:f=>{queue.push(f);return queue.length;}};
vm.createContext(sandbox);vm.runInContext(script,sandbox);
function run(code){return vm.runInContext(code,sandbox);}
function flush(){while(queue.length)queue.shift()();}
flush();assert.ok(strokes.some(s=>s.startsWith('rgb(')),'elevation colors drawn');
element('zoom-in').onclick();assert.ok(run('state.zoom')>1);
element('reset').onclick();assert.equal(run('state.zoom'),1);
const id=run('trails[0].id');
run('select(trails[0])');flush();assert.equal(element('selected').hidden,false);assert.ok(element('profile').innerHTML.includes('<line'));
assert.match(element('profile')['aria-label'],/elevations from/);
element('clear').onclick();assert.equal(run('state.selected'),null);
// Hit-testing at the middle of a real segment returns a nearby trail, then a tap
// populates its profile. Geometry is transformed from map units to CSS pixels.
const tap=run('(()=>{const t=trails.reduce((a,b)=>a.miles>b.miles?a:b);const p=t.points[Math.floor(t.points.length/2)];return {clientX:p[0]*.6,clientY:p[1]*.6,pointerId:1,pointerType:"touch"};})()');
assert.ok(run(`nearest(${JSON.stringify(tap)}).trail`));
element('map').listeners.pointerdown(tap);element('map').listeners.pointerup(tap);assert.ok(run('state.selected'));flush();
const selected=run('state.selected.id');
element('map').listeners.pointerdown(tap);element('map').listeners.pointermove({...tap,clientX:tap.clientX+50});element('map').listeners.pointerup({...tap,clientX:tap.clientX+50});assert.equal(run('state.selected.id'),selected,'drag must not select another line');
element('map').listeners.keydown({key:']',preventDefault(){}});assert.ok(run('state.selected'));assert.ok(run('state.zoom')>=1);
element('map').listeners.keydown({key:'Escape',preventDefault(){}});assert.equal(run('state.selected'),null);
element('reset').onclick();flush();assert.equal(run('state.x'),0);assert.equal(run('state.y'),0);
console.log('Trail controls passed: drawing, zoom, reset, profile, tap, drag, keyboard.');
