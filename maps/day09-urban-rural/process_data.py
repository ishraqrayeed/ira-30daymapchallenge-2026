"""Reproduce Day 9 public-source layers; raw responses stay in ignored data/raw."""
from pathlib import Path
import argparse, hashlib, json, math, re
from datetime import datetime, timezone
import requests
import numpy as np
import rasterio
from rasterio.warp import reproject, calculate_default_transform, Resampling
from shapely.geometry import box, Polygon, LineString, mapping, shape
from shapely.ops import transform, unary_union
from shapely.validation import make_valid
from pyproj import Transformer

HERE = Path(__file__).resolve().parent
CACHE = HERE.parents[1] / 'data/raw/day09'
OUT = HERE / 'data'
BBOX = (-115.48, 35.96, -114.98, 36.34)
WCS = 'https://www.mrlc.gov/geoserver/mrlc_display/wcs'
QUERY = '[out:json][timeout:90];way["building"]["height"](36.05,-115.4,36.25,-115.05);out tags geom;'

def download():
    CACHE.mkdir(parents=True, exist_ok=True)
    if not (CACHE/'nlcd2021.tif').exists():
        r = requests.get(WCS, params=dict(service='WCS', version='1.0.0', request='GetCoverage',
            coverage='mrlc_display:NLCD_2021_Land_Cover_L48', CRS='EPSG:4326',
            BBOX=','.join(map(str,BBOX)), RESX=.00027, RESY=.00027, FORMAT='GeoTIFF'), timeout=180)
        r.raise_for_status(); (CACHE/'nlcd2021.tif').write_bytes(r.content)
    for layer in (11,12):
        if (CACHE/f'places_{layer}.geojson').exists():continue
        url=f'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/{layer}/query'
        r=requests.get(url,params={'f':'geojson','where':"STATE='32'",'geometry':','.join(map(str,BBOX)),'geometryType':'esriGeometryEnvelope','inSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':'GEOID,NAME,BASENAME','outSR':4326,'returnGeometry':'true'},timeout=90)
        r.raise_for_status();a=r.json();assert 'features' in a
        (CACHE/f'places_{layer}.geojson').write_text(json.dumps(a))
    for name,bounds in [('strip','-115.18,36.10,-115.16,36.13'),('west','-115.36,36.13,-115.33,36.17')]:
        if (CACHE/f'lidar_{name}.json').exists():continue
        r=requests.get('https://tnmaccess.nationalmap.gov/api/v1/products',params={'bbox':bounds,'datasets':'Lidar Point Cloud (LPC)','max':3},timeout=60)
        r.raise_for_status();(CACHE/f'lidar_{name}.json').write_text(r.text)
    if not (CACHE/'osm.json').exists():
        errors=[]
        for host in ['https://overpass.private.coffee/api/interpreter','https://overpass.kumi.systems/api/interpreter','https://overpass-api.de/api/interpreter']:
            try:
                r=requests.get(host,params={'data':QUERY},timeout=150);r.raise_for_status()
                a=r.json(); assert 'elements' in a
                (CACHE/'osm.json').write_text(json.dumps(a));break
            except Exception as e: errors.append(str(e))
        else: raise RuntimeError('No Overpass endpoint returned buildings: '+str(errors))

def write(name, data):
    (OUT/name).write_text(json.dumps(data,separators=(',',':'))+'\n')

def feature(geom, props):
    return {'type':'Feature','geometry':mapping(geom),'properties':props}

def height_m(text):
    # Accept explicit meters or feet only. Never infer a height from levels.
    m=re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*(m|meter|meters|ft|feet|\')?\s*', str(text))
    if not m:return None
    h=float(m[1]) * (.3048 if m[2] in ('ft','feet',"'") else 1)
    return h if 1 <= h <= 500 else None

def zonal(array, affine, bounds, classes=(21,22,23,24)):
    """Exact fractional pixel weights in a projected, north-up raster."""
    left,bottom,right,top=bounds
    x0,dy,dx,y0=affine.c,-affine.e,affine.a,affine.f
    c0=max(0,int(math.floor((left-x0)/dx)));c1=min(array.shape[1],int(math.ceil((right-x0)/dx)))
    r0=max(0,int(math.floor((y0-top)/dy)));r1=min(array.shape[0],int(math.ceil((y0-bottom)/dy)))
    xx=x0+np.arange(c0,c1)*dx; yy=y0-np.arange(r0,r1)*dy
    wx=np.maximum(0,np.minimum(xx+dx,right)-np.maximum(xx,left))
    wy=np.maximum(0,np.minimum(yy,top)-np.maximum(yy-dy,bottom))
    weights=wy[:,None]*wx[None,:]; values=array[r0:r1,c0:c1]
    valid=(values!=0)&(values!=255)
    total=float(weights[valid].sum())
    developed=float(weights[np.isin(values,classes)].sum())
    return developed,total

