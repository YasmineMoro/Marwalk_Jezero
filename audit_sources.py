"""Bounded public-source verification. No fabricated success, preserve failures."""
import sys,json,hashlib,datetime,concurrent.futures,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.deps'))
import httpx
P=ROOT/'data/MarsWalk_Data_Release'
urls={
 'USGS SIM3464':'https://pubs.usgs.gov/sim/3464/',
 'CTX DEM catalog':'https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic',
 'HiRISE DTM catalog':'https://www.uahirise.org/dtm/ESP_045994_1985',
 'CRISM rim catalog':'https://zenodo.org/records/22257754',
 'CRISM PDS':'https://pds-geosciences.wustl.edu/missions/mro/crism.htm',
 'PLACES DEM label':'https://pds-geosciences.wustl.edu/m2020/urn-nasa-pds-mars2020_rover_places/data_maps/m20_orbital_dem.xml',
 'Surface PDS report':'https://pds-geosciences.wustl.edu/missions/mars2020/Mars%202020%20Initial%20Reports%20Volume%202%20Release%202.pdf',
 'Murray DEM catalog':'https://murray-lab.caltech.edu/Mars2020/index.html'}
ns={'w':'http://www.opengis.net/wmts/1.0','o':'http://www.opengis.net/ows/1.1'}
for name in ['HiRISE','CTX']:
 tree=ET.parse(P/f'imagery/mars_trek/{name}_WMTSCapabilities.xml')
 base=json.loads((P/f'imagery/mars_trek/{name}_services.json').read_text(encoding='utf-8'))['response']['docs'][0]['endPoint']
 urls[name+' capabilities']=base+'/1.0.0/WMTSCapabilities.xml'
 template=tree.find('.//w:ResourceURL',ns).attrib['template']
 style=tree.find('.//w:Style/o:Identifier',ns).text
 matrix=tree.find('.//w:TileMatrixSet/o:Identifier',ns).text
 urls[name+' tile']=template.replace('{Style}',style).replace('{TileMatrixSet}',matrix).replace('{TileMatrix}','12').replace('{TileRow}','1627').replace('{TileCol}','5857')
def check(item):
 name,url=item
 try:
  with httpx.Client(follow_redirects=True,timeout=25) as c:
   with c.stream('GET',url,headers={'Origin':'http://localhost:8000','Range':'bytes=0-65535'}) as r:
    data=b''
    for chunk in r.iter_bytes():
     data+=chunk
     if len(data)>=65536:break
    import re
    folder=ROOT/'runtime/source-checks';folder.mkdir(exist_ok=True)
    target=folder/(re.sub('[^a-zA-Z0-9]+','_',name)+'.sample')
    target.write_bytes(data)
    title=re.search(b'<title[^>]*>(.*?)</title>',data,re.I|re.S)
    return dict(name=name,url=url,retrieved=datetime.datetime.now(datetime.timezone.utc).isoformat(),http=r.status_code,content_type=r.headers.get('content-type'),size_header=r.headers.get('content-length'),cors=r.headers.get('access-control-allow-origin'),content_range=r.headers.get('content-range'),sample_sha256=hashlib.sha256(data).hexdigest(),sample_file=str(target.relative_to(ROOT)),page_title=title.group(1).decode('utf-8',errors='replace') if title else None)
 except Exception as e:return dict(name=name,url=url,error=str(e),status='UNAVAILABLE')
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(check,urls.items()))
 (ROOT/'runtime/network-audit.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
 for r in results: print(r['name'],r.get('http',r.get('error')))
