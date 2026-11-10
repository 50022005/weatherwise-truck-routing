"""Pure, provider-independent risk, road sampling, and recommendation logic."""
import math
from datetime import datetime,timezone
MILE=1609.344
LABELS=['Low','Moderate','High','Severe','No Travel']
def timestamp(iso):
    return datetime.fromisoformat(iso.replace('Z','+00:00')).timestamp()
def iso(ts):
    return datetime.fromtimestamp(ts,timezone.utc).isoformat().replace('+00:00','Z')
def finite(v):
    return isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v)
def risk(weather,load):
    if weather is None or not all(finite(v) and v>=0 for v in [weather.get('wind'),weather.get('rain'),weather.get('snow'),load]): return None
    w,r,s=weather['wind'],weather['rain'],weather['snow']
    wind=0 if w<25 else 1 if w<35 else 2 if w<45 else 3 if w<55 else 4
    rain=0 if r<.1 else 1 if r<=.25 else 2 if r<=.5 else 3 if r<=1 else 4
    snow=0 if s<.5 else 1 if s<=1 else 2 if s<=2 else 3 if s<=3 else 4
    return max(wind,rain,snow,4 if w>=45 and load>30000 else 0,3 if 35<=w<45 and load>40000 else 0)
def hav(a,b):
    p=math.pi/180
    h=math.sin((b[1]-a[1])*p/2)**2+math.cos(a[1]*p)*math.cos(b[1]*p)*math.sin((b[0]-a[0])*p/2)**2
    return 6371000*2*math.asin(min(1,math.sqrt(h)))
def sample(route,spacing,departure):
    cs=route['geometry']['coordinates']
    if len(cs)<2: raise ValueError('Incomplete route geometry.')
    ds=[v for leg in route.get('legs',[]) for v in leg.get('annotation',{}).get('distance',[])]
    ts=[v for leg in route.get('legs',[]) for v in leg.get('annotation',{}).get('duration',[])]
    aligned=len(ds)==len(cs)-1 and len(ts)==len(ds)
    distances=ds if aligned else [hav(a,b) for a,b in zip(cs,cs[1:])]
    total=sum(distances)
    if total<=0: raise ValueError('Origin and destination must differ.')
    vertices=[(0,0,cs[0])];d=t=0
    for i,x in enumerate(distances):
        d+=x*route['distance']/total
        t+=ts[i] if aligned else route['duration']*x/total
        vertices.append((d,t,cs[i+1]))
    targets=[];x=0
    while x<route['distance']:
        targets.append(x);x+=spacing*MILE
        if len(targets)>219: raise ValueError('Trip exceeds 220 checkpoints. Use wider spacing or split the trip.')
    targets.append(route['distance'])
    j=1;result=[]
    for i,x in enumerate(targets):
        while j<len(vertices)-1 and vertices[j][0]<x:j+=1
        a,b=vertices[j-1],vertices[j]
        f=0 if b[0]==a[0] else (x-a[0])/(b[0]-a[0])
        result.append({'id':i,'segmentIndex':j,'coord':[a[2][k]+(b[2][k]-a[2][k])*f for k in range(2)],'mile':x/MILE,'eta':iso(timestamp(departure)+a[1]+(b[1]-a[1])*f)})
    return result

def at_time(forecast,eta):
    h=(forecast or {}).get('hourly',{});times=h.get('time',[]);ts=timestamp(eta)
    if not times or ts<times[0] or ts>times[-1]:return None
    i=next(i for i,t in enumerate(times) if t>=ts)
    vals=[h.get(k,[])[i] if i<len(h.get(k,[])) else None for k in ['wind_speed_10m','rain','showers','snowfall']]
    if not all(finite(v) for v in vals):return None
    return {'wind':vals[0],'rain':(vals[1]+vals[2])/25.4,'snow':vals[3]/2.54,'forecastTime':iso(times[i])}
def summarize(route,points,load):
    points=[dict(p,risk=risk(p.get('weather'),load)) for p in points]
    miles=[0]*5;unknown=weighted=0
    for a,b in zip(points,points[1:]):
        length=b['mile']-a['mile']
        if a['risk'] is None or b['risk'] is None:unknown+=length
        else:
            level=max(a['risk'],b['risk']);miles[level]+=length;weighted+=level*length
    return dict(route,checkpoints=points,miles=miles,unknown=unknown,average=weighted/(route['distance']/MILE or 1),blocked=any(p['risk']==4 for p in points),maxRisk=None if any(p['risk'] is None for p in points) else max(p['risk'] for p in points))
def recommend(routes):
    eligible=[r for r in routes if not r['blocked'] and r['unknown']<1e-7]
    return min(eligible,key=lambda r:(r['miles'][3],r['miles'][2],r['average'],r['duration']))['id'] if eligible else None
