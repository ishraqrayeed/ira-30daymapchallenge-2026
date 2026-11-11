"""Fetch OSM public drive-service streets, project to local UTM and clip at 1 km."""
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/day11-mpl')
import argparse, json, hashlib, time, math, re, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone
import osmnx as ox
from shapely.geometry import Point
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent
CACHE = ROOT.parents[1] / 'data/day11-traffic'

def map_tile(path, bbox):
    if path.exists(): return ET.parse(path).getroot()
    url='https://api.openstreetmap.org/api/0.6/map?bbox='+','.join(f'{n:.7f}' for n in bbox)
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'30DayMapChallenge-2026/Day11'})
            with urllib.request.urlopen(req,timeout=45) as response: data=response.read()
            doc=ET.fromstring(data);path.write_bytes(data);return doc
        except urllib.error.HTTPError as error:
            if error.code==400 and 'too many nodes' in error.read().decode().lower():
                west,south,east,north=bbox;mx=(west+east)/2;my=(south+north)/2
                merged=ET.Element('osm',version='0.6')
                for index,box in enumerate([(west,south,mx,my),(west,my,mx,north),(mx,south,east,my),(mx,my,east,north)]):
                    doc=map_tile(path.with_stem(path.stem+'-'+str(index)),box)
                    merged.extend(doc)
                return merged
            if attempt==2: raise
            time.sleep(3*2**attempt)
        except Exception:
            if attempt==2: raise
            time.sleep(3*2**attempt)