def process():
    OUT.mkdir(exist_ok=True)
    with rasterio.open(CACHE/'nlcd2021.tif') as src:
        affine,w,h=calculate_default_transform(src.crs,'EPSG:32611',src.width,src.height,*src.bounds,resolution=30)
        a=np.zeros((h,w),dtype='uint8')
        reproject(src.read(1),a,src_transform=src.transform,src_crs=src.crs,
            dst_transform=affine,dst_crs='EPSG:32611',resampling=Resampling.nearest,dst_nodata=0)
    inverse=Transformer.from_crs(32611,4326,always_xy=True).transform
    cells=[]; urban=[]; totals={'developed_m2':0,'valid_m2':0}; categories={}
    # Full grid cells only; coverage threshold excludes edges with missing source pixels.
    for x in range(math.floor(affine.c/500)*500,math.ceil((affine.c+w*30)/500)*500,500):
        for y in range(math.floor((affine.f-h*30)/500)*500,math.ceil(affine.f/500)*500,500):
            geom=box(x,y,x+500,y+500); dev,valid=zonal(a,affine,geom.bounds)
            if valid < 249999:continue
            intensive,_=zonal(a,affine,geom.bounds,classes=(23,24))
            pct=100*dev/valid; intensive_pct=100*intensive/valid
            category='Urban' if intensive_pct>=50 else 'Suburban' if pct>=10 else 'Rural'
            categories[category]=categories.get(category,0)+1
            props={'id':f'{x}-{y}','developed_pct':round(pct,2),'intensive_pct':round(intensive_pct,2),'intensive_m2':round(intensive,2),'class':category,'valid_m2':round(valid,2),'developed_m2':round(dev,2)}
            cells.append(feature(transform(inverse,geom),props))
            if pct>=50:urban.append(geom)
            totals['developed_m2']+=dev;totals['valid_m2']+=valid
    developed_union=unary_union(urban)
    components=list(developed_union.geoms) if developed_union.geom_type=='MultiPolygon' else [developed_union]
    boundary=LineString(max(components,key=lambda g:g.area).exterior.coords)
    write('grid.geojson',{'type':'FeatureCollection','features':cells})
    write('boundary.geojson',{'type':'FeatureCollection','features':[feature(transform(inverse,boundary),{'threshold_pct':50,'meaning':'Exterior of largest connected union of 500 m cells with at least 50% developed cover; holes and detached islands omitted; clipped study extent'})]})
    osm=json.loads((CACHE/'osm.json').read_text());buildings=[];excluded=0
    for e in osm['elements']:
        tags=e.get('tags',{});height=height_m(tags.get('height'));coords=[(v['lon'],v['lat']) for v in e.get('geometry',[])]
        if height is None or len(coords)<4 or coords[0]!=coords[-1]:excluded+=1;continue
        geom=Polygon(coords)
        if not geom.is_valid or geom.area<=0:excluded+=1;continue
        buildings.append(feature(geom,{'id':f"way/{e['id']}",'name':tags.get('name','OSM building'),'height_m':round(height,3),'height_original':tags['height'],'height_source':'OSM explicit height tag; measurement method unverified','osm_url':f"https://www.openstreetmap.org/way/{e['id']}"}))
    if not buildings:raise ValueError('No usable height-tagged buildings')
    write('buildings.geojson',{'type':'FeatureCollection','features':buildings})
    places=[]
    project=Transformer.from_crs(4326,32611,always_xy=True).transform
    for layer,kind in [(11,'Incorporated city'),(12,'Census-designated place (unincorporated)')]:
        source=json.loads((CACHE/f'places_{layer}.geojson').read_text())
        for f in source['features']:
            projected=make_valid(transform(project,shape(f['geometry'])))
            if projected.geom_type=='GeometryCollection':
                projected=unary_union([g for g in projected.geoms if g.geom_type in ('Polygon','MultiPolygon')])
            geom=make_valid(transform(inverse,projected.simplify(10,preserve_topology=True)))
            if geom.geom_type=='GeometryCollection':
                geom=unary_union([g for g in geom.geoms if g.geom_type in ('Polygon','MultiPolygon')])
            props=f['properties'];point=geom.representative_point()
            places.append(feature(geom,{'geoid':props['GEOID'],'name':props['NAME'],'place_type':kind,'label_lon':point.x,'label_lat':point.y,'vintage':'BAS 2026','display_simplification_m':10}))
    write('places.geojson',{'type':'FeatureCollection','features':places})
    manifest={'generated_utc':datetime.now(timezone.utc).isoformat(),'grid_crs':'EPSG:32611','cell_size_m':500,'nlcd_year':2021,'developed_classes':[21,22,23,24],'thresholds':{'urban_min_intensive_pct':50,'suburban_min_developed_pct':10,'developed_boundary_min_pct':50},'cells':len(cells),'classes':categories,'places':len(places),'buildings':len(buildings),'excluded_buildings':excluded,'totals':totals,'osm_base_timestamp':osm.get('osm3s',{}).get('timestamp_osm_base'),'source_sha256':{n:hashlib.sha256((CACHE/n).read_bytes()).hexdigest() for n in ['nlcd2021.tif','osm.json','places_11.geojson','places_12.geojson']},'boundary_length_m':boundary.length}
    write('analysis.json',manifest);print(json.dumps(manifest,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--download',action='store_true');args=p.parse_args()
    if args.download:download()
    process()
