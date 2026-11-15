import csv, io, itertools, json, os, sqlite3, uuid,hashlib,datetime,time
from functools import lru_cache
from pathlib import Path
import numpy as np
import rasterio
import httpx,xml.etree.ElementTree as ET
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, FileResponse,JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict, field_validator
from .engine import Terrain, NoRoute, VERSION
from .simulation import state_at
from .presentation import present_document
from .settings import ROOT,PACK as P,RUNTIME as RUN,DATABASE
DATA_VERSION=hashlib.sha256((P/'terrain/relief_delta.tif').read_bytes()).hexdigest()[:16]
app=FastAPI(title='MarsWalk — Jezero HydroExplorer',version=VERSION)
@app.exception_handler(RequestValidationError)
async def validation_error(request,exc):
    # Do not echo non-finite input values into an otherwise valid JSON error body.
    return JSONResponse(status_code=422,content={'detail':[{'loc':e['loc'],'msg':e['msg'],'type':e['type']} for e in exc.errors()]})
DB=str(DATABASE)
def prepare_science_copy():
    """Immutable release -> separate working scientific copy. Missions remain in their existing DB."""
    target=RUN/'science-working.sqlite'
    if not target.exists():
        with sqlite3.connect((P/'backend/marswalk.sqlite').as_uri()+'?mode=ro',uri=True) as source,sqlite3.connect(target) as destination:source.backup(destination)
prepare_science_copy()
def db():
    c=sqlite3.connect(DB)
    c.execute('PRAGMA foreign_keys=ON')
    if c.execute('PRAGMA user_version').fetchone()[0]==0:
        c.executescript((ROOT/'backend/schema.sql').read_text(encoding='utf-8'))
    if c.execute('PRAGMA user_version').fetchone()[0]<2:
        c.executescript((ROOT/'backend/migrations/002.sql').read_text(encoding='utf-8'))
    return c
SITES=json.loads((P/'frontend/sites.json').read_text(encoding='utf-8'))
SITE_EN=json.loads((ROOT/'config/sites.en.json').read_text(encoding='utf-8'))
IMAGE_METADATA=json.loads((ROOT/'config/site-image-metadata.json').read_text(encoding='utf-8'))
for s in SITES:
    s.update(SITE_EN[s['id']])
    s.update(observation_min=10,science_criteria={'eau_ancienne':2,'preuves':2,'nouveaute':1},diversity_category=s['roche'],
             marker_status='Published coordinate; 5 m routing cell selected for simulation. Absolute positional accuracy is not established.',
             image_metadata=IMAGE_METADATA[s['id']],image=f"/data/science/images/{Path(s['image']).name}")
BYID={s['id']:s for s in SITES}
data=np.load(RUN/'terrain.npz')
with rasterio.open(P/'terrain/relief_delta.tif') as native:
    NATIVE_Z=native.read(1,masked=True).filled(np.nan)
