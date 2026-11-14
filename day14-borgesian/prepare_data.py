"""Rebuild static Day 14 layers. Requires Python 3, shapely>=2, osmium>=4, and curl.
Raw downloads stay in ignored data/raw/day14; --refresh re-downloads sources.
"""
from pathlib import Path
import argparse, collections, datetime, hashlib, json, subprocess, sys, math
from shapely.geometry import shape, mapping, Point, LineString, Polygon
from shapely.ops import unary_union, polygonize
from shapely import make_valid, prepare
from orient_benches import orient_benches

HERE = Path(__file__).resolve().parent
CACHE = HERE.parent / 'data/raw/day14'
OUT = HERE / 'data'
PARK = 'https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/ArcGIS/rest/services/ODC_PARK_PARKLAND_A/FeatureServer/87'
BOUNDARY = 'https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/ArcGIS/rest/services/ODC_ENG_SRVCCDBOUNDARY_A/FeatureServer/40'

def dump(path, data):
    path.write_text(json.dumps(data, separators=(',', ':'), ensure_ascii=False))

def fetch(name, url, query=None, refresh=False):
    path = CACHE / (name + '.json')
    if refresh or not path.exists():
        tmp = path.with_suffix('.tmp')
        cmd = ['curl','--fail','--silent','--show-error','--location','--retry','2','--max-time','240','--get',url]
        if query: cmd += ['--data-urlencode','data='+query]
        subprocess.run(cmd + ['--output',str(tmp)], check=True)
        data = json.loads(tmp.read_text())
        if 'error' in data or data.get('remark'): raise ValueError(data)
        tmp.replace(path)
    return json.loads(path.read_text())

def feature(g, props):
    return {'type':'Feature','geometry':mapping(g),'properties':props}

def fc(features): return {'type':'FeatureCollection','features':features}

def polygon_parts(g):
    if g.geom_type == 'Polygon': return [g]
    if hasattr(g, 'geoms'): return [p for x in g.geoms for p in polygon_parts(x)]
    return []

def osm_geometry(e):
    if '_geometry' in e: return make_valid(shape(e['_geometry']))
    if e['type']=='node': return Point(e['lon'],e['lat'])
    if e['type']=='way':
        coords=[(p['lon'],p['lat']) for p in e.get('geometry',[]) if p and 'lon' in p]
        if len(coords)<2: return None
        t=e.get('tags',{})
        area=(t.get('natural')=='water' or t.get('leisure') in ['pitch','playground'] or t.get('area')=='yes')
        return make_valid(Polygon(coords)) if area and len(coords)>3 and coords[0]==coords[-1] else LineString(coords)
    # Assemble OSM multipolygon rings, retaining inner holes and separate outer rings.
    rings={}
    for role in ['outer','inner']:
        lines=[LineString([(p['lon'],p['lat']) for p in m['geometry'] if p and 'lon' in p]) for m in e.get('members',[]) if m.get('role','outer')==role and len(m.get('geometry',[]))>=2]
        rings[role]=unary_union(list(polygonize(unary_union(lines)))) if lines else Polygon()
    return make_valid(rings['outer'].difference(rings['inner']))

def tour_landmarks(features, wash):
    inside=[f for f in features if wash.intersects(shape(f['geometry']))]
    def named(name):return next(f for f in inside if f['properties'].get('name')==name)
    def landmark(f,name=None):
        point=shape(f['geometry']).representative_point()
        return {'coordinates':[point.x,point.y],'osm':[f['properties']['osm']],'name':name or f['properties'].get('name') or f['properties']['kind']}
    smith=named('Smith Lake');grasmere=named('Grasmere Lake')
    playgrounds=[f for f in inside if f['properties']['kind']=='playground']
    north=max(playgrounds,key=lambda f:shape(f['geometry']).representative_point().y)
    south=min(playgrounds,key=lambda f:shape(f['geometry']).representative_point().y)
    lake=shape(grasmere['geometry']);lake_point=lake.representative_point()
    courts=[f for f in inside if f['properties']['kind']=='pitch' and f['properties'].get('sport')=='tennis' and shape(f['geometry']).representative_point().y<lake_point.y]
    assert courts,'No verified south tennis courts'
    center=unary_union([shape(f['geometry']) for f in courts]).centroid
    from shapely.ops import nearest_points
    west=nearest_points(lake,Point(lake.bounds[0]+(lake.bounds[2]-lake.bounds[0])*.25,lake_point.y))[0]
    return {'smith_lake':landmark(smith),'north_playground':landmark(north,'North playground'),
            'south_playground':landmark(south,'South playground'),'grasmere_lake':landmark(grasmere),
            'tennis_courts':{'coordinates':[center.x,center.y],'osm':[f['properties']['osm'] for f in courts],'name':'Tennis courts'},
            'lake_west':{'coordinates':[west.x,west.y],'osm':[grasmere['properties']['osm']],'name':'Grasmere Lake western view'}}

