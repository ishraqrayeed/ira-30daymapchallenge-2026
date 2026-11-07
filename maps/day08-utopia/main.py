"""Build a geographic fiction from sourced stops and OSM locations."""
from pathlib import Path
import csv, io, zipfile, json, math, html
from collections import defaultdict
import geopandas as gpd
from shapely.geometry import shape, mapping, Point, LineString
from shapely.ops import unary_union, transform
from pyproj import Transformer
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]; RAW=ROOT/'data/raw/day08-utopia'
project=Transformer.from_crs(4326,32614,always_xy=True).transform
nyproject=Transformer.from_crs(4326,32618,always_xy=True).transform
J=lambda p:json.loads(p.read_text())
def save(n,v): (HERE/n).write_text(json.dumps(v,separators=(',',':'))+'\n')
def feature(g,p): return {'type':'Feature','geometry':mapping(g),'properties':p}
def fc(v):return {'type':'FeatureCollection','features':v}
existing=[]; rail=[]; feeds={}; anchors={}
for agency in ['dart','trinity','dcta']:
 z=zipfile.ZipFile(RAW/(agency+'.zip'))
 def read(n):return list(csv.DictReader(io.StringIO(z.read(n+'.txt').decode('utf-8-sig'))))
 routes={r['route_id']:r for r in read('routes') if r['route_type'] in ['0','1','2']}
 trips=[t for t in read('trips') if t['route_id'] in routes]; tids={t['trip_id'] for t in trips}
 stopids={s['stop_id'] for s in read('stop_times') if s['trip_id'] in tids}
 for s in read('stops'):
  if s['stop_id'] not in stopids or any(x in s['stop_name'] for x in ['POCKET','YARD LIMIT']):continue
  p={'name':s['stop_name'],'source':agency,'source_id':s['stop_id']}
  g=Point(float(s['stop_lon']),float(s['stop_lat']));existing.append(feature(g,p)); anchors[agency+':'+s['stop_id']]=feature(g,p)
 sh=defaultdict(list)
 for s in read('shapes'):sh[s['shape_id']].append(s)
 # One longest pattern per route: directional/short-turn variants are not additive.
 for rid,r in routes.items():
  options=[]
  for sid in {t.get('shape_id') for t in trips if t['route_id']==rid}:
   pts=sorted(sh[sid],key=lambda s:int(s['shape_pt_sequence']))
   if len(pts)>1:
    geom=LineString([(float(s['shape_pt_lon']),float(s['shape_pt_lat'])) for s in pts]);options.append(geom)
  if options:
   g=max(options,key=lambda g:transform(project,g).length)
   rail.append(feature(g.simplify(.0001),{'name':r['route_long_name'],'source':agency,'route_id':rid}))
 feeds[agency]=read('feed_info') if 'feed_info.txt' in z.namelist() else []
# Agglomerate physical platform records within 250m, including cross-agency duplicates.
complexes=[]
for f in existing:
 p=transform(project,shape(f['geometry']))
 match=next((c for c in complexes if c[0].distance(p)<250),None)
 if match:match[1].append(f['properties'])
 else:complexes.append((p,[f['properties']]))
save('existing-stations.geojson',fc(existing));save('existing-routes.geojson',fc(rail))
osm=J(RAW/'osm.json');elements=osm['elements'];places={e['tags']['name']:e for e in elements if e['type']=='node' and 'name' in e.get('tags',{}) and 'place' in e['tags']}
places_census=gpd.read_file('zip://'+str(RAW/'places.zip')).set_index('NAME')
stations={}
def a(key,source,label=None):
 f=anchors[source];stations[key]={'id':key,'name':label or f['properties']['name'].title().replace(' Station',''),'coordinates':f['geometry']['coordinates'],'anchor':'Existing rail station','source':source};return key
def o(key,name,label=None):
 if name in places:
  e=places[name];coord=[e['lon'],e['lat']];source='osm:'+str(e['id']);anchor='Fictional stop at a real OSM place'
 else:
  row=places_census.loc[name];g=row.geometry.representative_point();coord=[g.x,g.y];source='census-place:'+row.GEOID;anchor='Fictional stop at Census place interior point'
 stations[key]={'id':key,'name':label or name,'coordinates':coord,'anchor':anchor,'source':source};return key