def build(city):
    ox.settings.use_cache = True
    ox.settings.cache_folder = str(CACHE / 'osmnx')
    ox.settings.requests_timeout = 180
    lat, lon = city['map_center']
    path = CACHE / (city['id'] + '-' + hashlib.sha256(f'{lat},{lon}'.encode()).hexdigest()[:8] + '.graphml')
    legacy = CACHE / (city['id'] + '.graphml')
    if legacy.exists() and not path.exists():
        old = ox.load_graphml(legacy)
        if city['id'] != 'dhaka':
            ox.save_graphml(old,path)
    if path.exists():
        graph = ox.load_graphml(path)
    elif city['id'] in ['dhaka','cairo','bangkok','sydney','istanbul','sao-paulo','johannesburg','mexico-city']:
        # Official OSM map API fallback: small quadrants avoid its 50,000-node cap.
        # OSMnx still constructs and simplifies the topology from real OSM XML.
        delta_lat=1300/111195
        delta_lon=delta_lat/math.cos(math.radians(lat))
        nodes={}; ways={}
        for ix in range(2):
            for iy in range(2):
                bbox=[lon-delta_lon+ix*delta_lon,lat-delta_lat+iy*delta_lat,lon+ix*delta_lon,lat+iy*delta_lat]
                tile=CACHE/f"{city['id']}-{lat}-{lon}-{ix}-{iy}.osm"
                print('  OSM quadrant '+str(ix)+str(iy),flush=True)
                doc=map_tile(tile,bbox)
                for node in doc.findall('node'): nodes[node.attrib['id']]=node
                for way in doc.findall('way'):
                    tags={t.attrib['k']:t.attrib['v'] for t in way.findall('tag')}
                    excluded=r'^(abandoned|bridleway|bus_guideway|construction|corridor|cycleway|elevator|escalator|footway|no|path|pedestrian|planned|platform|proposed|raceway|razed|steps|track)$'
                    if not tags.get('highway') or re.match(excluded,tags['highway']): continue
                    if tags.get('area')=='yes' or tags.get('access')=='private' or tags.get('motor_vehicle')=='no' or tags.get('motorcar')=='no': continue
                    if tags.get('service') in ['emergency_access','parking','parking_aisle','private']: continue
                    ways[way.attrib['id']]=way
        needed={nd.attrib['ref'] for way in ways.values() for nd in way.findall('nd')}
        xml=ET.Element('osm',version='0.6',generator='Day11 OSM road filter')
        for id in needed: xml.append(nodes[id])
        for way in ways.values(): xml.append(way)
        filtered=CACHE/f"{city['id']}-public-roads.osm"
        ET.ElementTree(xml).write(filtered,encoding='utf-8',xml_declaration=True)
        graph=ox.graph_from_xml(filtered,simplify=True,retain_all=True)
        ox.save_graphml(graph,path)
    else:
        for attempt in range(5):
            try:
                graph = ox.graph_from_point((lat, lon), dist=1300, network_type='drive_service', simplify=True, retain_all=True, truncate_by_edge=True)
                break
            except Exception:
                if attempt == 4: raise
                print('Overpass busy; retrying in '+str(5 * 2**attempt)+' seconds', flush=True)
                time.sleep(5 * 2**attempt)
        ox.save_graphml(graph, path)
    projected = ox.project_graph(graph)
    edges = ox.graph_to_gdfs(projected, nodes=False)
    x, y = Transformer.from_crs('EPSG:4326', edges.crs, always_xy=True).transform(lon, lat)
    boundary = Point(x, y).buffer(1000, resolution=256)
    groups = {'minor': [], 'major': []}
    count = 0
    for _, edge in edges.iterrows():
        geometry = edge.geometry.intersection(boundary)
        road = edge.get('highway', '')
        major = any(h in ['motorway','trunk','primary','secondary','tertiary','motorway_link','trunk_link','primary_link','secondary_link','tertiary_link'] for h in (road if isinstance(road,list) else [road]))
        parts = list(geometry.geoms) if geometry.geom_type == 'MultiLineString' else [geometry]
        for line in parts:
            if line.is_empty or line.geom_type != 'LineString': continue
            line = line.simplify(0.6, preserve_topology=True)
            coords = [(150+(a-x)*.15,150-(b-y)*.15) for a,b in line.coords]
            groups['major' if major else 'minor'].append('M'+' L'.join(f'{a:.2f},{b:.2f}' for a,b in coords))
            count += 1
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" role="img"><title>'+city['city']+' · OpenStreetMap streets · 2 km diameter</title><defs><clipPath id="circle"><circle cx="150" cy="150" r="150"/></clipPath></defs><circle cx="150" cy="150" r="150" fill="#F0F0EC"/><g clip-path="url(#circle)" fill="none" stroke-linecap="round" stroke-linejoin="round">'
    for kind,color,width in [('minor','#B9BFBB',.9),('major','#87928F',1.35)]:
        svg += '<path stroke="'+color+'" stroke-width="'+str(width)+'" d="'+' '.join(groups[kind])+'"/>'
    svg += '</g></svg>'
    target = ROOT/'streets'/f"{city['id']}.svg"
    target.write_text(svg)
    return {'id':city['id'],'center_lat_lon':[lat,lon],'center_basis':city['center_note'],'crs':str(edges.crs),'radius_m':1000,'extraction_distance_m':1300,'rendered_line_parts':count,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'download_method':'OSM map API quadrants' if city['id'] in ['dhaka','cairo','bangkok','sydney','istanbul','sao-paulo','johannesburg','mexico-city'] else 'OSMnx / Overpass','osm_retrieved_utc':datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()}

if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--city'); args=parser.parse_args()
    CACHE.mkdir(parents=True,exist_ok=True); (ROOT/'streets').mkdir(exist_ok=True)
    cities=json.loads((ROOT/'recordings.json').read_text())['cities']
    report_path=ROOT/'streets/qa.json'
    report=json.loads(report_path.read_text()) if report_path.exists() else {}
    for city in cities:
        if args.city and city['id'] != args.city: continue
        print('Building '+city['city'],flush=True)
        report[city['id']]=build(city)
        report_path.write_text(json.dumps(report,indent=2)+'\n')
        manifest_path=ROOT/'recordings.json'
        manifest=json.loads(manifest_path.read_text())
        for item in manifest['cities']:
            if item['id']==city['id']: item['map_version']=report[city['id']]['sha256'][:12]
        manifest_path.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
