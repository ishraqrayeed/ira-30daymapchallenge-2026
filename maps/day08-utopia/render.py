"""Generate the shared SVG artboard and interactive HTML; no online tiles."""
from pathlib import Path
import json,html,math,subprocess
from collections import defaultdict
H=Path(__file__).resolve().parent
D=json.loads((H/'map-data.json').read_text());S={s['id']:s for s in D['stations']}
# Local equirectangular frame: constant metric aspect near DFW (33°N).
def xy(c):return (75+(c[0]+97.48)*1010,1130-(c[1]-32.55)*1204)
def path(coords):return 'M'+' L'.join('%.2f,%.2f'%xy(c) for c in coords)
def esc(s):return html.escape(str(s),quote=True)
parts=[]
def add(s):parts.append(s)
add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 1500" role="group" aria-label="A fictional ten-service DFW subway network at real geographic locations"><defs><style>text{font-family:Helvetica,Arial,sans-serif;fill:#172326}.label{pointer-events:none;font-size:10px;font-weight:600;paint-order:stroke;stroke:#f4f1e8;stroke-width:3;stroke-linejoin:round}.route{fill:none;stroke-linecap:round;stroke-linejoin:round}.station{cursor:pointer}.station:focus circle{stroke:#0079bd;stroke-width:4}.place{font-size:13px;font-weight:700;letter-spacing:2px;fill:#89918b}.source{font-size:10px;fill:#5e6864}</style><clipPath id="frame"><rect x="35" y="320" width="1130" height="850" rx="2"/></clipPath></defs><rect width="1200" height="1500" fill="#f4f1e8"/>')
add('<text x="55" y="55" font-size="13" letter-spacing="3" font-weight="700">30DAYMAPCHALLENGE 2026 / 08 — UTOPIA</text><path d="M55 78H1145" stroke="#172326" stroke-width="3"/><text x="52" y="154" font-size="76" font-weight="900" letter-spacing="-4">WHAT IF DFW HAD</text><text x="52" y="234" font-size="76" font-weight="900" letter-spacing="-4">NYC’S SUBWAY?</text><text x="55" y="278" font-size="22" fill="#66716b">An alternate reality where the Metroplex runs on rails.</text>')
add('<g clip-path="url(#frame)"><g id="geography">')
for f in D['boundaries']:
 g=f['geometry'];polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
 for poly in polys:add('<path d="'+path(poly[0])+' Z" fill="#eae9df" fill-opacity=".45" stroke="#d9dacf" stroke-width="1" stroke-dasharray="3 5"/>')
for f in D['context']:
 kind=f['properties']['kind'];c=f['geometry']['coordinates'];add(f'<path d="{path(c)}" fill="'+('#d8e5e3' if kind=='water' else 'none')+'" stroke="'+('#d8e5e3' if kind!='road' else '#e0ded3')+f'" stroke-width="{1 if kind=="road" else 2}"/>')
add('</g><g id="existing" visibility="hidden">')
for f in D['existing']:add(f'<path class="route" d="{path(f["geometry"]["coordinates"])}" stroke="#59635f" stroke-width="3" stroke-dasharray="4 5" opacity=".7"/>')
add('</g>')
# Split each corridor into consistently ordered parallel service lanes. Every lane
# reaches the station, with a small shared approach under the interchange symbol.
edge_services=defaultdict(list)
for f in D['lines']:
 ids=f['properties']['stations']
 for a,b in zip(ids,ids[1:]):edge_services[tuple(sorted((a,b)))].append(f['properties']['id'])
for f in D['lines']:
 p=f['properties'];id=p['id'];add(f'<g class="service" data-route="{id}">')
 for a,b in zip(p['stations'],p['stations'][1:]):
  u,v=sorted((a,b));x1,y1=xy(S[u]['coordinates']);x2,y2=xy(S[v]['coordinates']);services=edge_services[(u,v)];off=(services.index(id)-(len(services)-1)/2)*5
  dx=x2-x1;dy=y2-y1;dist=math.hypot(dx,dy);ox=-dy/dist*off;oy=dx/dist*off
  # Soft parallel curve, tangent to direct geographic corridor at each endpoint.
  d=f'M{x1:.2f},{y1:.2f} C{x1+dx*.25+ox:.2f},{y1+dy*.25+oy:.2f} {x1+dx*.75+ox:.2f},{y1+dy*.75+oy:.2f} {x2:.2f},{y2:.2f}'
  add(f'<path class="route" d="{d}" stroke="#f4f1e8" stroke-width="7"/><path class="route" d="{d}" stroke="{p["color"]}" stroke-width="3.4"/>')
 add('</g>')