# Shared IDs define interchanges exactly; no fabricated geographic coordinates.
for key,source,label in [
 ('dallas','dart:22748','Dallas Union'),('westend','dart:22749','West End'),('akard','dart:22750','Akard'),('arts','dart:22752','Arts District'),('victory','dart:28264','Victory'),('uptown','dart:26420','Cityplace / Uptown'),('smu','dart:22938','SMU / Mockingbird'),('park','dart:28755','Park Lane'),('forest','dart:26671','Forest Lane'),('richardson','dart:26673','Richardson / Arapaho'),('galatyn','dart:26674','Galatyn Park'),('cityline','dart:26895','CityLine'),('plano','dart:26896','Downtown Plano'),('parker','dart:26897','Parker Road'),('utd','dart:33598','UT Dallas'),('addison','dart:33596','Addison'),('carrollton','dart:29817','Downtown Carrollton'),('mills','dart:29816','Trinity Mills'),('branch','dart:29818','Farmers Branch'),('bachman','dart:29821','Bachman'),('inwood','dart:29824','Inwood'),('medical','dart:29826','Medical District'),('market','dart:29825','Market Center'),('irving','dart:28174','Downtown Irving'),('westirving','dart:28176','West Irving'),('lascolinas','dart:32337','Las Colinas'),('university','dart:31084','University of Dallas'),('belt','dart:31089','Belt Line'),('dfw','dart:32553','DFW Airport'),('dfwnorth','dart:33474','DFW North'),('grapevine','trinity:4155','Grapevine'),('smithfield','trinity:4154','Smithfield'),('ironhorse','trinity:4153','Iron Horse'),('northside','trinity:4166','North Side'),('mercantile','trinity:4167','Mercantile Center'),('fw','dart:28251','Fort Worth Central'),('tp','dart:28252','T&P'),('bell','dart:28180','Bell'),('centre','dart:28178','CentrePort'),('trinitylakes','dart:34126','Trinity Lakes'),('denton','dcta:838958','Downtown Denton'),('medpark','dcta:839272','MedPark'),('lake','dcta:839273','Lewisville Lake'),('lewisville','dcta:839274','Old Town Lewisville'),('hebron','dcta:839275','Hebron'),('garland','dart:26691','Downtown Garland'),('jupiter','dart:26690','Forest / Jupiter'),('whiterock','dart:26652','White Rock'),('lakehighlands','dart:32049','Lake Highlands'),('deepellum','dart:32043','Deep Ellum'),('fairpark','dart:32041','Fair Park'),('lawnview','dart:29832','Lawnview'),('buckner','dart:29834','Buckner'),('cedars','dart:22729','Cedars'),('zoo','dart:13659','Dallas Zoo'),('tyler','dart:22730','Tyler / Vernon'),('westmoreland','dart:15913','Westmoreland')]: a(key,source,label)
for key,name in [('arlington','Arlington'),('gp','Grand Prairie'),('mesquite','Mesquite'),('frisco','Frisco'),('mckinney','McKinney'),('oakcliff','Oak Cliff'),('bedford','Bedford'),('euless','Euless'),('hurst','Hurst'),('thecolony','The Colony'),('allen','Allen'),('southlake','Southlake'),('keller','Keller'),('haltom','Haltom City'),('duncanville','Duncanville'),('cedarhill','Cedar Hill')]:o(key,name)
# OurAirports public-domain geographic airport reference; fictional station placement.
airport=next(r for r in csv.DictReader((RAW/'airports.csv').open()) if r['ident']=='KDAL')
stations['love']={'id':'love','name':'Love Field','coordinates':[float(airport['longitude_deg']),float(airport['latitude_deg'])],'anchor':'Fictional stop at published airport reference point','source':'OurAirports:KDAL'}
SERVICES=[
 ('1','#ee352e','Metroplex','fw trinitylakes arlington gp westirving irving dallas westend akard arts deepellum fairpark mesquite'),
 ('2','#b5251a','Preston','cedarhill duncanville oakcliff dallas westend victory uptown smu park forest richardson galatyn cityline plano parker allen mckinney'),
 ('3','#00933c','Denton','denton medpark lake lewisville hebron mills carrollton branch bachman inwood medical market victory westend dallas'),
 ('4','#007b43','North Dallas','frisco thecolony addison utd richardson forest park smu uptown arts deepellum fairpark lawnview buckner'),
 ('A','#0039a6','Airport Express','fw northside mercantile ironhorse smithfield grapevine dfwnorth dfw belt lascolinas university irving dallas'),
 ('C','#267bc0','Crosstown','southlake grapevine dfwnorth dfw euless centre gp arlington'),
 ('E','#713e9b','Eastern Arc','lewisville thecolony frisco allen mckinney plano cityline utd garland mesquite'),
 ('B','#ff6319','Love & Culture','keller haltom fw tp arlington gp oakcliff zoo cedars dallas victory medical inwood love bachman lascolinas dfw'),
 ('D','#d69c00','Mid-Cities','fw trinitylakes hurst bell bedford euless dfw dfwnorth carrollton addison utd cityline jupiter garland'),
 ('F','#00a1de','Lakes & Arts','westmoreland tyler oakcliff dallas arts uptown smu whiterock lakehighlands jupiter garland')]
