import io,json,math,sqlite3
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from backend import app as service
from backend.engine import Terrain,NoRoute,walking_factor

@pytest.fixture
def client(tmp_path,monkeypatch):
 monkeypatch.setattr(service,'DB',str(tmp_path/'v2.sqlite'));return TestClient(service.app)

def request():return {'base':{'x':620,'y':-450},'destination_site_id':'C','via_site_ids':[],'scenario':{'duration_min':120,'reserve_min':20,'observation_min':10,'nominal_speed_m_s':35/60,'max_slope_deg':30,'is_simulated':True},'criteria':['distance','estimated_time','slope_cost']}

def test_pack_contract_and_reproducibility(client):
 sites=client.get('/api/v1/sites').json();assert [s['id'] for s in sites]==['A','B','C'];assert sites[0]['position']['x']==pytest.approx(694.09304059)
 first=client.post('/api/v1/routes/compare',json=request());assert first.status_code==200;data=first.json();assert data['routes'] and data['model_version']==service.VERSION
 second=client.post('/api/v1/routes/compare',json=request()).json();assert [r['id'] for r in data['routes']]==[r['id'] for r in second['routes']]
 assert data['dataset_version']==service.DATA_VERSION
 explicit=request();explicit['via_site_ids']=['A'];explicit['ordered_site_ids']=['C','A'];ordered=client.post('/api/v1/routes/compare',json=explicit).json();assert ordered['routes'][0]['details']['parameters']['sites']==['C','A']
 for r in data['routes']:
  details=r['details'];coords=details['geometry']['coordinates'];z=details['elevations_m'];distance=sum(math.hypot(math.dist(a,b),zz-z0) for a,b,z0,zz in zip(coords,coords[1:],z,z[1:]))
  assert distance==pytest.approx(r['metrics']['distance_roundtrip_m'])
  assert coords[0]==coords[-1];assert max(math.dist(a,b) for a,b in zip(coords,coords[1:]))<=math.sqrt(2)+1e-6
  assert details['outbound_m']+details['return_m']==pytest.approx(distance)
  expected=sum(math.hypot(math.dist(a,b),zz-z0)*float(walking_factor(zz-z0,math.dist(a,b))) for a,b,z0,zz in zip(coords,coords[1:],z,z[1:]))/35
  assert expected==pytest.approx(details['travel_min'])
 bad=request();bad['destination_site_id']='unknown';assert client.post('/api/v1/routes/compare',json=bad).status_code==404
 bad=request();bad['scenario']['max_slope_deg']=.001;response=client.post('/api/v1/routes/compare',json=bad).json();assert response['routes']==[] and response['no_route_reason']
 bad=request();bad['scenario']['reserve_min']=120;assert client.post('/api/v1/routes/compare',json=bad).status_code==422

def test_mission_signatures_ignore_json_key_order():
 import subprocess,shutil
 from pathlib import Path
 root=Path(__file__).resolve().parents[1]
 script="import {canonical} from './frontend/client.ts';let a={base:[620,-450],criterion:'distance',observation_overrides:{B:12,A:5}},b={observation_overrides:{A:5,B:12},criterion:'distance',base:[620,-450]};if(canonical(a)!==canonical(b))process.exit(1);b.observation_overrides.A=7;if(canonical(a)===canonical(b))process.exit(2);"
 subprocess.run([shutil.which('node'),'--experimental-strip-types','--input-type=module','-e',script],cwd=root,check=True,capture_output=True)

def test_native_edges_cannot_skip_spike_or_nodata():
 for value in [50,np.nan]:
  native=np.zeros((10,10));native[2,4]=value
  terrain=Terrain(np.zeros((2,2)),5,np.zeros((2,2)),np.ones((2,2),dtype=bool),native,np.zeros((10,10)))
  with pytest.raises(NoRoute):terrain.path((2.5,-2.5),(7.5,-2.5),blocked=[(2.5,-7.5),(7.5,-7.5)])

