"""Build a directed, contracted OSM highway graph and ordered Census state intervals.

Only source OSM node IDs create junctions. Display simplification never changes
routing weights, topology or the full-resolution geometry used for state scoring.
"""
from pathlib import Path
from collections import Counter,defaultdict
import json,gzip,hashlib,re,math,pickle,time
import numpy as np
import ijson
import geopandas as gpd
from shapely.geometry import LineString,Point,shape,mapping
from shapely.ops import unary_union
from shapely import prepare,points,covers
from shapely.strtree import STRtree
from pyproj import Geod,Transformer
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
DAY=Path(__file__).resolve().parent;CACHE=DAY.parents[1]/'data/raw/day24/highways';GEOD=Geod(ellps='WGS84')
PROJ=Transformer.from_crs(4326,5070,always_xy=True);UNPROJ=Transformer.from_crs(5070,4326,always_xy=True)
KEEP=['highway','ref','name','oneway','oneway:motor_vehicle','oneway:motorcar','junction','maxspeed','access','vehicle','motor_vehicle','motorcar','hov','access:conditional','motor_vehicle:conditional','motorcar:conditional']
def dump(path,obj):path.write_text(json.dumps(obj,separators=(',',':'))+'\n')
def polyline(c):
 out=[];previous=[0,0]
 for x,y in c:
  for k,v in enumerate([round(y*1e6),round(x*1e6)]):
   d=v-previous[k];previous[k]=v;d=~(d<<1) if d<0 else d<<1
   while d>=32:out.append(chr((32|(d&31))+63));d>>=5
   out.append(chr(d+63))
 return ''.join(out)
def permitted(t):
 for k in ['motorcar','motor_vehicle','vehicle','access']:
  if k in t:
   if t[k] in ['no','private','destination','customers','delivery','agricultural','forestry','permit']:return False
   if t[k] in ['yes','designated','permissive']:break
 if any(k in t for k in ['access:conditional','motor_vehicle:conditional','motorcar:conditional']):return False
 return t.get('hov')!='designated' and t.get('oneway') not in ['reversible','alternating']
def speed(t):
 match=re.match(r'^([0-9.]+)\s*(mph)?$',t.get('maxspeed',''))
 if match:return min(140,max(15,float(match[1])*(1.609344 if match[2] else 1)))
 return 48.28032 if t['highway'].endswith('_link') else 104.60736 if t['highway']=='motorway' else 88.51392

def load():
 manifest=json.loads((CACHE/'tiles.json').read_text());signature=hashlib.sha256((CACHE/'tiles.json').read_bytes()).hexdigest();cache=CACHE/'parsed.pkl'
 if cache.exists():
  with cache.open('rb') as f:obj=pickle.load(f)
  if obj[0]==signature:print('Using parsed source cache',flush=True);return obj[1:]
 source_states=gpd.read_file(CACHE.parent/'states-full.geojson');coverage=unary_union(source_states.geometry);prepare(coverage)
 ways={};rules={};rejected=Counter()
 for name in manifest['tiles']:
  with gzip.open(CACHE/(name+'.json.gz'),'rb') as f:
   for e in ijson.items(f,'elements.item',use_float=True):
    if e['type']=='relation':rules[e['id']]=e;continue
    if e['type']!='way' or e['id'] in ways:continue
    tags={k:v for k,v in e.get('tags',{}).items() if k in KEEP}
    if not permitted(tags):rejected['access_or_time_restricted_ways']+=1;continue
    refs=np.asarray(e['nodes'],dtype=np.int64);coords=np.asarray([[p['lon'],p['lat']] for p in e.get('geometry',[])],dtype=np.float64)
    if len(coords)!=len(refs) or len(coords)<2:rejected['missing_geometry']+=1;continue
    line=LineString(coords)
    if not coverage.intersects(line):continue
    # Do not retain an international detour or bridge disconnected portions.
    if coverage.covers(line):chunks=[(refs,coords)]
    else:
     mids=(coords[1:]+coords[:-1])/2;inside=covers(coverage,points(mids));chunks=[];start=None
     for i,good in enumerate(inside):
      if good and start is None:start=i
      if start is not None and (not good or i==len(inside)-1):
       end=i+2 if good else i+1
       if end-start>=2:chunks.append((refs[start:end],coords[start:end]))
       start=None
    if chunks:ways[e['id']]=(chunks,tags)
  print('Read',name,'→',len(ways),'distinct public US ways',flush=True)
 with cache.open('wb') as f:pickle.dump((signature,ways,rules,rejected),f,protocol=5)
 return ways,rules,rejected

