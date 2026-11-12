"""Prepare a cached EIA/HIFLD transmission portrait; animation is not power flow."""
from pathlib import Path
import argparse, collections, datetime, hashlib, json, math, shutil, time
import requests
from pyproj import Transformer
from shapely.geometry import shape, mapping, box, LineString, Point
from shapely.ops import transform, substring

ROOT=Path(__file__).resolve().parent
CACHE=ROOT.parents[1]/'data/raw/day12'
SERVICE='https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/US_Electric_Power_Transmission_Lines/FeatureServer/0'
REGION=[-119.8,32,-110.2,38.3]
HOOVER=[-114.738,36.0155]
FORWARD=Transformer.from_crs(4326,5070,always_xy=True).transform
BACK=Transformer.from_crs(5070,4326,always_xy=True).transform
NE='https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/'


def fetch(name,url,params=None):
    target=CACHE/name
    if target.exists(): return json.loads(target.read_text())
    for attempt in range(3):
        try:
            response=requests.get(url,params=params,timeout=90);response.raise_for_status();data=response.json()
            if 'error' in data: raise ValueError(data['error'])
            target.write_text(json.dumps(data,separators=(',',':')));return data
        except Exception:
            if attempt==2:raise
            time.sleep(2**attempt)


def write(name,data):
    (ROOT/'data'/name).write_text(json.dumps(data,separators=(',',':'),ensure_ascii=False)+'\n')


def parts(geom):
    if geom.is_empty:return []
    if geom.geom_type=='LineString':return [geom]
    if geom.geom_type in ['MultiLineString','GeometryCollection']:
        return [part for item in geom.geoms for part in parts(item)]
    return []


def mercator(lon,lat):
    return [(lon+180)/360,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2]