def test_english_presentation_preserves_user_notes(client):
 sites=client.get('/api/v1/sites').json()
 assert sites[0]['roche']=='Fine- to medium-grained sandstone'
 assert 'Published coordinate' in sites[0]['marker_status']
 assert 'Enhanced colour' in sites[0]['image_metadata']['processing']
 mission=service.Mission(name='Delta de Jezero · mission Amalik',sites=['C'],required=['C'],available_min=120)
 saved=client.post('/api/v1/missions',json=mission.model_dump()).json();id=saved['id']
 text='Ma note personnelle reste exactement comme saisie.'
 client.post(f'/api/v1/missions/{id}/observations',json={'position':[600,-650],'note':text})
 loaded=client.get(f'/api/v1/missions/{id}').json()
 assert loaded['mission']['name']=='Jezero Delta · Amalik mission'
 assert loaded['observations'][0]['note']==text
 assert client.post(f'/api/v1/missions/{id}/progress',json={'fraction':1}).json()['phase']=='completed'
 report=client.get(f'/api/v1/missions/{id}/report').json()
 assert report['observations'][0]['note']==text
 assert 'Historical rover' in client.get('/api/v1/environment/meda').json()['warning']

def test_native_sampling_history_meda(client):
 r=client.get('/api/v1/terrain/sample?x=100.5&y=-500.5').json();assert r['resolution_m']==1;assert r['elevation_m']==pytest.approx(float(service.NATIVE_Z[500,100]))
 history=client.get('/api/v1/history').json();assert history['coordinate_system']=='MARS_LOCAL_METERS_NOT_RFC7946';assert history['features'][0]['properties']['nature'].startswith('Historical reference')
 meda=client.get('/api/v1/environment/meda').json();assert meda['unit']=='Pa' and meda['sol']==29;assert meda['valid_rows']>1000;assert meda['min_pa']<meda['max_pa'];assert meda['start_utc'].startswith('2021-03-19');assert all(s['pressure_pa']>0 for s in meda['samples'])

def test_observation_photo_reset_and_budget_guard(client):
 mission=service.Mission(sites=['C'],required=['C'],available_min=120);eva=client.post('/api/v1/missions',json=mission.model_dump()).json();id=eva['id']
 result=client.post(f'/api/v1/missions/{id}/observations',json={'position':[600,-650],'note':'Une question de terrain','category':'géologie'}).json();note=result['observations'][-1];assert note['validation_status']=='user_unverified' and note['created_at']
 summary=client.get('/api/v1/missions').json()[0];assert summary['observation_count']==1 and 'route' not in summary and 'observations' not in summary
 buf=io.BytesIO();Image.new('RGB',(8,8),(20,40,60)).save(buf,'PNG')
 photo=client.put(f"/api/v1/missions/{id}/observations/{note['id']}/photo",content=buf.getvalue(),headers={'Content-Type':'image/png','Content-Disposition':'filename="../../escape.png"'});assert photo.status_code==200
 path=photo.json()['image'];assert path.startswith('/runtime/uploads/') and '..' not in path;assert client.get(path).status_code==200
 assert client.put(f"/api/v1/missions/{id}/observations/{note['id']}/photo",content=b'not an image').status_code==422
 assert client.put(f"/api/v1/missions/{id}/observations/{note['id']}/photo",content=b'x'*5_000_001).status_code==413
 client.post(f'/api/v1/missions/{id}/progress',json={'fraction':.3})
 reset=client.post(f'/api/v1/missions/{id}/reset',json={}).json();assert len(reset['observations'])==1 and reset['mission']['elapsed_min']==0
 csv=client.get(f'/api/v1/missions/{id}/report?format=csv').text;assert 'x_local_m' in csv and 'user_unverified' in csv
 poor=client.post('/api/v1/missions',json=mission.model_copy(update={'available_min':1}).model_dump()).json();assert not poor['route']['feasible']
 assert client.post('/api/v1/missions/'+poor['id']+'/progress',json={'fraction':.01}).status_code==409
 with service.db() as connection:assert connection.execute('PRAGMA foreign_keys').fetchone()[0]==1;assert connection.execute('PRAGMA user_version').fetchone()[0]==2
