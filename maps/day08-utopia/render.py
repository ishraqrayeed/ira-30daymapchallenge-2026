"""Generate the editorial poster; --update-interactive also replaces the HTML artboard."""
from pathlib import Path
import json,html,math,subprocess,sys,hashlib,tempfile,datetime
from collections import defaultdict
from shapely.geometry import shape, mapping, LineString, box as rectangle
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
D=json.loads((H/'map-data.json').read_text());S={s['id']:s for s in D['stations']}
# Dissolve four real Census county polygons into the study-region exterior.
region=unary_union([shape(f['geometry']) for f in D['boundaries']])
(H/'study-region.geojson').write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','geometry':mapping(region),'properties':{'name':'DFW four-county study region','counties':['Dallas','Tarrant','Denton','Collin'],'source':'US Census 2024 cartographic county boundaries','official_msa':False}}]},separators=(',',':'))+'\n')
# Poster crop fits the existing station extent, rather than empty northern county land.
# All coordinates retain the same geographic aspect; data and service geometry are untouched.
coords=[station['coordinates'] for station in S.values()]
minlon=min(c[0] for c in coords);maxlon=max(c[0] for c in coords)
minlat=min(c[1] for c in coords);maxlat=max(c[1] for c in coords)
sy=min(910/(maxlat-minlat),1010/((maxlon-minlon)*math.cos(math.radians(33))))
sx=sy*math.cos(math.radians(33))
map_left=600-(maxlon-minlon)*sx/2
# The 945-unit map frame keeps the full station extent and leaves compact credits below.
def xy(c):return (map_left+(c[0]-minlon)*sx,315+(maxlat-c[1])*sy)
OFFSETS=json.loads((H/'poster-offsets.json').read_text())['offsets']
def station_xy(key):
 x,y=xy(S[key]['coordinates']);dx,dy=OFFSETS.get(key,(0,0));return x+dx,y+dy
terminals={f['properties']['stations'][i] for f in D['lines'] for i in (0,-1)}
def path(coords):return 'M'+' L'.join('%.2f,%.2f'%xy(c) for c in coords)
def esc(s):return html.escape(str(s),quote=True)
parts=[]
def add(s):parts.append(s)
add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 1500" role="group" aria-label="A fictional ten-service DFW subway network at real geographic locations"><defs><style>text{font-family:Helvetica,Arial,sans-serif;fill:#172326}.label{pointer-events:none;font-size:15px;font-weight:650;paint-order:stroke;stroke:#f4f1e8;stroke-width:4;stroke-linejoin:round}.route{vector-effect:non-scaling-stroke;fill:none;stroke-linecap:round;stroke-linejoin:round}.station{cursor:pointer}.station:focus circle{stroke:#0079bd;stroke-width:4}.place{font-size:15px;font-weight:700;letter-spacing:2px;fill:#89918b}.source{font-size:10px;fill:#5e6864}</style><clipPath id="frame"><rect x="35" y="305" width="1130" height="940" rx="2"/></clipPath></defs><rect width="1200" height="1500" fill="#f4f1e8"/>')
# Add 18 SVG units = 36 pixels to the header only; map size and position stay fixed.
add('<g id="poster-header" transform="translate(0,18)">')
add('<text x="55" y="55" font-size="13" letter-spacing="3" font-weight="700">30DAYMAPCHALLENGE 2026 / 08 — UTOPIA</text><path d="M55 78H1145" stroke="#172326" stroke-width="3"/><text x="52" y="154" font-size="76" font-weight="900" letter-spacing="-4">WHAT IF DFW HAD</text><text x="52" y="234" font-size="76" font-weight="900" letter-spacing="-4">NYC’S SUBWAY?</text><text x="55" y="278" font-size="22" fill="#66716b">An alternate reality where the Metroplex runs on rails.</text>')
add('</g>')
add('<g clip-path="url(#frame)"><g id="geography">')
# Geographic context covers all four counties, with no rectangular county frame.
water_features=json.loads((H/'basemap-water.geojson').read_text())['features']
highway_features=json.loads((H/'basemap-highways.geojson').read_text())['features']
add('<g id="basemap-water">')
for feature in water_features:
 geometry=feature['geometry'];polygons=geometry['coordinates'] if geometry['type']=='MultiPolygon' else [geometry['coordinates']]
 water_path=' '.join(path(ring)+' Z' for polygon in polygons for ring in polygon)
 add(f'<path d="{water_path}" fill="#d8e6e8" fill-rule="evenodd" stroke="#bed2d6" stroke-width=".6"/>')
