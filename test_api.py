import json, math,re
import pytest
from fastapi.testclient import TestClient
from backend import app as module
from backend.app import Mission,plan
@pytest.fixture
def client(tmp_path,monkeypatch):
 monkeypatch.setattr(module,'DB',str(tmp_path/'test.sqlite'))
 return TestClient(module.app)
def test_real_data(client):
 for path in ['health','roi','datasets','layers','science-sites','models','geology']:
  assert client.get('/api/'+path).status_code==200
 assert len(client.get('/api/science-sites').json())==3
 geo=client.get('/api/geology').json();assert len([f for f in geo['features'] if f['properties']['source_layer']=='GeoUnits_v1'])==5
 for url in ['/','/runtime/HiRISE.png','/runtime/CTX.png','/runtime/slope.png']:
  assert client.get(url).status_code==200
 html=client.get('/').text
 for url in re.findall(r'(?:src|href)="(/assets/[^"]+)"',html):assert client.get(url).status_code==200
 tile=client.get('/api/tiles/HiRISE/12/1627/5857.png');assert tile.status_code==200 and tile.content.startswith(b'\x89PNG')
 assert client.get('/api/tiles/HiRISE/18/1/1.png').status_code==422
 assert client.get('/api/tiles/CTX/14/1/1.png').status_code==422
def test_budget_speed_and_return():
 m=Mission();r=plan(m);assert r['geometry']['coordinates'][0]==r['geometry']['coordinates'][-1]
 assert r['surface_m']>=r['horizontal_m']>100
 slower=plan(m.model_copy(update={'speed_m_min':17.5}));assert slower['geometry']==r['geometry'];assert slower['travel_min']==pytest.approx(r['travel_min']*2)
 exact=plan(m.model_copy(update={'available_min':r['total_min']+m.reserve_min}));assert exact['feasible']
 bad=plan(m.model_copy(update={'available_min':r['total_min']+m.reserve_min-.01}));assert not bad['feasible']
def test_validation(client):
 for change in [{'sites':['BAD']},{'base':[1200,-500]},{'speed_m_min':0},{'required':['C']},{'base':[-1,0]}]:
  response=client.post('/api/routes/plan',json={**Mission().model_dump(),**change});assert response.status_code==422
 assert client.post('/api/routes/plan',json={**Mission().model_dump(),'max_slope':.01}).status_code==409
 e=client.post('/api/evas',json=Mission(elapsed_min=1400).model_dump()).json()
 assert client.post('/api/evas/'+e['id']+'/events',json={'kind':'delay','value':100}).status_code==422
 assert client.post('/api/evas/'+e['id']+'/observations',content='{"site":"A","note":"x","simulated_min":Infinity}',headers={'Content-Type':'application/json'}).status_code==422
def test_persistence_events_exports(client):
 e=client.post('/api/evas',json=Mission().model_dump()).json();id=e['id']
 assert client.get('/api/evas/'+id).json()['mission']==e['mission']
 assert client.post(f'/api/evas/{id}/observations',json={'site':'A','note':'strates — simulation','sample_id':'SIM-1'}).status_code==200
 assert len(client.get(f'/api/evas/{id}/observations').json())==1
 assert 'SIM-1' in client.get(f'/api/evas/{id}/report?format=csv').text
 assert client.get(f'/api/evas/{id}/report').json()['sources']
 slowed=client.post(f'/api/evas/{id}/events',json={'kind':'slow'}).json();assert slowed['route']['travel_min']>e['route']['travel_min']
 delayed=client.post(f'/api/evas/{id}/events',json={'kind':'delay','value':5}).json();assert delayed['route']['total_min']==pytest.approx(slowed['route']['total_min']+5)
 blocked=client.post(f'/api/evas/{id}/events',json={'kind':'block','point':e['route']['geometry']['coordinates'][0]}).json();assert blocked['route'] is None and blocked['route_error']
 assert len(client.get('/api/evas').json())==1
 assert client.delete('/api/evas/'+id).status_code==200
 assert client.get('/api/evas/'+id).status_code==404
def test_opportunity_compare_return(client):
 m=Mission().model_dump();ops=client.post('/api/science/opportunities',json=m).json();assert ops[0]['site']=='C';assert ops[0]['extra_min']>10
 variants=client.post('/api/routes/compare',json=m).json();assert variants
 serialized=[json.dumps(v['geometry']) for v in variants];assert len(set(serialized))==len(serialized)
 assert all('A' in v['parameters']['sites'] for v in variants)
 result=client.post('/api/routes/return',json={'mission':m,'position':[694,-387],'elapsed_min':20}).json();assert result['return_min']>0
