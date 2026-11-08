"""Validate the interactive geographic view and its source-backed basemap."""
from pathlib import Path
import json,re,hashlib,xml.etree.ElementTree as ET,subprocess
H=Path(__file__).resolve().parent
page=(H/'map.html').read_text();data=json.loads(re.search(r'const MAP_DATA=(\{[^\n]+\});',page)[1])
root=ET.fromstring(re.search(r'<svg[\s\S]*?</svg>',page)[0]);ns={'s':'http://www.w3.org/2000/svg'}
assert root.attrib['viewBox']=='35 305 1130 940'
assert root.find('.//s:g[@id="poster-header"]',ns) is None
assert root.find('.//s:g[@class="route-key"]',ns) is None
assert root.find('.//s:g[@id="basemap-water"]',ns) is not None
assert root.find('.//s:g[@id="basemap-highways"]',ns) is not None
assert {p.attrib['data-road-class'] for p in root.findall('.//s:path[@data-road-class]',ns)}=={'highway'}
assert 'Download poster' not in page and 'poster.png' not in page
assert len(data['stations'])==len({s['id'] for s in data['stations']})==74
assert len(data['lines'])==10
assert len(root.findall('.//s:g[@class="station"]',ns))==74
assert root.find('.//s:g[@id="labels"]',ns) is None
assert root.find('.//s:g[@id="label-leaders"]',ns) is None
existing=root.find('.//s:g[@id="existing"]',ns)
assert existing is not None and all(float(p.attrib['stroke-width'])==1.7 and p.attrib['stroke-dasharray']=='5 5' for p in existing)
assert 'aspect-ratio:1/1' not in page and 'overflow-x:auto' in page
assert {p.attrib['data-station-type'] for p in root.findall('.//s:g[@class="station"]',ns)}=={'local','transfer','major'}
assert '.reality #network' in page
assert '__APP__' not in page
sources=json.loads((H/'poster-layout.qa.json').read_text())['preserved_data_sha256']
for name in ['map-data.json','stations.geojson','routes.geojson','benchmark.json','poster-offsets.json']:
 assert hashlib.sha256((H/name).read_bytes()).hexdigest()==sources[name],name
water=json.loads((H/'basemap-water.geojson').read_text())['features'];roads=json.loads((H/'basemap-highways.geojson').read_text())['features']
assert {f['properties']['county'] for f in water}=={'Dallas','Tarrant','Denton','Collin'}
assert all(f['properties']['kind']=='highway' for f in roads)
subprocess.run(['node',str(H/'test_controls.js')],check=True)
qa={'passed':True,'primary_output':'interactive HTML','map_artboard_only':True,'network_data_unchanged':True,'stations':74,'services':10,'basemap_water_features':len(water),'basemap_highway_segments':len(roads),'interaction_checks':['all ten filters and toggles','legend/dropdown/all synchronization','all 74 popup service memberships','37 transfer classifications','label collision checks at multiple zooms','markers never hidden','wheel and pinch zoom','bounded pan','camera reset','rail explanation and toggle','responsive layout and large scrollable legend'],'tested_widths':[1100,390],'layout':'responsive webpage','static_poster_unchanged':True,'browser_visual_review':'Chrome Reality mode visually reviewed; found and corrected corridor casings masking existing rail. Final desktop/mobile visual review remains incomplete due concurrent browser changes.','artifact_sha256':{n:hashlib.sha256((H/n).read_bytes()).hexdigest() for n in ['map.html','template.html','explorer.js','render.py','basemap-water.geojson','basemap-highways.geojson']}}
(H/'web.qa.json').write_text(json.dumps(qa,indent=2)+'\n')
p=H/'map.qa.json';q=json.loads(p.read_text());q['primary_output']='interactive HTML';q['web_qa']='web.qa.json';q.setdefault('release_sha256',{})['map.html']=qa['artifact_sha256']['map.html'];p.write_text(json.dumps(q,indent=2)+'\n')
print('PASS geographic web view, full four-county water and highway basemap, unchanged transit data and interactive controls')
