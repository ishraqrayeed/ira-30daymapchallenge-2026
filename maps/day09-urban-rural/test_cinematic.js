const assert=require('node:assert/strict'),M=require('./cinematic-core');
for(let i=0;i<9;i++){const f=M.frame((i+.2)/9,9);assert.equal(f.index,i);assert.ok(Math.abs(f.phase-.2)<1e-10);}
assert.deepEqual(M.frame(1,9),{index:8,phase:1});assert.equal(M.frame(-1,9).index,0);
const a={lon:-105,lat:35,range:22000000,pitch:-90},b={lon:-115.15,lat:36.16,range:105000,pitch:-65};
assert.ok(Math.abs(M.pose(a,b,0).range-a.range)<1e-7);assert.ok(Math.abs(M.pose(a,b,1).range-b.range)<1e-7);
for(let i=1;i<=100;i++)assert.ok(M.pose(a,b,i/100).range<M.pose(a,b,(i-1)/100).range);
console.log('Historical timeline and continuous camera tests passed');
