"""Read only the small core metadata archive linked by the verified Zenodo page."""
import sys,re,zipfile,json,hashlib
from pathlib import Path
from urllib.parse import urljoin
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.deps'))
import httpx
page=(ROOT/'runtime/source-checks/CRISM_rim_catalog.sample').read_text(encoding='utf-8')
links=re.findall(r'href="([^"]+jezero_rim_maps_v1_core.zip[^"]*)"',page)
if not links:raise SystemExit('No core archive link in verified page')
url=urljoin('https://zenodo.org',links[0].replace('&amp;','&'))
target=ROOT/'runtime/crism-core.zip'
if not target.exists():
 with httpx.Client(follow_redirects=True,timeout=30) as client:
  with client.stream('GET',url) as r:
   r.raise_for_status();data=b''
   for chunk in r.iter_bytes():
    data+=chunk
    if len(data)>4_000_000:raise RuntimeError('Metadata download exceeds 4 MB cap')
  target.write_bytes(data)
digest=hashlib.md5(target.read_bytes()).hexdigest()
if digest!='5d923ebaf76804a184b4a3a1911e5214':raise RuntimeError('Zenodo MD5 differs from verified record')
with zipfile.ZipFile(target) as z:
 inventory=[{'name':i.filename,'bytes':i.file_size} for i in z.infolist()]
 (ROOT/'runtime/crism-inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
 for i in z.infolist():
  if i.filename.lower().endswith(('.json','.md','.txt','.prj','.geojson')) and i.file_size<300000:
   path=ROOT/'runtime/crism-metadata'/Path(i.filename).name;path.parent.mkdir(exist_ok=True);path.write_bytes(z.read(i))
 import rasterio,numpy as np
 from rasterio.io import MemoryFile
 from rasterio.windows import from_bounds
 bbox=json.loads((ROOT/'config/roi.json').read_text(encoding='utf-8'))['extent_lonlat_mars']
 coverage=[]
 for name in z.namelist():
  if not name.endswith('.tif'):continue
  with MemoryFile(z.read(name)) as mem:
   with mem.open() as ds:
    values=ds.read(1,window=from_bounds(*bbox,transform=ds.transform))
    coverage.append(dict(file=name,roi_bounds=bbox,valid_pixels=int(np.count_nonzero(values)),values=np.unique(values).tolist(),crs=ds.crs.to_wkt(),nodata=ds.nodata,grid_degrees=ds.res,zip_md5=digest))
 (ROOT/'runtime/crism-coverage.json').write_text(json.dumps(coverage,indent=2),encoding='utf-8')
print(url);print(json.dumps(inventory,indent=2))