# Collision-aware labels; all stations receive labels at detailed zoom.
boxes=[];labels=[];major={'dallas','fw','dfw','denton','plano','mckinney','frisco','arlington','gp','mesquite','garland','love','irving','grapevine','lewisville','oakcliff','richardson'}
ordered=sorted(S.values(),key=lambda s:(s['id'] not in major,-len(s['services'])))
for s in ordered:
 x,y=xy(s['coordinates']);r=5 if len(s['services'])>1 else 3;add(f'<g class="station" tabindex="0" data-station="{s["id"]}" aria-label="{esc(s["name"])}"><title>{esc(s["name"])} · {" / ".join(s["services"])}</title><circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="white" stroke="#172326" stroke-width="1.5"/></g>')
 w=len(s['name'])*5.25;chosen=None
 for dx,dy,anchor in [(9,-8,'start'),(9,14,'start'),(-9,-8,'end'),(-9,14,'end'),(0,-15,'middle'),(0,23,'middle')]:
  xx=x+dx;yy=y+dy;left=xx-(w if anchor=='end' else w/2 if anchor=='middle' else 0);box=(left-2,yy-10,left+w+2,yy+3)
  if box[0]<38 or box[2]>1160 or box[1]<320 or box[3]>1168:continue
  if not any(box[0]<b[2] and box[2]>b[0] and box[1]<b[3] and box[3]>b[1] for b in boxes):chosen=(xx,yy,anchor,box);break
 if chosen:
  xx,yy,anchor,box=chosen;boxes.append(box);cls='label'
 else:xx,yy,anchor=x+9,y-8,'start';cls='label detail-label'
 labels.append(f'<text class="{cls}" x="{xx:.2f}" y="{yy:.2f}" text-anchor="{anchor}" data-label="{s["id"]}">{esc(s["name"])}</text>')
add('<g id="labels">'+''.join(labels)+'</g></g>')
add('<path d="M1100 350v-30m-5 8 5-8 5 8" fill="none" stroke="#65716a"/><text x="1100" y="310" text-anchor="middle" font-size="11">N</text><path d="M65 1155h175m-175-4v8m175-8v8" stroke="#65716a"/><text x="152.5" y="1145" text-anchor="middle" font-size="10">≈ 10 MILES</text>')
add('<path d="M55 1195H1145" stroke="#172326" stroke-width="2"/>')
for i,f in enumerate(D['lines']):
 p=f['properties'];x=65+(i%5)*221;y=1230+(i//5)*45
 add(f'<g class="route-key" data-select="{p["id"]}"><circle cx="{x}" cy="{y}" r="14" fill="{p["color"]}"/><text x="{x}" y="{y+5}" text-anchor="middle" style="fill:white" font-size="15" font-weight="bold">{p["id"]}</text><text x="{x+23}" y="{y+4}" font-size="13" font-weight="600">{esc(p["name"])}</text></g>')
st=D['stats'];add(f'<text x="55" y="1335" font-size="18" font-weight="700">10 services · {len(S)} real locations · {st["fictional_transfers"]} imagined interchanges</text><text x="55" y="1365" font-size="13">A geographic fiction. New York is the inspiration; this is no claim of equivalent coverage.</text><text x="55" y="1402" font-size="12" font-weight="700">Conceptual transit network. Not an existing or officially proposed transit system.</text><text class="source" x="55" y="1431">Geography: © OpenStreetMap contributors (ODbL) · US Census 2024 · Rail anchors: DART / Trinity Metro / DCTA</text><text class="source" x="55" y="1452">Source snapshots: November 2026 · Distances and alignments are conceptual · ira / 30DayMapChallenge</text></svg>')
svg=''.join(parts);(H/'poster.svg').write_text(svg.replace('class="label detail-label"','class="label detail-label" style="display:none"'))
page=(H/'template.html').read_text().replace('__SVG__',svg).replace('__DATA__',json.dumps(D,separators=(',',':')))
(H/'map.html').write_text(page)
subprocess.run(['rsvg-convert','-w','2400','-h','3000','-o',str(H/'poster.png'),str(H/'poster.svg')],check=True)
print('Rendered map.html, poster.svg, poster.png')
