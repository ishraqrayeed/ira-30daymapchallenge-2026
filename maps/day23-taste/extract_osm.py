"""Extract Old Dhaka context, POIs and an OSM pedestrian network from a PBF."""
from pathlib import Path
import json,sys,hashlib,datetime
import xml.etree.ElementTree as ET
import osmium
from shapely.geometry import LineString,Polygon,mapping
ROOT=Path(__file__).resolve().parent
CACHE=ROOT.parents[1]/'data/raw/day23';CACHE.mkdir(exist_ok=True)
BBOX=[90.383,23.694,90.435,23.735]
class Extract(osmium.SimpleHandler):
 def __init__(self):super().__init__();self.nodes={};self.pois=[];self.ways=[];self.water=[];self.blocked=set()
 def node(self,n):
  x,y=n.location.lon,n.location.lat
  if not (BBOX[0]<=x<=BBOX[2] and BBOX[1]<=y<=BBOX[3]):return
  t=dict(n.tags);self.nodes[n.id]=[x,y]
  if t.get('name') or t.get('name:en') or t.get('amenity') in ['restaurant','cafe','fast_food']:self.pois.append(dict(osm_type='node',osm_id=n.id,coordinates=[x,y],tags=t))
  if t.get('barrier') and (t.get('access') in ['no','private'] or t.get('foot') in ['no','private']):self.blocked.add(n.id)
 def way(self,w):
  refs=[n.ref for n in w.nodes]
  coords=[[n.lon,n.lat] for n in w.nodes if n.location.valid()]
  if not coords or not any(BBOX[0]<=x<=BBOX[2] and BBOX[1]<=y<=BBOX[3] for x,y in coords):return
  t=dict(w.tags);complete=len(coords)==len(refs)
  if complete and len(coords)>3 and refs[0]==refs[-1] and t.get('name'):
   g=Polygon(coords)
   if g.is_valid and not g.is_empty:self.pois.append(dict(osm_type='way',osm_id=w.id,coordinates=list(g.representative_point().coords)[0],tags=t))
  if complete and len(coords)>3 and refs[0]==refs[-1] and (t.get('natural')=='water' or t.get('water')):
   g=Polygon(coords)
   if g.is_valid:self.water.append(dict(type='Feature',properties=dict(name=t.get('name:en') or t.get('name',''),kind='water',osm_id=w.id),geometry=mapping(g)))
  if t.get('highway'):self.ways.append(dict(id=w.id,refs=refs,tags=t))
def main():
 src=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT.parents[1]/'data/raw/day03-polygons/bangladesh-20261102.osm.pbf'
 h=Extract();print('Reading tagged food, place and water features…',flush=True)
 h.apply_file(str(src),locations=True,filters=[osmium.filter.KeyFilter('amenity','shop','place','historic','tourism','natural','water')])
 print('Reading cached pedestrian geometry…',flush=True)
 walk=ROOT.parents[1]/'data/raw/day03-polygons/walk.osm'
 nodes={};ways=[]
 for event,e in ET.iterparse(walk,events=('end',)):
  if e.tag=='node':
   x,y=float(e.attrib['lon']),float(e.attrib['lat'])
   if BBOX[0]<=x<=BBOX[2] and BBOX[1]<=y<=BBOX[3]:nodes[int(e.attrib['id'])]=[x,y]
   e.clear()
  elif e.tag=='way':
   refs=[int(n.attrib['ref']) for n in e.findall('nd')];t={n.attrib['k']:n.attrib['v'] for n in e.findall('tag')}
   if any(n in nodes for n in refs):ways.append(dict(id=int(t.get('original_osm_way',e.attrib['id'])),refs=refs,tags=t))
   e.clear()
 out=dict(bounds=BBOX,nodes=nodes,ways=ways,blocked=sorted(h.blocked),pois=h.pois,water=h.water,source=str(src.name),source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),walk_source_sha256=hashlib.sha256(walk.read_bytes()).hexdigest(),extracted_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
 (CACHE/'osm.json').write_text(json.dumps(out,separators=(',',':'),ensure_ascii=False));print(json.dumps({k:len(out[k]) for k in ['nodes','ways','pois','water','blocked']}))
if __name__=='__main__':main()
