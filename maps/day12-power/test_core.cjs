const assert=require('node:assert/strict');
const {camera,smooth,stage,seeded,opacityExpression,revealTime,trailTime}=require('./core.js');
const final={center:[-115.2,35.4],zoom:5.5,padding:{left:380,right:45,top:60,bottom:90}};
const hoover=[-114.738,36.0155];
for(const mobile of [false,true]){
 let previousZoom=Infinity;
 for(let t=0;t<=10;t+=.05){const c=camera(t,final,hoover,mobile);assert(c.zoom<=previousZoom+1e-10);previousZoom=c.zoom;assert.equal(c.pitch,0);assert.equal(c.bearing,0)}
 assert.deepEqual(camera(0,final,hoover,mobile).center,hoover);
 assert.deepEqual(camera(10,final,hoover,mobile),{...final,pitch:0,bearing:0});
 assert.deepEqual(camera(100,final,hoover,mobile),camera(10,final,hoover,mobile));
 const middle=camera(5,final,hoover,mobile);assert(middle.zoom>final.zoom);
}
let previous=0;
for(let reveal=14;reveal<=32;reveal+=.01){
 const born=revealTime(reveal);assert(born>=1&&born>=previous);assert(born+1.2<=4.01);previous=born;
 const trail=trailTime(reveal);assert(trail>=2&&trail+.7<=3.41);
}
assert.equal(revealTime(14),1);assert.equal(revealTime(32),2.8);
assert.equal(smooth(-1),0);assert.equal(smooth(2),1);assert.equal(stage(4.5),'The pulse continues');
assert.equal(opacityExpression(4.5,.58)[1][3],0);
const a=seeded(12),b=seeded(12);for(let n=0;n<100;n++)assert.equal(a(),b());
console.log('PASS: smooth ten-second Hoover-to-region camera; outward corridor reveal complete by 4 seconds; trails visible by 3.4 seconds; active/background hierarchy');
