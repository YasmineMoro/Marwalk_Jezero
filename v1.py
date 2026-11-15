"""Versioned pack contract and adapters. Coordinates are local Mars metres."""
import hashlib,json
from .presentation import mission_name
from typing import Literal
from fastapi import HTTPException
from pydantic import BaseModel,ConfigDict,Field,model_validator
class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
class Point(Strict):
    x:float=Field(description='Local Mars metres east; projected origin x=4351286 m')
    y:float=Field(description='Local Mars metres north; projected origin y=1094535 m; not Earth WGS84')
class Scenario(Strict):
    duration_min:float=Field(gt=0,le=1440)
    reserve_min:float=Field(ge=0,le=240)
    observation_min:float=Field(ge=0,le=240)
    nominal_speed_m_s:float=Field(gt=0,le=5)
    max_slope_deg:float=Field(gt=0,le=60)
    is_simulated:Literal[True]=True
    @model_validator(mode='after')
    def reserve(self):
        if self.reserve_min>=self.duration_min:raise ValueError('Reserve must be less than available time')
        return self
class RouteRequest(Strict):
    base:Point
    destination_site_id:str
    via_site_ids:list[str]=Field(default_factory=list,max_length=2)
    scenario:Scenario
    criteria:list[Literal['distance','estimated_time','slope_cost']]=Field(min_length=1,max_length=3)
    slope_weight:float=Field(default=8,ge=0,le=20)
    visibility_factor:float=Field(default=1,ge=.2,le=1)
    blocked:list[tuple[float,float]]=Field(default_factory=list,max_length=100)
    ordered_site_ids:list[str]|None=Field(default=None,max_length=3)
class Metrics(Strict):
    distance_roundtrip_m:float
    travel_roundtrip_min:float
    observation_min:float
    remaining_after_reserve_min:float
class RouteEnvelope(Strict):
    id:str
    criteria:list[Literal['distance','estimated_time','slope_cost']]
    roundtrip_points:list[Point]=Field(description='Scientific local Mars metres, NOT GeoJSON RFC7946 terrestrial degrees')
    metrics:Metrics
    details:dict
class RouteResponse(Strict):
    routes:list[RouteEnvelope]
    no_route_reason:str|None=None
    dataset_version:str
    model_version:str
    warnings:list[str]
    assumptions:Scenario
class SiteResponse(BaseModel):
    model_config=ConfigDict(extra='allow')
    id:str
    name:str
    position:Point
    elevation_m:float|None
    source_url:str
    image_path:str
class TerrainSample(BaseModel):
    model_config=ConfigDict(extra='allow')
    position:Point
    elevation_m:float
    slope_deg:float|None
    dataset_id:str
    resolution_m:float
