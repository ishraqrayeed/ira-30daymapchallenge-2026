"""Independent graph, provenance, artifact and embedded-data checks."""
from pathlib import Path
import json, math, re, hashlib, xml.etree.ElementTree as ET
from collections import defaultdict
from PIL import Image
H=Path(__file__).resolve().parent
read=lambda n:json.loads((H/n).read_text())
stops=read('stations.geojson')['features'];routes=read('routes.geojson')['features'];s={f['properties']['id']:f for f in stops};adj=defaultdict(set)
assert len(s)==len(stops)
for f in stops:
 x,y=f['geometry']['coordinates'];assert math.isfinite(x) and math.isfinite(y) and -97.6<x<-96.3 and 32.4<y<33.4
 assert f['properties']['source'] and f['properties']['services']
for f in routes:
 p=f['properties'];ids=p['stations'];assert f['geometry']['coordinates']==[s[i]['geometry']['coordinates'] for i in ids]
 for i in ids:assert p['id'] in s[i]['properties']['services']
 for a,b in zip(ids,ids[1:]):adj[a].add(b);adj[b].add(a)
seen=set();stack=[next(iter(s))]
while stack:
 a=stack.pop()
 if a not in seen:seen.add(a);stack.extend(adj[a]-seen)
assert seen==set(s)
assert 8<=len(routes)<=12
page=(H/'map.html').read_text();data=json.loads(re.search(r'const MAP_DATA=(\{[^\n]+\});',page)[1]);assert len(data['stations'])==len(s)
assert Image.open(H/'poster.png').size==(2400,3000)
svg=ET.parse(H/'poster.svg');ns={'s':'http://www.w3.org/2000/svg'}
assert len(svg.findall('.//s:g[@class="station"]',ns))==len(s)
assert len(svg.findall('.//s:g[@class="service"]',ns))==len(routes)
from shapely.geometry import shape
from shapely.ops import unary_union
region=shape(read('study-region.geojson')['features'][0]['geometry'])
counties=unary_union([shape(f['geometry']) for f in read('boundaries.geojson')['features']])
assert region.is_valid and region.equals(counties)
outline=svg.find('.//s:path[@id="region-outline"]',ns)
assert outline is None  # Final static poster deliberately omits boundary fragments.
assert 'Not an existing or officially proposed transit system.' in page
qa=read('map.qa.json');qa.update({'independent_validation_passed':True,'poster_pixels':[2400,3000],'study_outline_matches_four_county_union':True,'release_sha256':{n:hashlib.sha256((H/n).read_bytes()).hexdigest() for n in ['map.html','poster.svg','poster.png','stations.geojson','routes.geojson']}});(H/'map.qa.json').write_text(json.dumps(qa,indent=2)+'\n');print(f'PASS: {len(s)} sourced stations; {len(routes)} services; connected graph; poster and embedded data agree')
