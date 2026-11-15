"""Download only public OSM geometry and USGS 3DEP raster; cache outside Git."""
from pathlib import Path
import json
import hashlib
from datetime import datetime, timezone
import requests
from pyproj import Transformer

HERE = Path(__file__).resolve().parent
CACHE = HERE.parents[1] / 'data/raw/day15-inside-out'
SERVICE = 'https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer'
QUERY = '[out:json][timeout:90];(way[highway][ref~"550"](37.78,-107.80,38.04,-107.62);node[name="Red Mountain Pass"](37.8,-107.8,38.0,-107.6););out body;>;out skel qt;'

def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    s.headers['User-Agent'] = '30DayMapChallenge-Day15/1.0 (public geographic art)'
    osm = CACHE / 'osm.json'
    if not osm.exists():
        for host in ['https://overpass.kumi.systems/api/interpreter', 'https://overpass-api.de/api/interpreter', 'https://overpass.private.coffee/api/interpreter']:
            try:
                print('Fetching', host, flush=True)
                r = s.get(host, params={'data': QUERY}, timeout=110)
                r.raise_for_status()
                assert 'elements' in r.json()
                osm.write_bytes(r.content)
                break
            except Exception as e:
                print(str(e), flush=True)
        else:
            raise RuntimeError('OSM endpoints unavailable')
    # Explicit 10 m UTM grid covering all of the corridor, not point API samples.
    tr = Transformer.from_crs(4326, 26913, always_xy=True)
    corners = [tr.transform(x, y) for x in [-107.80, -107.62] for y in [37.78, 38.04]]
    import math
    bounds = [math.floor(min(p[0] for p in corners)/10)*10,
              math.floor(min(p[1] for p in corners)/10)*10,
              math.ceil(max(p[0] for p in corners)/10)*10,
              math.ceil(max(p[1] for p in corners)/10)*10]
    params = dict(bbox=','.join(map(str, bounds)), bboxSR=26913, imageSR=26913,
                  size=f'{(bounds[2]-bounds[0])//10},{(bounds[3]-bounds[1])//10}',
                  format='tiff', pixelType='F32', interpolation='RSP_BilinearInterpolation',
                  renderingRule=json.dumps({'rasterFunction':'None'}), f='image')
    for name, url, p in [('elevation.tif', SERVICE+'/exportImage', params),
                          ('service.json', SERVICE, {'f':'pjson'})]:
        target = CACHE/name
        if not target.exists():
            print('Fetching', name, flush=True)
            r=s.get(url,params=p,timeout=240); r.raise_for_status()
            if name.endswith('.tif'):
                assert r.content[:2] in [b'II', b'MM'], r.text[:500]
            else:
                assert 'error' not in r.json(), r.text[:500]
            target.write_bytes(r.content)
    manifest = dict(retrieved_utc=datetime.now(timezone.utc).isoformat(), osm_query=QUERY,
                    osm_base_timestamp=json.loads(osm.read_text()).get('osm3s'),
                    elevation_service=SERVICE, export_parameters=params,
                    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in CACHE.iterdir() if p.name in ['osm.json','elevation.tif','service.json']})
    if not (CACHE/'manifest.json').exists():
        (CACHE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Cache ready:', CACHE)

if __name__ == '__main__':
    main()
