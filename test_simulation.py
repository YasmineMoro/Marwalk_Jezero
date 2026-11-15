import pytest
from backend.app import Mission,plan
from backend.simulation import state_at
from fastapi.testclient import TestClient
from backend import app as module
def test_timeline_stops_and_return():
 m=Mission();r=plan(m);end=state_at(r,m.model_dump(),1)
 assert end['phase']=='completed';assert end['completed_sites']==['A','B'];assert end['remaining_distance_m']==pytest.approx(0)
 assert end['position']==r['geometry']['coordinates'][0]
 first=r['legs'][0];minute=first['travel_min']+2
 state=state_at(r,m.model_dump(),minute/r['total_min'])
 assert state['phase']=='observation' and state['next_site']=='A'
 assert state['remaining_observation_min']==pytest.approx(8)
 assert not state['completed_sites']
def test_persisted_progress_and_replan(tmp_path,monkeypatch):
 monkeypatch.setattr(module,'DB',str(tmp_path/'progress.sqlite'));client=TestClient(module.app)
 m=Mission();e=client.post('/api/evas',json=m.model_dump()).json();id=e['id'];r=e['route']
 time=r['legs'][0]['travel_min']+m.observation_min+1
 state=client.post(f'/api/evas/{id}/progress',json={'fraction':time/r['total_min']}).json()
 assert 'A' in state['completed_sites'];assert state['elapsed_min']==pytest.approx(time)
 assert client.get('/api/evas/'+id).json()['progress']==state
 changed=client.post(f'/api/evas/{id}/events',json={'kind':'delay','value':5}).json()
 assert changed['mission']['elapsed_min']==pytest.approx(time+5)
 assert 'A' in changed['mission']['completed_sites']
 assert changed['route']['observation_min']<=10
 assert changed['route']['geometry']['coordinates'][0]!=changed['route']['geometry']['coordinates'][-1]
 final=client.post(f'/api/evas/{id}/progress',json={'fraction':1}).json();assert final['phase']=='completed'
 report=client.get(f'/api/evas/{id}/report').json();assert report['summary']['completed_sites']==['A','B'];assert report['summary']['travelled_m']>100
