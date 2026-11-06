"""Acquire authoritative vector inventory, OSM streets and USGS bare-earth terrain."""
import datetime,hashlib,json,os,subprocess
from pathlib import Path
from urllib.parse import urlencode
ROOT=Path(__file__).resolve().parents[1]; RAW=ROOT/'data/raw';RAW.mkdir(parents=True,exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'data/matplotlib'));os.environ.setdefault('XDG_CACHE_HOME',str(ROOT/'data/cache'))
BASE='https://services.arcgis.com/aXqye4IXyXsdIpPb/ArcGIS/rest/services/Telluride_Historic_Structure/FeatureServer'
DEM='https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer'
records=[]
def fetch(name,url):
 p=RAW/name
 if not p.exists():
  subprocess.run(['curl','--fail','-sSL','--retry','1','--connect-timeout','20','--max-time','180',url,'-o',str(p)+'.part'],check=True)
  Path(str(p)+'.part').rename(p)
 records.append({'file':name,'url':url,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 return p
def js(name,url):
 d=json.loads(fetch(name,url).read_text())
 if 'error' in d:raise ValueError(d)
 return d
s=js('service.json',BASE+'?f=pjson'); layer=next(l for l in s['layers'] if 'Historic Structure' in l['name']);url=BASE+'/'+str(layer['id']);meta=js('layer.json',url+'?f=pjson')
js('arcgis_item.json','https://www.arcgis.com/sharing/rest/content/items/'+s['serviceItemId']+'?f=pjson')
ids=js('ids.json',url+'/query?'+urlencode({'where':'1=1','returnIdsOnly':'true','f':'json'}))['objectIds'];features=[]
for off in range(0,len(ids),200):
 d=js(f'structures_{off:05}.json',url+'/query?'+urlencode({'objectIds':','.join(map(str,ids[off:off+200])),'outFields':'*','outSR':26913,'returnGeometry':'true','f':'json'}))
 assert not d.get('exceededTransferLimit');features.extend(d['features'])
assert set(ids)=={f['attributes']['OBJECTID'] for f in features} and len(features)==len(ids)
d['features']=features;(RAW/'structures_esri.json').write_text(json.dumps(d))
# Review documentation, not map imagery. No archival raster is used by this pipeline.
fetch('survey_index.html','https://www.telluride.gov/391/2013-Telluride-Historic-Architectural-Su')
fetch('2013_survey_log.pdf','https://www.telluride.gov/DocumentCenter/View/2456/2013-Survey-Log-PDF')
fetch('103_w_colorado_survey.pdf','https://www.telluride.gov/DocumentCenter/View/2117/ColoradoAvenue103W-REVISED?bidId=')
fetch('preservation.html','https://www.telluride.gov/239/Historic-Preservation')
# Direct OSM API avoids the Overpass request that stalled in the previous draft.
# OSMnx constructs and simplifies the road graph from original OSM node/way data.
osmurl='https://api.openstreetmap.org/api/0.6/map?bbox=-107.845,37.923,-107.794,37.953'
osmpath=fetch('streets.osm',osmurl)
import osmnx as ox
ox.settings.use_cache=True;ox.settings.cache_folder=str(ROOT/'data/osmnx_cache');ox.settings.log_console=False
G=ox.graph_from_xml(osmpath,simplify=True,retain_all=True,bidirectional=True)
edges=ox.graph_to_gdfs(G,nodes=False,fill_edge_geometry=True).reset_index()
keep={'motorway','motorway_link','trunk','trunk_link','primary','primary_link','secondary','secondary_link','tertiary','tertiary_link','residential','living_street','unclassified','service'}
mask=edges.highway.map(lambda v:bool(set(v if isinstance(v,list) else [v])&keep))
edges=edges[mask].copy()
# Preserve the raw XML and all OSMnx edge tags. Stringify compound tags for GeoJSON.
for c in edges.columns:
 if c!='geometry' and c not in ['u','v','key','length']: edges[c]=edges[c].map(lambda x:';'.join(map(str,x)) if isinstance(x,(list,tuple)) else json.dumps(x) if isinstance(x,dict) else None if x is None else str(x))
# Bidirectional graph edges share geometry. Keep one copy per source way/shape.
edges['_shape']=edges.geometry.map(lambda g:min(g.wkb_hex,type(g)(list(g.coords)[::-1]).wkb_hex));edges=edges.drop_duplicates(['osmid','_shape']).drop(columns='_shape')
edges.to_file(RAW/'streets.geojson',driver='GeoJSON')
js('dem_service.json',DEM+'?f=pjson')
params={'bbox':'-107.86,37.902,-107.78,37.975','bboxSR':4326,'imageSR':26913,'size':'2000,2300','format':'tiff','pixelType':'F32','interpolation':'RSP_BilinearInterpolation','renderingRule':json.dumps({'rasterFunction':'None'}),'f':'image'}
fetch('dem.tif',DEM+'/exportImage?'+urlencode(params))
(ROOT/'source-manifest.json').write_text(json.dumps({'cache_verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'downloads':records,'structures':len(features),'osm_road_edges':len(edges),'osmnx_version':ox.__version__,'roads_method':'Official OSM API XML -> OSMnx graph_from_xml -> simplified edge geometries; Overpass avoided after previous draft stalled.'},indent=2))
print(f'Cached {len(features)} inventory polygons, {len(edges)} OSMnx street edges and USGS DEM.',flush=True)
