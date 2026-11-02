"""Download the fixed public OSM snapshot and station-coordinate cross-check."""
from pathlib import Path
import hashlib
import json
import requests

DAY = Path(__file__).resolve().parent
CACHE = DAY.parents[1] / 'data/raw/day03-polygons'
PBF_URL = 'https://download.geofabrik.de/asia/bangladesh-261102.osm.pbf'


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    source_manifest = DAY / 'source-manifest.json'
    expected = json.loads(source_manifest.read_text()) if source_manifest.exists() else {}
    source = CACHE / 'bangladesh-20261102.osm.pbf'
    if not source.exists():
        response = requests.get(PBF_URL, stream=True, timeout=(20, 90))
        response.raise_for_status()
        temporary = source.with_suffix('.download')
        with temporary.open('wb') as target:
            for block in response.iter_content(1024 * 1024):
                target.write(block)
        temporary.replace(source)
    if expected and hashlib.sha256(source.read_bytes()).hexdigest() != expected['pbf_sha256']:
        raise ValueError('Source snapshot checksum differs; do not silently substitute newer OSM')
    check = CACHE / 'citylines-stations.geojson'
    if not check.exists():
        response = requests.get('https://www.citylines.co/api/dhaka/raw_source/stations', timeout=45)
        response.raise_for_status()
        check.write_bytes(response.content)
    print(f'Cached fixed snapshot: {source}')


if __name__ == '__main__':
    main()
