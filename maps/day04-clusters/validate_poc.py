"""Check every embedded location and all exploratory models against the source CSV."""
import csv
import hashlib
import json
import re
import shutil
from collections import Counter
import numpy as np
from sklearn.cluster import DBSCAN
from shapely.geometry import shape, Point
from clean_data import OUT, DAY, PROJECT

rows = list(csv.DictReader((OUT/'manhattan_halal_locations.csv').open()))
text = (DAY/'poc.html').read_text()
data = json.loads(re.search(r'const DATA=(.*);\nconst NS=', text)[1])
assert len(rows) == len(data['points']) == len({r['id'] for r in rows})
boundary = shape(json.loads((OUT/'manhattan_boundary.geojson').read_text())['features'][0]['geometry'])
assert all(boundary.covers(Point(float(r['longitude']),float(r['latitude']))) for r in rows)
assert [r['id'] for r in rows] == [r['id'] for r in data['points']]
xy = np.array([PROJECT.transform(float(r['longitude']),float(r['latitude'])) for r in rows])
for key,model in data['models'].items():
    eps,minimum = map(int,key.split('-'))
    labels = DBSCAN(eps=eps,min_samples=minimum).fit_predict(xy)
    assert labels.tolist() == model['labels']
    assert model['noise']+model['clustered'] == len(rows)
    counts=Counter(int(i) for i in labels if i>=0)
    assert {g['id']:g['count'] for g in model['clusters']} == counts
    for g in model['clusters']:
        envelope=shape(g['geometry'])
        assert envelope.is_valid
        for p,k in zip(data['points'],labels):
            if k==g['id']:
                # Display simplification and 0.001-unit coordinate rounding tolerance.
                assert envelope.buffer(.02).covers(Point(p['x'],p['y']))
audit=json.loads((OUT/'day04_audit.json').read_text())
assert audit['candidate_establishments']-len(audit['excluded_records'])-audit['duplicates_removed']==len(rows)
for name in ['manhattan_halal_locations.csv','dbscan_parameter_sweep.csv','day04_audit.json','manhattan_boundary.geojson']:
    shutil.copyfile(OUT/name,DAY/name)
qa={'locations':len(rows),'models_recomputed':len(data['models']),'all_points_inside_manhattan':True,'all_hulls_cover_members':True,'all_model_counts_match':True,'csv_sha256':hashlib.sha256((OUT/'manhattan_halal_locations.csv').read_bytes()).hexdigest(),'stage':'Exploratory comparison; default matches the reviewed final model'}
(DAY/'poc.qa.json').write_text(json.dumps(qa,indent=2)+'\n')
print(json.dumps(qa,indent=2))
