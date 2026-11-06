"""Validate interactive assets, source coverage, print download and behavior tests."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[1]
subprocess.run(['node',str(REPO/'tests/test_telluride_controls.js')],check=True)
subprocess.run(['node','--check',str(ROOT/'web/app.js')],check=True)
data=json.loads((ROOT/'web/map-data.json').read_text());qa=json.loads((ROOT/'web-data.qa.json').read_text())
assert len(data['buildings']['features'])==1131 and len(data['landmarks']['features'])==3
assert hashlib.sha256((ROOT/'web/map-data.json').read_bytes()).hexdigest()==qa['web_data_sha256']
assert data['summary']['pre1900_count'] is None
files=['map.html','web/map-data.json','web/style.css','web/map-controls.js','web/app.js','web/vendor/leaflet.js','web/vendor/leaflet.css','web/vendor/LEAFLET-LICENSE.txt']
html=(ROOT/'map.html').read_text();assert 'L.map' in (ROOT/'web/app.js').read_text() and '<img id="poster"' not in html
for match in re.finditer(r'(?:src|href)="((?:web|exports)/[^"#]+)"',html):assert (ROOT/match[1]).is_file(),match[1]
high=json.loads((ROOT/'highres-export.qa.json').read_text());assert high['dimensions_px']==[3000,3750]
assert hashlib.sha256((ROOT/'exports/day06_telluride_3000x3750.png').read_bytes()).hexdigest()==high['sha256']
report={'automated_checks_passed':True,'interactive_vector_features':1131,'historic_rated_footprints':293,'verified_landmarks':3,'checks':['unique source IDs and class counts','rating popup content and HTML escaping','classification filter toggles','landmark selection and selected popup','downtown and full-town extents','terrain toggle','rating dialog','data load error handling','local asset and print download paths','JavaScript syntax','11.25 MP export checksum'],'browser_visual_review_passed':False,'browser_visual_review_limit':'Browser runtime lists no connected browsers; in-app browser reports unavailable. Desktop and mobile visual review of the new interactive page could not be completed in this session.','publication_authorized':True,'authorization':'User requested a GitHub Page like the other days.','asset_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files}}
(ROOT/'web.qa.json').write_text(json.dumps(report,indent=2));print('Interactive vector and asset checks passed; browser visual review unavailable.')
