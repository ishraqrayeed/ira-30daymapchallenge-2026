"""Bounded, research-only current OpenSky snapshot cache; no historical claims."""
import argparse
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / 'data/raw/day13-aviation'
URL = 'https://opensky-network.org/api/states/all'


def register(path, url):
    manifest_path = CACHE / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    manifest[path.name] = {
        'url': url, 'cached_at_utc': datetime.now(timezone.utc).isoformat(),
        'bytes': path.stat().st_size,
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')


def validate(path):
    data = json.loads(path.read_text())
    if (data.get('complete_snapshot') is False
            or not isinstance(data.get('time'), int)
            or not isinstance(data.get('states'), list)):
        raise ValueError('Not a complete OpenSky snapshot')
    states = data['states']
    ids = [s[0] for s in states]
    report = {
        'snapshot_utc': datetime.fromtimestamp(data['time'], timezone.utc).isoformat(),
        'global_rows': len(states),
        'duplicate_identifiers': len(ids) - len(set(ids)),
        'missing_identifiers': sum(not i for i in ids),
        'invalid_ground_flags': sum(type(s[8]) is not bool for s in states),
        'missing_or_invalid_coordinates': sum(
            s[5] is None or s[6] is None or not -180 <= s[5] <= 180
            or not -90 <= s[6] <= 90 for s in states),
        'stale_or_missing_positions_over_60s': sum(
            s[3] is None or not 0 <= data['time'] - s[3] <= 60 for s in states),
    }
    return data, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count', type=int, default=1)
    parser.add_argument('--interval', type=int, default=300)
    args = parser.parse_args()
    if not 1 <= args.count <= 12 or args.interval < 60:
        parser.error('Use 1–12 snapshots, at least 60 seconds apart')
    CACHE.mkdir(parents=True, exist_ok=True)
    for index in range(args.count):
        temporary = CACHE / 'download.partial'
        subprocess.run(['curl', '--compressed', '--max-time', '180', '-fsSL', URL,
                        '-o', str(temporary)], check=True)
        data, report = validate(temporary)
        destination = CACHE / f"opensky-{data['time']}.json"
        temporary.replace(destination)
        register(destination, URL)
        destination.with_suffix('.qa.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report), flush=True)
        if index + 1 < args.count:
            time.sleep(args.interval)


if __name__ == '__main__':
    main()