lines=[];edges=set();adj=defaultdict(set)
for id,color,name,seq in SERVICES:
 ids=seq.split();coords=[stations[s]['coordinates'] for s in ids]
 for s in ids:stations[s].setdefault('services',[]).append(id)
 for u,v in zip(ids,ids[1:]):edges.add(tuple(sorted((u,v))));adj[u].add(v);adj[v].add(u)
 lines.append(feature(LineString(coords),{'id':id,'color':color,'name':name,'stations':ids,'fictional':True}))
seen=set();todo=[next(iter(stations))]
while todo:
 s=todo.pop()
 if s not in seen:seen.add(s);todo.extend(adj[s]-seen)
assert seen==set(stations),set(stations)-seen
for s in stations.values():
 lon,lat=s['coordinates'];assert -97.6<lon<-96.3 and 32.4<lat<33.4
save('stations.geojson',fc([feature(Point(s['coordinates']),s) for s in stations.values()]));save('routes.geojson',fc(lines))
counties=gpd.read_file('zip://'+str(RAW/'counties.zip'))
dfw=counties[(counties.STATEFP=='48')&counties.NAME.isin(['Dallas','Tarrant','Denton','Collin'])]
land_km2=dfw.ALAND.sum()/1e6;save('boundaries.geojson',json.loads(dfw.to_crs(4326).to_json()))
ny=J(RAW/'nyc-stations.json');ny=[s for s in ny if s['division']!='SIR'];nycomplex={s['complex_id'] for s in ny}
nyboroughs=J(RAW/'nyc-boroughs.geojson');nyarea=sum(float(f['properties']['shape_area']) for f in nyboroughs['features'])/10763910.41671
# NYC borough shoreline polygons: projected area, avoiding source-unit assumptions.
nyarea=transform(nyproject,unary_union([shape(f['geometry']) for f in nyboroughs['features']])).area/1e6
nylines=[shape(f['geometry']) for f in J(RAW/'nyc-routes.geojson')['features'] if f['properties'].get('service') not in ['SI','SIR']]
length=lambda g:transform(project,g).length/1609.344
service_miles=sum(length(shape(f['geometry'])) for f in lines)
unique_miles=sum(length(LineString([stations[u]['coordinates'],stations[v]['coordinates']])) for u,v in edges)
benchmark={'dfw_existing_complexes':len(complexes),'dfw_source_stop_records':len(existing),'nyc_station_records_excluding_sir':len(ny),'nyc_unique_stations_excluding_sir':len({s['station_id'] for s in ny}),'nyc_complexes_excluding_sir':len(nycomplex),'dfw_four_county_land_km2':round(land_km2,2),'nyc_shoreline_polygon_km2':round(nyarea,2),'dfw_complexes_per_100km2':round(len(complexes)/land_km2*100,2),'nyc_complexes_per_100km2':round(len(nycomplex)/nyarea*100,2),'dfw_existing_service_miles_longest_pattern':round(sum(length(shape(f['geometry'])) for f in rail),1),'nyc_service_miles':round(sum(transform(nyproject,g).length for g in nylines)/1609.344,1),'fictional_service_miles':round(service_miles,1),'fictional_unique_corridor_miles':round(unique_miles,1),'fictional_stations':len(stations),'fictional_transfers':sum(len(s['services'])>1 for s in stations.values()),'fictional_services':len(lines),'feed_info':feeds}
save('benchmark.json',benchmark)
# OSM background, lightly simplified. Motorways remain context, never route constraints.
context=[]
for e in elements:
 t=e.get('tags',{});coords=[(p['lon'],p['lat']) for p in e.get('geometry',[])]
 if len(coords)<2:continue
 kind='water' if t.get('water')=='reservoir' else 'river' if t.get('waterway')=='river' else 'road' if t.get('highway')=='motorway' else None
 if kind:context.append(feature(LineString(coords).simplify(.00025),{'kind':kind,'name':t.get('name',''),'osm_id':e['id']}))
save('context.geojson',fc(context))
qa={'passed':True,'network_components':1,'valid_coordinates':len(stations),'edges':len(edges),'stations':len(stations),'services':len(lines),'source_anchored_all':all(s['source'] for s in stations.values()),'all_routes_pass_through_stations':True,'shared_interchange_ids':True}
save('map.qa.json',qa)
# Embedded geographic data powers a self-contained SVG interface.
save('map-data.json',{'stations':list(stations.values()),'lines':lines,'existing':rail,'context':context,'boundaries':J(HERE/'boundaries.geojson')['features'],'stats':benchmark})
print(json.dumps(benchmark,indent=2))