def components(edges):
 ids=sorted({int(e['u']) for e in edges}|{int(e['v']) for e in edges});index={n:i for i,n in enumerate(ids)}
 a=np.fromiter((index[e['u']] for e in edges),dtype=np.int32);b=np.fromiter((index[e['v']] for e in edges),dtype=np.int32)
 graph=csr_matrix((np.ones(len(a),dtype=np.uint8),(a,b)),shape=(len(ids),len(ids)))
 count,labels=connected_components(graph,directed=True,connection='strong');best=int(np.argmax(np.bincount(labels)));chosen={ids[i] for i in np.flatnonzero(labels==best)}
 return [e for e in edges if e['u'] in chosen and e['v'] in chosen],count,len(ids)-len(chosen)

def topology(ways,rules):
 allrefs=np.concatenate([refs for chunks,_ in ways.values() for refs,_ in chunks]);unique,counts=np.unique(allrefs,return_counts=True);junctions=set(map(int,unique[counts>1]));del allrefs,unique,counts
 turns=[];stats=Counter()
 for rule in rules.values():
  t=rule.get('tags',{});members=rule.get('members',[]);via=[m for m in members if m['role']=='via'];fr=[m for m in members if m['role']=='from' and m['type']=='way'];to=[m for m in members if m['role']=='to' and m['type']=='way']
  if not fr or not to:continue
  if not any(m['ref'] in ways for m in fr):continue
  if any(k.startswith('restriction:') and k.endswith('conditional') for k in t) or 'restriction:conditional' in t:stats['conditional_turn_relations_not_modeled']+=1;continue
  if len(via)!=1 or via[0]['type']!='node':stats['via_way_or_complex_turn_relations_not_modeled']+=1;continue
  if any(s in t.get('except','').split(';') for s in ['motorcar','motor_vehicle','vehicle']):continue
  restriction=t.get('restriction:motorcar',t.get('restriction:motor_vehicle',t.get('restriction','')))
  if not restriction.startswith(('no_','only_')):continue
  node=int(via[0]['ref']);junctions.add(node)
  turns.append((node,[int(m['ref']) for m in fr],[int(m['ref']) for m in to],restriction,int(rule['id'])))
 raw=[]
 for way,(chunks,t) in ways.items():
  one=t.get('oneway:motorcar',t.get('oneway:motor_vehicle',t.get('oneway')))
  if one is None:one='yes' if t['highway']=='motorway' or t.get('junction') in ['roundabout','circular'] else 'no'
  forward=one!='-1';backward=one not in ['yes','true','1'];ref=t.get('ref','');kph=speed(t)
  for refs,c in chunks:
   cuts=[0]+[i for i in range(1,len(refs)-1) if int(refs[i]) in junctions]+[len(refs)-1]
   for a,b in zip(cuts,cuts[1:]):
    if a==b:continue
    u,v=int(refs[a]),int(refs[b]);geometry=c[a:b+1].copy()
    if not np.any(np.diff(geometry,axis=0)):continue
    if forward:raw.append(dict(u=u,v=v,c=geometry,ref=ref,kind=t['highway'],first=way,last=way,kph=kph))
    if backward:raw.append(dict(u=v,v=u,c=geometry[::-1].copy(),ref=ref,kind=t['highway'],first=way,last=way,kph=kph))
 print('Raw directed segments',len(raw),flush=True)
 raw,ncomp,dropped=components(raw);stats.update(source_strong_components=ncomp,dropped_nodes_outside_largest_scc=dropped)
 incoming=defaultdict(list);outgoing=defaultdict(list)
 for i,e in enumerate(raw):outgoing[e['u']].append(i);incoming[e['v']].append(i)
 protected={r[0] for r in turns};keep=set()
 for node,outs in outgoing.items():
  ins=incoming[node];neighbors={raw[i]['v'] for i in outs}|{raw[i]['u'] for i in ins};types={(raw[i]['ref'],raw[i]['kind'],round(raw[i]['kph'],3)) for i in outs+ins}
  if node in protected or len(neighbors)!=2 or (len(ins),len(outs)) not in [(1,1),(2,2)] or len(types)!=1:keep.add(node)
 if not keep:keep.add(min(outgoing))
 used=set();edges=[]
 for node in sorted(keep):
  for start in outgoing[node]:
   if start in used:continue
   chain=[start];used.add(start);current=raw[start]
   while current['v'] not in keep:
    options=[i for i in outgoing[current['v']] if raw[i]['v']!=current['u']]
    if len(options)!=1 or options[0] in used:break
    nxt=options[0];chain.append(nxt);used.add(nxt);current=raw[nxt]
   first,last=raw[chain[0]],raw[chain[-1]];coords=np.concatenate([raw[chain[0]]['c']]+[raw[i]['c'][1:] for i in chain[1:]])
   edges.append({**first,'v':last['v'],'last':last['last'],'c':coords})
 # Residual isolated rings are not joined to a different road to force connectivity.
 stats['residual_segments_not_contracted']=len(raw)-len(used);stats['raw_directed_segments']=len(raw);stats['contracted_edges']=len(edges)
 print('Contracted directed edges',len(edges),flush=True)
 return edges,turns,stats

