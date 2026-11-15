import json,math,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import pytest
from pyproj import CRS,Transformer
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'data/MarsWalk_Data_Release'
def test_mars_projection_controls():
 cfg=json.loads((ROOT/'config/roi.json').read_text(encoding='utf-8'));crs=CRS.from_wkt(cfg['crs_wkt']);t=Transformer.from_crs(crs.geodetic_crs,crs,always_xy=True)
 for s in json.loads((P/'frontend/sites.json').read_text(encoding='utf-8')):
  x,y=t.transform(s['longitude'],s['latitude']);assert abs(x-cfg['origin_projected_m'][0]-s['x_local_m'])<.001;assert abs(y-cfg['origin_projected_m'][1]-s['y_local_m'])<.001
 x1,y1=t.transform(77.4,18.46);x2,y2=t.transform(77.4,18.461)
 assert abs((y2-y1)-3396190*math.pi/180*.001)<.001
def test_coverage_and_wmts():
 a=np.load(ROOT/'runtime/terrain.npz');assert a['valid'].all();assert a['z'].shape==(260,240)
 ns={'w':'http://www.opengis.net/wmts/1.0'}
 for name in ['HiRISE','CTX']:
  root=ET.parse(P/f'imagery/mars_trek/{name}_WMTSCapabilities.xml');assert root.find('.//w:ResourceURL',ns).attrib['template'].endswith('.png');assert len(root.findall('.//w:TileMatrix',ns))>10
def test_authoritative_geology_clip():
 import sqlite3
 from shapely.geometry import shape
 c=sqlite3.connect(P/'geology/usgs_original_MARS.gpkg')
 geo=json.loads((ROOT/'runtime/geology.json').read_text(encoding='utf-8'))
 for f in geo['features']:
  p=f['properties'];original=c.execute('SELECT name,symbol,ORIG_FID FROM GeoUnits_v1 WHERE fid=?',(p['fid'],)).fetchone()
  assert original==(p['name'],p['symbol'],p['ORIG_FID'])
  minx,miny,maxx,maxy=shape(f['geometry']).bounds
  assert minx>=-.001 and miny>=-1300.001 and maxx<=1200.001 and maxy<=.001
def test_north_south_display_contract():
 import subprocess,shutil
 from backend.coordinates import local_to_scene,scene_to_local,local_to_projected,projected_to_local
 p=(694.093,-387.448,-2520.185)
 assert scene_to_local(*local_to_scene(*p))==pytest.approx(p)
 assert projected_to_local(*local_to_projected(*p[:2]))==pytest.approx(p[:2])
 script="import {toScene,fromScene,toSvg} from './frontend/coordinates.ts';let p=[694.093,-387.448];console.log(JSON.stringify({scene:toScene(p,-2520.185),back:fromScene(...toScene(p,-2520.185)),north:toSvg([0,0]),south:toSvg([0,-1300])}));"
 result=subprocess.run([shutil.which('node'),'--experimental-strip-types','--input-type=module','-e',script],cwd=ROOT,capture_output=True,text=True,check=True)
 result=json.loads(result.stdout);assert result['back']==pytest.approx(p);assert result['scene']==pytest.approx(local_to_scene(*p));assert result['north']==[0,0] and result['south']==[0,1300]
