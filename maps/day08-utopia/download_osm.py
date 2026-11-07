"""Fetch BBBike Dallas OSM snapshot and extract place/context records (requires osmium)."""
from pathlib import Path
import urllib.request,json,hashlib,datetime
import osmium
ROOT=Path(__file__).resolve().parents[2];RAW=ROOT/'data/raw/day08-utopia'
u='https://download.bbbike.org/osm/bbbike/Dallas/Dallas.osm.pbf';p=RAW/'dallas.osm.pbf'
if not p.exists():p.write_bytes(urllib.request.urlopen(u,timeout=120).read())
elements=[]
class Extract(osmium.SimpleHandler):
 def node(self,n):
  t=dict(n.tags)
  if t.get('place') in ['city','town','suburb','neighbourhood'] and 'name' in t:elements.append({'type':'node','id':n.id,'lat':n.location.lat,'lon':n.location.lon,'tags':t})
 def way(self,w):
  t=dict(w.tags)
  if t.get('aeroway')=='aerodrome' or t.get('water')=='reservoir' or t.get('waterway')=='river' or t.get('highway')=='motorway':
   try:g=[{'lon':n.lon,'lat':n.lat} for n in w.nodes]
   except osmium.InvalidLocationError:return
   elements.append({'type':'way','id':w.id,'tags':t,'geometry':g})
Extract().apply_file(str(p),locations=True)
(RAW/'osm.json').write_text(json.dumps({'elements':elements}))
m=ROOT/'maps/day08-utopia/source-manifest.json';a=[r for r in json.loads(m.read_text()) if r['file'] not in ['osm.json','dallas.osm.pbf']];a.append({'file':p.name,'url':u,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'snapshot_last_modified':'2026-10-31T17:04:47Z'});m.write_text(json.dumps(a,indent=2));print(len(elements),'OSM records')
