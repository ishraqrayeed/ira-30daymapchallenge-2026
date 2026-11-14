"""Paced, resumable adsb.lol samples within 10 NM of 95 selected airports."""
import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from fetch_aircraft import CACHE
from compare_sources import normalize
from pyproj import Geod


def groups(airports):
    """Greedy coverage of airport centers plus a 15 km margin inside 250 NM."""
    geod = Geod(ellps='WGS84')
    remaining = {a['ident']: a for a in airports}
    planned = []
    while remaining:
        candidates = []
        for center in airports:
            covered = [code for code, a in remaining.items()
                       if geod.inv(float(center['longitude_deg']), float(center['latitude_deg']),
                                   float(a['longitude_deg']), float(a['latitude_deg']))[2] + 15000 <= 250 * 1852]
            candidates.append((len(covered), center['ident'], center, covered))
        _, _, center, covered = max(candidates, key=lambda c: (c[0], c[1]))
        assert covered
        planned.append({**center, 'covers_airports': sorted(covered)})
        for code in covered:
            remaining.pop(code)
    return planned


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--pause', type=float, default=7.0)
    parser.add_argument('--grouped', action='store_true', help='Share 250 NM requests across nearby major airports')
    args = parser.parse_args()
    if args.pause < 2:
        parser.error('Use at least two seconds between requests')
    airports = json.loads((CACHE / 'major-airports.json').read_text())
    planned = groups(airports) if args.grouped else [{**a, 'covers_airports': [a['ident']]} for a in airports]
    radius = 250 if args.grouped else 10
    directory = args.resume or CACHE / (('majorregions-' if args.grouped else 'major-') + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / 'collection.json'
    manifest = json.loads(path.read_text()) if path.exists() else {
        'source': 'adsb.lol contributors', 'license': 'ODbL-1.0', 'radius_nm': radius,
        'selection': 'OurAirports US large_airport and scheduled_service=yes',
        'planned_airports': [a['ident'] for a in airports],
        'warning': 'Sequential airport samples. Raw radius counts are not counts assigned to airport boundaries.',
        'requests': {}}
    path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'{len(planned)} requests cover {len(airports)} major airports', flush=True)
    for i, airport in enumerate(planned):
        code = airport['ident']
        if manifest['requests'].get(code, {}).get('status') == 'complete':
            continue
        url = f'https://api.adsb.lol/v2/point/{airport["latitude_deg"]}/{airport["longitude_deg"]}/{radius}'
        partial = directory / f'{code}.partial'
        headers = directory / f'{code}.headers'
        entry = {'url': url, 'covers_airports': airport['covers_airports'],
                 'requested_utc': datetime.now(timezone.utc).isoformat()}
        response = subprocess.run(['curl', '--max-time', '45', '-sS', '-D', str(headers),
                                   '-w', '%{http_code}', url, '-o', str(partial)], capture_output=True, text=True)
        status = response.stdout[-3:]
        entry['http_status'] = status
        try:
            if response.returncode or status != '200':
                raise ValueError(f'HTTP {status}; curl {response.returncode}')
            data = json.loads(partial.read_text())
            stamp, rows = normalize(data, 'adsblol')
            if abs(time.time() - stamp) > 120:
                raise ValueError('Snapshot more than 120 seconds from retrieval')
            destination = directory / f'{code}.json'
            partial.replace(destination)
            import hashlib
            entry.update(status='complete', file=destination.name, snapshot_epoch=stamp,
                         sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                         bytes=destination.stat().st_size, raw_rows=len(rows))
            print(f'{i+1}/{len(planned)} {code}: {len(rows)} raw regional observations; covers {", ".join(airport["covers_airports"])}', flush=True)
        except (ValueError, KeyError, TypeError) as error:
            entry.update(status='failed', error=str(error))
            print(f'{code}: FAILED {error}', flush=True)
        entry['received_utc'] = datetime.now(timezone.utc).isoformat()
        manifest['requests'][code] = entry
        path.write_text(json.dumps(manifest, indent=2) + '\n')
        if entry['status'] != 'complete':
            raise SystemExit(f'Stopped on first failure; consult {headers} before resuming')
        time.sleep(args.pause)
    print('Cache:', directory, flush=True)


if __name__ == '__main__':
    main()
