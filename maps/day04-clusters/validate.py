"""Validate source evidence, projected clustering, membership geometry and final HTML."""
import csv,hashlib,json,re
from collections import Counter
from pathlib import Path
import numpy as np
from sklearn.cluster import DBSCAN
from shapely.geometry import Point,shape
from shapely.ops import transform
from clean_data import DAY,OUT,PROJECT,normalized


def validate():
 rows=list(csv.DictReader((DAY/'manhattan_halal_locations.csv').open()))
 audit=json.loads((DAY/'day04_audit.json').read_text())
 config=json.loads((DAY/'config.json').read_text())
 text=(DAY/'map.html').read_text()
 data=json.loads(re.search(r'const MAP_DATA=(.*);\nconst NS=',text)[1])
 assert len(rows)==data['total']==audit['final_unique_locations']
 assert len({r['id'] for r in rows})==len(rows)
 assert [(r['id'],float(r['latitude']),float(r['longitude']),int(r['cluster_id'])) for r in rows]==[(r['id'],float(r['latitude']),float(r['longitude']),r['cluster_id']) for r in data['points']]
 assert all(r['source_url'].startswith('https://') and r['retrieval_date'] and r['halal_evidence'] for r in rows)
 assert len({(normalized(r['name']),r['latitude'],r['longitude']) for r in rows})==len(rows)
 for r in rows:
  evidence=json.loads(r['provenance'])
  assert any(('halal' in p.get('name','').lower()) or ('halal' in p.get('tags',{}).get('name','').lower()) or p.get('tags',{}).get('diet:halal') in ('yes','only') for p in evidence)
  assert all(p.get('tags',{}).get('diet:halal')!='no' for p in evidence)
  assert 40.68<float(r['latitude'])<40.90 and -74.06<float(r['longitude'])< -73.90
 boundary=shape(json.loads((DAY/'manhattan_boundary.geojson').read_text())['features'][0]['geometry'])
 assert all(boundary.covers(Point(float(r['longitude']),float(r['latitude']))) for r in rows)
 xy=np.array([PROJECT.transform(float(r['longitude']),float(r['latitude'])) for r in rows])
 model=DBSCAN(eps=config['selected_model']['epsilon_m'],min_samples=config['selected_model']['min_samples']).fit(xy)
 old=sorted(set(model.labels_)-{-1},key=lambda k:np.mean(xy[model.labels_==k,1]));relabel={k:i for i,k in enumerate(old)}
 labels=[relabel.get(k,-1) for k in model.labels_]
 assert labels==[int(r['cluster_id']) for r in rows]
 counts=Counter(labels);stats=audit['dbscan_selected']
 assert len(counts)-(-1 in counts)==stats['clusters']==data['stats']['clusters']
 assert counts[-1]==stats['noise_locations'] and len(rows)-counts[-1]==stats['clustered_locations']
 assert round((len(rows)-counts[-1])/len(rows)*100,2)==stats['percentage_clustered']
 cluster_features=json.loads((DAY/'manhattan_halal_clusters.geojson').read_text())['features']
 for f in cluster_features:
  props=f['properties'];k=props['cluster_id'];members=[r for r in rows if int(r['cluster_id'])==k]
  assert len(members)==props['locations']==counts[k]
  assert set(props['member_ids'])=={r['id'] for r in members}
  g=transform(PROJECT.transform,shape(f['geometry']));assert g.is_valid
  assert all(g.buffer(.01).covers(Point(p)) for p,label in zip(xy,labels) if label==k)
  assert props['name']==audit['cluster_interpretation'][str(k)]['name']
 assert len(data['labels'])==5 and {f['cluster_id'] for f in data['labels']}==set(k for k,v in sorted(counts.items(),key=lambda x:(-x[1],x[0])) if k>=0 and v>=6)
 assert audit['candidate_establishments']-len(audit['excluded_records'])-audit['duplicates_removed']==len(rows)
 for field,filename in [('csv_sha256','manhattan_halal_locations.csv'),('config_sha256','config.json')]:
  assert data[field]==hashlib.sha256((DAY/filename).read_bytes()).hexdigest()
 assert data['csv_sha256']==audit['csv_sha256']==config['reviewed_dataset_sha256']
 assert len(data['points'])==121 and data['stats']['clusters']==14, 'Reviewed dataset changed; revisit labels and prose'
 for href in re.findall(r'href="([^"#]+)"',text):
  if not href.startswith(('https://','http://')):assert (DAY/href).is_file(),href
 qa={'all_points_match_dataset':True,'all_points_in_manhattan':True,'explicit_halal_evidence_all_locations':True,'no_duplicate_ids_or_exact_name_coordinates':True,'dbscan_recomputed_projected_metres':True,'all_envelopes_valid_and_cover_members':True,'statistics':stats,'locations':len(rows),'labels_match_clusters':True,'csv_sha256':data['csv_sha256'],'config_sha256':data['config_sha256'],'html_sha256':hashlib.sha256((DAY/'map.html').read_bytes()).hexdigest(),'artifact_sha256':{p:hashlib.sha256((DAY/p).read_bytes()).hexdigest() for p in ['manhattan_halal_locations.csv','manhattan_halal_clusters.geojson','manhattan_boundary.geojson','analysis.json','day04_audit.json']},'caveat':'No known duplicates after reviewed identity merges; source staleness and co-location ambiguity cannot be ruled out.'}
 (DAY/'map.qa.json').write_text(json.dumps(qa,indent=2)+'\n')
 print('Day 4 QA passed:',len(rows),'locations;',stats['clusters'],'clusters;',counts[-1],'noise')
 return qa

if __name__=='__main__':validate()
