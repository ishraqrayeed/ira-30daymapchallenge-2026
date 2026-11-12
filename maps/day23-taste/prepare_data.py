"""Build bounded OSM context, curated places and a pedestrian graph. No geocoding guesses."""
from pathlib import Path
import json,math,hashlib,heapq
from shapely.geometry import shape,mapping,box,Polygon
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
def write(name,obj):
 (ROOT/name).write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n')
def fc(features):return {'type':'FeatureCollection','features':features}
def point(c,p):return {'type':'Feature','geometry':{'type':'Point','coordinates':c},'properties':p}
def distance(a,b):
 p,q=map(math.radians,[a[1],b[1]]);dy=q-p;dx=math.radians(b[0]-a[0]);return 6371008.8*2*math.asin(min(1,math.sqrt(math.sin(dy/2)**2+math.cos(p)*math.cos(q)*math.sin(dx/2)**2)))
def main():
 raw=json.loads((REPO/'data/raw/day23/osm.json').read_text());pois={(p['osm_type'],p['osm_id']):p for p in raw['pois']}
 nodes=raw['nodes'];used={};edges={};streets=[]
 for w in raw['ways']:
  chunks=[];chunk=[]
  for n in w['refs']:
   if str(n) in nodes:chunk.append(str(n))
   else:
    if len(chunk)>1:chunks.append(chunk)
    chunk=[]
  if len(chunk)>1:chunks.append(chunk)
  t=w['tags'];one=t.get('oneway:foot');reverse=one=='-1';directed=one in ['yes','1','true','-1']
  for refs in chunks:
   coords=[nodes[n] for n in refs]
   streets.append({'type':'Feature','geometry':{'type':'LineString','coordinates':coords},'properties':{'osm_way':w['id'],'highway':t.get('highway',''),'name':t.get('name:en',t.get('name',''))}})
   for a,b in zip(refs,refs[1:]):
    if a==b:continue
    used[a]=nodes[a];used[b]=nodes[b];d=round(distance(nodes[a],nodes[b]),3)
    if not reverse:edges[(a,b)]=min(d,edges.get((a,b),math.inf))
    if not directed or reverse:edges[(b,a)]=min(d,edges.get((b,a),math.inf))
 ids=list(used);idx={n:i for i,n in enumerate(ids)};coordinates=[used[n] for n in ids];adj=[[] for _ in ids]
 for (a,b),d in edges.items():adj[idx[a]].append([idx[b],d])
 restaurants=[]
 curated=json.loads((ROOT/'curated.json').read_text())
 for r in curated:
  ref=r.pop('osm',None)
  if ref:
   typ,ident=ref;poi=pois[(typ,ident)];c=poi['coordinates'];r['name_bn']=poi['tags'].get('name:bn') or r.get('name_bn');r['coordinate_source']=f'https://www.openstreetmap.org/{typ}/{ident}';r['coordinate_precision']='Mapped OSM point or building representative point; entrance not surveyed.'
  else:c=r.pop('coordinates')
  snap=min(range(len(coordinates)),key=lambda i:distance(c,coordinates[i]));offset=round(distance(c,coordinates[snap]),1)
  r.update(latitude=c[1],longitude=c[0],photo_url=None,photo_credit=None,verification_status='Location and specialty source-checked; not field-verified',historic_status=r.get('historic_status','Documented Old Dhaka food establishment'),operating_status=r.get('operating_status','OSM mapped in November 2026; hours and current operation not field-checked.'),walk_node=snap,walk_offset_m=offset)
  r['source_urls']=list(dict.fromkeys(r['source_urls']+[r['coordinate_source']]))
  restaurants.append(dict(point(c,r),id=r['id']))
 # Assemble water relations from the same PBF; this preserves the Buriganga shoreline.
 water_source=REPO/'data/raw/day23/water.geojson';water=json.loads(water_source.read_text());clipped=water['features']
 neighborhood_ids=[('Chawkbazar',9035013164),('Becharam Deuri',9076478272),('Nazira Bazar',9087435013),('Bangshal',9031452193),('Shankhari Bazar',393920647),('Sutrapur',9076402952),('Narinda',9076243667),('Lalbagh',9031543668),('Islampur',394216065),('Tatibazar',393921256),('Bangla Bazar',396699842),('Armanitola',9031452196),('Chankharpul',9076503767)]
 neighborhoods=[]
 for name,n in neighborhood_ids:
  p=pois[('node',n)];neighborhoods.append(point(p['coordinates'],{'name':name,'kind':'neighborhood','source':f'https://www.openstreetmap.org/node/{n}'}))
 landmarks=[]
 for name,typ,n in [('Lalbagh Fort','node',13954132428),('Star Mosque','way',245019710),('Ahsan Manzil','node',9365643172)]:
  p=pois[(typ,n)];landmarks.append(point(p['coordinates'],{'name':name,'kind':'landmark','source':f'https://www.openstreetmap.org/{typ}/{n}'}))
 # OSM leisure way 34339923, read from the same PBF snapshot with pyosmium KeyFilter('leisure').
 park=[[90.4121417,23.7096093],[90.4122219,23.7096654],[90.4123056,23.7096842],[90.4124704,23.7096508],[90.4125449,23.7095872],[90.4126069,23.7094792],[90.4126228,23.7094064],[90.4126106,23.709255],[90.4125763,23.7090742],[90.412542,23.7089328],[90.4124905,23.708807],[90.4123875,23.7087677],[90.4123102,23.7087677],[90.41219,23.7087992],[90.4121128,23.7088542],[90.4120871,23.708972],[90.4120956,23.7091685],[90.4121042,23.7094593],[90.4121417,23.7096093]]
 landmarks.append(point(list(Polygon(park).representative_point().coords)[0],{'name':'Bahadur Shah Park','kind':'landmark','source':'https://www.openstreetmap.org/way/34339923'}))
 write('data/restaurants.geojson',fc(restaurants));write('data/streets.geojson',fc(streets));write('data/context.geojson',fc(clipped));write('data/neighborhoods.geojson',fc(neighborhoods));write('data/landmarks.geojson',fc(landmarks));write('data/routes.geojson',fc([]))
 write('data/network.json',{'coordinates':coordinates,'osm_node_ids':ids,'adjacency':adj,'speed_kmh':4,'source_date':'2026-11-02','notes':'Routes stop at mapped street nodes, not surveyed entrances. Pedestrian access filters and explicitly mapped foot one-ways applied. Car one-ways ignored for walking.'})
 # QA: directed reachability between every pair of curated street-access nodes.
 failures=[]
 for f in restaurants:
  start=f['properties']['walk_node'];seen={start};todo=[start]
  while todo:
   for n,_ in adj[todo.pop()]:
    if n not in seen:seen.add(n);todo.append(n)
  for g in restaurants:
   if g['properties']['walk_node'] not in seen:failures.append([f['id'],g['id']])
 qa={'restaurants':len(restaurants),'street_features':len(streets),'network_nodes':len(ids),'directed_edges':len(edges),'unreachable_pairs':failures,'maximum_street_access_offset_m':max(f['properties']['walk_offset_m'] for f in restaurants),'categories':sorted({x for f in restaurants for x in f['properties']['category_ids']}),'passed':not failures and all(f['properties']['walk_offset_m']<100 for f in restaurants)}
 write('data/qa.json',qa)
 manifest={'geography':'Historic Old Dhaka only; representative neighborhood points, no invented boundaries','osm_snapshot':'2026-11-02','pbf_url':'https://download.geofabrik.de/asia/bangladesh.html','pbf_sha256':raw['source_sha256'],'walking_cache_sha256':raw['walk_source_sha256'],'water_geometry_sha256':hashlib.sha256(water_source.read_bytes()).hexdigest(),'license':'ODbL 1.0','license_url':'https://opendatacommons.org/licenses/odbl/1-0/','attribution':'© OpenStreetMap contributors','restaurant_review_date':'2026-11-11','photographs':'None bundled; reporting photographs are not licensed for reuse.','bounds_wgs84':raw['bounds'],'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'data').glob('*') if p.suffix in ['.geojson','.json'] and p.name!='sources.json'}}
 write('data/sources.json',manifest);print(json.dumps(qa,indent=2));assert qa['passed']
if __name__=='__main__':main()