add('</g><g id="basemap-highways" fill="none" stroke-linejoin="round" stroke-linecap="round">')
road_paths=[]
for feature in highway_features:
 geometry=feature['geometry'];lines=geometry['coordinates'] if geometry['type']=='MultiLineString' else [geometry['coordinates']]
 road_paths.extend(path(coords) for coords in lines)
roads=' '.join(road_paths)
add(f'<path d="{roads}" stroke="#fbfaf5" stroke-width="3"/><path data-road-class="highway" d="{roads}" stroke="#bfc7bc" stroke-width="1.15"/>')
add('</g>')
add('</g><g id="existing" visibility="hidden">')
for f in D['existing']:add(f'<path class="route" d="{path(f["geometry"]["coordinates"])}" stroke="#59635f" stroke-width="3" stroke-dasharray="4 5" opacity=".7"/>')
add('</g>')
# Split each corridor into consistently ordered parallel service lanes. Every lane
# reaches the station, with a small shared approach under the interchange symbol.
edge_services=defaultdict(list)
for f in D['lines']:
 ids=f['properties']['stations']
 for a,b in zip(ids,ids[1:]):edge_services[tuple(sorted((a,b)))].append(f['properties']['id'])
add('<g id="network"><g id="lanes">')
route_shapes=[]
# Lay every corridor casing beneath all colored lanes; later services cannot erase earlier ones.
for (u,v), services in edge_services.items():
 casing_path='M%.2f,%.2f L%.2f,%.2f'%(*station_xy(u),*station_xy(v))
 add(f'<path class="route" d="{casing_path}" stroke="#f4f1e8" stroke-width="{len(services)*10+8}"/>')
for f in D['lines']:
 p=f['properties'];id=p['id'];add(f'<g class="service" data-route="{id}">')
 for a,b in zip(p['stations'],p['stations'][1:]):
  u,v=sorted((a,b));x1,y1=station_xy(u);x2,y2=station_xy(v);services=edge_services[(u,v)];off=(services.index(id)-(len(services)-1)/2)*10.5
  dx=x2-x1;dy=y2-y1;dist=math.hypot(dx,dy);ox=-dy/dist*off;oy=dx/dist*off
  # Soft parallel curve, tangent to direct geographic corridor at each endpoint.
  d=f'M{x1:.2f},{y1:.2f} C{x1+dx*.25+ox:.2f},{y1+dy*.25+oy:.2f} {x1+dx*.75+ox:.2f},{y1+dy*.75+oy:.2f} {x2:.2f},{y2:.2f}'
  add(f'<path class="route" data-from="{u}" data-to="{v}" d="{d}" stroke="{p["color"]}" stroke-width="8.55"/>')
  points=[]
  for step in range(31):
   t=step/30;one=1-t
   points.append((one**3*x1+3*one**2*t*(x1+dx*.25+ox)+3*one*t*t*(x1+dx*.75+ox)+t**3*x2,one**3*y1+3*one**2*t*(y1+dy*.25+oy)+3*one*t*t*(y1+dy*.75+oy)+t**3*y2))
  route_shapes.append(LineString(points))
 add('</g>')
# Collision-aware labels; all stations receive labels at detailed zoom.
add('</g>')
route_ink=unary_union(route_shapes).buffer(6)
boxes=[(75,372,360,420)];labels=[];leaders=[];core={'westend','akard','arts','deepellum','victory','cedars'};major={'dallas','fw','dfw','denton','plano','mckinney','frisco','arlington','gp','mesquite','garland','love','irving','grapevine','lewisville','oakcliff','richardson','northside','tp'}
station_boxes=[]
for station in S.values():
 px,py=station_xy(station['id']);radius=8.2 if len(station['services'])>1 else 4.5
 station_boxes.append((px-radius-2,py-radius-2,px+radius+2,py+radius+2))
# A geographic area label, not a station: no new node or transfer is implied.
# Reserve two short bold lines in open space just northeast of the Dallas cluster.
city_candidates=[]
for city_x in range(850,971,5):
 for city_y in range(825,1001,5):
  b=(city_x-5,city_y-22,city_x+158,city_y+34)
  if b[2]>1160 or route_ink.intersects(rectangle(*b)):continue
  if any(b[0]<q[2] and b[2]>q[0] and b[1]<q[3] and b[3]>q[1] for q in station_boxes):continue
  distance=math.hypot(city_x+65-810,city_y+6-940)
  city_candidates.append((distance,city_x,city_y,b))
