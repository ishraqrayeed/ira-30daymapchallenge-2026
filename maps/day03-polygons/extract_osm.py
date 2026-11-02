"""Extract a bounded, walk-filtered OSM snapshot without an Overpass dependency.

Usage: python extract_osm.py /path/to/bangladesh.osm.pbf
Requires pyosmium (osmium). All source caches remain outside version control.
"""
import hashlib
import json
from pathlib import Path
import re
import sys
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import osmium

DAY = Path(__file__).resolve().parent
CACHE = DAY.parents[1] / 'data/raw/day03-polygons'


def walkable(tags):
    highway = tags.get('highway', '')
    if not highway or tags.get('area') == 'yes':
        return False
    if re.search('abandoned|bus_guideway|construction|cycleway|motor|^no$|planned|platform|proposed|raceway|razed', highway):
        return False
    if tags.get('foot') in ['no', 'private'] or tags.get('service') == 'private':
        return False
    if tags.get('access') in ['no', 'private'] and tags.get('foot') not in ['yes', 'designated', 'permissive']:
        return False
    return True


class Extract(osmium.SimpleHandler):
    def __init__(self, bbox):
        super().__init__()
        self.bbox = bbox
        self.nodes, self.walkways, self.metro, self.water, self.roads, self.relations = {}, [], [], [], [], []
        self.stations, self.entrances, self.barriers = [], [], set()

    def node(self, node):
        x, y = node.location.lon, node.location.lat
        west, south, east, north = self.bbox
        if not (west <= x <= east and south <= y <= north):
            return
        tags = dict(node.tags)
        self.nodes[node.id] = (x, y)
        record = {'type': 'node', 'id': node.id, 'coordinates': [x, y], 'tags': tags}
        if tags.get('railway') == 'station':
            self.stations.append(record)
        if tags.get('railway') == 'subway_entrance':
            self.entrances.append(record)
        if tags.get('barrier') and (tags.get('foot') in ['no', 'private'] or tags.get('access') in ['no', 'private']):
            self.barriers.add(node.id)

    def way(self, way):
        refs = [node.ref for node in way.nodes]
        if not any(ref in self.nodes for ref in refs):
            return
        tags = dict(way.tags)
        coords = [self.nodes[ref] for ref in refs if ref in self.nodes]
        if len(coords) < 2:
            return
        record = {'type': 'way', 'id': way.id, 'nodes': refs, 'coordinates': coords, 'tags': tags}
        if tags.get('railway') == 'station':
            self.stations.append(record)
        if tags.get('railway') == 'subway' and tags.get('service') not in ['siding', 'yard', 'spur']:
            self.metro.append(record)
        if walkable(tags):
            self.walkways.append(record)
        if tags.get('natural') == 'water' or tags.get('water') or tags.get('landuse') == 'reservoir':
            self.water.append(record)
        if tags.get('highway') in ['primary', 'secondary', 'trunk']:
            self.roads.append(record)

    def relation(self, relation):
        tags = dict(relation.tags)
        if tags.get('route') == 'subway':
            self.relations.append({'id': relation.id, 'tags': tags,
                                   'members': [{'type': m.type, 'ref': m.ref, 'role': m.role} for m in relation.members]})


def main(filename):
    config = json.loads((DAY / 'config.json').read_text())
    source = Path(filename)
    reader = osmium.io.Reader(str(source))
    header = reader.header()
    snapshot = {key: header.get(key) for key in ['osmosis_replication_timestamp', 'osmosis_replication_sequence_number', 'generator']}
    reader.close()
    handler = Extract(config['extraction_bbox_wgs84'])
    handler.apply_file(str(source))
    CACHE.mkdir(parents=True, exist_ok=True)
    # Split at excluded barrier nodes; retain every other mapped graph component.
    xml = ET.Element('osm', version='0.6', generator='Day03 bounded pedestrian extraction')
    used = {n for way in handler.walkways for n in way['nodes'] if n in handler.nodes and n not in handler.barriers}
    for identifier in sorted(used):
        x, y = handler.nodes[identifier]
        ET.SubElement(xml, 'node', id=str(identifier), lon=str(x), lat=str(y))
    synthetic = -1
    for way in handler.walkways:
        chunks, current = [], []
        for identifier in way['nodes']:
            if identifier in used:
                current.append(identifier)
            else:
                if len(current) > 1:
                    chunks.append(current)
                current = []
        if len(current) > 1:
            chunks.append(current)
        for chunk in chunks:
            element = ET.SubElement(xml, 'way', id=str(synthetic))
            synthetic -= 1
            for identifier in chunk:
                ET.SubElement(element, 'nd', ref=str(identifier))
            for key, value in {**way['tags'], 'original_osm_way': str(way['id'])}.items():
                ET.SubElement(element, 'tag', k=key, v=value)
    ET.ElementTree(xml).write(CACHE / 'walk.osm', encoding='utf-8', xml_declaration=True)
    data = {name: getattr(handler, name) for name in ['stations', 'entrances', 'metro', 'water', 'roads', 'relations']}
    (CACHE / 'context.json').write_text(json.dumps(data, separators=(',', ':')) + '\n')
    report = {'source': 'https://download.geofabrik.de/asia/bangladesh.html',
              'download_url': 'https://download.geofabrik.de/asia/bangladesh-latest.osm.pbf',
              'pbf_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'retrieved_utc': datetime.now(timezone.utc).isoformat(), 'snapshot': snapshot,
              'bbox_wgs84': config['extraction_bbox_wgs84'], 'walking_way_count': len(handler.walkways),
              'walking_node_count': len(used), 'restricted_barrier_nodes': len(handler.barriers),
              'walk_xml_sha256': hashlib.sha256((CACHE / 'walk.osm').read_bytes()).hexdigest(),
              'context_sha256': hashlib.sha256((CACHE / 'context.json').read_bytes()).hexdigest(),
              'license': 'Open Database License (ODbL) 1.0; © OpenStreetMap contributors'}
    (CACHE / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    for station in handler.stations:
        print(station['type'], station['id'], station['tags'])


if __name__ == '__main__':
    main(sys.argv[1])
