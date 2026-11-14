import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
const code=readFileSync(new URL('../day14-borgesian/camera-path.js',import.meta.url),'utf8');
const {parkFlightCamera,parkFlightProgress,PARK_ENTRY_TIME_MS,PARK_ENTRY_PROGRESS,PARK_FLIGHT_DURATION_MS,PARK_FOCUS_TIMES,PARK_FOCUS_KEYS}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
const qa=JSON.parse(readFileSync(new URL('../day14-borgesian/data/qa.json',import.meta.url)));
const start={center:[-104.85,39.76],zoom:9.8,padding:{top:210,bottom:245,left:30,right:30}};
const inset={top:205,bottom:260,left:25,right:25};
const camera=t=>parkFlightCamera(t,start,qa.bench.coordinates,qa.tour_entry,inset,qa.tour_landmarks);

test('route begins in Denver and lands precisely on the original bench',()=>{
  assert.deepEqual(camera(0).center,start.center);assert.deepEqual(camera(1).center,qa.bench.coordinates);
  assert.equal(camera(1).zoom,20.2);assert.equal(camera(1).pitch,52);
});
test('aerial circuit visits each source-verified lake, playground and tennis landmark',()=>{
  for(let i=1;i<7;i++){
    const progress=(PARK_ENTRY_TIME_MS+PARK_FOCUS_TIMES[i]*1000)/PARK_FLIGHT_DURATION_MS;
    const a=camera(progress).center,b=qa.tour_landmarks[PARK_FOCUS_KEYS[i]].coordinates;
    assert.ok(Math.hypot(a[0]-b[0],a[1]-b[1])<1e-9,PARK_FOCUS_KEYS[i]);
  }
});
test('north entry has continuous position and velocity without a pause',()=>{
  const t=PARK_ENTRY_PROGRESS,e=1e-7,a=camera(t-e),b=camera(t),c=camera(t+e);
  assert.ok(Math.abs(b.center[1]-qa.tour_entry[1])<1e-10);
  for(const key of ['zoom','pitch','bearing']){
    const left=(b[key]-a[key])/e,right=(c[key]-b[key])/e;
    assert.ok(Math.abs(left-right)<.05,key+' velocity changes abruptly');
  }
  assert.ok(c.center[1]<a.center[1],'camera pauses at north entry');
});
test('park gets 50 seconds and landing zoom is gradual and monotonic',()=>{
  assert.equal(PARK_FLIGHT_DURATION_MS-PARK_ENTRY_TIME_MS,50000);assert.equal(parkFlightProgress(PARK_FLIGHT_DURATION_MS),1);
  let previous=0;
  for(let ms=PARK_ENTRY_TIME_MS+39000;ms<=PARK_FLIGHT_DURATION_MS;ms+=50){
    const frame=camera(parkFlightProgress(ms));assert.ok(frame.zoom>=previous);previous=frame.zoom;assert.ok(frame.pitch>=0&&frame.pitch<=55);
  }
});
const samples=Array.from({length:501},(_,i)=>camera((PARK_ENTRY_TIME_MS+(PARK_FLIGHT_DURATION_MS-PARK_ENTRY_TIME_MS)*i/500)/PARK_FLIGHT_DURATION_MS).center);
writeFileSync('/tmp/day14-park-flight-samples.json',JSON.stringify(samples));
