"""Check source provenance and geometric fidelity, using the ignored raw cache."""
from pathlib import Path
import hashlib, json, math
from shapely.geometry import LineString, Point, shape
from shapely.ops import transform, unary_union
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent
CACHE = ROOT.parents[1] / 'data/raw/day12'
load = lambda p: json.loads(p.read_text())
metric = Transformer.from_crs(4326, 5070, always_xy=True).transform
source = load(ROOT / 'data/sources.json')
lines = load(ROOT / 'data/transmission.geojson')['features']
routes = load(ROOT / 'data/routes.json')
raw = [f for p in sorted(CACHE.glob('lines-*.json')) for f in load(p)['features']]
ids = load(CACHE / 'transmission-ids.json')['objectIds']
assert len(raw) == len(ids) == len({f['attributes']['OBJECTID_1'] for f in raw})
assert set(ids) == {f['attributes']['OBJECTID_1'] for f in raw}
original = {f['attributes']['OBJECTID_1']: f for f in raw}
projected = {}
for f in raw:
    paths = f.get('geometry', {}).get('paths', [])
    if paths:
        projected[f['attributes']['OBJECTID_1']] = unary_union([
            transform(metric, LineString([(p[0],p[1]) for p in path])) for path in paths if len(path)>1])
assert len(lines) == source['rendered_line_parts']
assert len({f['properties']['id'] for f in lines}) == len(lines)
assert len({f['properties']['source_id'] for f in lines}) == source['retained_source_records']
by_id = {}
worst_deviation = 0
for f in lines:
    p=f['properties']; a=original[p['source_id']]['attributes']; geom=transform(metric,shape(f['geometry']))
    assert a['STATUS']=='IN SERVICE' and a['VOLTAGE']>=115
    assert p['voltage_kv']==a['VOLTAGE'] and .3<geom.length/1000<=60.01
    assert geom.is_valid and not geom.is_empty
    # Every rendered point stays inside a 35 m simplification envelope (+ rounding).
    for n in range(101):
        distance=geom.interpolate(n/100,normalized=True).distance(projected[p['source_id']])
        worst_deviation=max(worst_deviation,distance)
        assert distance<=35.2,(p['id'],distance)
    by_id[p['id']]=geom
worst_sample_error=0
for route in routes['routes']:
    assert route['id'] in by_id and len(route['samples'])==2*routes['sample_count']
    points=list(zip(route['samples'][::2],route['samples'][1::2]))
    for x,y in points:
        assert 0<x<1 and 0<y<1
        lon=x*360-180;lat=math.degrees(math.atan(math.sinh(math.pi*(1-2*y))))
        distance=transform(metric,Point(lon,lat)).distance(by_id[route['id']])
        worst_sample_error=max(worst_sample_error,distance)
        assert distance<.03,(route['id'],distance)
assert len(routes['routes'])==source['particle_routes']
assert any(f['properties']['name']=='Lake Mead' and shape(f['geometry']).area>0 for f in load(ROOT/'data/context.geojson')['features'])
world=load(ROOT/'data/world.geojson')['features']
assert len(world)>150 and all(shape(f['geometry']).is_valid for f in world)
assert any(shape(f['geometry']).bounds[3]>38.3 for f in load(ROOT/'data/context.geojson')['features'])
assert -114.75<source['hoover_coordinates'][0]<-114.72 and 36<source['hoover_coordinates'][1]<36.03
for name,digest in source['sha256'].items():
    assert hashlib.sha256((ROOT/'data'/name).read_bytes()).hexdigest()==digest,name
for name,digest in source.get('raw_sha256',{}).items():
    assert hashlib.sha256((CACHE/name).read_bytes()).hexdigest()==digest,name
report=dict(passed=True,source_records=len(raw),retained_source_records=source['retained_source_records'],display_segments=len(lines),particle_routes=len(routes['routes']),maximum_simplification_deviation_m=round(worst_deviation,4),maximum_route_sample_error_m=round(worst_sample_error,4))
print(json.dumps(report,indent=2))