def install(app,service):
    @app.get('/api/v1/missions')
    def mission_summaries():
        with service.db() as connection:
            summaries=[]
            for row in connection.execute("SELECT id,json_extract(body,'$.mission'),json_array_length(json_extract(body,'$.observations')) FROM evas"):
                mission=json.loads(row[1]);mission['name']=mission_name(mission['name'])
                summaries.append({'id':row[0],'mission':mission,'observation_count':row[2]})
            return summaries
    @app.get('/api/v1/datasets')
    def datasets():return [dict(**d,title=d['id'],kind=d['format'],status=d['integration'],source=d['url_tested']) for d in service.datasets()]
    @app.get('/api/v1/sites',response_model=list[SiteResponse])
    def sites():return [dict(**s,name=s['nom'],position={'x':s['x_local_m'],'y':s['y_local_m']},elevation_m=s['altitude_DTM_m'],source_url=s['source'],image_path=s['image']) for s in service.SITES]
    @app.get('/api/v1/terrain/sample',response_model=TerrainSample)
    def sample(x:float,y:float):
        d=service.sample(x,y)
        if not d['valid']:raise HTTPException(422,'NoData: terrain is not admissible')
        return dict(**d,position={'x':x,'y':y},slope_deg=d.get('max_native_slope_deg'),dataset_id='PLACES DEM',resolution_m=1)
    @app.post('/api/v1/routes/compare',response_model=RouteResponse)
    def compare(request:RouteRequest):
        ids=request.via_site_ids+[request.destination_site_id]
        if request.ordered_site_ids is not None:
            if set(request.ordered_site_ids)!=set(ids):raise HTTPException(422,'Explicit order must match the destination and stops')
            ids=request.ordered_site_ids
        if len(set(ids))!=len(ids):raise HTTPException(422,'Duplicate stops')
        if any(s not in service.BYID for s in ids):raise HTTPException(404,'Unknown site')
        if len(set(request.criteria))!=len(request.criteria):raise HTTPException(422,'Duplicate criteria')
        s=request.scenario
        try:m=service.Mission(base=(request.base.x,request.base.y),sites=ids,required=[request.destination_site_id],available_min=s.duration_min,reserve_min=s.reserve_min,speed_m_min=s.nominal_speed_m_s*60,max_slope=s.max_slope_deg,observation_min=s.observation_min,slope_weight=request.slope_weight,visibility_factor=request.visibility_factor,blocked=request.blocked)
        except ValueError as error:raise HTTPException(422,str(error))
        routes=[];reason=None
        for criterion in request.criteria:
            try:r=service.plan(m.model_copy(update={'criterion':criterion}))
            except HTTPException as error:reason=error.detail;continue
            same=next((v for v in routes if v['details']['geometry']==r['geometry']),None)
            if same:same['criteria'].append(criterion);continue
            ident=hashlib.sha256(json.dumps([r['geometry'],r['parameters'],service.DATA_VERSION],sort_keys=True).encode()).hexdigest()[:16]
            routes.append(dict(id=ident,criteria=[criterion],roundtrip_points=[{'x':p[0],'y':p[1]} for p in r['geometry']['coordinates']],metrics=dict(distance_roundtrip_m=r['surface_m'],travel_roundtrip_min=r['travel_min'],observation_min=r['observation_min'],remaining_after_reserve_min=r['margin_min']),details=r))
        return dict(routes=routes,no_route_reason=reason if not routes else None,dataset_version=service.DATA_VERSION,model_version=service.VERSION,warnings=['Experimental routing. Regional geology may be offset by 100–200 m and is excluded from routing costs.'],assumptions=s.model_dump())
    @app.get('/api/v1/environment/meda')
    def meda():
        from .environment import pressure_context
        return pressure_context(service.P)
    @app.get('/api/v1/history')
    def history():
        from pyproj import CRS,Transformer
        cfg=service.roi();crs=CRS.from_wkt(cfg['crs_wkt']);t=Transformer.from_crs(crs.geodetic_crs,crs,always_xy=True)
        geo=json.loads((service.P/'science/mission_original/trace_historique_MARS.geojson').read_text(encoding='utf-8'))
        for f in geo['features']:
            if 'nature' in f.get('properties',{}):f['properties']['nature']='Historical reference; not an algorithm-generated route'
            f['geometry']['coordinates']=[[t.transform(*p)[0]-cfg['origin_projected_m'][0],t.transform(*p)[1]-cfg['origin_projected_m'][1]] for p in f['geometry']['coordinates']]
        geo['coordinate_system']='MARS_LOCAL_METERS_NOT_RFC7946';return geo
    for route in list(app.routes):
        path=getattr(route,'path','')
        if path.startswith('/api/') and not path.startswith('/api/v1/'):
            target=path.replace('/api/evas','/api/v1/missions',1) if path.startswith('/api/evas') else path.replace('/api/','/api/v1/',1)
            if target in ['/api/v1/datasets','/api/v1/terrain/sample','/api/v1/routes/compare']:continue
            if target=='/api/v1/missions' and 'GET' in route.methods:continue
            app.add_api_route(target,route.endpoint,methods=list(route.methods),name='v1_'+route.name,response_model=route.response_model,openapi_extra=route.openapi_extra)
