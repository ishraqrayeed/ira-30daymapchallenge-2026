"""Sensitivity analysis, post-model interpretation, and reproducible cluster geometry."""
import csv,json,hashlib
from collections import Counter
import numpy as np
from sklearn.cluster import DBSCAN,HDBSCAN
from shapely import concave_hull
from shapely.geometry import Point,MultiPoint,shape,mapping
from shapely.ops import transform,unary_union
from pyproj import Transformer
from clean_data import OUT,DAY,PROJECT,write_csv

LABELS={0:'Civic Center / Chinatown',1:'East Village / Lower East Side',2:'Greenwich Village',3:'Kips Bay / Gramercy',4:'Turtle Bay / Murray Hill',5:'Midtown West / Chelsea',6:'Sixth Avenue / Midtown',7:'Midtown East',8:'Lenox Hill / Sutton Place',9:'Upper East Side / First Avenue',10:'Yorkville / Carnegie Hill',11:'East Harlem South',12:'Harlem South',13:'Morningside Heights / Broadway'}

def run():
 reviewed = json.loads((DAY/'config.json').read_text())
 if hashlib.sha256((OUT/'manhattan_halal_locations.csv').read_bytes()).hexdigest() != reviewed['reviewed_dataset_sha256']:
  raise ValueError('Processed dataset changed: review source identities, model and geographic labels before rendering')
 rows=list(csv.DictReader((OUT/'manhattan_halal_locations.csv').open()))
 xy=np.array([PROJECT.transform(float(r['longitude']),float(r['latitude'])) for r in rows])
 epsilon=reviewed['selected_model']['epsilon_m'];minimum=reviewed['selected_model']['min_samples']
 # CSV IDs are relabeled south-to-north by cluster.py, not sklearn's traversal order.
 ids=np.array([int(r['cluster_id']) for r in rows])
 checks={}
 for title,mask in {'all_sources':[True]*len(rows),'osm_only':['OpenStreetMap' in r['source'] for r in rows],'explicit_diet_tag_only':['osm_diet_halal' in r['halal_evidence'] for r in rows],'food_service_only':[r['category'] not in ('convenience','butcher','supermarket','deli','food') for r in rows]}.items():
  mask=np.array(mask);labels=DBSCAN(eps=epsilon,min_samples=minimum).fit_predict(xy[mask]);counts=Counter(int(k) for k in labels if k>=0)
  checks[title]={'locations':int(sum(mask)),'clusters':len(counts),'clustered':int(sum(labels>=0)),'noise':int(sum(labels<0)),'cluster_sizes':sorted(counts.values(),reverse=True)}
 hdb=HDBSCAN(min_cluster_size=minimum,min_samples=minimum,copy=True,metric='euclidean').fit_predict(xy)
 hcounts=Counter(int(k) for k in hdb if k>=0)
 hresult={'implementation':'sklearn.cluster.HDBSCAN','min_cluster_size':minimum,'min_samples':minimum,'cluster_selection_method':'eom','clusters':len(hcounts),'noise':int(sum(hdb<0)),'cluster_sizes':sorted(hcounts.values(),reverse=True)}
 stability=[]
 for eps,alternative_minimum in [(350,3),(450,4),(450,5),(550,3)]:
  labels=DBSCAN(eps=eps,min_samples=alternative_minimum).fit_predict(xy)
  matches={}
  for k in sorted(set(ids)-{-1}):
   members=set(np.where(ids==k)[0]);others=[set(np.where(labels==j)[0]) for j in set(labels)-{-1}]
   matches[str(k)]=round(max((len(members&m)/len(members|m) for m in others),default=0),3)
  stability.append({'epsilon_m':eps,'min_samples':alternative_minimum,'best_membership_jaccard':matches})
 boundary=transform(PROJECT.transform,shape(json.loads((OUT/'manhattan_boundary.geojson').read_text())['features'][0]['geometry']))
 inverse=Transformer.from_crs('EPSG:32618','EPSG:4326',always_xy=True)
 features=[];geometry_checks=[]
 for k in sorted(set(ids)-{-1}):
  members=[r for r in rows if int(r['cluster_id'])==k];points=MultiPoint(xy[ids==k]);centroid=points.centroid
  assert len(members)>=minimum
  hull=concave_hull(points,ratio=.35,allow_holes=False)
  support=unary_union([p.buffer(225) for p in points.geoms])
  envelope=hull.buffer(140).intersection(support).intersection(boundary)
  assert envelope.is_valid and all(envelope.buffer(.01).covers(p) for p in points.geoms)
  nta=Counter(r['neighborhood'] for r in members)
  props={'cluster_id':int(k),'name':LABELS[int(k)],'locations':len(members),'neighborhood_membership':dict(nta),'centroid':list(inverse.transform(centroid.x,centroid.y)),'member_ids':[r['id'] for r in members]}
  features.append({'type':'Feature','properties':props,'geometry':mapping(transform(inverse.transform,envelope))})
  geometry_checks.append({'cluster_id':int(k),'concave_area_m2':hull.area,'convex_area_m2':points.convex_hull.area,'final_envelope_area_m2':envelope.area,'all_members_covered':True,'nta_counts':dict(nta)})
 geo={'type':'FeatureCollection','features':features}
 (OUT/'manhattan_halal_clusters.geojson').write_text(json.dumps(geo,separators=(',',':'))+'\n')
 pointgeo={'type':'FeatureCollection','features':[{'type':'Feature','properties':r,'geometry':{'type':'Point','coordinates':[float(r['longitude']),float(r['latitude'])]}} for r in rows]}
 (OUT/'manhattan_halal_locations.geojson').write_text(json.dumps(pointgeo,separators=(',',':'))+'\n')
 decision={'selected':{'epsilon_m':epsilon,'min_samples':minimum,'crs':'EPSG:32618','units':'metres'},'rationale':'450 m retains the reviewed neighborhood-scale distance. The user selected minimum 3 to include small concentrations, rather than requiring five locations in a core neighborhood. This includes trios and more small groups. The unchanged source dataset gives 14 clusters at this setting; no target cluster count was imposed. The previous minimum 5 produced 6 clusters. Smaller groups are threshold-sensitive; geographic names were reviewed again after recomputing memberships.','source_sensitivity':checks,'parameter_sensitivity':stability,'hdbscan':hresult,'hdbscan_decision':'Retain DBSCAN for an explicit common spatial scale and visually explainable rule. HDBSCAN is a sensitivity check, not ground truth; see its cluster sizes and noise in this report.','geometry':{'method':'GEOS concave hull ratio .35; buffer 140m; intersect union of member 225m buffers and Manhattan boundary. No simplification in export.','qa':geometry_checks},'interpretation':{str(f['properties']['cluster_id']):f['properties'] for f in features},'caveat':'Descriptive concentrations in this source sample, not statistically significant clusters or a census of halal food.'}
 (OUT/'analysis.json').write_text(json.dumps(decision,indent=2)+'\n')
 audit=json.loads((OUT/'day04_audit.json').read_text());audit.update(analysis_status='Descriptive source-sample clustering supports visualization with explicit coverage limitations',cluster_interpretation=decision['interpretation'],source_sensitivity=checks,final_source_counts=dict(Counter(r['source'] for r in rows)),hdbscan=hresult,geometry=decision['geometry'],csv_sha256=hashlib.sha256((OUT/'manhattan_halal_locations.csv').read_bytes()).hexdigest())
 (OUT/'day04_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
 print(json.dumps({'source_sensitivity':checks,'hdbscan':hresult,'parameter_sensitivity':stability},indent=2))

if __name__=='__main__':run()