if not city_candidates:raise ValueError('No clear position for Downtown Dallas area label')
_,city_x,city_y,city_box=min(city_candidates)
boxes.append(city_box)
city_label=f'<g id="city-labels"><text id="downtown-dallas-label" class="label" x="{city_x}" y="{city_y}" style="font-size:22px;font-weight:800"><tspan x="{city_x}" y="{city_y}">DOWNTOWN</tspan><tspan x="{city_x}" y="{city_y+28}">DALLAS</tspan></text></g>'
ordered=sorted(S.values(),key=lambda s:(s['id'] not in terminals,s['id'] not in major,-len(s['services'])))
for s in ordered:
 x,y=station_xy(s['id']);r=8.2 if len(s['services'])>1 else 4.5;add(f'<g class="station" tabindex="0" data-station="{s["id"]}" aria-label="{esc(s["name"])}"><title>{esc(s["name"])} · {" / ".join(s["services"])}</title><circle cx="{x:.2f}" cy="{y:.2f}" r="12" fill="transparent"/><circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="white" stroke="#172326" stroke-width="1.8"/></g>')
 font=22 if s['id'] in {'dallas','fw','arlington','dfw','plano','frisco','denton','mckinney'} else 17
 display=s['name']
 w=sum(.32 if c in ' ilI.,/rt' else .85 if c in 'MWmw' else .61 for c in display)*font;chosen=None
 for dx,dy,anchor in ([(-60,4,'end')] if s['id']=='dallas' else [])+[(-8,-18,'start'),(8,-18,'end'),(13,-12,'start'),(13,26,'start'),(-13,-12,'end'),(-13,26,'end'),(0,-20,'middle'),(0,34,'middle'),(25,7,'start'),(-25,7,'end'),(0,48,'middle'),(20,-30,'start'),(-20,-30,'end'),(0,-36,'middle'),(0,62,'middle'),(42,7,'start'),(-42,7,'end'),(28,42,'start'),(-28,42,'end'),(40,-45,'start'),(-40,-45,'end')]+[(radius*math.cos(angle),radius*math.sin(angle),'end' if math.cos(angle)<-.3 else 'start' if math.cos(angle)>.3 else 'middle') for radius in (75,95,120,145) for angle in (0,math.pi/4,math.pi/2,3*math.pi/4,math.pi,5*math.pi/4,3*math.pi/2,7*math.pi/4)]:
  xx=x+dx;yy=y+dy;left=xx-(w if anchor=='end' else w/2 if anchor=='middle' else 0);box=(left-5,yy-font,left+w+5,yy+6)
  if box[0]<38 or box[2]>1160 or box[1]<305 or box[3]>1240:continue
  if route_ink.intersects(rectangle(*box)):continue
  if math.hypot(xx-x,yy-y)>55:
   leader_end=(max(box[0]+3,min(x,box[2]-3)),max(box[1]+3,min(y,box[3]-3)))
   leader=LineString([(x,y),leader_end]).buffer(.5)
   if any(leader.intersects(rectangle(*b)) for b in station_boxes if not(b[0]<=x<=b[2] and b[1]<=y<=b[3])):continue
  if not any(box[0]<b[2] and box[2]>b[0] and box[1]<b[3] and box[3]>b[1] for b in boxes+station_boxes):chosen=(xx,yy,anchor,box);break
 if s['id'] not in terminals and (s['id'] in core or s['id'] not in major):chosen=None
 if s['id'] in terminals and chosen is None:raise ValueError('No clear terminal label position: '+s['name'])
 if chosen:
  xx,yy,anchor,box=chosen;boxes.append(box);cls='label'
  if math.hypot(xx-x,yy-y)>55:
   lx=max(box[0]+3,min(x,box[2]-3));ly=max(box[1]+3,min(y,box[3]-3))
   leaders.append(f'<path d="M{x:.2f},{y:.2f} L{lx:.2f},{ly:.2f}" fill="none" stroke="#89918b" stroke-width=".85"/>')
 else:xx,yy,anchor=x+9,y-8,'start';cls='label detail-label'
 labels.append(f'<text style="font-size:{font}px;font-weight:{800 if font==22 else 650}" class="{cls}" x="{xx:.2f}" y="{yy:.2f}" text-anchor="{anchor}" data-label="{s["id"]}" data-terminal="{str(s["id"] in terminals).lower()}">{esc(display)}</text>')
