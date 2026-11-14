/* Continuous aerial circuit of source-verified Washington Park features. */
const cubic=(a,b,c,d,t)=>(1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d;
const ORIGINAL_DURATION_MS=18500;
let lo=0,hi=1;
for(let i=0;i<60;i++){const m=(lo+hi)/2;if(m*m*(3-2*m)<.45)lo=m;else hi=m;}
const ORIGINAL_ENTRY=(lo+hi)/2;
export const PARK_ENTRY_TIME_MS=ORIGINAL_ENTRY*ORIGINAL_DURATION_MS;
export const PARK_TRAVEL_DURATION_MS=50000;
export const PARK_FLIGHT_DURATION_MS=PARK_ENTRY_TIME_MS+PARK_TRAVEL_DURATION_MS;
export const PARK_ENTRY_PROGRESS=PARK_ENTRY_TIME_MS/PARK_FLIGHT_DURATION_MS;
export const PARK_FOCUS_TIMES=[0,6,11,20,28,34,39,50];
export const PARK_FOCUS_KEYS=['entry','smith_lake','north_playground','south_playground','grasmere_lake','tennis_courts','lake_west','bench'];
export function parkFlightProgress(ms){return Math.max(0,Math.min(1,ms/PARK_FLIGHT_DURATION_MS));}
function hermite(a,b,ma,mb,seconds,t){return (2*t**3-3*t*t+1)*a+(t**3-2*t*t+t)*seconds*ma+(-2*t**3+3*t*t)*b+(t**3-t*t)*seconds*mb;}
export function parkFlightCamera(progress,start,bench,entry,padding,landmarks={}){
  const t=Math.max(0,Math.min(1,progress)),elapsed=t*PARK_FLIGHT_DURATION_MS;
  let center,zoom,pitch,bearing,label,phase;
  if(elapsed<=PARK_ENTRY_TIME_MS){
    const old=elapsed/ORIGINAL_DURATION_MS,f=old*old*(3-2*old)/.45;
    center=[cubic(start.center[0],entry[0]+.025,entry[0],entry[0],f),cubic(start.center[1],entry[1]+.018,entry[1]+.0007,entry[1],f)];
    zoom=cubic(start.zoom,start.zoom+1,14.9,15.2,f);pitch=cubic(0,25,48,50,f);bearing=cubic(0,65,165,175,f);
    phase='city';label='Approaching Washington Park from the north.';
  }else{
    const focus=key=>landmarks[key]?.coordinates||entry;
    const points=[entry,focus('smith_lake'),focus('north_playground'),focus('south_playground'),focus('grasmere_lake'),focus('tennis_courts'),focus('lake_west'),bench];
    const zs=[15.2,15.8,17.1,17,15.8,16.9,15.9,20.2],ps=[50,48,50,50,47,50,48,52],bs=[175,195,210,240,280,330,380,440];
    const labels=['North entrance','Smith Lake','North playground','South playground','Grasmere Lake','Tennis courts','Grasmere Lake from the west','Returning to our mapped bench'];
    const seconds=(elapsed-PARK_ENTRY_TIME_MS)/1000;
    let segment=0;while(segment<6&&seconds>PARK_FOCUS_TIMES[segment+1])segment++;
    const span=PARK_FOCUS_TIMES[segment+1]-PARK_FOCUS_TIMES[segment],f=Math.max(0,Math.min(1,(seconds-PARK_FOCUS_TIMES[segment])/span));
    const approachDerivative=6*ORIGINAL_ENTRY*(1-ORIGINAL_ENTRY)/ORIGINAL_DURATION_MS/.45*1000;
    const sample=(values,initial)=>{
      const tangent=index=>{
        if(index===0)return initial;if(index===7)return 0;
        const left=(values[index]-values[index-1])/(PARK_FOCUS_TIMES[index]-PARK_FOCUS_TIMES[index-1]);
        const right=(values[index+1]-values[index])/(PARK_FOCUS_TIMES[index+1]-PARK_FOCUS_TIMES[index]);
        if(left*right<=0)return 0;
        const central=(values[index+1]-values[index-1])/(PARK_FOCUS_TIMES[index+1]-PARK_FOCUS_TIMES[index-1]);
        return Math.sign(central)*Math.min(Math.abs(central),3*Math.abs(left),3*Math.abs(right));
      };
      return hermite(values[segment],values[segment+1],tangent(segment),tangent(segment+1),span,f);
    };
    center=[sample(points.map(p=>p[0]),0),sample(points.map(p=>p[1]),-.0021*approachDerivative)];
    zoom=sample(zs,.9*approachDerivative);pitch=sample(ps,6*approachDerivative);bearing=sample(bs,30*approachDerivative);
    phase=segment===6?'bench':'park';label=labels[segment+1]+'.';
  }
  const inset=Object.fromEntries(['top','bottom','left','right'].map(key=>[key,start.padding[key]+(padding[key]-start.padding[key])*t]));
  return {center,zoom,pitch,bearing,padding:inset,label,phase};
}
