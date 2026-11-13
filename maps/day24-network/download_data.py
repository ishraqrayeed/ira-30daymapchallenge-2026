"""Offline-only acquisition of original OSM ways, node references and turn relations."""
from pathlib import Path
import json,gzip,time,hashlib,concurrent.futures,requests
DAY=Path(__file__).resolve().parent;CACHE=DAY.parents[1]/'data/raw/day24/highways';CACHE.mkdir(parents=True,exist_ok=True)
ENDPOINT='https://ovp.dresel.systems/api-na/interpreter'
def get_tile(b,depth=0):
 s,w,n,e=b;name=f'{s}_{w}_{n}_{e}'.replace('.','p');target=CACHE/(name+'.json.gz');meta=CACHE/(name+'.source.json')
 if target.exists() and meta.exists():return [name]
 query=f'[out:json][timeout:180][maxsize:805306368];way[highway~"^(motorway|motorway_link|trunk|trunk_link)$"]({s},{w},{n},{e})->.roads;rel(bw.roads)[type=restriction]->.rules;(.roads;.rules;);out body geom;'
 for attempt in range(2):
  try:
   r=requests.get(ENDPOINT,params={'data':query},timeout=(20,210),headers={'User-Agent':'30DayMapChallenge2026-offline-GIS/1.0'});r.raise_for_status();obj=r.json()
   if obj.get('remark'):raise ValueError(obj['remark'])
   data=r.content;compressed=gzip.compress(data,compresslevel=6,mtime=0);target.write_bytes(compressed)
   meta.write_text(json.dumps({'url':r.url,'query':query,'bbox_south_west_north_east':b,'osm3s':obj.get('osm3s'),'elements':len(obj['elements']),'sha256':hashlib.sha256(compressed).hexdigest()},indent=2)+'\n');print(f'Cached {name}: {len(obj["elements"]):,} features, {len(compressed)/1e6:.1f} MB compressed',flush=True);return [name]
  except Exception as ex:
   print(f'Retry {name}: {str(ex)[:100]}',flush=True);time.sleep(3*(attempt+1))
 if depth>=3:raise RuntimeError(f'Unable to acquire complete OSM tile {b}')
 # Split a busy tile rather than accepting a truncated or incomplete response.
 if e-w>=n-s:
  mid=(w+e)/2;children=[(s,w,n,mid),(s,mid,n,e)]
 else:
  mid=(s+n)/2;children=[(s,w,mid,e),(mid,w,n,e)]
 return [name for child in children for name in get_tile(child,depth+1)]
if __name__=='__main__':
 census=CACHE.parent/'states-2024.zip'
 if not census.exists():
  response=requests.get('https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_state_500k.zip',timeout=120);response.raise_for_status()
  if not response.content.startswith(b'PK'):raise RuntimeError('The Census download is not a ZIP archive.')
  census.write_bytes(response.content)
 xs=[-125,-115,-105,-95,-85,-75,-66];ys=[24,32,40,50];bounds=[(s,w,n,e) for s,n in zip(ys,ys[1:]) for w,e in zip(xs,xs[1:])]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  result=[name for names in pool.map(get_tile,bounds) for name in names]
 (CACHE/'tiles.json').write_text(json.dumps({'endpoint':ENDPOINT,'tiles':result},indent=2)+'\n');print('Complete:',len(result),'tiles',flush=True)
