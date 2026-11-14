"""Bounded adsb.lol US survey using fully covering 5-degree request tiles."""
import argparse
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point, box
from pyproj import Geod

from fetch_aircraft import CACHE
from compare_sources import download, normalize

GEOD = Geod(ellps='WGS84')


def plan():
    states = gpd.read_file('zip://' + str(CACHE / 'states-2025.zip')).to_crs(4326)
    states = states[~states.STUSPS.isin(['PR', 'VI', 'GU', 'MP', 'AS'])]
    tiles = []
    for south in range(15, 75, 5):
        for west in range(-180, 180, 5):
            cell = box(west, south, west + 5, south + 5)
            intersecting = states[states.intersects(cell)]
            if intersecting.empty:
                continue
            lon, lat = west + 2.5, south + 2.5
            radius = math.ceil(max(GEOD.inv(lon, lat, x, y)[2] for x, y in cell.exterior.coords) / 1852) + 2
            assert radius <= 250
            tiles.append({'key': f'{south}_{west}', 'bounds': [west, south, west + 5, south + 5],
                          'center': [lon, lat], 'radius_nm': radius,
                          'states': sorted(intersecting.STUSPS)})
    return states, tiles


def build(directory, states, manifest):
    records = {}
    failures = []
    excluded = {'outside_owning_tile': 0, 'outside_US': 0, 'invalid_id_or_coordinates': 0,
                'stale_position': 0, 'surface_or_obstacle': 0, 'unknown_ground_state': 0,
                'duplicate_ids': 0}
    times = []
    import re
    for key, entry in manifest['requests'].items():
        if entry['status'] != 'complete':
            failures.append(key)
            continue
        data = json.loads((directory / entry['file']).read_text())
        stamp, rows = normalize(data, 'adsblol')
        times.append(stamp)
        west, south, east, north = entry['bounds']
        candidates = states[states.STUSPS.isin(entry['states'])]
        for raw, r in zip(data['ac'], rows):
            if (not isinstance(r['id'], str) or not re.fullmatch('[0-9a-fA-F]{6}', r['id'])
                    or not all(isinstance(r[k], (float, int)) and math.isfinite(r[k]) for k in ('lat', 'lon'))
                    or not (-90 <= r['lat'] <= 90 and -180 <= r['lon'] <= 180)):
                excluded['invalid_id_or_coordinates'] += 1
                continue
            if not west <= r['lon'] < east or not south <= r['lat'] < north:
                excluded['outside_owning_tile'] += 1
                continue
            if r['age'] is None or not 0 <= r['age'] <= 60:
                excluded['stale_position'] += 1
                continue
            if r['vehicle']:
                excluded['surface_or_obstacle'] += 1
                continue
            point = Point(r['lon'], r['lat'])
            hits = candidates[candidates.covers(point)]
            if hits.empty:
                excluded['outside_US'] += 1
                continue
            if r['ground'] is None:
                excluded['unknown_ground_state'] += 1
            identity = r['id'].lower()
            record = {'icao24': identity, 'longitude': r['lon'], 'latitude': r['lat'],
                      'timestamp': stamp, 'position_timestamp': stamp - r['age'],
                      'on_ground': r['ground'], 'state': sorted(hits.STUSPS)[0],
                      'callsign': (raw.get('flight') or '').strip() or None,
                      'baro_altitude_ft': raw.get('alt_baro'), 'velocity_knots': raw.get('gs'),
                      'heading': raw.get('track') or raw.get('true_heading'),
                      'aircraft_type': raw.get('t'), 'category': raw.get('category'),
                      'position_source': raw.get('type'), 'source_tile': key}
            if identity in records:
                excluded['duplicate_ids'] += 1
                if records[identity]['position_timestamp'] >= record['position_timestamp']:
                    continue
            records[identity] = record
    rows = sorted(records.values(), key=lambda r: r['icao24'])
    summary = {'planned_tiles': len(manifest['plan']), 'complete_tiles': len(times),
               'failed_tiles': failures, 'distinct_fresh_observations': len(rows),
               'ground': sum(r['on_ground'] is True for r in rows),
               'airborne': sum(r['on_ground'] is False for r in rows),
               'unknown_state': sum(r['on_ground'] is None for r in rows),
               'source_time_start': min(times) if times else None,
               'source_time_end': max(times) if times else None, 'exclusions': excluded,
               'states': {code: {'observations': sum(r['state'] == code for r in rows),
                                 'ground': sum(r['state'] == code and r['on_ground'] is True for r in rows)}
                          for code in sorted(states.STUSPS)}}
    (directory / 'observations.json').write_text(json.dumps({'metadata': summary, 'observations': rows}, separators=(',', ':')) + '\n')
    (directory / 'qa.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'states'}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--build-only', action='store_true')
    args = parser.parse_args()
    states, tiles = plan()
    directory = args.resume or CACHE / ('adsblol-us-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / 'collection.json'
    manifest = json.loads(path.read_text()) if path.exists() else {
        'source': 'adsb.lol contributors', 'license': 'ODbL-1.0', 'plan': tiles,
        'warning': 'Sequential survey, not a simultaneous national snapshot. No inference about restriction impact.',
        'requests': {}}
    path.write_text(json.dumps(manifest, indent=2) + '\n')
    if not args.build_only:
        failures = 0
        for i, tile in enumerate(tiles):
            key = tile['key']
            if manifest['requests'].get(key, {}).get('status') == 'complete':
                continue
            lon, lat = tile['center']
            url = f'https://api.adsb.lol/v2/point/{lat}/{lon}/{tile["radius_nm"]}'
            entry = dict(tile)
            try:
                data, meta = download(url, directory / f'{key}.json')
                stamp, rows = normalize(data, 'adsblol')
                if abs(time.time() - stamp) > 120:
                    raise ValueError('Source snapshot more than 120 seconds from retrieval time')
                entry.update(meta, status='complete', snapshot_epoch=stamp, returned_rows=len(rows))
                failures = 0
                print(f'{i + 1}/{len(tiles)} {key}: {len(rows)} raw rows', flush=True)
            except (subprocess.CalledProcessError, ValueError, KeyError, TypeError) as error:
                entry.update(status='failed', error=str(error))
                failures += 1
                print(f'{key}: FAILED {error}', flush=True)
            manifest['requests'][key] = entry
            path.write_text(json.dumps(manifest, indent=2) + '\n')
            if failures >= 3:
                break
            time.sleep(0.25)
    build(directory, states, manifest)
    print(f'Cache: {directory}', flush=True)


if __name__ == '__main__':
    import subprocess
    main()
