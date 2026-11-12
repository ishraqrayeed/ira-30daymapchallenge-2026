/* Display time and geography only. No electrical-network solver or flow model. */
(function(root){
  'use strict';
  const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
  const smooth=x=>{x=clamp(x);return x*x*(3-2*x)};
  const mix=(a,b,t)=>a+(b-a)*t;
  // One gentle ten-second pullback; no rotation or repeated camera movement.
  function camera(t,final,hoover,mobile=false){
    const u=smooth(t/10),startZoom=Math.max(final.zoom,Math.min(mobile?7:7.7,final.zoom+2));
    return {center:hoover.map((v,i)=>mix(v,final.center[i],u)),zoom:mix(startZoom,final.zoom,u),padding:final.padding,pitch:0,bearing:0};
  }
  function revealTime(reveal){return 1+clamp((reveal-14)/18)*1.8}
  function trailTime(reveal){return 2+clamp((reveal-14)/18)*.7}
  function stage(t){return t<.5?'The Southwest':t<1?'The source':t<2.5?'An awakening':t<4.5?'Across the Southwest':'The pulse continues'}
  function opacityExpression(t,maximum){return ['*',['case',['==',['get','active'],1],maximum,0],['interpolate',['linear'],['-',t,['get','start']],0,0,1.2,1]]}
  function seeded(seed){return ()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296}}
  const api={clamp,smooth,camera,stage,opacityExpression,revealTime,trailTime,seeded};
  if(typeof module!=='undefined')module.exports=api;else root.PulseCore=api;
})(globalThis);
