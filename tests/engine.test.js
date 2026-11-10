import test from 'node:test';import assert from 'node:assert/strict';import {risk,sample,summarize,recommend,atTime,MILE} from '../src/engine.js';
const w=(wind=0,rain=0,snow=0)=>({wind,rain,snow});
for(const [wind,expected] of [[24.999,0],[25,1],[34.999,1],[35,2],[44.999,2],[45,3],[54.999,3],[55,4]])test(`wind boundary ${wind}`,()=>assert.equal(risk(w(wind),0),expected));
for(const [rain,expected] of [[.0999,0],[.1,1],[.25,1],[.25001,2],[.5,2],[.50001,3],[1,3],[1.001,4]])test(`rain boundary ${rain}`,()=>assert.equal(risk(w(0,rain),0),expected));
for(const [snow,expected] of [[.499,0],[.5,1],[1,1],[1.001,2],[2,2],[2.001,3],[3,3],[3.001,4]])test(`snow boundary ${snow}`,()=>assert.equal(risk(w(0,0,snow),0),expected));
test('strict load thresholds and combined hazards',()=>{assert.equal(risk(w(45),30000),3);assert.equal(risk(w(45),30001),4);assert.equal(risk(w(35),40000),2);assert.equal(risk(w(35),40001),3);assert.equal(risk(w(55),0),4);assert.equal(risk(w(0,2),0),4);});
test('invalid or missing forecasts stay unknown',()=>{assert.equal(risk(null,10),null);assert.equal(risk(w(NaN),0),null);assert.equal(risk(w(-1),0),null);});
const route={id:0,distance:100*MILE,duration:10000,geometry:{coordinates:[[0,0],[1,0],[2,0]]},legs:[{annotation:{distance:[50*MILE,50*MILE],duration:[1000,9000]}}]};
test('distance sampling uses segment travel time, includes both endpoints',()=>{const p=sample(route,25,'2026-11-10T00:00:00Z');assert.equal(p.length,5);assert.deepEqual(p.map(x=>Math.round(x.mile)),[0,25,50,75,100]);assert.equal(Date.parse(p[1].eta)-Date.parse(p[0].eta),500000);assert.equal(Date.parse(p[3].eta)-Date.parse(p[2].eta),4500000);assert.deepEqual(p.at(-1).coord,[2,0]);});
test('short route includes endpoint',()=>assert.equal(sample({...route,distance:1000},25,'2026-11-10T00:00:00Z').length,2));
test('forecast hour containing ETA; cm/mm conversion; null and horizon handling',()=>{const f={hourly:{time:[0,3600,7200],wind_speed_10m:[1,2,3],rain:[0,25.4,null],showers:[0,0,0],snowfall:[0,2.54,0]}};assert.deepEqual(atTime(f,'1970-01-01T00:30:00Z'),{wind:2,rain:1,snow:1,forecastTime:'1970-01-01T01:00:00.000Z'});assert.equal(atTime(f,'1970-01-01T01:30:00Z'),null);assert.equal(atTime(f,'1970-01-01T03:00:00Z'),null);});
test('interval risk uses worse endpoint; total miles conserved',()=>{const r=summarize(route,[{mile:0,weather:w()},{mile:25,weather:w(40)},{mile:100,weather:w(50)}],0);assert.deepEqual(r.miles,[0,0,25,75,0]);assert.equal(r.average,2.75);});
const r=(id,severe,high,average,duration,extra={})=>({id,miles:[0,0,high,severe,0],average,duration,blocked:false,unknown:0,...extra});
test('recommendation prioritizes severe then high then average then time',()=>{assert.equal(recommend([r(0,1,0,0,1),r(1,0,50,3,99)]),1);assert.equal(recommend([r(0,0,1,0,1),r(1,0,0,3,99)]),1);assert.equal(recommend([r(0,0,0,2,1),r(1,0,0,1,99)]),1);assert.equal(recommend([r(0,0,0,1,20),r(1,0,0,1,10)]),1);});
test('blocked and unknown never win; all blocked has no recommendation',()=>{assert.equal(recommend([r(0,0,0,0,1,{blocked:true}),r(1,1,1,3,20)]),1);assert.equal(recommend([r(0,0,0,0,1,{unknown:2})]),null);assert.equal(recommend([r(0,0,0,0,1,{blocked:true})]),null);});

// Keep the browser fallback and Django implementations from drifting.
test('Python and JavaScript risk engines agree across thresholds and load combinations',async()=>{
 const {spawnSync}=await import('node:child_process');
 const fixtures=[];
 for(const wind of [0,24.999,25,34.999,35,44.999,45,54.999,55,70])for(const load of [0,30000,30001,40000,40001])for(const [rain,snow] of [[0,0],[.1,.5],[.25,1],[.5,2],[1,3],[1.001,3.001]])fixtures.push({wind,rain,snow,load});
 const result=spawnSync(process.env.PYTHON||(process.platform==='win32'?'python':'python3'),['-c',`import sys,json;sys.path.insert(0,'backend');from routing.engine import risk;print(json.dumps([risk(x,x['load']) for x in json.load(sys.stdin)]))`],{input:JSON.stringify(fixtures),encoding:'utf8'});
 assert.equal(result.status,0,result.stderr);assert.deepEqual(JSON.parse(result.stdout),fixtures.map(x=>risk(x,x.load)));
});
