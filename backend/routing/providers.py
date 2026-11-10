"""Fixed-host public providers with timeout, bounded batches, and TTL caching."""
import json,math,hashlib
from urllib.request import urlopen,Request
from urllib.parse import urlencode
from urllib.error import URLError,HTTPError
from django.core.cache import cache
from .engine import sample,at_time,summarize,recommend,hav,iso
from datetime import datetime,timezone
class ProviderError(Exception):pass
def get(url):
    cache_key=hashlib.sha256(url.encode()).hexdigest()
    data=cache.get(cache_key)
    if data is not None:return data
    try:
        with urlopen(Request(url,headers={'User-Agent':'WeatherWise-Educational/1.0'}),timeout=25) as res:
            data=json.load(res)
    except (URLError,HTTPError,TimeoutError,ValueError) as e:
        raise ProviderError('Routing or weather provider unavailable. Please try again.') from e
    if isinstance(data,dict) and data.get('error'):raise ProviderError(data.get('reason','Provider error.'))
    cache.set(cache_key,data,600);return data

def routes_for(coords):
    data=get('https://router.project-osrm.org/route/v1/driving/'+';'.join(','.join(str(v) for v in c) for c in coords)+'?'+urlencode({'alternatives':3,'overview':'full','geometries':'geojson','annotations':'distance,duration','steps':'false'}))
    if data.get('code')!='Ok':raise ProviderError(data.get('message','No road route found.'))
    return data['routes']
def forecasts(coords):
    results=[]
    for i in range(0,len(coords),30):
        batch=coords[i:i+30]
        data=get('https://api.open-meteo.com/v1/forecast?'+urlencode({'latitude':','.join(str(c[1]) for c in batch),'longitude':','.join(str(c[0]) for c in batch),'hourly':'wind_speed_10m,rain,showers,snowfall','wind_speed_unit':'mph','forecast_days':7,'timeformat':'unixtime','timezone':'GMT'}))
        data=data if isinstance(data,list) else [data]
        if len(data)!=len(batch):raise ProviderError('Incomplete weather response.')
        results.extend(data)
    return results

def key(c):return ','.join(f'{v:.4f}' for v in c)
def signature(r):
    cs=r['geometry']['coordinates'];step=max(1,len(cs)//20)
    return ';'.join(','.join(f'{v:.2f}' for v in c) for c in cs[::step])
def build_plan(data):
    a,b=data['origin']['coord'],data['destination']['coord']
    raw=[]
    for r in routes_for([a,b]):
        if not any(signature(x)==signature(r) for x in raw):raw.append(r)
    if not raw:raise ProviderError('No road route found.')
    if len(raw)<3:
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy) or 1;offset=min(length*.15,1)
        for sign in [-1,1]:
            if len(raw)>=3:break
            via=[(a[0]+b[0])/2-sign*dy/length*offset,(a[1]+b[1])/2+sign*dx/length*offset]
            try:
                for r in routes_for([a,via,b]):
                    if r['distance']<raw[0]['distance']*1.8 and not any(signature(x)==signature(r) for x in raw):raw.append(r)
            except ProviderError:pass
    routes=[dict(r,id=i,name=['Primary corridor','Alternative corridor','Scenic detour'][i]) for i,r in enumerate(raw[:3])]
    unique={}
    for r in routes:
        r['checkpoints']=sample(r,data['spacing'],data['departure'])
        for p in r['checkpoints']:unique[key(p['coord'])]=p['coord']
    weather=dict(zip(unique,forecasts(list(unique.values()))))
    final=[]
    for r in routes:
        # Return ETA weather only. Full checkpoint forecasts and OSRM annotations
        # are computation inputs, not UI data; duplicating them can exceed host limits.
        points=[dict(p,weather=at_time(weather[key(p['coord'])],p['eta'])) for p in r['checkpoints']]
        final.append(summarize({k:v for k,v in r.items() if k!='legs'},points,data['load']))
    corridor=[]
    for r in routes:
        stride=max(1,math.ceil(len(r['checkpoints'])/4))
        for p in r['checkpoints'][::stride]:
            for delta in [-.16,0,.16]:
                c=[p['coord'][0],max(-89,min(89,p['coord'][1]+delta))]
                if not any(hav(q['coord'],c)<10000 for q in corridor):corridor.append({'coord':c})
    corridor=corridor[:36];warnings=[]
    try:
        for p,f in zip(corridor,forecasts([p['coord'] for p in corridor])):p['forecast']=f
    except ProviderError:
        corridor=[];warnings.append('Corridor forecast unavailable. Route weather remains available.')
    if len(routes)<3:warnings.insert(0,f'Provider returned {len(routes)} distinct route(s), fewer than the requested 3.')
    return {'routes':final,'recommended':recommend(final),'corridor':corridor,'warnings':warnings,'mode':'live','generatedAt':iso(datetime.now(timezone.utc).timestamp())}
