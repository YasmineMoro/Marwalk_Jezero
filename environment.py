"""MEDA PS only. The pressure field's pascal unit is checked in the original XML."""
import csv,math,xml.etree.ElementTree as ET
from functools import lru_cache
@lru_cache(maxsize=1)
def pressure_context(pack):
    stem=pack/'environment/MEDA_sol_0029/WE__0029___________DER_PS__________________P01'
    root=ET.parse(stem.with_suffix('.xml'));ns={'p':'http://pds.nasa.gov/pds4/pds/v1'}
    field=next(f for f in root.findall('.//p:Field_Delimited',ns) if f.findtext('p:name',namespaces=ns)=='PRESSURE')
    if field.findtext('p:unit',namespaces=ns)!='pascal':raise ValueError('PRESSURE unit not validated')
    values=[];missing=0
    with stem.with_suffix('.CSV').open(newline='',encoding='utf-8') as file:
        for row in csv.DictReader(file):
            try:v=float(row['PRESSURE'])
            except ValueError:missing+=1;continue
            if not math.isfinite(v) or v<=0:missing+=1;continue
            values.append({'sclk_s':float(row['SCLK']),'lmst':row['LMST'],'pressure_pa':v})
    return dict(kind='historical',instrument='MEDA PS',sol=29,unit='Pa',start_utc=root.findtext('.//p:start_date_time',namespaces=ns),stop_utc=root.findtext('.//p:stop_date_time',namespaces=ns),samples=values[::max(1,len(values)//240)],valid_rows=len(values),missing_rows=missing,min_pa=min(v['pressure_pa'] for v in values),max_pa=max(v['pressure_pa'] for v in values),warning='Historical rover measurement, not current weather for this area. Humidity is unavailable. The XML uncertainty unit is inconsistent, so that column is excluded. TIRS irradiance is not converted to temperature.',source='https://pdsatmospheres.nmsu.edu/data_and_services/atmospheres_data/PERSEVERANCE/meda.html')
