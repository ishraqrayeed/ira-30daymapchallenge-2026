"""Render an analysis preview. This is deliberately not the final poster."""
import csv
import json
from pathlib import Path
from collections import Counter
import numpy as np
from sklearn.cluster import DBSCAN
from shapely.geometry import shape, mapping, MultiPoint, Point
from shapely.ops import transform, unary_union
from pyproj import Transformer
from clean_data import OUT, PROJECT, DAY


def main():
    rows = list(csv.DictReader((OUT / 'manhattan_halal_locations.csv').open()))
    if len(rows) < 31:
        raise ValueError('Insufficient locations: no visualization')
    xy = np.array([PROJECT.transform(float(r['longitude']), float(r['latitude'])) for r in rows])
    boundaries = json.loads((OUT / 'manhattan_boundary.geojson').read_text())
    boundary = transform(PROJECT.transform, shape(boundaries['features'][0]['geometry']))
    minx, miny, maxx, maxy = boundary.bounds
    # Fixed geometric projection preserves scale in both axes.
    scale = 850 / (maxy-miny)
    def display(x,y,z=None):
        return (x-minx)*scale+70, 915-(y-miny)*scale
    land = transform(display, boundary.simplify(15))
    points = [dict(r, x=round(display(*p)[0],3), y=round(display(*p)[1],3)) for r,p in zip(rows,xy)]
    models = {}
    config = json.loads((DAY / 'config.json').read_text())
    for eps in config['epsilon_grid_m']:
        for minimum in config['min_samples_grid']:
            labels = DBSCAN(eps=eps, min_samples=minimum).fit_predict(xy)
            counts = Counter(int(k) for k in labels if k >= 0)
            clusters = []
            for k in counts:
                members = [Point(p) for p,label in zip(xy,labels) if label == k]
                # Member buffers produce local envelopes without huge convex bridges.
                envelope = unary_union([p.buffer(min(eps/2,150)) for p in members]).intersection(boundary)
                center = MultiPoint(members).centroid
                clusters.append(dict(id=k, count=counts[k], geometry=mapping(transform(display,envelope.simplify(8))), center=display(center.x,center.y)))
            models[f'{eps}-{minimum}'] = dict(labels=[int(k) for k in labels], clusters=clusters,
                noise=sum(labels < 0).item(), clustered=sum(labels >= 0).item())
    data = dict(points=points, land=mapping(land), models=models, audit=json.loads((OUT / 'day04_audit.json').read_text()))
    template = (DAY / 'poc-template.html').read_text()
    (DAY / 'poc.html').write_text(template.replace('__DATA__',json.dumps(data,separators=(',',':')).replace('</','<\\/')))
    print('Analysis preview:', DAY / 'poc.html')


if __name__ == '__main__':
    main()