def main():
    refresh=argparse.ArgumentParser();refresh.add_argument('--refresh',action='store_true');args=refresh.parse_args()
    CACHE.mkdir(parents=True,exist_ok=True); OUT.mkdir(exist_ok=True)
    schema=fetch('schema',PARK+'?f=pjson',refresh=args.refresh)
    assert schema['geometryType']=='esriGeometryPolygon'
    domains={f['name']:f.get('domain') for f in schema['fields']}
    assert {'Park','Open Space'} <= {v['code'] for v in domains['PARK_TYPE']['codedValues']}
    count=fetch('park-count',PARK+'/query?where=1%3D1&returnCountOnly=true&f=json',refresh=args.refresh)['count']
    raw=fetch('parks',PARK+'/query?where=1%3D1&outFields=*&outSR=4326&f=geojson',refresh=args.refresh)
    assert not raw.get('exceededTransferLimit') and len(raw['features'])==count, 'Incomplete park response'
    assert {'LOC_CODE','PARK_TYPE','PARK_CLASS','FORMAL_NAME'} <= {f['name'] for f in schema['fields']}
    braw=fetch('boundary',BOUNDARY+'/query?where=1%3D1&outFields=*&outSR=4326&f=geojson',refresh=args.refresh)
    boundary=unary_union([make_valid(shape(f['geometry'])) for f in braw['features'] if f['properties']['COUNTY']=='Denver'])
    groups=collections.defaultdict(list); exclusions=collections.Counter(); types=collections.Counter(); names=collections.defaultdict(set)
    for f in raw['features']:
        p=f['properties'];types[p['PARK_TYPE']+' / '+p['PARK_CLASS']]+=1
        if p['PARK_CLASS']=='Mountain' or p['MAINT_DIST']=='Mountain Parks': exclusions['mountain']+=1;continue
        if p['PARK_TYPE'] not in ['Park','Open Space'] or p['PARK_CLASS']=='Undeveloped': exclusions['other type / undeveloped']+=1;continue
        g=make_valid(shape(f['geometry'])).intersection(boundary)
        if g.is_empty or not polygon_parts(g): exclusions['outside Denver']+=1;continue
        assert p['LOC_CODE'], 'Missing reliable identifier'
        groups[p['LOC_CODE']].append((p,unary_union(polygon_parts(g))))
        names[p['FORMAL_NAME'] or p['LOCATION']].add(p['LOC_CODE'])
    parks=[];centers=[];geoms=[];wash=None
    for code,parts in sorted(groups.items()):
        assert len({p['LOCATION'] for p,g in parts})==1, f'Identifier collision: {code}'
        p=parts[0][0];g=unary_union([g for p,g in parts]);geoms.append(g)
        props={'id':code,'name':p['FORMAL_NAME'] or p['LOCATION'],'kind':p['PARK_TYPE'],'class':p['PARK_CLASS']}
        parks.append(feature(g,props));centers.append(feature(g.representative_point(),props))
        if p['FORMAL_NAME']=='Washington Park': wash=g
    assert wash is not None
    union=unary_union(geoms)
    prepare(union)
    if args.refresh or not (CACHE/'interiors.json').exists():
        pbf=CACHE/'colorado.osm.pbf'
        if args.refresh or not pbf.exists():
            subprocess.run(['curl','--fail','--location','--retry','2','--max-time','600','https://download.geofabrik.de/north-america/us/colorado-latest.osm.pbf','--output',str(pbf)],check=True)
        subprocess.run([sys.executable,str(HERE/'extract_osm.py'),str(pbf)],check=True)
    osm=json.loads((CACHE/'interiors.json').read_text())
    style=fetch('basemap','https://tiles.openfreemap.org/styles/positron',refresh=args.refresh)
    dump(OUT/'basemap.json',style)
    # The extraction envelope must cover every selected polygon; fail rather than silently omit edge parks.
    from shapely.geometry import box
    assert box(-105.12,39.60,-104.60,39.86).covers(union), 'Expand OSM query envelope'
    amenities=[];counts=collections.Counter();clipped=collections.Counter();wash_benches=[];seen=set(); rejected=0
    for e in osm['elements']:
        key=(e['type'],e['id'])
        if key in seen:continue
        seen.add(key);t=e.get('tags',{})
        kind=('bench' if t.get('amenity')=='bench' else 'tree' if t.get('natural')=='tree' else 'water' if t.get('natural')=='water' or 'waterway' in t else t.get('leisure') if t.get('leisure') in ['pitch','playground'] else 'path' if 'highway' in t else None)
        if not kind: continue
        g=osm_geometry(e)
        if g is None or g.is_empty or not union.intersects(g):rejected+=1;continue
        cut=g if union.covers(g) else g.intersection(union)
        if cut.is_empty:continue
        if not g.equals(cut):clipped[kind]+=1
        props={'kind':kind,'osm':e['type']+'/'+str(e['id'])}
        for tag in ['name','sport','surface','material','backrest','species','genus','water','waterway','highway','direction','seats','armrest','leaf_type','leaf_cycle','height','circumference']:
            if tag in t:props[tag]=t[tag]
        amenities.append(feature(cut,props));counts[kind]+=1
        if kind=='bench' and g.geom_type=='Point' and wash.covers(g):wash_benches.append((e,g))
    assert wash_benches, 'No verified Washington Park bench'
    # Choose a real seat amid mapped trees: a tangible final scene, never invented foliage.
    wash_trees=[shape(f['geometry']) for f in amenities if f['properties']['kind']=='tree' and wash.covers(shape(f['geometry']))]
    def nearby_trees(g):
        sx=111320*math.cos(math.radians(g.y))
        return int(sum(((t.x-g.x)*sx)**2+((t.y-g.y)*111320)**2<=30**2 for t in wash_trees))
    e,bench=min(wash_benches,key=lambda pair:(-nearby_trees(pair[1]),-sum(k in pair[0].get('tags',{}) for k in ['direction','material','backrest','seats']),pair[1].distance(wash.representative_point())))
    assert wash.covers(bench) and any(f['properties']['osm']=='node/'+str(e['id']) for f in amenities)
    bounds=list(boundary.bounds)
    qa={'passed':True,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'park_source_last_edit_utc':datetime.datetime.fromtimestamp(schema['editingInfo']['dataLastEditDate']/1000,datetime.timezone.utc).isoformat(),'source_record_count':count,'source_type_counts':dict(types),'excluded':dict(exclusions),'parks_mapped':len(parks),'selected_parcels':sum(len(x) for x in groups.values()),'name_collisions':{k:sorted(v) for k,v in names.items() if len(v)>1},'amenities':dict(counts),'edge_clipped':dict(clipped),'outside_features_rejected':rejected,'washington_benches':len(wash_benches),'osm_timestamp':osm['osm3s']['timestamp_osm_base'],'bench':{'osm':'node/'+str(e['id']),'coordinates':[bench.x,bench.y],'tags':e.get('tags',{}),'mapped_trees_within_30m':nearby_trees(bench)},'bounds':[[bounds[0],bounds[1]],[bounds[2],bounds[3]]],'washington_bounds':list(wash.bounds),'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(CACHE.glob('*.json'))}}
    qa['tour_entry']=[(wash.bounds[0]+wash.bounds[2])/2,wash.bounds[3]-.0007]
    assert wash.covers(Point(qa['tour_entry']))
    qa['tour_landmarks']=tour_landmarks(amenities,wash)
    qa['bench_display_facing']=orient_benches(amenities)
    qa['raw_pbf_sha256']=hashlib.sha256((CACHE/'colorado.osm.pbf').read_bytes()).hexdigest() if (CACHE/'colorado.osm.pbf').exists() else None
    sources={'retrieved_utc':qa['retrieved_utc'],'parkland':{'url':PARK,'last_edit_utc':qa['park_source_last_edit_utc'],'records':count,'terms':'https://www.arcgis.com/sharing/rest/content/items/e752556524024fbfac700b35f33c0f2c?f=pjson','credit':'Denver Parks & Recreation','constraints':'Denver data supplied as-is, without warranties; not for engineering purposes.'},'boundary':{'url':BOUNDARY,'selection':"COUNTY = 'Denver' (exclude neighboring-county enclaves)",'credit':'City and County of Denver — Public Works/Survey','terms':'https://www.arcgis.com/sharing/rest/content/items/53a0ae35c018471788efe36b6f730a79?f=pjson'},'osm':{'url':'https://download.geofabrik.de/north-america/us/colorado.html','download':'https://download.geofabrik.de/north-america/us/colorado-latest.osm.pbf','snapshot_utc':qa['osm_timestamp'],'license':'ODbL 1.0','terms':'https://www.openstreetmap.org/copyright','raw_sha256':qa['raw_pbf_sha256'],'extract_bbox':[-105.12,39.60,-104.60,39.86]},'basemap':{'style':'https://tiles.openfreemap.org/styles/positron','credit':'OpenFreeMap / OpenMapTiles / OpenStreetMap contributors','terms':'https://openfreemap.org/tos/','usage':'Public interactive vector tiles; no offline bulk tile download.'},'published_urban_park_figure':{'url':'https://www.denvergov.org/Government/Agencies-Departments-Offices/Agencies-Departments-Offices-Directory/Parks-Recreation/Urban-Parks-Trails','figure':'over 280 urban parks','distinct_from_parks_mapped':True}}
    dump(OUT/'sources.json',sources)
    for name,value in [('parks',fc(parks)),('park-points',fc(centers)),('boundary',fc([feature(boundary,{'name':'City and County of Denver'})])),('interiors',fc(amenities)),('qa',qa)]:dump(OUT/(name+'.geojson' if name!='qa' else 'qa.json'),value)
    print(json.dumps({k:qa[k] for k in ['parks_mapped','amenities','edge_clipped','washington_benches','bench','name_collisions']},indent=2))

if __name__=='__main__':main()
