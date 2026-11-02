"""Explore the entire requested parameter grid before selecting a final model."""
import argparse
import csv
import json
from collections import Counter
from statistics import median
import numpy as np
from sklearn.cluster import DBSCAN
from clean_data import OUT, DAY, PROJECT, write_csv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--epsilon', type=float)
    parser.add_argument('--min-samples', type=int)
    args = parser.parse_args()
    config = json.loads((DAY / 'config.json').read_text())
    rows = list(csv.DictReader((OUT / 'manhattan_halal_locations.csv').open()))
    xy = np.array([PROJECT.transform(float(r['longitude']), float(r['latitude'])) for r in rows])
    sweep = []
    for eps in config['epsilon_grid_m']:
        for n in config['min_samples_grid']:
            labels = DBSCAN(eps=eps, min_samples=n).fit_predict(xy)
            counts = Counter(int(x) for x in labels if x >= 0)
            clustered = sum(counts.values())
            sweep.append(dict(epsilon_m=eps, min_samples=n, clusters=len(counts),
                clustered_locations=clustered, noise_locations=len(rows)-clustered,
                percentage_clustered=round(100*clustered/len(rows), 2),
                largest_cluster_size=max(counts.values(), default=0), median_cluster_size=median(counts.values()) if counts else 0))
    write_csv(OUT / 'dbscan_parameter_sweep.csv', sweep)
    print((OUT / 'dbscan_parameter_sweep.csv').read_text())
    audit = json.loads((OUT / 'day04_audit.json').read_text())
    if len(rows) < config['minimum_dataset_size']:
        audit.update(analysis_status='STOP: insufficient defensible locations; no visualization', dbscan_selected=None)
        (OUT / 'day04_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
        return
    if args.epsilon is None or args.min_samples is None:
        print('Exploration only. Review the sweep before specifying final parameters.')
        return
    if args.epsilon not in config['epsilon_grid_m'] or args.min_samples not in config['min_samples_grid']:
        raise ValueError('Review grid expansion explicitly before selecting outside it')
    model = DBSCAN(eps=args.epsilon, min_samples=args.min_samples).fit(xy)
    # Deterministic cluster IDs ordered south to north; no hand-assigned membership.
    original = sorted(set(model.labels_) - {-1}, key=lambda k: np.mean(xy[model.labels_ == k, 1]))
    relabel = {k:i for i,k in enumerate(original)}
    for r, k in zip(rows, model.labels_):
        r['cluster_id'] = relabel.get(k, -1)
    write_csv(OUT / 'manhattan_halal_locations.csv', rows)
    counts = Counter(r['cluster_id'] for r in rows)
    audit.update(dbscan_selected={'epsilon_m': args.epsilon, 'min_samples': args.min_samples, 'metric': 'Euclidean',
        'crs': 'EPSG:32618', 'units': 'metres', 'core_locations': len(model.core_sample_indices_),
        'clusters': len(original), 'clustered_locations': len(rows)-counts[-1], 'noise_locations': counts[-1],
        'percentage_clustered': round(100*(len(rows)-counts[-1])/len(rows),2),
        'membership_counts': {str(k):v for k,v in sorted(counts.items())}}, analysis_status='Model selected; interpretation and visualization gate require review')
    (OUT / 'day04_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    for k in sorted(counts):
        members = [r for r in rows if r['cluster_id'] == k]
        print(k, counts[k], [(r['name'], r['address']) for r in members])


if __name__ == '__main__':
    main()