def line_parts(g):
 if g.geom_type=='LineString':return [g]
 if hasattr(g,'geoms'):return [p for child in g.geoms for p in line_parts(child)]
 return []
def prepare_output(edges,turns,stats,rejected):
 states=gpd.read_file(CACHE.parent/'states-full.geojson').sort_values('STATEFP');abbreviations=states.STUSPS.tolist();shapes=list(states.geometry);tree=STRtree(shapes)
 def intervals(c):
  line=LineString(c);dist=np.maximum(0,GEOD.inv(c[:-1,0],c[:-1,1],c[1:,0],c[1:,1])[2]);cum=np.r_[0,np.cumsum(dist)];total=float(cum[-1]);total_cm=round(total*100)
  planar=np.r_[0,np.cumsum(np.linalg.norm(np.diff(c,axis=0),axis=1))];candidates=list(tree.query(line,predicate='intersects'))
  if len(candidates)==1 and shapes[candidates[0]].covers(line):return total_cm,[total_cm,int(candidates[0])]
  cuts={0.,float(planar[-1])};coverages=[]
  for index in candidates:
   for part in line_parts(line.intersection(shapes[index])):
    a,b=sorted([line.project(Point(part.coords[0])),line.project(Point(part.coords[-1]))])
    if b-a>1e-12:cuts.update([a,b]);coverages.append((a,b,int(index)))
  result=[];previous=0
  for a,b in zip(sorted(cuts),sorted(cuts)[1:]):
   mid=(a+b)/2;eligible=[idx for x,y,idx in coverages if x<=mid<=y]
   # A boundary-coincident positive-length interval gets one deterministic FIPS,
   # never two states from a zero-area border touch.
   interior=[idx for idx in eligible if shapes[idx].contains(line.interpolate(mid))];idx=min(interior or eligible,default=-1)
   end=round(float(np.interp(b,planar,cum))*100)
   if end<=previous:continue
   if result and result[-1]==idx:result[-2]=end
   else:result.extend([end,idx])
   previous=end
  if not result:result=[total_cm,-1]
  else:result[-2]=total_cm
  return total_cm,result
 ids=sorted({e['u'] for e in edges}|{e['v'] for e in edges});index={n:i for i,n in enumerate(ids)};node_coords={};geometries=[];geo_index={};rows=[];refs=[];refmap={};display=[];reverse_lookup={};edge_states=set();original_points=0;display_points=0
 for i,e in enumerate(edges):
  c=e['c'];node_coords[e['u']]=c[0].tolist();node_coords[e['v']]=c[-1].tolist();length,spans=intervals(c);original_points+=len(c)
  # Only shape/display is simplified, by at most 2 m. Weights and state spans use original nodes.
  if len(c)>2:
   x,y=PROJ.transform(c[:,0],c[:,1]);simplified=LineString(np.column_stack([x,y])).simplify(2,preserve_topology=True);sx,sy=UNPROJ.transform(*np.asarray(simplified.coords).T);draw=np.column_stack([sx,sy]);draw[0]=c[0];draw[-1]=c[-1]
  else:draw=c
  code=polyline(draw);backcode=polyline(draw[::-1]);canonical=min(code,backcode);direction=1 if code==canonical else -1
  key=(min(e['u'],e['v']),max(e['u'],e['v']),min(e['first'],e['last']),max(e['first'],e['last']),canonical)
  if key not in geo_index:geo_index[key]=len(geometries);geometries.append(canonical)
  gid=geo_index[key]
  if e['ref'] not in refmap:refmap[e['ref']]=len(refs);refs.append(e['ref'])
  row=[index[e['u']],index[e['v']],length,gid,direction,refmap[e['ref']],e['first'],e['last'],round(length/100/e['kph']*3.6,2),spans]
  rows.append(row);edge_states.update(abbreviations[spans[k]] for k in range(1,len(spans),2) if spans[k]>=0 and spans[k-1]-(spans[k-3] if k>=3 else 0)>=100)
  if direction==1:reverse_lookup[(gid,1)]=i
  else:reverse_lookup[(gid,-1)]=i
  if i%10000==0:print('Measured',i,'/',len(edges),flush=True)
 # One simplified geographic line per actual carriageway; no crossing-based unions.
 seen=set()
 for i,e in enumerate(edges):
  gid=rows[i][3]
  if gid in seen:continue
  seen.add(gid);c=e['c'];x,y=PROJ.transform(c[:,0],c[:,1]);g=LineString(np.column_stack([x,y])).simplify(100,preserve_topology=True);sx,sy=UNPROJ.transform(*np.asarray(g.coords).T);coords=[[round(float(a),5),round(float(b),5)] for a,b in zip(sx,sy)];display_points+=len(coords)
  match=re.search(r'(?:^|[; ])I[ -]?(\d{1,3}[A-Z]?)\b',e['ref']);interstate=match[1] if match else ''
  display.append({'type':'Feature','id':gid,'properties':{'g':gid,'ref':e['ref'],'shield':interstate,'kind':e['kind'],'major':bool(interstate) or e['kind']=='motorway'},'geometry':{'type':'LineString','coordinates':coords}})
 ins=defaultdict(list);outs=defaultdict(list)
 for i,e in enumerate(edges):ins[e['v']].append(i);outs[e['u']].append(i)
 prohibitions=set();applied=0;unresolved=0
 for node,fr,to,restriction,rid in turns:
  only=restriction.startswith('only_')
  incoming=[i for i in ins[node] if edges[i]['last'] in fr];outgoing=outs[node];targets=[j for j in outgoing if edges[j]['first'] in to]
  if not incoming:continue
  if not targets:unresolved+=1
  for i in incoming:
   for j in outgoing:
    is_target=j in targets
    if restriction in ['no_u_turn','only_u_turn'] and set(fr)==set(to):is_target=is_target and edges[j]['v']==edges[i]['u']
    if (only and not is_target) or (not only and is_target):prohibitions.add((i,j));applied+=1
 nodes=[[round(v*1e6) for v in node_coords[n]] for n in ids]
 obj={'version':1,'precision':6,'nodes':nodes,'geometries':geometries,'edges':rows,'refs':refs,'states':abbreviations,'state_names':states.NAME.tolist(),'turns':sorted(prohibitions),'edge_schema':['from','to','length_cm','geometry','direction','ref','first_osm_way','last_osm_way','seconds','ordered_end_cm_state_index'],'state_minimum_interval_cm':100,'state_boundary_rule':'Positive-length road intervals only; at least 1 m. Coincident borders assigned once by lowest Census FIPS. DC uncounted.'}
 raw=json.dumps(obj,separators=(',',':')).encode();compressed=gzip.compress(raw,compresslevel=9,mtime=0);(DAY/'data/graph.json.gz').write_bytes(compressed)
 d=json.dumps({'type':'FeatureCollection','features':display},separators=(',',':')).encode();(DAY/'data/highways.geojson.gz').write_bytes(gzip.compress(d,compresslevel=9,mtime=0))
 qa={**stats,**rejected,'nodes':len(nodes),'directed_edges':len(rows),'physical_geometries':len(geometries),'original_geometry_points':original_points,'display_points':display_points,'graph_gzip_bytes':len(compressed),'display_gzip_bytes':(DAY/'data/highways.geojson.gz').stat().st_size,'states_represented':sorted(edge_states-{'DC'}),'state_count':len(edge_states-{'DC'}),'applied_node_turn_prohibitions':len(prohibitions),'restriction_relations_without_retained_to_way':unresolved,'source_osm_node_junctions_only':True,'passed':len(edge_states-{'DC'})==48 and all(e[2]>0 for e in rows)}
 dump(DAY/'data/graph.qa.json',qa)
 sources={'provider':'OpenStreetMap via North America Overpass','license':'ODbL 1.0','license_url':'https://opendatacommons.org/licenses/odbl/1-0/','tiles':[json.loads((CACHE/(n+'.source.json')).read_text()) for n in json.loads((CACHE/'tiles.json').read_text())['tiles']],'graph_sha256':hashlib.sha256(compressed).hexdigest(),'state_source':json.loads((DAY/'data/census-source.json').read_text()),'limitations':['Conditional and via-way turn relations are counted but not enforced.','Time-restricted driving access and reversible/alternating roads are excluded.','This is a restricted highway model, not live navigation.','Time uses mapped maxspeed where parseable; otherwise 65 mph motorway, 55 mph trunk and 30 mph links.','Only the largest strongly connected source-node component is retained; missing links are not fabricated.','Connectivity after turn restrictions is tested separately in JavaScript.']}
 dump(DAY/'data/sources.json',sources);print(json.dumps(qa,indent=2),flush=True);assert qa['passed'],'The graph must reach all 48 states before gameplay is enabled.'
if __name__=='__main__':
 started=time.time();ways,rules,rejected=load();edges,turns,stats=topology(ways,rules);del ways;prepare_output(edges,turns,stats,rejected);from optimize_display import main as optimize;optimize();from prepare_shields import main as shields;shields();print('Seconds:',round(time.time()-started),flush=True)
