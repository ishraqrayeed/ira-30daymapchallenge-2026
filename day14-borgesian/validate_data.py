"""Independent checks on the shipped geometry, counts and guided feature."""
import collections, json, math
from pathlib import Path
from shapely.geometry import shape, Point
from shapely.ops import unary_union
from shapely import prepare
ROOT=Path(__file__).resolve().parent

def main():
    read=lambda n:json.loads((ROOT/'data'/n).read_text())
    qa=read('qa.json');parks=read('parks.geojson')['features'];items=read('interiors.geojson')['features']
    boundary=shape(read('boundary.geojson')['features'][0]['geometry']);union=unary_union([shape(f['geometry']) for f in parks])
    prepare(union)
    assert qa['parks_mapped']==len(parks)==len({f['properties']['id'] for f in parks})
    assert all(f['properties']['kind'] in ['Park','Open Space'] and f['properties']['class'] not in ['Mountain','Golf','Recreation Center','Undeveloped'] for f in parks)
    assert union.difference(boundary).area<1e-12
    assert all(shape(f['geometry']).is_valid and not shape(f['geometry']).is_empty for f in parks+items)
    # Overlay roundoff can leave zero-area boundary slivers; tolerance <0.02 mm.
    tolerant_union=union.buffer(1e-10);prepare(tolerant_union)
    assert all(tolerant_union.covers(shape(f['geometry'])) for f in items)
    assert all(union.covers(shape(f['geometry'])) for f in items if shape(f['geometry']).geom_type=='Point')
    counts=collections.Counter(f['properties']['kind'] for f in items);assert dict(counts)==qa['amenities']
    wash=next(shape(f['geometry']) for f in parks if f['properties']['name']=='Washington Park')
    bench=next(f for f in items if f['properties']['osm']==qa['bench']['osm'])
    assert bench['properties']['kind']=='bench' and bench['geometry']['type']=='Point'
    assert bench['geometry']['coordinates']==qa['bench']['coordinates'] and wash.covers(shape(bench['geometry']))
    assert sum(1 for f in items if f['properties']['kind']=='bench' and f['geometry']['type']=='Point' and wash.covers(shape(f['geometry'])))==qa['washington_benches']
    x,y=qa['bench']['coordinates'];sx=111320*math.cos(math.radians(y))
    nearby=sum(1 for f in items if f['properties']['kind']=='tree' and f['geometry']['type']=='Point'
               and math.hypot((f['geometry']['coordinates'][0]-x)*sx,
                              (f['geometry']['coordinates'][1]-y)*111320)<=30)
    assert nearby==qa['bench']['mapped_trees_within_30m'] and nearby>0
    index={f['properties']['osm']:f for f in items}
    for key,landmark in qa['tour_landmarks'].items():
        assert wash.covers(Point(landmark['coordinates'])), key
        assert all(osm in index for osm in landmark['osm']), key
        if key=='tennis_courts':assert all(index[osm]['properties'].get('sport')=='tennis' for osm in landmark['osm'])
        if 'playground' in key:assert all(index[osm]['properties']['kind']=='playground' for osm in landmark['osm'])
    assert counts['path'] and counts['tree'] and counts['pitch'] and counts['playground'] and counts['water']
    print(f"PASS: {len(parks)} parks; {len(items)} OSM features; {qa['washington_benches']} Washington Park benches; verified final stop {qa['bench']['osm']}")

if __name__=='__main__':main()