gy,gx=np.gradient(NATIVE_Z);NATIVE_SLOPE=np.degrees(np.arctan(np.hypot(gx,gy)));del gx,gy
TERRAIN=Terrain(data['z'],5,data['slope'],data['valid'],NATIVE_Z,NATIVE_SLOPE)
class ApiModel(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
class Mission(ApiModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    name:str=Field(default='Western delta — simulated EVA',min_length=1,max_length=120)
    base:tuple[float,float]=(620,-450)
    sites:list[str]=Field(default_factory=lambda:['A','B'],max_length=3)
    required:list[str]=Field(default_factory=lambda:['A'],max_length=3)
    available_min:float=Field(default=90,gt=0,le=1440)
    reserve_min:float=Field(default=15,ge=0,le=240)
    speed_m_min:float=Field(default=35,gt=0,le=300)
    observation_min:float=Field(default=10,ge=0,le=240)
    max_slope:float=Field(default=30,gt=0,le=60)
    slope_weight:float=Field(default=2,ge=0,le=20)
    blocked:list[tuple[float,float]]=Field(default_factory=list,max_length=100)
    elapsed_min:float=Field(default=0,ge=0,le=1440)
    start:tuple[float,float]|None=None
    completed_sites:list[str]=Field(default_factory=list,max_length=3)
    observation_overrides:dict[str,float]=Field(default_factory=dict)
    criterion:str=Field(default='slope_cost',pattern='^(distance|estimated_time|slope_cost)$')
    visibility_factor:float=Field(default=1,ge=.2,le=1)
    @field_validator('sites','required','completed_sites')
    @classmethod
    def ids(cls,v):
        if len(set(v))!=len(v) or any(x not in BYID for x in v): raise ValueError('Unknown or duplicate sites')
        return v
    @field_validator('base')
    @classmethod
    def base_valid(cls,v): TERRAIN.cell(v); return v
    @field_validator('blocked')
    @classmethod
    def blocked_valid(cls,v):
        for p in v:TERRAIN.cell(p)
        return v
    @field_validator('start')
    @classmethod
    def start_valid(cls,v):
        if v is not None:TERRAIN.cell(v)
        return v
    @field_validator('observation_overrides')
    @classmethod
    def stops_valid(cls,v):
        if any(k not in BYID or not 0<=t<=240 for k,t in v.items()):raise ValueError('Invalid per-site durations')
        return v

@lru_cache(maxsize=256)
def segment(a,b,max_slope,weight,blocked,criterion='slope_cost',data_version=DATA_VERSION):
    cells,n=TERRAIN.path(a,b,max_slope,weight,blocked,criterion)
    return tuple(cells),n

def science_score(subset):
    # Relevance per target; diversity counted once per lithology; evidence capped.
    return (sum(BYID[s]['science_criteria']['eau_ancienne'] for s in subset)
            + len({BYID[s]['roche'] for s in subset})
            + max((BYID[s]['science_criteria']['preuves'] for s in subset),default=0)
            + sum(BYID[s]['science_criteria']['nouveaute'] for s in subset))

def plan(m:Mission):
    started=time.perf_counter()
    if not set(m.required)<=set(m.sites): raise HTTPException(422,'Required sites must remain selected')
    if not set(m.completed_sites)<=set(m.sites):raise HTTPException(422,'Completed sites are outside the selected objectives')
    pending=[s for s in m.sites if s not in m.completed_sites]
    points=[m.start or m.base]+[(BYID[s]['x_local_m'],BYID[s]['y_local_m']) for s in pending]+[m.base]
    cells=[]; expanded=0; legs=[];leg_details=[];dense_count=0
    try:
        for index,(a,b) in enumerate(zip(points,points[1:])):
            part,n=segment(tuple(a),tuple(b),m.max_slope,m.slope_weight,tuple(tuple(p) for p in m.blocked),m.criterion)
            metric=TERRAIN.metrics(part)
            legs.append(metric['surface_m']); expanded+=n
            begin=max(0,dense_count-1)
            cells.extend(part if not cells else part[1:])
            dense_count+=len(metric['coordinates']) if dense_count==0 else len(metric['coordinates'])-1
            site=pending[index] if index<len(pending) else None
            leg_details.append(dict(start_index=begin,end_index=dense_count-1,surface_m=legs[-1],travel_min=metric['time_distance_m']/(m.speed_m_min*m.visibility_factor),target_site=site,observation_min=m.observation_overrides.get(site,m.observation_min) if site else 0))
    except NoRoute as e: raise HTTPException(409,str(e))
    out=TERRAIN.metrics(cells)
    travel=sum(l['travel_min'] for l in leg_details)
    obs=sum(l['observation_min'] for l in leg_details)
    total=travel+obs+m.elapsed_min
    out.update(type='Feature',geometry={'type':'LineString','coordinates':out.pop('coordinates')},
       coordinate_system='MARS_LOCAL_METERS_NOT_RFC7946',travel_min=travel,observation_min=obs,legs=leg_details,
       total_min=total,remaining_min=m.available_min-total,reserve_min=m.reserve_min,
       feasible=total+m.reserve_min<=m.available_min,return_min=leg_details[-1]['travel_min'],outbound_m=sum(legs[:-1]),return_m=legs[-1],margin_min=m.available_min-total-m.reserve_min,
       dataset_version=DATA_VERSION,calculation_ms=(time.perf_counter()-started)*1000,criterion=m.criterion,
       model=VERSION,parameters=m.model_dump(),expanded_nodes=expanded,coverage='Valid DEM only; unknown sub-grid hazards',
       uncertainty='DEM accuracy unquantified; geology offset 100–200 m; not operational navigation')
    return out

@app.get('/api/health')
def health(): return {'status':'ok','mode':'SIMULATION','model':VERSION,'real_dem':True}
@app.get('/api/roi')
def roi(): return json.loads((ROOT/'config/roi.json').read_text(encoding='utf-8'))
@app.get('/api/science-sites')
def sites(): return SITES
@app.get('/api/datasets')
def datasets(): return json.loads((RUN/'datasets.json').read_text(encoding='utf-8'))
@app.get('/api/layers')
def layers(): return [{'id':x,'status':'VERIFIED_USED','url':f'/runtime/{x}.png'} for x in ['HiRISE','CTX','slope']]+[{'id':'geology','status':'VERIFIED_USED','warning':'Unregistered; possible 100–200 m offset'},{'id':'CRISM','status':'VERIFIED_NOT_USED','warning':'No valid CRISM class pixels integrated in the area'}]
@app.get('/api/geology')
def geology(): return json.loads((RUN/'geology.json').read_text(encoding='utf-8'))
@app.get('/api/models')
def models(): return {'version':VERSION,'dataset_version':DATA_VERSION,'distance':'Local Mars metres, R3396190 m, lat_ts18.4663°','cost':{'distance':'native surface length','estimated_time':'sum(native surface*(1+3*abs(grade)+2*max(grade,0)))','slope_cost':'horizontal*(1+w*(max local slope/30)^2)'},'slope':'atan(dz/d); native directional and local slope separate','duration':'sum(native surface*(1+3*abs(grade)+2*max(grade,0))/(nominal speed*visibility)) + observations + elapsed','grid':'Conservative 5 m graph; every edge and profile checked at native 1 m; diagonal corners forbidden','limits':'Experimental assumptions, not validated human walking or safety'}
@app.get('/api/terrain/sample')
def sample(x:float,y:float):
    try:r,c=TERRAIN.cell((x,y))
    except (NoRoute,ValueError,OverflowError):raise HTTPException(422,'Point outside DEM coverage')
    if not TERRAIN.valid[r,c]:return {'valid':False,'warning':'NoData; traversal prohibited'}
    nr,nc=int(-y),int(x)
    return {'valid':True,'elevation_m':float(NATIVE_Z[nr,nc]),'max_native_slope_deg':float(NATIVE_SLOPE[nr,nc]),'support_m':1,'source':'PLACES DEM native pixel','accuracy':'unknown; not a ground hazard measurement'}
@app.get('/api/tiles/{instrument}/{z}/{row}/{col}.png')
def wmts_tile(instrument:str,z:int,row:int,col:int):
    if instrument not in ('HiRISE','CTX') or not 0<=z<=(17 if instrument=='HiRISE' else 13):raise HTTPException(422,'WMTS layer or level unavailable')
    if not 0<=row<2**z or not 0<=col<2**(z+1):raise HTTPException(422,'Invalid tile index')
    existing=P/f'imagery/mars_trek/tuiles/{instrument}/{z}/{row}/{col}.png'
    cached=RUN/f'tiles/{instrument}/{z}/{row}/{col}.png'
    for path in (existing,cached):
        if path.exists():return FileResponse(path,media_type='image/png')
    ns={'w':'http://www.opengis.net/wmts/1.0','o':'http://www.opengis.net/ows/1.1'}
    tree=ET.parse(P/f'imagery/mars_trek/{instrument}_WMTSCapabilities.xml')
    template=tree.find('.//w:ResourceURL',ns).attrib['template']
    style=tree.find('.//w:Style/o:Identifier',ns).text;matrix=tree.find('.//w:TileMatrixSet/o:Identifier',ns).text
    url=template.replace('{Style}',style).replace('{TileMatrixSet}',matrix).replace('{TileMatrix}',str(z)).replace('{TileRow}',str(row)).replace('{TileCol}',str(col))
    try:
        response=httpx.get(url,timeout=20,follow_redirects=True)
        if response.status_code==404:raise HTTPException(404,'Tile outside available coverage')
        if response.status_code not in (200,206) or not response.content.startswith(b'\x89PNG\r\n\x1a\n') or len(response.content)>2_000_000:raise HTTPException(502,'Invalid WMTS response')
    except httpx.HTTPError as e:raise HTTPException(503,'WMTS unavailable; no cached tile: '+str(e))
    cached.parent.mkdir(parents=True,exist_ok=True)
    temporary=cached.with_name(str(uuid.uuid4())+'.part');temporary.write_bytes(response.content);temporary.replace(cached)
    return Response(response.content,media_type='image/png',headers={'Cache-Control':'public, max-age=86400'})
@app.post('/api/routes/plan')
def route(m:Mission): return plan(m)
@app.post('/api/routes/compare')
def compare(m:Mission):
    results=[]
    for label,criterion,w in [('Shortest distance','distance',0),('Shortest estimated walking time','estimated_time',0),('Reduced slope cost','slope_cost',max(8,m.slope_weight))]:
        try: r=plan(m.model_copy(update={'slope_weight':w,'criterion':criterion}))
        except HTTPException: continue
        if not any(r['geometry']==a['geometry'] for a in results): r['label']=label;results.append(r)
    return results
@app.post('/api/science/optimize')
def optimize(m:Mission):
    best=None
    for count in range(len(m.required),4):
        for subset in itertools.combinations(BYID,count):
            if not set(m.required)<=set(subset): continue
            for order in itertools.permutations(subset):
                try: r=plan(m.model_copy(update={'sites':list(order)}))
                except HTTPException: continue
                score=science_score(subset)
                if r['feasible'] and (best is None or (score,-r['total_min'])>(best[0],-best[1]['total_min'])):best=(score,r)
    if not best:raise HTTPException(409,'No subset satisfies the objectives and time budget')
    best[1].update(label='Mission with scientific stops',subjective_science_score=best[0]);return best[1]
@app.post('/api/science/opportunities')
def opportunities(m:Mission):
    original=plan(m); out=[]
    for s in BYID:
        if s in m.sites:continue
        candidates=[]
        for i in range(len(m.sites)+1):
            order=m.sites[:i]+[s]+m.sites[i:]
            try: r=plan(m.model_copy(update={'sites':order}))
            except HTTPException:continue
            candidates.append(r)
        if candidates:
            r=min(candidates,key=lambda x:x['total_min'])
            from shapely.geometry import Point,LineString
            proximity=Point(BYID[s]['x_local_m'],BYID[s]['y_local_m']).distance(LineString(original['geometry']['coordinates']))
            out.append({'site':s,'order':r['parameters']['sites'],'extra_m':r['surface_m']-original['surface_m'],'extra_min':r['total_min']-original['total_min'],'extra_travel_min':r['travel_min']-original['travel_min'],'extra_observation_min':r['observation_min']-original['observation_min'],'proximity_m':proximity,'feasible':r['feasible'],'remaining_min':r['remaining_min'],'margin_min':r['margin_min']})
    return out
def fetch(id):
    with db() as c: row=c.execute('SELECT body FROM evas WHERE id=?',(id,)).fetchone()
    if not row: raise HTTPException(404,'Unknown EVA')
    body=json.loads(row[0])
    # Migrate development-era saved documents to the final route/timeline contract.
    changed=False
    if body.get('route') and ('legs' not in body['route'] or body['route'].get('model')!=VERSION or body['route'].get('dataset_version')!=DATA_VERSION):
        body.setdefault('route_history',[]).append(body['route'])
        m=Mission(**body['mission']);body['mission']=m.model_dump();body['route']=plan(m)
        if body.get('progress'):body['progress']=state_at(body['route'],body['mission'],body['progress']['fraction'])
        changed=True
    for note in body.get('observations',[]):
        if not note.get('id'):
            note['id']=str(uuid.uuid4());note['validation_status']='user_unverified';note['created_at']=None
            if note.get('site') in BYID:note['position']=[BYID[note['site']]['x_local_m'],BYID[note['site']]['y_local_m']]
            changed=True
    if changed:store(id,body)
    return present_document(body)
def store(id,body):
    with db() as c:c.execute('INSERT OR REPLACE INTO evas VALUES (?,?)',(id,json.dumps(body)))
    return body
@app.get('/api/evas')
def evas():
    with db() as c:return [json.loads(r[0]) for r in c.execute('SELECT body FROM evas')]
@app.post('/api/evas')
def create(m:Mission):
    r=plan(m);id=str(uuid.uuid4());return store(id,dict(id=id,mission=m.model_dump(),route=r,events=[],observations=[],route_history=[],travelled_before_m=0))
@app.get('/api/evas/{id}')
def get_eva(id:str):return fetch(id)
@app.put('/api/evas/{id}')
def update(id:str,m:Mission):
    body=fetch(id);state=body.get('progress')
    if state:
        m.start=tuple(state['position']);m.elapsed_min=state['elapsed_min'];m.completed_sites=[s for s in state['completed_sites'] if s in m.sites]
        if state['phase']=='observation' and state['next_site'] in m.sites:m.observation_overrides[state['next_site']]=state['remaining_observation_min']
    r=plan(m)
    if state:
        body['travelled_before_m']=body.get('travelled_before_m',0)+body['route']['surface_m']-state['remaining_distance_m']
        body.pop('progress',None)
    if body.get('route')!=r:body.setdefault('route_history',[]).append(body.get('route'))
    body.update(mission=m.model_dump(),route=r);return store(id,body)
@app.delete('/api/evas/{id}')
def delete(id:str):
    fetch(id)
    with db() as c:c.execute('DELETE FROM evas WHERE id=?',(id,))
    return {'deleted':id}
class Event(ApiModel):
    kind:str
    value:float=Field(default=5,ge=0,le=1440)
    point:tuple[float,float]|None=None
@app.post('/api/evas/{id}/events')
def event(id:str,e:Event):
    body=fetch(id);m=Mission(**body['mission'])
    progress=body.get('progress')
    if progress:
        m.start=tuple(progress['position']);m.elapsed_min=progress['elapsed_min'];m.completed_sites=progress['completed_sites']
        if progress['phase']=='observation':m.observation_overrides[progress['next_site']]=progress['remaining_observation_min']
        body['travelled_before_m']=body.get('travelled_before_m',0)+body['route']['surface_m']-progress['remaining_distance_m']
    if e.kind=='slow': m.speed_m_min=max(.1,m.speed_m_min*.7)
    elif e.kind=='return':m.required=[];m.sites=list(m.completed_sites)
    elif e.kind=='delay':m.elapsed_min+=e.value
    elif e.kind=='block' and e.point is not None:m.blocked.append(e.point)
    else:raise HTTPException(422,'Unknown event')
    try:validated=Mission(**m.model_dump())
    except ValueError as error:raise HTTPException(422,str(error))
    body['mission']=validated.model_dump();body['events'].append(dict(simulation=True,**e.model_dump()))
    body.pop('progress',None)
    body.setdefault('route_history',[]).append(body.get('route'))
    try:body['route']=plan(m);body.pop('route_error',None)
    except HTTPException as error:body['route']=None;body['route_error']=error.detail
    return store(id,body)
class Progress(ApiModel):
    fraction:float=Field(ge=0,le=1)
@app.post('/api/evas/{id}/progress')
def progress(id:str,p:Progress):
    body=fetch(id)
    if body['route'] is None:raise HTTPException(409,'Progress requires a calculated route')
    if p.fraction>0 and not body.get('simulation_started') and not body['route']['feasible']:raise HTTPException(409,'Mission exceeds the time budget and reserve: launch blocked')
    if p.fraction>0:body['simulation_started']=True
    state=state_at(body['route'],body['mission'],p.fraction)
    m=Mission(**body['mission'])
    try:
        cells,_=segment(tuple(state['position']),tuple(m.base),m.max_slope,m.slope_weight,tuple(tuple(v) for v in m.blocked),m.criterion)
        state['immediate_return_min']=TERRAIN.metrics(cells)['time_distance_m']/(m.speed_m_min*m.visibility_factor)
        state['return_reserve_min']=m.available_min-state['elapsed_min']-state['immediate_return_min']
    except NoRoute:state['immediate_return_min']=None;state['return_reserve_min']=None
    body['progress']=state;store(id,body)
    return state
@app.post('/api/evas/{id}/reset')
def reset(id:str):
    body=fetch(id);m=Mission(**body['mission']);m.start=None;m.elapsed_min=0;m.completed_sites=[];m.observation_overrides={}
    body.setdefault('route_history',[]).append(body.get('route'));body['route']=plan(m);body['mission']=m.model_dump();body.pop('progress',None);body['simulation_started']=False;body['travelled_before_m']=0
    body.setdefault('events',[]).append({'kind':'reset_playback','simulation':True,'observations_retained':True});return store(id,body)
class Observation(ApiModel):
    site:str|None=None
    note:str=Field(min_length=1,max_length=4000)
    category:str='geology'
    status:str='observed (simulation)'
    simulated_min:float=Field(default=0,ge=0,le=1440)
    image:str|None=None
    sample_id:str|None=None
    position:tuple[float,float]|None=None
    created_at:str|None=None
    validation_status:str='user_unverified'
class ProgressRequest(ApiModel):
    mission:Mission
    position:tuple[float,float]
    elapsed_min:float=Field(default=0,ge=0,le=1440)
@app.post('/api/routes/return')
def immediate_return(p:ProgressRequest):
    m=p.mission
    try: cells,n=segment(tuple(p.position),tuple(m.base),m.max_slope,m.slope_weight,tuple(tuple(p) for p in m.blocked),m.criterion)
    except NoRoute as e:raise HTTPException(409,str(e))
    r=TERRAIN.metrics(cells);r['return_min']=r['time_distance_m']/(m.speed_m_min*m.visibility_factor)
    r['remaining_after_return_min']=m.available_min-p.elapsed_min-r['return_min']
    r['reserve_satisfied']=r['remaining_after_return_min']>=m.reserve_min
    return r
@app.post('/api/evas/{id}/observations')
def observe(id:str,o:Observation):
    if o.site is not None and o.site not in BYID:raise HTTPException(422,'Unknown site')
    if o.position is None:
        if o.site is None:raise HTTPException(422,'A site or position is required')
        o.position=(BYID[o.site]['x_local_m'],BYID[o.site]['y_local_m'])
    try:TERRAIN.cell(o.position)
    except NoRoute as error:raise HTTPException(422,str(error))
    o.created_at=datetime.datetime.now(datetime.timezone.utc).isoformat();o.validation_status='user_unverified'
    body=fetch(id);record=o.model_dump();record['id']=str(uuid.uuid4());body['observations'].append(record);return store(id,body)
@app.get('/api/evas/{id}/observations')
def observations(id:str):return fetch(id)['observations']
@app.get('/api/evas/{id}/report')
def report(id:str,format:str='json'):
    body=fetch(id);body['sources']=[s['source'] for s in SITES];body['simulation']=True
    p=body.get('progress');r=body.get('route')
    body['summary']=dict(completed_sites=p['completed_sites'] if p else body['mission'].get('completed_sites',[]),
        elapsed_min=p['elapsed_min'] if p else body['mission']['elapsed_min'],
        travelled_m=body.get('travelled_before_m',0)+(r['surface_m']-p['remaining_distance_m'] if p and r else 0),
        reserve_after_plan_min=r['remaining_min'] if r else None,model=VERSION,observations=len(body['observations']))
    body['dataset_sources']=datasets()
    if format=='csv':
        rows=[{**o,'x_local_m':o.get('position',[None,None])[0],'y_local_m':o.get('position',[None,None])[1],'coordinate_system':'Mars local metres; x east; y north; origin (4351286,1094535) projected m'} for o in body['observations']]
        buf=io.StringIO();writer=csv.DictWriter(buf,fieldnames=['id',*Observation.model_fields,'x_local_m','y_local_m','coordinate_system'],extrasaction='ignore');writer.writeheader();writer.writerows(rows)
        return Response(buf.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename=observations.csv'})
    return body
@app.put('/api/evas/{id}/observations/{observation_id}/photo')
async def observation_photo(id:str,observation_id:str,request:__import__('fastapi').Request):
    body=fetch(id);note=next((o for o in body['observations'] if o.get('id')==observation_id),None)
    if not note:raise HTTPException(404,'Unknown observation')
    content=bytearray()
    async for chunk in request.stream():
        content.extend(chunk)
        if len(content)>5_000_000:raise HTTPException(413,'Photo limited to 5 MB')
    from PIL import Image,UnidentifiedImageError
    try:
        with Image.open(io.BytesIO(content)) as im:
            if im.format not in ('JPEG','PNG','WEBP') or im.width*im.height>20_000_000:raise ValueError('Unsupported image format or dimensions')
            im.load();im=im.convert('RGB');folder=RUN/'uploads';folder.mkdir(exist_ok=True)
            name=uuid.uuid4().hex+'.jpg';im.save(folder/name,'JPEG',quality=88)
    except (UnidentifiedImageError,ValueError,OSError,Image.DecompressionBombError) as error:raise HTTPException(422,'Invalid photo: '+str(error))
    note['image']='/runtime/uploads/'+name;store(id,body);return note
@app.get('/api/terrain/display')
def terrain_display():return FileResponse(P/'frontend/terrain_grid.json',media_type='application/json')
from .v1 import install
import sys
install(app,sys.modules[__name__])
app.mount('/runtime',StaticFiles(directory=RUN),name='runtime')
app.mount('/data',StaticFiles(directory=P),name='data')
app.mount('/',StaticFiles(directory=ROOT/'frontend/dist',html=True),name='frontend')
