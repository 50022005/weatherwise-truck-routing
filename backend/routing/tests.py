from django.test import SimpleTestCase,Client
from unittest.mock import patch
from datetime import datetime,timezone,timedelta
from .engine import risk,sample,summarize,recommend,at_time,MILE
from .views import validate
class EngineTests(SimpleTestCase):
    def test_boundaries(self):
        for wind,result in [(24.99,0),(25,1),(34.99,1),(35,2),(44.99,2),(45,3),(54.99,3),(55,4)]:self.assertEqual(risk(dict(wind=wind,rain=0,snow=0),0),result)
        for value,result in [(.0999,0),(.1,1),(.25,1),(.25001,2),(.5,2),(.50001,3),(1,3),(1.001,4)]:self.assertEqual(risk(dict(wind=0,rain=value,snow=0),0),result)
        for value,result in [(.499,0),(.5,1),(1,1),(1.001,2),(2,2),(2.001,3),(3,3),(3.001,4)]:self.assertEqual(risk(dict(wind=0,rain=0,snow=value),0),result)
    def test_load(self):
        for wind,load,result in [(45,30000,3),(45,30001,4),(35,40000,2),(35,40001,3),(55,0,4)]:self.assertEqual(risk(dict(wind=wind,rain=0,snow=0),load),result)
    def test_sampling(self):
        route=dict(distance=100*MILE,duration=10000,geometry={'coordinates':[[0,0],[1,0],[2,0]]},legs=[{'annotation':{'distance':[50*MILE]*2,'duration':[1000,9000]}}])
        points=sample(route,25,'2026-11-10T00:00:00Z')
        self.assertEqual([round(p['mile']) for p in points],[0,25,50,75,100]);self.assertEqual(points[1]['eta'],'2026-11-10T00:08:20Z');self.assertEqual(points[3]['eta'],'2026-11-10T01:31:40Z')
    def test_weather(self):
        f={'hourly':{'time':[0,3600,7200],'wind_speed_10m':[1,2,None],'rain':[0,25.4,0],'showers':[0,0,0],'snowfall':[0,2.54,0]}}
        w=at_time(f,'1970-01-01T00:30:00Z');self.assertEqual(w['rain'],1);self.assertEqual(w['snow'],1);self.assertIsNone(at_time(f,'1970-01-01T01:30:00Z'));self.assertIsNone(at_time(f,'1970-01-01T03:00:00Z'))
    def test_summary_and_no_travel(self):
        r=dict(id=0,distance=100*MILE,duration=10)
        result=summarize(r,[{'mile':0,'weather':dict(wind=0,rain=0,snow=0)},{'mile':100,'weather':dict(wind=55,rain=0,snow=0)}],0)
        self.assertEqual(result['miles'][4],100);self.assertTrue(result['blocked']);self.assertIsNone(recommend([result]))
    def test_unknown(self):
        result=summarize(dict(id=0,distance=MILE,duration=10),[{'mile':0,'weather':None},{'mile':1,'weather':None}],0)
        self.assertEqual(result['unknown'],1);self.assertIsNone(recommend([result]))
    def test_rank(self):
        def r(id,severe,high,avg,seconds):return dict(id=id,miles=[0,0,high,severe,0],average=avg,duration=seconds,blocked=False,unknown=0)
        for a,b in [(r(0,1,0,0,1),r(1,0,50,3,99)),(r(0,0,1,0,1),r(1,0,0,3,99)),(r(0,0,0,2,1),r(1,0,0,1,99)),(r(0,0,0,1,20),r(1,0,0,1,10))]:self.assertEqual(recommend([a,b]),1)
class APITests(SimpleTestCase):
    def setUp(self):
        self.data={'origin':{'name':'A','coord':[0,0]},'destination':{'name':'B','coord':[1,1]},'departure':(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat(),'load':32000,'spacing':25}
    def test_validation(self):
        self.assertEqual(validate(self.data),self.data)
        for field,value in [('load',-1),('load',float('nan')),('spacing',15),('departure','nope'),('departure','2026-11-10T01:00:00')]:
            with self.assertRaises(ValueError):validate(dict(self.data,**{field:value}))
    def test_http(self):
        c=Client();self.assertEqual(c.get('/api/health/').status_code,200);self.assertEqual(c.get('/api/plan/').status_code,405);self.assertEqual(c.post('/api/plan/',data='bad',content_type='application/json').status_code,400)
    def test_oversized_request_returns_json(self):
        res=Client().post('/api/plan/',data='x'*17000,content_type='application/json')
        self.assertEqual(res.status_code,413)
        self.assertIn('error',res.json())
    def test_blank_place_is_invalid(self):
        with self.assertRaises(ValueError):validate(dict(self.data,origin={'name':'  ','coord':[0,0]}))
    @patch('routing.views.build_plan',return_value={'routes':[],'recommended':None})
    def test_api_contract(self,mocked):
        res=Client().post('/api/plan/',data=self.data,content_type='application/json');self.assertEqual(res.status_code,200);self.assertEqual(res.json()['routes'],[]);mocked.assert_called_once()

class ProviderTests(SimpleTestCase):
    @patch('routing.providers.forecasts',side_effect=lambda coords:[{} for _ in coords])
    @patch('routing.providers.routes_for')
    def test_duplicate_initial_routes_do_not_hide_equal_length_alternatives(self,routes_for,forecasts):
        from .providers import build_plan
        def route(coords):return dict(distance=10000,duration=600,geometry={'coordinates':coords})
        a=route([[0,0],[.05,0],[.1,0]])
        b=route([[0,0],[.05,.03],[.1,0]])
        c=route([[0,0],[.05,-.03],[.1,0]])
        routes_for.side_effect=[[a,a],[b],[c]]
        result=build_plan({'origin':{'coord':[0,0]},'destination':{'coord':[.1,0]},'departure':'2026-11-10T00:00:00Z','load':0,'spacing':25})
        self.assertEqual(len(result['routes']),3)
        self.assertEqual(routes_for.call_count,3)
