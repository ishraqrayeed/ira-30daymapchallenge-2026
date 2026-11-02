"""Cache public sources; extract explicit OSM halal candidates, never cuisine inference."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import requests
import osmium
from shapely.geometry import Polygon, LineString

DAY = Path(__file__).resolve().parent
ROOT = DAY.parents[1]
CACHE = ROOT / 'data/raw/day04-clusters'
URLS = {
    'new-york-261101.osm.pbf': 'https://download.geofabrik.de/north-america/us/new-york-261101.osm.pbf',
    'boroughs.geojson': 'https://data.cityofnewyork.us/resource/gthc-hcne.geojson',
    'inspections.json': 'https://data.cityofnewyork.us/resource/43nn-pn8j.json?$where=upper(dba)%20like%20%22%25HALAL%25%22&$limit=50000',
    'neighborhoods.geojson': 'https://data.cityofnewyork.us/resource/9nt8-h7nd.geojson',
}


def explicit(tags):
    return tags.get('diet:halal') in ('yes', 'only') or bool(re.search(r'halal', tags.get('name', ''), re.I))


class Candidates(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.records, self.ways = [], []

    def node(self, n):
        if not ('diet:halal' in n.tags or 'halal' in n.tags.get('name', '').lower()):
            return
        tags = dict(n.tags)
        if explicit(tags) and 40.68 < n.location.lat < 40.90 and -74.06 < n.location.lon < -73.90:
            self.records.append({'type': 'node', 'id': n.id, 'tags': tags,
                                 'lat': n.location.lat, 'lon': n.location.lon})

    def way(self, w):
        if not ('diet:halal' in w.tags or 'halal' in w.tags.get('name', '').lower()):
            return
        tags = dict(w.tags)
        if explicit(tags):
            self.ways.append({'type': 'way', 'id': w.id, 'tags': tags, 'refs': [n.ref for n in w.nodes]})

    def relation(self, r):
        if explicit(dict(r.tags)):
            raise ValueError('Explicit halal relation found: add relation geometry support before proceeding')


class Nodes(osmium.SimpleHandler):
    def __init__(self, ids):
        super().__init__()
        self.ids, self.coords = ids, {}

    def node(self, n):
        if n.id in self.ids:
            self.coords[n.id] = (n.location.lon, n.location.lat)


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((DAY / 'source-manifest.json').read_text()) if (DAY / 'source-manifest.json').exists() else {}
    for name, url in URLS.items():
        path = CACHE / name
        if not path.exists():
            response = requests.get(url, stream=True, timeout=(20, 180))
            response.raise_for_status()
            temporary = path.with_suffix('.download')
            with temporary.open('wb') as f:
                for block in response.iter_content(1024 * 1024):
                    f.write(block)
            temporary.replace(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if name in manifest and manifest[name]['sha256'] != digest:
            raise ValueError(f'{name} changed from reviewed snapshot; explicitly review a new snapshot')
        manifest.setdefault(name, {'url': url, 'retrieval_date': datetime.now(timezone.utc).isoformat(),
                                   'sha256': digest, 'bytes': path.stat().st_size})
    (DAY / 'source-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    c = Candidates()
    for obj in osmium.FileProcessor(str(CACHE / 'new-york-261101.osm.pbf')).with_filter(osmium.filter.KeyFilter('name', 'diet:halal')):
        if obj.is_node():
            c.node(obj)
        elif obj.is_way():
            c.way(obj)
        elif obj.is_relation():
            c.relation(obj)
    print(f'First pass: {len(c.records)} nodes; {len(c.ways)} candidate ways statewide', flush=True)
    nodes = Nodes({i for w in c.ways for i in w['refs']})
    for obj in osmium.FileProcessor(str(CACHE / 'new-york-261101.osm.pbf'), entities=osmium.osm.NODE).with_filter(osmium.filter.IdFilter(nodes.ids)):
        nodes.node(obj)
    for w in c.ways:
        coords = [nodes.coords[i] for i in w.pop('refs') if i in nodes.coords]
        if len(coords) < 2:
            raise ValueError(f'Missing way geometry: {w["id"]}')
        geom = Polygon(coords) if len(coords) >= 4 and coords[0] == coords[-1] else LineString(coords)
        p = geom.representative_point()
        if 40.68 < p.y < 40.90 and -74.06 < p.x < -73.90:
            w.update(lat=p.y, lon=p.x)
            c.records.append(w)
    (CACHE / 'osm-candidates.json').write_text(json.dumps(c.records, indent=2))
    print(f'{len(c.records)} explicit OSM candidates in collection bounding box')


if __name__ == '__main__':
    main()
