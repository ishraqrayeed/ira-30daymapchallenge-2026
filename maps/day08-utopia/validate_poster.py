"""Check the reviewed poster layout and unchanged data independently of rendering."""
import json,hashlib,re,math,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import ImageFont
H=Path(__file__).resolve().parent;ns={'s':'http://www.w3.org/2000/svg'};root=ET.parse(H/'poster.svg');d=json.loads((H/'map-data.json').read_text());stations=d['stations'];coords=[s['coordinates'] for s in stations]
minlon=min(c[0] for c in coords);maxlon=max(c[0] for c in coords);minlat=min(c[1] for c in coords);maxlat=max(c[1] for c in coords);sy=min(910/(maxlat-minlat),1010/((maxlon-minlon)*math.cos(math.radians(33))));sx=sy*math.cos(math.radians(33));left=600-(maxlon-minlon)*sx/2
offsets=json.loads((H/'poster-offsets.json').read_text())['offsets']
for g in root.findall('.//s:g[@class="station"]',ns):
 st=next(s for s in stations if s['id']==g.attrib['data-station']);c=g.find('s:circle',ns);x,y=st['coordinates'];dx,dy=offsets.get(st['id'],(0,0));assert abs(float(c.attrib['cx'])-(left+(x-minlon)*sx+dx))<.011;assert abs(float(c.attrib['cy'])-(315+(maxlat-y)*sy+dy))<.011
labels=root.findall('.//s:g[@id="labels"]/s:text',ns);visible=[t for t in labels if 'detail-label' not in t.attrib['class']];fontfile='/System/Library/Fonts/Supplemental/Arial Bold.ttf' if Path('/System/Library/Fonts/Supplemental/Arial Bold.ttf').exists() else 'DejaVuSans-Bold.ttf';boxes=[]
for t in visible:
 size=float(re.search(r'font-size:([\d.]+)',t.attrib['style'])[1]);font=ImageFont.truetype(fontfile,round(size*10));width=font.getlength(t.text)/10;x=float(t.attrib['x']);y=float(t.attrib['y']);anchor=t.attrib['text-anchor'];x-=width if anchor=='end' else width/2 if anchor=='middle' else 0;box=(x,y-size,width,size,t.text)
 assert x>=35 and x+width<=1165 and y-size>=305 and y+4<=1240,box
 for bx,by,bw,bh,name in boxes:assert not(x<bx+bw and x+width>bx and y-size<by+bh and y>by),(t.text,name)
 boxes.append(box)
city=root.find('.//s:text[@id="downtown-dallas-label"]',ns)
assert city is not None and ' '.join(t.text for t in city.findall('s:tspan',ns))=='DOWNTOWN DALLAS'
assert city.attrib['style']=='font-size:22px;font-weight:800'
city_boxes=[]
for line in city.findall('s:tspan',ns):
 font=ImageFont.truetype(fontfile,220);width=font.getlength(line.text)/10
 x=float(line.attrib['x']);y=float(line.attrib['y']);city_boxes.append((x,y-22,width,22))
 for bx,by,bw,bh,name in boxes:
  assert not(x<bx+bw and x+width>bx and y-22<by+bh and y>by),('DOWNTOWN DALLAS',name)
assert root.find('.//s:g[@id="poster-header"]',ns).attrib['transform']=='translate(0,18)'
assert all(sid in {t.attrib['data-label'] for t in visible} for sid in ['northside','tp'])
assert all(next(t.text for t in visible if t.attrib['data-label']==sid)==next(s['name'] for s in stations if s['id']==sid) for sid in ['northside','tp'])
terminals={f['properties']['stations'][i] for f in d['lines'] for i in (0,-1)}
by_label={t.attrib['data-label']:t for t in visible}
assert terminals<=set(by_label)
assert all(by_label[s['id']].text==s['name'] for s in stations if s['id'] in terminals)
assert root.find('.//s:path[@id="region-outline"]',ns) is None
assert root.find('.//s:g[@id="geography"]',ns) is not None
assert not list(root.find('.//s:g[@id="geography"]',ns))
required={'dallas','fw','arlington','dfw','plano','frisco','denton','mckinney'};assert required<={t.attrib['data-label'] for t in visible}
assert {p.attrib['data-road-class'] for p in root.findall('.//s:path[@data-road-class]',ns)}==set()
assert {p.attrib['stroke-width'] for g in root.findall('.//s:g[@class="service"]',ns) for p in g.findall('s:path',ns)}=={'8.55'}
assert root.find('.//s:g[@id="core-inset"]',ns) is None
assert not any('DFW STUDY REGION' in (text.text or '') for text in root.findall('.//s:text',ns))
members={s['id']:set() for s in stations}
for line in d['lines']:
 for sid in line['properties']['stations']:members[sid].add(line['properties']['id'])
assert all(members[s['id']]==set(s['services']) for s in stations)
assert len(members)==len({s['id'] for s in stations})==74
assert len({tuple(s['coordinates']) for s in stations})==74
assert sum(len(v)>=2 for v in members.values())==37
assert {g.attrib['data-select'] for g in root.findall('.//s:g[@class="route-key"]',ns)}=={f['properties']['id'] for f in d['lines']}
# Each rendered edge keeps its original station IDs and terminates at the same
# per-ID display position across services. Offsets never imply a new transfer.
for g in root.findall('.//s:g[@class="service"]',ns):
 line=next(f for f in d['lines'] if f['properties']['id']==g.attrib['data-route'])
 expected={tuple(sorted(pair)) for pair in zip(line['properties']['stations'],line['properties']['stations'][1:])}
 assert {(p.attrib['data-from'],p.attrib['data-to']) for p in g.findall('s:path',ns)}==expected
 for p in g.findall('s:path',ns):
  values=[float(v) for v in re.findall(r'-?[0-9]+(?:\.[0-9]+)?',p.attrib['d'])]
  for key,point in [(p.attrib['data-from'],values[:2]),(p.attrib['data-to'],values[-2:])]:
   station=next(s for s in stations if s['id']==key);lon,lat=station['coordinates'];dx,dy=offsets.get(key,(0,0))
   assert abs(point[0]-(left+(lon-minlon)*sx+dx))<.011
   assert abs(point[1]-(315+(maxlat-lat)*sy+dy))<.011
  assert p.attrib['stroke']==line['properties']['color']
assert (H/'day08-utopia-final.png').read_bytes()==(H/'poster.png').read_bytes()
assert '74 real-world locations · 37 imagined interchanges' in (H/'poster.svg').read_text()
report=json.loads((H/'poster-layout.qa.json').read_text())
for name,digest in report['preserved_data_sha256'].items():
 assert hashlib.sha256((H/name).read_bytes()).hexdigest()==digest, f'Data changed: {name}'
for name,digest in report['artifact_sha256'].items():
 assert hashlib.sha256((H/name).read_bytes()).hexdigest()==digest, f'Reviewed artifact changed: {name}'
print('PASS poster: documented station offsets, original service topology, all terminal names, Downtown Dallas / North Side / T&P labels, +36px header padding, label bounds/collisions, uniform background, no inset, 74 unique locations and 37 verified transfers, 50% route emphasis, preserved source hashes and reviewed exports')
