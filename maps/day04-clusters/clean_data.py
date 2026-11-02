"""Normalize, collapse inspection observations, spatially filter, audit and deduplicate."""
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from pyproj import Transformer
from shapely.geometry import Point, shape
from collect_data import DAY, ROOT, CACHE

OUT = ROOT / 'data/processed/day04-clusters'
PROJECT = Transformer.from_crs('EPSG:4326', 'EPSG:32618', always_xy=True)


def normalized(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().lower()
    value = value.replace('&', 'and')
    for before, after in [('avenue', 'ave'), ('street', 'st'), ('west', 'w'), ('east', 'e')]:
        value = re.sub(r'\b' + before + r'\b', after, value)
    return re.sub(r'[^a-z0-9]', '', value)


def write_csv(path, records):
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]))
        w.writeheader()
        w.writerows(records)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((DAY / 'source-manifest.json').read_text())
    boundaries = json.loads((CACHE / 'boroughs.geojson').read_text())
    boundary = next(f for f in boundaries['features'] if f['properties']['boroname'] == 'Manhattan')
    geom = shape(boundary['geometry'])
    neighborhoods = [(f['properties']['ntaname'], shape(f['geometry'])) for f in
        json.loads((CACHE / 'neighborhoods.geojson').read_text())['features']
        if f['properties'].get('boroname') == 'Manhattan']
    (OUT / 'manhattan_boundary.geojson').write_text(json.dumps({'type': 'FeatureCollection', 'features': [boundary]}))
    inspections = json.loads((CACHE / 'inspections.json').read_text())
    assert isinstance(inspections, list) and len(inspections) < 50000, 'API error or pagination required'
    groups = defaultdict(list)
    for r in inspections:
        groups[r['camis']].append(r)
    records, exclusions, merges = [], [], []
    review_decisions = json.loads((DAY / 'record-review.json').read_text())
    for camis, rows in sorted(groups.items()):
        # Most recent observation; deterministic tiebreak, no selection by geography.
        r = max(rows, key=lambda x: (x.get('inspection_date', ''), json.dumps(x, sort_keys=True)))
        records.append(dict(id='nyc-' + camis, name=r['dba'],
            address=' '.join([r.get('building', ''), r.get('street', ''), r.get('zipcode', '')]).strip(),
            latitude=r.get('latitude', ''), longitude=r.get('longitude', ''), category='food establishment',
            source='NYC DOHMH', source_url='https://data.cityofnewyork.us/resource/43nn-pn8j.json?camis=' + camis,
            source_name='DOHMH New York City Restaurant Inspection Results',
            retrieval_date=manifest['inspections.json']['retrieval_date'], halal_evidence='business_name_explicit',
            borough='Manhattan', neighborhood='', cluster_id='', osm_id='',
            notes='Halal in registered business name; not independently certified. Latest inspection: ' + r.get('inspection_date', '')[:10],
            provenance=json.dumps([{'source': 'NYC DOHMH', 'id': camis, 'name': r['dba'], 'observation_count': len(rows)}])))
    osm = json.loads((CACHE / 'osm-candidates.json').read_text())
    for r in osm:
        t = r['tags']
        oid = f'{r["type"]}/{r["id"]}'
        record_id = 'osm-' + oid.replace('/', '-')
        reason = None
        if t.get('diet:halal') == 'no':
            reason = 'explicit_halal_no'
        elif any(k.startswith(('disused:', 'abandoned:', 'demolished:')) for k in t) or t.get('disused') == 'yes':
            reason = 'inactive_osm_feature'
        elif t.get('amenity') not in ('restaurant', 'fast_food', 'cafe', 'food_court', 'ice_cream') and t.get('shop') not in ('deli', 'convenience', 'butcher', 'supermarket', 'food') and t.get('street_vendor') != 'food':
            reason = 'not_identified_food_business'
        if record_id in review_decisions['exclude']:
            reason = 'uncertain_operating_status'
        if reason:
            exclusions.append({'id': record_id, 'name': t.get('name', ''), 'reason': reason})
            continue
        records.append(dict(id='osm-' + oid.replace('/', '-'), name=t.get('name') or 'Unnamed halal food establishment (' + oid + ')',
            address=' '.join(t.get(k, '') for k in ['addr:housenumber', 'addr:street', 'addr:postcode']).strip(),
            latitude=r['lat'], longitude=r['lon'], category=t.get('amenity') or t.get('shop') or 'street food',
            source='OpenStreetMap', source_url='https://www.openstreetmap.org/' + oid, source_name='OpenStreetMap via Geofabrik',
            retrieval_date=manifest['new-york-261101.osm.pbf']['retrieval_date'],
            halal_evidence='osm_diet_halal' if t.get('diet:halal') in ('yes', 'only') else 'business_name_explicit',
            borough='Manhattan', neighborhood='', cluster_id='', osm_id=oid,
            notes='diet:halal=' + t.get('diet:halal', 'not tagged') + '; mapped position, not independently verified',
            provenance=json.dumps([{'source': 'OpenStreetMap', 'id': oid, 'tags': t}])) )
    for r in records:
        r['name'] = ' '.join(r['name'].split())
        r['address'] = ' '.join(r['address'].split())
        r['normalized_name'] = normalized(r['name'])
        r['normalized_address'] = normalized(r['address'])
        if '1900-01-01' in r['notes']:
            r['notes'] = r['notes'].replace('Latest inspection: 1900-01-01', 'No inspection date available (1900 sentinel)')
        provenance = json.loads(r['provenance'])
        for p in provenance:
            p.update(source_url=r['source_url'], retrieval_date=r['retrieval_date'],
                     source_name=r['source_name'], halal_evidence=r['halal_evidence'])
        r['provenance'] = json.dumps(provenance)
    eligible = []
    for r in records:
        try:
            lat, lon = float(r['latitude']), float(r['longitude'])
            if not (40 < lat < 42 and -75 < lon < -73):
                raise ValueError()
        except (ValueError, TypeError):
            exclusions.append({'id': r['id'], 'name': r['name'], 'reason': 'no_usable_coordinates'})
            continue
        if not geom.covers(Point(lon, lat)):
            exclusions.append({'id': r['id'], 'name': r['name'], 'reason': 'outside_manhattan'})
            continue
        r.update(latitude=lat, longitude=lon)
        r['neighborhood'] = next((name for name, area in neighborhoods if area.covers(Point(lon,lat))), '')
        eligible.append(r)
    unique = []
    # Explicit reviewed identity merges are applied before generic matching.
    def merge_into(target, incoming):
        for k in ('source', 'source_url', 'source_name', 'halal_evidence', 'osm_id'):
            target[k] = ' | '.join(dict.fromkeys(filter(None, (target[k] + ' | ' + incoming[k]).split(' | '))))
        target['provenance'] = json.dumps(json.loads(target['provenance']) + json.loads(incoming['provenance']))
    by_id = {r['id']:r for r in eligible}
    removed = set()
    for incoming_id, decision in review_decisions['merges'].items():
        if incoming_id in by_id and decision['into'] in by_id:
            merge_into(by_id[decision['into']], by_id[incoming_id])
            removed.add(incoming_id)
            merges.append({'kept_id': decision['into'], 'merged_id': incoming_id, 'rule': 'reviewed_identity', 'reason': decision['reason']})
    eligible = [r for r in eligible if r['id'] not in removed]
    for r in sorted(eligible, key=lambda x: x['id']):
        x, y = PROJECT.transform(r['longitude'], r['latitude'])
        match = None
        for q in unique:
            a, b = PROJECT.transform(q['longitude'], q['latitude'])
            distance = ((x-a)**2 + (y-b)**2)**0.5
            same_name = normalized(q['name']) == normalized(r['name'])
            similar_name = SequenceMatcher(None, normalized(q['name']), normalized(r['name'])).ratio() >= .88
            same_address = bool(r['address'] and q['address'] and normalized(r['address']) == normalized(q['address']))
            if distance <= 60 and (same_name or (same_address and similar_name)):
                match = q
                break
        if match:
            merges.append({'kept_id': match['id'], 'merged_id': r['id'], 'name': r['name'], 'distance_m': round(distance, 2), 'rule': 'within_60m_and_same_normalized_name_or_same_address_similar_name'})
            merge_into(match, r)
        else:
            unique.append(r)
    # Flag unresolved close pairs for review rather than silently over-merging carts.
    review = []
    for i, r in enumerate(unique):
        x, y = PROJECT.transform(r['longitude'], r['latitude'])
        for q in unique[:i]:
            a, b = PROJECT.transform(q['longitude'], q['latitude'])
            d = ((x-a)**2+(y-b)**2)**.5
            if d < 60:
                review.append({'ids': [r['id'], q['id']], 'names': [r['name'], q['name']], 'distance_m': round(d, 2)})
    write_csv(OUT / 'manhattan_halal_locations.csv', unique)
    source_dates = sorted({r['inspection_date'][:10] for r in inspections if r.get('inspection_date', '')[:4] > '1900'})
    record_dates = sorted({r['record_date'] for r in inspections if r.get('record_date')})
    coverage = {'osm_snapshot_utc': '2026-11-01T21:21:36Z',
                'nyc_record_dates': [record_dates[0], record_dates[-1]],
                'nyc_non_sentinel_inspection_dates': [source_dates[0], source_dates[-1]],
                'neighborhood_reference_year': 2020}
    audit = dict(source_coverage=coverage, source_counts={'osm_bbox_candidates': len(osm), 'nyc_inspection_rows_citywide': len(inspections), 'nyc_unique_ids_citywide': len(groups)},
        raw_records=len(osm)+len(inspections), repeated_inspection_rows_removed=len(inspections)-len(groups),
        candidate_establishments=len(osm)+len(groups), duplicates_removed=len(merges), duplicate_merges=merges,
        excluded_records=exclusions, exclusion_counts=dict(Counter(x['reason'] for x in exclusions)),
        final_unique_locations=len(unique), unresolved_close_pairs=review,
        crs='EPSG:32618 / WGS 84 UTM zone 18N; metres',
        scope='Identifiable halal food locations compiled from public sources. Not a census.',
        geocoding='None: original NYC coordinates and OSM nodes/way representative points.')
    assert audit['candidate_establishments'] - len(exclusions) - len(merges) == len(unique)
    (OUT / 'day04_audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    print(json.dumps({k:v for k,v in audit.items() if k not in ('excluded_records', 'duplicate_merges', 'unresolved_close_pairs')}, indent=2))
    print('Review nearby pairs:', json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
