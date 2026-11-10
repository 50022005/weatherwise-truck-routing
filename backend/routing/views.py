import json
from datetime import datetime,timezone
from django.http import JsonResponse,FileResponse,HttpResponse
from django.conf import settings
from django.views.decorators.http import require_POST,require_GET
from django.core.exceptions import RequestDataTooBig
from .engine import finite,timestamp
from .providers import build_plan,ProviderError

def validate(data):
    if not isinstance(data,dict):raise ValueError('Expected a JSON object.')
    for name in ['origin','destination']:
        p=data.get(name)
        if not isinstance(p,dict) or not isinstance(p.get('name'),str) or not p['name'].strip() or len(p['name'])>250:raise ValueError('Choose valid origin and destination cities.')
        c=p.get('coord')
        if not isinstance(c,list) or len(c)!=2 or not all(finite(v) for v in c) or not -180<=c[0]<=180 or not -90<=c[1]<=90:raise ValueError('Invalid coordinates.')
    if data['origin']['coord']==data['destination']['coord']:raise ValueError('Origin and destination must differ.')
    if not finite(data.get('load')) or not 0<=data['load']<=200000:raise ValueError('Load must be between 0 and 200,000 lb.')
    if data.get('spacing') not in [10,25,50] or isinstance(data.get('spacing'),bool):raise ValueError('Spacing must be 10, 25, or 50 miles.')
    departure=data.get('departure')
    if not isinstance(departure,str) or len(departure)>40:raise ValueError('Invalid departure time.')
    parsed=datetime.fromisoformat(departure.replace('Z','+00:00'))
    if parsed.tzinfo is None:raise ValueError('Departure must include a timezone offset.')
    diff=parsed.timestamp()-datetime.now(timezone.utc).timestamp()
    if not -60<=diff<=48*3600:raise ValueError('Choose a departure within the next 48 hours.')
    return data
@require_POST
def plan_view(request):
    # Stateless read-only computation. No login/session or mutable resources.
    try:
        data=validate(json.loads(request.body))
        return JsonResponse(build_plan(data))
    except RequestDataTooBig:return JsonResponse({'error':'Trip request is too large.'},status=413)
    except (ValueError,TypeError,KeyError,OverflowError) as e:return JsonResponse({'error':str(e)},status=400)
    except ProviderError as e:return JsonResponse({'error':str(e)},status=502)
@require_GET
def health(request):return JsonResponse({'status':'ok','service':'weatherwise-django'})
@require_GET
def index(request):
    path=settings.BASE_DIR/'dist'/'index.html'
    if not path.exists():return HttpResponse('Build the React client with npm run build.',status=503)
    return FileResponse(path.open('rb'),content_type='text/html')