add('</g><g id="label-leaders">'+''.join(leaders)+'</g><g id="labels">'+''.join(labels)+'</g>'+city_label)
# Repeat route identities on open corridor stretches, not only in the legend.
for f in D['lines']:
 p=f['properties'];candidates=[]
 for u,v in zip(p['stations'],p['stations'][1:]):
  ax,ay=station_xy(u);bx,by=station_xy(v);mx,my=(ax+bx)/2,(ay+by)/2
  box=(mx-14,my-14,mx+14,my+14)
  if not (55<mx<1140 and 340<my<1205):continue
  if any(box[0]<b[2] and box[2]>b[0] and box[1]<b[3] and box[3]>b[1] for b in boxes):continue
  candidates.append((math.hypot(ax-bx,ay-by),mx,my,box))
 if candidates:
  _,mx,my,box=max(candidates);boxes.append(box)
  add(f'<g class="service route-badge" data-route="{p["id"]}"><circle cx="{mx:.1f}" cy="{my:.1f}" r="13" fill="{p["color"]}" stroke="#f4f1e8" stroke-width="2"/><text x="{mx:.1f}" y="{my+4.5:.1f}" text-anchor="middle" style="fill:white;font-size:15px;font-weight:700">{p["id"]}</text></g>')
# Basemap names are secondary, and never displace already-placed station labels.
background_labels=[]
water_names={'Lk Lewisville':'Lewisville Lake','Lewisville Lk':'Lewisville Lake','Grapevine Lk':'Grapevine Lake','Lk Ray Hubbard':'Lake Ray Hubbard','Joe Pool Lk':'Joe Pool Lake','Lk Arlington':'Lake Arlington','Lk Worth':'Lake Worth','Lavon Lk':'Lavon Lake','Eagle Mountain Lk':'Eagle Mountain Lake'}
water_by_name=defaultdict(list)
for f in water_features:
 name=water_names.get(f['properties']['name'])
 if name:water_by_name[name].append(shape(f['geometry']))
for name,geometries in water_by_name.items():
 geometry=unary_union(geometries);point=geometry.representative_point();wx,wy=xy((point.x,point.y));width=len(name)*6.2
 for delta_y in (0,14,-14,28,-28):
  lx=wx-width/2;ly=wy+delta_y;label_box=(lx-3,ly-12,lx+width+3,ly+4)
  if label_box[0]<40 or label_box[2]>1155 or label_box[1]<320 or label_box[3]>1235:continue
  if route_ink.intersects(rectangle(*label_box)):continue
  if any(label_box[0]<b[2] and label_box[2]>b[0] and label_box[1]<b[3] and label_box[3]>b[1] for b in boxes+station_boxes):continue
  background_labels.append(f'<text x="{wx:.2f}" y="{ly:.2f}" text-anchor="middle" font-size="12" style="fill:#6e8991;font-style:italic;paint-order:stroke;stroke:#f4f1e8;stroke-width:2">{esc(name)}</text>')
  boxes.append(label_box);break
highway_names={'I- 35 W':'I-35W','I- 35 E':'I-35E','I- 30':'I-30','I- 20':'I-20','I- 635':'I-635','US Hwy 75':'US 75'}
for source,label in highway_names.items():
 geometries=[shape(f['geometry']) for f in highway_features if f['properties']['name']==source]
 candidates=[]
 for geom in sorted(geometries,key=lambda g:g.length,reverse=True):
  for fraction in (.5,.3,.7):
   point=geom.interpolate(fraction,normalized=True);hx,hy=xy((point.x,point.y));b=(hx-22,hy-9,hx+22,hy+9)
   if b[0]<45 or b[2]>1150 or b[1]<330 or b[3]>1220:continue
   if route_ink.intersects(rectangle(*b)):continue
   if any(b[0]<q[2] and b[2]>q[0] and b[1]<q[3] and b[3]>q[1] for q in boxes+station_boxes):continue
   candidates.append((hx,hy,b))
 if candidates:
  hx,hy,b=candidates[0];boxes.append(b)
  background_labels.append(f'<g><rect x="{hx-21:.2f}" y="{hy-8:.2f}" width="42" height="16" rx="3" fill="#f7f7f0" stroke="#c2cbbf" stroke-width=".7"/><text x="{hx:.2f}" y="{hy+4:.2f}" text-anchor="middle" font-size="11" style="fill:#7a8674">{label}</text></g>')
