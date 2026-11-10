export const LABELS=['Low','Moderate','High','Severe','No Travel'];
export const COLORS=['#329b78','#e5b946','#e98336','#d75151','#812b4d'];
export const MILE=1609.344;
export function risk(w,load){
 if(!w||![w.wind,w.rain,w.snow,load].every(Number.isFinite)||Math.min(w.wind,w.rain,w.snow,load)<0)return null;
 const wind=w.wind<25?0:w.wind<35?1:w.wind<45?2:w.wind<55?3:4;
 // Shared endpoints in the brief belong to the lower band (0.25, 0.50, 1.00).
 const rain=w.rain<.1?0:w.rain<=.25?1:w.rain<=.5?2:w.rain<=1?3:4;
 const snow=w.snow<.5?0:w.snow<=1?1:w.snow<=2?2:w.snow<=3?3:4;
 return Math.max(wind,rain,snow,w.wind>=45&&load>30000?4:0,w.wind>=35&&w.wind<45&&load>40000?3:0);
}
export function hav(a,b){const r=Math.PI/180,dp=(b[1]-a[1])*r,dl=(b[0]-a[0])*r;return 6371000*2*Math.asin(Math.min(1,Math.sqrt(Math.sin(dp/2)**2+Math.cos(a[1]*r)*Math.cos(b[1]*r)*Math.sin(dl/2)**2)));}
export function sample(route,spacing,departure){
 const cs=route.geometry.coordinates; if(cs.length<2)throw Error('Route geometry is incomplete.');
 const ds=route.legs?.flatMap(l=>l.annotation?.distance||[])||[],ts=route.legs?.flatMap(l=>l.annotation?.duration||[])||[];
 const aligned=ds.length===cs.length-1&&ts.length===ds.length;
 const distances=aligned?ds:cs.slice(1).map((c,i)=>hav(cs[i],c));
 const total=distances.reduce((a,b)=>a+b,0);if(!total)throw Error('Origin and destination must be different.');
 const factor=route.distance/total;let d=0,t=0;
 const vertices=[{d:0,t:0,c:cs[0]}];
 distances.forEach((x,i)=>{d+=x*factor;t+=aligned?ts[i]:route.duration*x/total;vertices.push({d,t,c:cs[i+1]});});
 const targets=[];for(let x=0;x<route.distance;x+=spacing*MILE)targets.push(x);targets.push(route.distance);
 if(targets.length>220)throw Error('Trip exceeds 220 checkpoints per route. Use wider spacing or split the trip.');
 let j=1;return targets.map((x,i)=>{while(j<vertices.length-1&&vertices[j].d<x)j++;const a=vertices[j-1],b=vertices[j],f=b.d===a.d?0:(x-a.d)/(b.d-a.d);return {id:i,segmentIndex:j,coord:a.c.map((v,k)=>v+(b.c[k]-v)*f),mile:x/MILE,eta:new Date(new Date(departure).getTime()+(a.t+(b.t-a.t)*f)*1000).toISOString()};});
}
export function atTime(forecast,iso){
 const hour=Date.parse(iso)/1000;const h=forecast?.hourly;if(!h?.time?.length)return null;
 // Hourly precipitation describes the preceding hour. Select the containing hour's end.
 const i=h.time.findIndex(t=>t>=hour);if(i<0||hour<h.time[0])return null;
 const vals=[h.wind_speed_10m?.[i],h.rain?.[i],h.showers?.[i],h.snowfall?.[i]];
 if(!vals.every(v=>typeof v==='number'&&Number.isFinite(v)))return null;
 return {wind:vals[0],rain:(vals[1]+vals[2])/25.4,snow:vals[3]/2.54,forecastTime:new Date(h.time[i]*1000).toISOString()};
}
export function summarize(route,checkpoints,load){
 const cps=checkpoints.map(p=>({...p,risk:risk(p.weather,load)}));const miles=[0,0,0,0,0];let unknown=0,total=0;
 for(let i=0;i<cps.length-1;i++){const length=cps[i+1].mile-cps[i].mile;const a=cps[i].risk,b=cps[i+1].risk;if(a===null||b===null)unknown+=length;else {const r=Math.max(a,b);miles[r]+=length;total+=r*length;}}
 return {...route,checkpoints:cps,miles,unknown,average:total/(route.distance/MILE||1),blocked:cps.some(p=>p.risk===4),maxRisk:cps.some(p=>p.risk===null)?null:Math.max(...cps.map(p=>p.risk))};
}
export function recommend(routes){const eligible=routes.filter(r=>!r.blocked&&r.unknown<1e-7);return [...eligible].sort((a,b)=>a.miles[3]-b.miles[3]||a.miles[2]-b.miles[2]||a.average-b.average||a.duration-b.duration)[0]?.id??null;}
