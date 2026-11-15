"""Idempotent offline preparation from the checksum-verified release."""
import sys, json, hashlib, shutil,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.deps'))
sys.path.insert(0,str(ROOT))
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from PIL import Image
from pyproj import CRS,Transformer
from shapely import from_wkb
from shapely.geometry import box,mapping
from shapely.ops import transform as transform_shape
from backend.settings import PACK as P,RUNTIME as OUT
OUT.mkdir(exist_ok=True)

def main():
    config=json.loads((P/'frontend/map_config.json').read_text(encoding='utf-8'))
    audit=[]
    with rasterio.open(P/'terrain/relief_delta.tif') as src:
        z=src.read(1,masked=True).filled(np.nan)
        assert src.res==(1.,1.) and z.shape==(1300,1200)
        # Conservative blocks: every native pixel must be valid; maximum native slope.
        gy,gx=np.gradient(z)
        slopes=np.degrees(np.arctan(np.hypot(gx,gy)))
        blocks=z.reshape(260,5,240,5)
        valid=np.isfinite(blocks).all(axis=(1,3))
        coarse=blocks.mean(axis=(1,3))
        maxs=slopes.reshape(260,5,240,5).max(axis=(1,3))
        np.savez_compressed(OUT/'terrain.npz',z=coarse,slope=maxs,valid=valid)
        target_transform=src.transform
        target_crs=src.crs
        for name in ['HiRISE','CTX']:
            with rasterio.open(P/f'imagery/mars_trek/{name}_extrait_MARS.tif') as im:
                dest=np.zeros((650,600),dtype=np.uint8)
                reproject(im.read(1),dest,src_transform=im.transform,src_crs=im.crs,
                          dst_transform=target_transform*rasterio.Affine.scale(2,2),dst_crs=target_crs,
                          resampling=Resampling.bilinear,src_nodata=im.nodata,dst_nodata=0)
                Image.fromarray(dest).save(OUT/f'{name}.png')
        scaled=np.uint8(np.clip(slopes/40,0,1)*255)
        rgba=np.zeros((*z.shape,4),dtype=np.uint8);rgba[:,:,0]=255;rgba[:,:,1]=120-scaled//3;rgba[:,:,3]=scaled
        Image.fromarray(rgba).resize((600,650)).save(OUT/'slope.png')
        norm=np.clip((z-np.nanmin(z))/(np.nanmax(z)-np.nanmin(z)),0,1)
        rgb=np.stack([80+norm*150,75+norm*100,65+norm*65],axis=-1).astype('uint8')
        Image.fromarray(rgb).resize((600,650)).save(OUT/'elevation.png')
        with rasterio.open(P/'terrain/ombrage_delta.tif') as hs:
            Image.fromarray(hs.read(1).astype('uint8')).resize((600,650)).save(OUT/'hillshade.png')
        for f in sorted(P.rglob('*.tif')):
            with rasterio.open(f) as ds:
                audit.append(dict(file=str(f.relative_to(P)),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),
                    bytes=f.stat().st_size,resolution=ds.res,crs=ds.crs.to_wkt(),bounds=list(ds.bounds),nodata=ds.nodata,
                    shape=[ds.height,ds.width],dtype=ds.dtypes[0]))
    config.update(id='jezero-west-delta',justification='Intersection DEM PLACES valide, extraits HiRISE/CTX et polygones SIM3464; trois prélèvements publiés dans la zone.',
                  registration_warning='Géologie non recalée : 100–200 m. Mars Trek/PLACES : erreur non quantifiée.',grid_step_m=5,native_dem_m=1)
    (ROOT/'config/roi.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    (OUT/'raster-audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    # Rebuild authoritative polygon clip, rather than trusting a web geometry export.
    connection=sqlite3.connect(P/'geology/usgs_original_MARS.gpkg')
    source_wkt=connection.execute('SELECT definition FROM gpkg_spatial_ref_sys WHERE srs_id=100000').fetchone()[0]
    transformer=Transformer.from_crs(CRS.from_wkt(source_wkt),CRS.from_wkt(config['crs_wkt']),always_xy=True)
    ox,oy=config['origin_projected_m']
    def local(x,y,z=None):
        xx,yy=transformer.transform(x,y)
        return np.asarray(xx)-ox,np.asarray(yy)-oy
    boundary=box(0,-1300,1200,0)
    features=[]
    columns=[r[1] for r in connection.execute('PRAGMA table_info(GeoUnits_v1)')]
    for row in connection.execute('SELECT * FROM GeoUnits_v1'):
        record=dict(zip(columns,row));blob=record.pop('geom')
        envelope=(blob[3]>>1)&7; offset=8+{0:0,1:32,2:48,3:48,4:64}[envelope]
        shape=transform_shape(local,from_wkb(blob[offset:]))
        if not shape.is_valid:shape=shape.buffer(0)
        if not shape.intersects(boundary):continue
        clipped=shape.intersection(boundary)
        if clipped.is_empty:continue
        record.update(source_layer='GeoUnits_v1',registration='UNREGISTERED_100_200M',use='regional_context_only')
        features.append(dict(type='Feature',id=f"GeoUnits_v1:{record['fid']}",geometry=mapping(clipped),properties=record))
    connection.close()
    geo=dict(type='FeatureCollection',coordinate_system='MARS_LOCAL_METERS_NOT_RFC7946',registration='UNREGISTERED_100_200M',features=features)
    descriptions=json.loads((P/'science/geologic_descriptions_web.json').read_text(encoding='utf-8'))['units']
    for f in geo['features']:
        prop=f['properties']; prop['description']=descriptions.get(prop.get('name'),{})
    (OUT/'geology.json').write_text(json.dumps(geo),encoding='utf-8')
    import runpy
    runpy.run_path(str(ROOT/'scripts/build_catalog.py'),run_name='__main__')
    print('Préparation terminée : DEM réel, grille conservatrice 5 m, imagerie reprojetée, géologie non recalée.')
if __name__=='__main__': main()
