export const DURATION=15, HOLD=1.3, TRAVEL=11;
export const distanceAt=t=>5*Math.max(0,Math.min(1,(t-HOLD)/TRAVEL));
export function positionAt(route,miles){
  let lo=0,hi=route.length-1;
  while(hi-lo>1){const mid=(lo+hi)>>1;if(route[mid][2]<=miles)lo=mid;else hi=mid;}
  const a=route[lo],b=route[hi],f=Math.max(0,Math.min(1,(miles-a[2])/(b[2]-a[2])));
  return {x:a[0]+(b[0]-a[0])*f,y:a[1]+(b[1]-a[1])*f,angle:Math.atan2(b[1]-a[1],b[0]-a[0])-Math.PI/2,time:a[3]+(b[3]-a[3])*f,index:lo};
}
// Distance along the closest projected route leg, used only for pointer scrubbing.
export function nearestDistance(route,x,y){
 let best=Infinity,miles=0;
 for(let i=0;i<route.length-1;i++){
  const a=route[i],b=route[i+1],dx=b[0]-a[0],dy=b[1]-a[1],den=dx*dx+dy*dy;
  const t=den?Math.max(0,Math.min(1,((x-a[0])*dx+(y-a[1])*dy)/den)):0;
  const d=(x-a[0]-t*dx)**2+(y-a[1]-t*dy)**2;
  if(d<best){best=d;miles=a[2]+t*(b[2]-a[2]);}
 }
 return Math.max(0,Math.min(5,miles));
}
