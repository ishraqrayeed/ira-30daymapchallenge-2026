"""Prepare continuous Natural Earth background from cached source inputs."""
from pathlib import Path
import json,hashlib
from shapely.geometry import shape,mapping,box
p=Path(__file__).resolve().parent;cache=p.parents[1]/'data/raw/day12'
world=[];context=[]
for f in json.loads((cache/'ne-land.geojson').read_text())['features']:
 g=shape(f['geometry']).simplify(.055,preserve_topology=True)
 world.append({'type':'Feature','properties':{'name':f['properties'].get('NAME','')},'geometry':mapping(g)})
for filename,kind in [('ne-states.geojson','boundary'),('ne-lakes.geojson','water')]:
 for f in json.loads((cache/filename).read_text())['features']:
  g=shape(f['geometry'])
  if not g.intersects(box(-119.8,32,-110.2,38.3)):continue
  context.append({'type':'Feature','properties':{'kind':kind,'name':f['properties'].get('name') or f['properties'].get('NAME','')},'geometry':mapping(g.simplify(.002,preserve_topology=True))})
for f in json.loads((cache/'ne-rivers.geojson').read_text())['features']:
 g=shape(f['geometry'])
 if f['properties'].get('name')=='Colorado' and g.intersects(box(-119.8,32,-110.2,38.3)):
  context.append({'type':'Feature','properties':{'kind':'river','name':'Colorado River'},'geometry':mapping(g.simplify(.001,preserve_topology=True))})
for name,features in [('world.geojson',world),('context.geojson',context)]:
 (p/'data'/name).write_text(json.dumps({'type':'FeatureCollection','features':features},separators=(',',':'))+'\n')
if (p/'data/sources.json').exists():
 s=json.loads((p/'data/sources.json').read_text());s['background_processing']='Worldwide generalized Natural Earth countries; regional water and boundaries retain whole geometry, without rectangular clipping.'
 s['river_source']='https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_rivers_lake_centerlines.geojson'
 s.setdefault('raw_sha256',{})['ne-rivers.geojson']=hashlib.sha256((cache/'ne-rivers.geojson').read_bytes()).hexdigest()
 s['sha256']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'data').glob('*') if f.name!='sources.json'};(p/'data/sources.json').write_text(json.dumps(s,separators=(',',':'))+'\n')
