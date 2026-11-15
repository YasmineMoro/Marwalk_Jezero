"""Jury scenario replayed against the actual local HTTP server."""
import sys,json,time,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.deps'))
import httpx
def main():
 with httpx.Client(base_url=os.environ.get('MARSWALK_URL','http://127.0.0.1:8000/api/v1/'),timeout=60) as client:
  def post(path,data):
   response=client.post(path,json=data);response.raise_for_status();return response.json()
  m=dict(name='MarsWalk team demonstration — Amalik',base=[620,-450],sites=['C'],required=['C'],available_min=120,reserve_min=20,speed_m_min=35,observation_min=10,max_slope=30,slope_weight=8,blocked=[],elapsed_min=0,criterion='estimated_time',visibility_factor=1,start=None,completed_sites=[],observation_overrides={})
  def compare():return post('routes/compare',dict(base={'x':620,'y':-450},destination_site_id='C',via_site_ids=[s for s in m['sites'] if s!='C'],ordered_site_ids=m['sites'],scenario=dict(duration_min=120,reserve_min=20,observation_min=10,nominal_speed_m_s=35/60,max_slope_deg=30,is_simulated=True),criteria=['distance','estimated_time','slope_cost'],slope_weight=8,visibility_factor=1,blocked=[]))
  timings=[]
  for i in range(3):
   start=time.perf_counter();compared=compare();timings.append((time.perf_counter()-start)*1000)
  assert compared['routes']
  opportunity=next(o for o in post('science/opportunities',m) if o['site']=='A');assert opportunity['feasible']
  m['sites']=opportunity['order'];with_stop=compare();chosen=next((r['details'] for r in with_stop['routes'] if 'estimated_time' in r['criteria']),with_stop['routes'][0]['details'])
  eva=post('missions',m);id=eva['id'];assert eva['route']['geometry']==chosen['geometry'];assert abs(eva['route']['total_min']-chosen['total_min'])<1e-8
  note=post(f'missions/{id}/observations',dict(position=[600,-650],note='Question about layering: unverified user observation at a manually selected point.',category='geology',simulated_min=0));assert note['observations'][-1]['position']==[600,-650]
  mid=post(f'missions/{id}/progress',dict(fraction=.2))
  slow=post(f'missions/{id}/events',dict(kind='slow'));assert slow['mission']['start'] is not None and slow['route'] is not None
  delayed=post(f'missions/{id}/events',dict(kind='delay',value=5));assert abs(delayed['route']['total_min']-slow['route']['total_min']-5)<1e-7
  point=delayed['route']['geometry']['coordinates'][len(delayed['route']['geometry']['coordinates'])//3]
  blocked=post(f'missions/{id}/events',dict(kind='block',point=point));adaptation='recalculated with a blocked cell'
  if blocked['route'] is None:
   adaptation='no path explicitly reported; simulated blockage explicitly lifted to continue the demonstration'
   updated=client.put(f'missions/{id}',json={**blocked['mission'],'blocked':[]});updated.raise_for_status();blocked=updated.json()
  final=post(f'missions/{id}/progress',dict(fraction=1));assert set(final['completed_sites'])=={'A','C'} and final['remaining_distance_m']==0
  report=client.get(f'missions/{id}/report');report.raise_for_status()
  (ROOT/'docs/demo-report.json').write_text(json.dumps(report.json(),indent=2,ensure_ascii=False),encoding='utf-8')
  (ROOT/'docs/demo-observations.csv').write_text(client.get(f'missions/{id}/report?format=csv').text,encoding='utf-8')
  result=dict(eva_id=id,model=compared['model_version'],dataset=compared['dataset_version'],compare_http_ms=timings,initial_routes=[dict(criteria=r['criteria'],distance_m=r['details']['surface_m'],travel_min=r['details']['travel_min'],total_min=r['details']['total_min'],margin_min=r['details']['margin_min'],calculation_ms=r['details']['calculation_ms']) for r in compared['routes']],opportunity=opportunity,with_stop=dict(sites=m['sites'],distance_m=chosen['surface_m'],total_min=chosen['total_min'],margin_min=chosen['margin_min']),progress_before_event=mid,adaptation=adaptation,final=final)
  (ROOT/'docs/demo-results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8');print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
