"""Compare fresh observations inside identical 100 NM airport-centered circles."""
import csv
import hashlib
import json
import math
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from pyproj import Geod
from fetch_aircraft import CACHE, URL

GEOD = Geod(ellps='WGS84')
RADIUS_M = 100 * 1852


def download(url, path):
    started = datetime.now(timezone.utc).isoformat()
    temporary = path.with_suffix('.partial')
    subprocess.run(['curl', '--max-time', '45', '-fsSL', url, '-o', str(temporary)], check=True)
    data = json.loads(temporary.read_text())
    temporary.replace(path)
    return data, {'url': url, 'file': path.name, 'requested_utc': started,
        'received_utc': datetime.now(timezone.utc).isoformat(),
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}


def normalize(data, source):
    if source == 'opensky':
        stamp = data['time']
        records = [{'id': s[0], 'lon': s[5], 'lat': s[6],
                    'age': stamp - s[3] if s[3] is not None else None,
                    'ground': s[8], 'vehicle': len(s) > 17 and s[17] in (16, 17, 18, 19, 20)}
                   for s in (data['states'] or [])]
    else:
        if data.get('msg') not in (None, 'No error'):
            raise ValueError(data['msg'])
        stamp = data['now']
        stamp = stamp / 1000 if stamp > 1e11 else stamp
        records = [{'id': s.get('hex'), 'lon': s.get('lon'), 'lat': s.get('lat'),
                    'age': s.get('seen_pos'), 'ground': True if s.get('alt_baro') == 'ground'
                    else False if isinstance(s.get('alt_baro'), (float, int)) else None,
                    'vehicle': s.get('category', '').startswith(('C', 'D'))
                    or s.get('type') == 'adsb_icao_nt'} for s in data['ac']]
    return stamp, records


def select(records, lat, lon):
    counts = {'raw_rows': len(records), 'invalid_id': 0, 'invalid_position': 0,
              'stale_or_missing_age': 0, 'outside_circle': 0, 'surface_or_obstacle': 0,
              'duplicates': 0}
    accepted = {}
    for r in records:
        if not isinstance(r['id'], str) or not re.fullmatch('[0-9a-fA-F]{6}', r['id']):
            counts['invalid_id'] += 1
        elif not all(isinstance(r[k], (float, int)) and math.isfinite(r[k]) for k in ('lat', 'lon')) or not (-90 <= r['lat'] <= 90 and -180 <= r['lon'] <= 180):
            counts['invalid_position'] += 1
        elif r['age'] is None or not 0 <= r['age'] <= 60:
            counts['stale_or_missing_age'] += 1
        elif GEOD.inv(lon, lat, r['lon'], r['lat'])[2] > RADIUS_M:
            counts['outside_circle'] += 1
        elif r['vehicle']:
            counts['surface_or_obstacle'] += 1
        else:
            identity = r['id'].lower()
            if identity in accepted:
                counts['duplicates'] += 1
                if accepted[identity]['age'] <= r['age']:
                    continue
            accepted[identity] = r
    counts.update(distinct_fresh=len(accepted), airborne=sum(r['ground'] is False for r in accepted.values()),
                  ground=sum(r['ground'] is True for r in accepted.values()),
                  unknown_ground_state=sum(r['ground'] is None for r in accepted.values()))
    return accepted, counts


def main():
    directory = CACHE / ('comparison-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    directory.mkdir(parents=True)
    airports = {r['ident']: r for r in csv.DictReader((CACHE / 'airports.csv').open())}
    result = {'method': 'WGS84 geodesic 100 NM circles; position age 0–60 seconds; distinct six-hex ICAO identifiers; known surface emitters excluded',
              'warning': 'Regional observations, not airport inventories or estimates of national completeness. Ground is not airport-assigned. Separate source timestamps.',
              'regions': {}}
    for code in ('KATL', 'KDFW', 'KDEN'):
        airport = airports[code]
        lat, lon = float(airport['latitude_deg']), float(airport['longitude_deg'])
        # A deliberately larger rectangle encloses the circle for these three latitudes.
        extent = {'lamin': lat - 2, 'lomin': lon - 3, 'lamax': lat + 2, 'lomax': lon + 3, 'extended': 1}
        urls = {'opensky': URL + '?' + urlencode(extent),
                'adsblol': f'https://api.adsb.lol/v2/point/{lat}/{lon}/100'}
        region = {'airport': airport['name'], 'center': [lon, lat], 'sources': {}}
        selected = {}
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {s: pool.submit(download, url, directory / f'{code}-{s}.json') for s, url in urls.items()}
            for source, future in futures.items():
                try:
                    data, meta = future.result()
                    stamp, records = normalize(data, source)
                    accepted, qa = select(records, lat, lon)
                    selected[source] = set(accepted)
                    region['sources'][source] = {**meta, 'snapshot_epoch': stamp,
                        'snapshot_utc': datetime.fromtimestamp(stamp, timezone.utc).isoformat(), 'qa': qa}
                except (subprocess.CalledProcessError, ValueError, KeyError, TypeError) as error:
                    region['sources'][source] = {'error': str(error), 'url': urls[source]}
        if len(selected) == 2:
            region['common_identifiers'] = len(selected['opensky'] & selected['adsblol'])
            region['source_timestamp_gap_seconds'] = abs(region['sources']['opensky']['snapshot_epoch'] - region['sources']['adsblol']['snapshot_epoch'])
            region['comparison_within_30s'] = region['source_timestamp_gap_seconds'] <= 30
        result['regions'][code] = region
        (directory / 'comparison.json').write_text(json.dumps(result, indent=2) + '\n')
        print(code, json.dumps(region), flush=True)
    print('Saved:', directory)


if __name__ == '__main__':
    main()