add('<g id="basemap-labels">'+''.join(background_labels)+'</g>')
add('<text x="80" y="389" font-size="14" letter-spacing="1.5" font-weight="700" style="fill:#7e8877">DALLAS–FORT WORTH</text><text x="80" y="411" font-size="13" style="fill:#8c9587">North Texas</text>')
add('</g>')
add(f'<path d="M80 350v-30m-5 8 5-8 5 8" fill="none" stroke="#65716a"/><text x="80" y="310" text-anchor="middle" font-size="11">N</text><path d="M65 1220h{10*1609.344/111320*sy:.2f}m{-10*1609.344/111320*sy:.2f}-4v8m{10*1609.344/111320*sy:.2f}-8v8" stroke="#65716a"/><text x="152.5" y="1210" text-anchor="middle" font-size="10">≈ 10 MILES</text>')
add('<path d="M55 1255H1145" stroke="#172326" stroke-width="2"/>')
for i,f in enumerate(D['lines']):
 p=f['properties'];x=65+(i%5)*221;y=1285+(i//5)*37
 add(f'<g class="route-key" data-select="{p["id"]}"><circle cx="{x}" cy="{y}" r="12" fill="{p["color"]}"/><text x="{x}" y="{y+5}" text-anchor="middle" style="fill:white" font-size="15" font-weight="bold">{p["id"]}</text><text x="{x+23}" y="{y+4}" font-size="13" font-weight="600">{esc(p["name"])}</text></g>')
# Recompute transfers from distinct service memberships; geometric crossings never enter this count.
station_services={station_id:set() for station_id in S}
for line in D['lines']:
 for station_id in line['properties']['stations']:station_services[station_id].add(line['properties']['id'])
transfer_count=sum(len(services)>=2 for services in station_services.values())
assert all(set(S[key]['services'])==services for key,services in station_services.items())
add(f'<text x="55" y="1363" font-size="15" font-weight="700">10 services · {len(S)} real-world locations · {transfer_count} imagined interchanges</text><text x="55" y="1388" font-size="12">White circles: stations · Larger circles: transfers · Lines cross without interchange unless marked.</text><text x="55" y="1418" font-size="12" font-weight="700">Conceptual transit network. Not an existing or officially proposed transit system.</text><text class="source" x="55" y="1442">Geography: US Census / USGS · © OpenStreetMap contributors (ODbL) · Rail anchors: DART / Trinity Metro / DCTA</text><text class="source" x="55" y="1463">November 2026 snapshots · Dallas symbols offset for clarity · Geographic coordinates unchanged · ira / 30DayMapChallenge</text></svg>')
svg=''.join(parts)
web_only='--web-only' in sys.argv
if not web_only:(H/'poster.svg').write_text(svg.replace('<style>','<style>.detail-label{display:none}'))
# The web view contains only geography. Header, legend and credits are HTML UI,
# so zoom/pan never move an entire poster around the page.
import xml.etree.ElementTree as ET
ET.register_namespace('', 'http://www.w3.org/2000/svg')
web_svg=ET.fromstring(svg)
for child in list(web_svg):
 if child.tag.rsplit('}',1)[-1]=='defs':continue
 if child.tag.rsplit('}',1)[-1]=='g' and child.attrib.get('clip-path')=='url(#frame)':continue
 web_svg.remove(child)
# The static poster is untouched; replace its fixed labels only in the web SVG.
for parent in web_svg.iter():
 for child in list(parent):
  if child.attrib.get('id') in ('labels','label-leaders','city-labels'):
   parent.remove(child)
existing_layer=web_svg.find('.//{http://www.w3.org/2000/svg}g[@id="existing"]')
if existing_layer is not None:
 for line in existing_layer:
  line.set('stroke','#7e8880');line.set('stroke-width','1.7');line.set('stroke-dasharray','5 5');line.set('opacity','.55')
# Web-only polish: retain every path endpoint and the existing parallel corridor offsets.
ns='{http://www.w3.org/2000/svg}'
for group in web_svg.findall('.//'+ns+'g[@class="service"]'):
 for line in list(group):
  if line.tag==ns+'path':
   line.set('stroke-width','9.6')
   casing=ET.Element(ns+'path',dict(line.attrib))
   casing.set('class','route route-casing');casing.set('stroke','#fffdf7');casing.set('stroke-width','12')
   group.insert(list(group).index(line),casing)
for node in web_svg.findall('.//'+ns+'g[@class="station"]'):
 key=node.attrib['data-station'];count=len(station_services[key]);symbol=list(node)[-1]
 symbol.set('stroke-width','2.4' if count>=2 else '1.5')
 node.set('data-station-type','major' if count>=4 else 'transfer' if count>=2 else 'local')
 if count>=4:
  x=float(symbol.attrib['cx']);y=float(symbol.attrib['cy'])
  node.remove(symbol)
  # Capsule centered on the original point; circles retain the same anchor for label QA.
  symbol.set('r','13');symbol.set('fill','none');symbol.set('stroke','none');node.append(symbol)
  node.append(ET.Element(ns+'rect',{'x':str(x-13),'y':str(y-7),'width':'26','height':'14','rx':'7','fill':'white','stroke':'#172326','stroke-width':'2.4'}))
web_svg.set('viewBox','35 305 1130 940')
svg_namespace='{http://www.w3.org/2000/svg}'
background=ET.Element(svg_namespace+'rect',{'x':'35','y':'305','width':'1130','height':'940','fill':'#f4f1e8'})
web_svg.insert(1,background)
web_artboard=ET.tostring(web_svg,encoding='unicode')
page=(H/'template.html').read_text().replace('__SVG__',web_artboard).replace('__DATA__',json.dumps(D,separators=(',',':'))).replace('__APP__',(H/'explorer.js').read_text())
if '--update-interactive' in sys.argv or web_only:
 (H/'map.html').write_text(page)
if web_only:
 print('Updated interactive geographic map.html only; no static exports generated.')
 sys.exit(0)
# Render into a new file, then atomically replace the public PNG. A failed
# conversion cannot silently leave an old export masquerading as a new one.
with tempfile.NamedTemporaryFile(prefix='.poster-render-',suffix='.png',dir=H,delete=False) as fresh:
 temporary_png=Path(fresh.name)
try:
 subprocess.run(['rsvg-convert','-w','2400','-h','3000','-o',str(temporary_png),str(H/'poster.svg')],check=True)
 from PIL import Image
 with Image.open(temporary_png) as exported:
  assert exported.size==(2400,3000), exported.size
 temporary_png.replace(H/'poster.png')
 (H/'day08-utopia-final.png').write_bytes((H/'poster.png').read_bytes())
finally:
 temporary_png.unlink(missing_ok=True)
exported_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
digest=hashlib.sha256((H/'poster.png').read_bytes()).hexdigest()
revision=digest[:12]+'-'+str((H/'poster.png').stat().st_mtime_ns)
(H/'poster.html').write_text(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate"><title>Day 8 — Final poster preview</title><style>body{{margin:0;background:#e3e4dd;font:14px Arial,sans-serif}}nav{{padding:14px;text-align:center}}a{{color:#172326}}img{{display:block;width:min(100%,1200px);height:auto;margin:auto}}</style></head><body><nav><a href="map.html?v={revision}">Open interactive map</a> · <a href="day08-utopia-final.png?v={revision}" download>Download static poster</a> · <a href="poster.svg?v={revision}">SVG</a></nav><img src="day08-utopia-final.png?v={revision}" width="2400" height="3000" alt="What If DFW Had NYC’s Subway? Final poster with no inset, no street grid, and ten bold transit services"></body></html>''')
report={'generator':'maps/day08-utopia/render.py','exported_utc':exported_at,'output_png':str((H/'day08-utopia-final.png').resolve()),'compatibility_png':str((H/'poster.png').resolve()),'pixels':[2400,3000],'png_bytes':(H/'poster.png').stat().st_size,'png_sha256':digest,'generator_sha256':hashlib.sha256((H/'render.py').read_bytes()).hexdigest(),'fresh_temporary_render':True,'poster_preview':'poster.html?v='+revision,'interactive_html_updated':'--update-interactive' in sys.argv}
(H/'poster-export.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
