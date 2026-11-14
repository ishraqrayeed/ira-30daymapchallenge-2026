"""Convert a Geofabrik Colorado PBF to the small raw interior extract.
Install osmium>=4,<5. Input remains in ignored data/raw/day14.
Usage: python3 day14-borgesian/extract_osm.py data/raw/day14/colorado.osm.pbf
"""
import json, sys
from pathlib import Path
import osmium
from shapely import wkb
from shapely.geometry import mapping, box
BBOX=box(-105.12,39.60,-104.60,39.86)
FACTORY=osmium.geom.WKBFactory()

def relevant(t):
    return (t.get('amenity')=='bench' or t.get('natural') in ['tree','water'] or 'waterway' in t or t.get('leisure') in ['playground','pitch'] or t.get('highway') in ['path','footway','cycleway','track','pedestrian','steps'])

def is_area(t):return t.get('natural')=='water' or t.get('leisure') in ['playground','pitch'] or t.get('area')=='yes'

class Extract(osmium.SimpleHandler):
    def __init__(self):super().__init__();self.elements=[]
    def node(self,n):
        t=dict(n.tags)
        if relevant(t) and BBOX.covers(__import__('shapely').geometry.Point(n.location.lon,n.location.lat)):
            self.elements.append({'type':'node','id':n.id,'tags':t,'lon':n.location.lon,'lat':n.location.lat})
    def way(self,w):
        t=dict(w.tags)
        if not relevant(t) or (w.is_closed() and is_area(t)):return
        if not all(n.location.valid() for n in w.nodes):return
        coords=[{'lon':n.lon,'lat':n.lat} for n in w.nodes]
        if len(coords)<2:return
        from shapely.geometry import LineString
        if LineString([(p['lon'],p['lat']) for p in coords]).intersects(BBOX):self.elements.append({'type':'way','id':w.id,'tags':t,'geometry':coords})
    def area(self,a):
        t=dict(a.tags)
        if not relevant(t) or not is_area(t):return
        g=wkb.loads(FACTORY.create_multipolygon(a),hex=True)
        if g.intersects(BBOX):self.elements.append({'type':'way' if a.from_way() else 'relation','id':a.orig_id(),'tags':t,'_geometry':mapping(g)})

if __name__=='__main__':
    path=Path(sys.argv[1]);handler=Extract()
    with osmium.io.Reader(str(path)) as reader:
        stamp=reader.header().get('osmosis_replication_timestamp') or reader.header().get('timestamp')
    # Filter in C++ before entering Python, while retaining all location references.
    processor=(osmium.FileProcessor(str(path)).with_locations()
               .with_areas(osmium.filter.KeyFilter('natural','leisure','waterway'))
               .with_filter(osmium.filter.KeyFilter('amenity','natural','waterway','leisure','highway')))
    for obj in processor:
        if obj.is_node():handler.node(obj)
        elif obj.is_way():handler.way(obj)
        elif obj.is_area():handler.area(obj)
    assert stamp,'PBF source timestamp missing'
    output={'osm3s':{'timestamp_osm_base':stamp},'source':'https://download.geofabrik.de/north-america/us/colorado.html','elements':handler.elements}
    path.with_name('interiors.json').write_text(json.dumps(output,separators=(',',':')))
    print(f'Extracted {len(handler.elements)} elements; source date {stamp}')