def main():
    CACHE.mkdir(parents=True,exist_ok=True);(ROOT/'data').mkdir(exist_ok=True)
    metadata=fetch('transmission-metadata.json',SERVICE,{'f':'json'})
    origin=fetch('transmission-item.json','https://www.arcgis.com/sharing/rest/content/items/d4090758322c4d32a4cd002ffaa0aa12',{'f':'json'})
    found=fetch('transmission-ids.json',SERVICE+'/query',dict(f='json',where='1=1',geometry=','.join(map(str,REGION)),geometryType='esriGeometryEnvelope',inSR=4326,spatialRel='esriSpatialRelIntersects',returnIdsOnly='true'))
    ids=sorted(found['objectIds']);rows=[]
    for start in range(0,len(ids),150):
        print(f'Transmission records {start+1}–{min(start+150,len(ids))} / {len(ids)}',flush=True)
        batch=fetch(f'lines-{start:05}.json',SERVICE+'/query',dict(f='json',objectIds=','.join(map(str,ids[start:start+150])),outFields='OBJECTID_1,ID,STATUS,TYPE,OWNER,VOLTAGE,VOLT_CLASS,SOURCE,SOURCEDATE,VAL_DATE',outSR=4326,returnGeometry='true'))
        if batch.get('exceededTransferLimit'):raise ValueError('Truncated batch')
        rows.extend(batch['features'])
    if len(rows)!=len(ids) or {r['attributes']['OBJECTID_1'] for r in rows}!=set(ids):raise ValueError('Object-ID coverage mismatch')
    # Plant location is taken from the accompanying EIA query, when cached.
    plant=fetch('hoover-plant.json','https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/Power_Plants_in_the_US/FeatureServer/0/query',dict(f='json',where='1=1',geometry='-114.76,35.99,-114.71,36.04',geometryType='esriGeometryEnvelope',inSR=4326,outSR=4326,outFields='*'))
    hoover=next((p for p in plant.get('features',[]) if 'hoover' in str(p.get('attributes',{})).lower()),None)
    if not hoover:raise ValueError('Verified Hoover plant point missing')
    HOOVER[:]=[hoover['geometry']['x'],hoover['geometry']['y']]
    origin_point=transform(FORWARD,Point(HOOVER));clip=transform(FORWARD,box(*REGION))
    lines=[];excluded=collections.Counter();source_dates=[]
    for row in rows:
        a=row['attributes'];g=row.get('geometry')
        if not g or not g.get('paths'):excluded['empty_geometry']+=1;continue
        if a.get('STATUS')!='IN SERVICE':excluded['not_reported_in_service']+=1;continue
        voltage=a.get('VOLTAGE') or -999999
        if voltage<115:excluded['below_115_kv_or_unknown']+=1;continue
        if a.get('SOURCEDATE'):source_dates.append(a['SOURCEDATE'])
        for index,path in enumerate(g['paths']):
            if len(path)<2:continue
            projected=transform(FORWARD,LineString([(p[0],p[1]) for p in path]))
            for clipped in parts(projected.intersection(clip)):
                if clipped.length<350:excluded['shorter_than_350_m']+=1;continue
                local=origin_point.distance(clipped)
                # Every line remains source geometry. Selection is cartographic, not electrical connectivity.
                featured=voltage>=230 or local<85000
                geometry=clipped.simplify(35,preserve_topology=True)
                # Split long features for local reveal timing, retaining the source ID.
                count=math.ceil(geometry.length/60000)
                for n in range(count):
                    piece=substring(geometry,n*geometry.length/count,(n+1)*geometry.length/count)
                    coords=list(transform(BACK,piece).coords)
                    if Point(coords[-1]).distance(Point(HOOVER))<Point(coords[0]).distance(Point(HOOVER)):coords.reverse();piece=LineString(list(piece.coords)[::-1])
                    distance=origin_point.distance(piece)
                    properties=dict(id=f"{a['OBJECTID_1']}-{index}-{n}",source_id=a['OBJECTID_1'],voltage_kv=voltage,featured=int(featured),distance_km=round(distance/1000,2),reveal=round(14+min(1,distance/570000)*18,2),length_km=round(piece.length/1000,2))
                    lines.append({'type':'Feature','properties':properties,'geometry':{'type':'LineString','coordinates':[[round(x,6),round(y,6)] for x,y in coords]}})
    write('transmission.geojson',{'type':'FeatureCollection','features':lines})
    candidates=[f for f in lines if f['properties']['featured'] and f['properties']['length_km']>2]
    # A deterministic length/voltage selection, with extra local corridors near Hoover.
    candidates.sort(key=lambda f:f['properties']['length_km']*(1+f['properties']['voltage_kv']/300)/(1+f['properties']['distance_km']/350),reverse=True)
    selected=candidates[:240]
    close=sorted(candidates,key=lambda f:f['properties']['distance_km'])[:32]
    selected=list({f['properties']['id']:f for f in close+selected}.values())
    routes=[]
    for f in selected:
        geom=LineString(f['geometry']['coordinates'])
        # Use projected interpolation for near-equal physical-distance samples.
        metric=transform(FORWARD,geom)
        samples=[]
        for i in range(256):
            p=transform(BACK,metric.interpolate(i/255,normalized=True));samples.extend(round(v,10) for v in mercator(p.x,p.y))
        routes.append(dict(id=f['properties']['id'],reveal=f['properties']['reveal'],length_km=f['properties']['length_km'],samples=samples))
    write('routes.json',{'sample_count':256,'coordinate_system':'normalized Web Mercator','routes':routes})
    # Whole background geometries avoid an artificial rectangular map panel.
    for filename,source in [('ne-states','ne_50m_admin_1_states_provinces_lines.geojson'),('ne-land','ne_50m_admin_0_countries.geojson'),('ne-lakes','ne_10m_lakes.geojson')]:
        fetch(filename+'.geojson',NE+source)
    import runpy
    fetch('ne-rivers.geojson',NE+'ne_50m_rivers_lake_centerlines.geojson')
    runpy.run_path(str(ROOT/'prepare_context.py'))
    manifest=dict(title='The Pulse of Hoover Dam',retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),transmission_service=SERVICE,source_item='https://www.arcgis.com/home/item.html?id=d4090758322c4d32a4cd002ffaa0aa12',archive_data_currency='2024-09-30',service_editing_info=metadata.get('editingInfo'),source_credit=origin.get('accessInformation'),public_use_metadata='https://gem.anl.gov/tool/layers/transmission_line_hifld/versions/5/metadata.pdf',host_terms=origin.get('licenseInfo'),bounds=REGION,hoover_coordinates=HOOVER,hoover_source='EIA Power Plants in the US query; plant point, not surveyed dam crest',queried_records=len(rows),retained_source_records=len(set(f['properties']['source_id'] for f in lines)),rendered_line_parts=len(lines),particle_routes=len(routes),excluded=dict(excluded),source_date_range_ms=[min(source_dates),max(source_dates)],simplification_m=35,minimum_line_km=.35,minimum_voltage_kv=115,network_connectivity='Not asserted; no lines, substations or connections are invented.',animation='Artistic distance-timed reveal and motion, not measured flow or verified Hoover delivery.',natural_earth=dict(source=NE,license='Public domain',terms='https://www.naturalearthdata.com/about/terms-of-use/'),sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'data').glob('*') if p.name!='sources.json'})
    # Keep the original camera and processing origins: this marker correction
    # must not alter framing, sampled corridors, or the reveal sequence.
    manifest['camera_anchor_coordinates']=HOOVER.copy()
    manifest['network_reference_coordinates']=HOOVER.copy()
    manifest['hoover_coordinates']=[-114.7372,36.0163]
    manifest['hoover_source']='Bureau of Reclamation Hoover Dam project, WGS84 project reference point (not a surveyed crest)'
    manifest['hoover_verification']=dict(source='https://www.usbr.gov/projects/index.php?id=122',corroborating_source='https://data.usbr.gov/location/3514',checked_date='2026-11-11',note='Dam project reference replaces the downstream powerplant point. Camera anchor, corridor geometry, route samples and reveal timing retained.')
    manifest['raw_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(CACHE.glob('*')) if p.is_file()}
    manifest['background_processing']='Worldwide generalized Natural Earth countries; regional water and boundaries retain whole geometry, without rectangular clipping.'
    write('sources.json',manifest)
    print(json.dumps({k:manifest[k] for k in ['queried_records','retained_source_records','rendered_line_parts','particle_routes','hoover_coordinates','excluded']},indent=2))

if __name__=='__main__':main()
