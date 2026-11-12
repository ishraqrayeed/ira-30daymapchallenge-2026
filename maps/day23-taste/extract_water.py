"""Assemble real OSM water multipolygons, including the Buriganga relation."""
from pathlib import Path
import json,sys
import osmium
from shapely import wkb
from shapely.geometry import box,mapping
DAY=Path(__file__).resolve().parent;REPO=DAY.parents[1]
class Water(osmium.SimpleHandler):
 def __init__(self):super().__init__();self.features=[];self.factory=osmium.geom.WKBFactory();self.bounds=box(90.383,23.694,90.435,23.735)
 def area(self,a):
  t=dict(a.tags)
  if not(t.get('natural')=='water' or t.get('water') in ['river','pond','lake','reservoir']):return
  try:
   g=wkb.loads(self.factory.create_multipolygon(a),hex=True)
   if not g.intersects(self.bounds):return
   if not g.is_valid:g=g.buffer(0)
   g=g.intersection(self.bounds)
   if g.is_empty or g.area==0:return
   self.features.append({'type':'Feature','properties':{'kind':'water','name':t.get('name:en',t.get('name','')),'osm_type':'way' if a.from_way() else 'relation','osm_id':a.orig_id()},'geometry':mapping(g)})
  except (RuntimeError,ValueError):return
if __name__=='__main__':
 h=Water();h.apply_file(sys.argv[1] if len(sys.argv)>1 else str(REPO/'data/raw/day03-polygons/bangladesh-20261102.osm.pbf'),locations=True,filters=[osmium.filter.KeyFilter('natural','water')])
 out={'type':'FeatureCollection','features':h.features};(REPO/'data/raw/day23/water.geojson').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n');print('Water features:',len(h.features),flush=True)
