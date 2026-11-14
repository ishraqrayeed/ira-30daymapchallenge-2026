"""Cache a sequential state survey, not a simultaneous national snapshot."""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import geopandas as gpd
from shapely.geometry import Point, box
from fetch_aircraft import CACHE, URL, register, validate


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--states', nargs='+', help='Postal codes; default all 50 + DC')
    parser.add_argument('--resume', type=Path, help='Existing collection directory')
    args = parser.parse_args()
    boundaries = CACHE / 'states-2025.zip'
    if not boundaries.exists():
        parser.error('Download Census cb_2025_us_state_500k.zip into states-2025.zip first')
    register(boundaries, 'https://www2.census.gov/geo/tiger/GENZ2025/shp/cb_2025_us_state_500k.zip')
    states = gpd.read_file('zip://' + str(boundaries)).to_crs(4326)
    states = states[~states.STUSPS.isin(['PR', 'VI', 'GU', 'MP', 'AS'])]
    if args.states:
        unknown = set(args.states) - set(states.STUSPS)
        if unknown:
            parser.error(f'Unknown state codes: {sorted(unknown)}')
        states = states[states.STUSPS.isin(args.states)]
    directory = args.resume or CACHE / ('states-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    directory.mkdir(parents=True, exist_ok=True)
    manifest_path = directory / 'collection.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        'started_utc': now(), 'kind': 'sequential state survey',
        'warning': 'Different source times; overlapping request rectangles. Never sum raw rectangles as a US snapshot.',
        'boundary_source': 'Census 2025 cartographic states 1:500,000; WGS84 reprojection',
        'requested_states': sorted(states.STUSPS), 'requests': {},
    }
    failures = 0
    for _, state in states.sort_values('STUSPS').iterrows():
        geometry = state.geometry
        parts = [('main', geometry)]
        if state.STUSPS == 'AK':
            parts = [('west', geometry.intersection(box(-180, 0, 0, 90))),
                     ('east', geometry.intersection(box(0, 0, 180, 90)))]
        for part, shape in parts:
            key = f'{state.STUSPS}-{part}'
            if manifest['requests'].get(key, {}).get('status') == 'complete':
                continue
            west, south, east, north = shape.bounds
            bounds = { 'lamin': south, 'lomin': west, 'lamax': north, 'lomax': east }
            url = URL + '?' + urlencode(bounds)
            partial = directory / f'{key}.partial'
            entry = {'state': state.STUSPS, 'name': state.NAME, 'url': url,
                     'bounds': bounds, 'requested_utc': now()}
            try:
                subprocess.run(['curl', '--max-time', '45', '-fsSL', url, '-o', str(partial)], check=True)
                # An API null states value means no observations, not a failed transfer.
                payload = json.loads(partial.read_text())
                if payload.get('states', 'missing') is None and isinstance(payload.get('time'), int):
                    payload['states'] = []
                    check = directory / f'{key}.validate.json'
                    check.write_text(json.dumps(payload))
                else:
                    check = partial
                data, qa = validate(check)
                if check != partial:
                    check.unlink()
                destination = directory / f'{key}.json'
                partial.replace(destination)
                accepted = [s for s in data['states'] if s[5] is not None and s[6] is not None
                            and shape.covers(Point(s[5], s[6]))]
                filtered = directory / f'{key}.state.json'
                filtered.write_text(json.dumps({'time': data['time'], 'state': state.STUSPS,
                    'scope': 'state polygon filtered; one part of sequential survey',
                    'states': accepted}, separators=(',', ':')) + '\n')
                qa['rectangle_rows'] = qa.pop('global_rows')
                qa['state_polygon_rows'] = len(accepted)
                qa['state_polygon_ground_rows'] = sum(s[8] is True for s in accepted)
                entry.update(status='complete', snapshot_utc=qa['snapshot_utc'], qa=qa,
                    source_file=destination.name, filtered_file=filtered.name,
                    sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                    bytes=destination.stat().st_size)
                failures = 0
                print(f'{key}: {len(accepted)} in state / {len(data["states"])} in rectangle at {qa["snapshot_utc"]}', flush=True)
            except (subprocess.CalledProcessError, ValueError, KeyError, IndexError, TypeError) as error:
                entry.update(status='failed', error=str(error))
                failures += 1
                print(f'{key}: FAILED {error}', flush=True)
            entry['finished_utc'] = now()
            manifest['requests'][key] = entry
            manifest['updated_utc'] = now()
            manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
            if failures >= 3:
                raise SystemExit('Stopped after 3 consecutive failures; resume later')
    print(f'Cache: {directory}', flush=True)
    if any(r['status'] != 'complete' for r in manifest['requests'].values()):
        raise SystemExit('Collection has failed requests; see collection.json')


if __name__ == '__main__':
    main()
