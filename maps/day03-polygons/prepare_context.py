"""Municipal city geometry, restrained display geofence, labels and overlap.

This module never changes the routing inputs or cumulative accessibility data.
Statistics use the original DNCC+DSCC union, never the smoothed geofence.
"""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import zipfile
import requests
from pyproj import Transformer
from shapely.geometry import shape, mapping, Polygon, Point
from shapely.ops import transform, unary_union

DAY = Path(__file__).resolve().parent
CACHE = DAY.parents[1] / 'data/raw/day03-polygons'


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n')


def parts(geometry):
    if geometry.geom_type == 'Polygon':
        yield geometry
    elif hasattr(geometry, 'geoms'):
        for part in geometry.geoms:
            yield from parts(part)


def smooth_ring(ring, max_segment):
    coords = list(ring.coords)
    dense = []
    for a, b in zip(coords[:-1], coords[1:]):
        segments = max(1, math.ceil(Point(a).distance(Point(b)) / max_segment))
        dense.extend([(a[0] + (b[0]-a[0])*i/segments, a[1] + (b[1]-a[1])*i/segments)
                      for i in range(segments)])
    smoothed = []
    for a, b in zip(dense, dense[1:] + dense[:1]):
        smoothed.extend([(.75*a[0]+.25*b[0], .75*a[1]+.25*b[1]),
                         (.25*a[0]+.75*b[0], .25*a[1]+.75*b[1])])
    return smoothed


def display_geofence(original, config):
    simplified = original.simplify(config['display_city_simplification_m'], preserve_topology=True)
    # The selected municipal union is already one polygon without holes. Never
    # replace a fragmented source with an invented convex hull.
    if simplified.geom_type != 'Polygon':
        raise ValueError('Municipal union is not a single connected geofence')
    result = Polygon(smooth_ring(simplified.exterior, config['display_city_max_segment_m']),
                     [smooth_ring(r, config['display_city_max_segment_m']) for r in simplified.interiors])
    if not result.is_valid or original.hausdorff_distance(result) > 130:
        raise ValueError('Display geofence is invalid or excessively displaced')
    return result


def fill_small_holes(geometry, maximum_area):
    return unary_union([Polygon(p.exterior, [r for r in p.interiors if Polygon(r).area >= maximum_area])
                        for p in parts(geometry)])


def acquire_boundaries(config):
    raw_subset = DAY / 'dhaka_city_corporations.geojson'
    provenance = DAY / 'boundary-source.json'
    if raw_subset.exists() and provenance.exists():
        source = json.loads(provenance.read_text())
        if hashlib.sha256(raw_subset.read_bytes()).hexdigest() != source['subset_sha256']:
            raise ValueError('Municipal source geometry checksum changed')
        return json.loads(raw_subset.read_text()), source
    metadata_path = CACHE / 'hdx-boundary-metadata.json'
    if not metadata_path.exists():
        response = requests.get(config['city_api'], timeout=60)
        response.raise_for_status()
        write(metadata_path, response.json())
    metadata = json.loads(metadata_path.read_text())['result']
    resource = next(r for r in metadata['resources'] if r['name'].endswith('geojson.zip'))
    archive = CACHE / 'hdx-admin.geojson.zip'
    if not archive.exists():
        response = requests.get(resource['url'], timeout=120)
        response.raise_for_status()
        archive.write_bytes(response.content)
    with zipfile.ZipFile(archive) as source:
        full = json.loads(source.read('bgd_admin3.geojson'))
    features = [f for f in full['features'] if f['properties']['adm3_pcode'] in config['city_pcodes']]
    if {f['properties']['adm3_name'] for f in features} != set(config['city_names']):
        raise ValueError('Source city names/codes do not match DNCC and DSCC')
    subset = {'type': 'FeatureCollection', 'features': features}
    write(raw_subset, subset)
    origin = {'dataset': metadata['title'], 'source': metadata['dataset_source'],
              'publisher': 'OCHA / HDX', 'url': config['city_source'], 'resource_url': resource['url'],
              'license': metadata['license_title'], 'license_url': 'https://creativecommons.org/licenses/by/3.0/igo/',
              'source_notes': metadata['notes'], 'resource_last_modified': resource.get('last_modified'),
              'retrieved_utc': datetime.now(timezone.utc).isoformat(),
              'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
              'subset_sha256': hashlib.sha256(raw_subset.read_bytes()).hexdigest(),
              'selected_pcodes': config['city_pcodes'], 'represents': 'DNCC + DSCC; not Dhaka District'}
    write(provenance, origin)
    return subset, origin


def main():
    config = json.loads((DAY / 'context-config.json').read_text())
    source, provenance = acquire_boundaries(config)
    project = Transformer.from_crs(4326, 32646, always_xy=True).transform
    inverse = Transformer.from_crs(32646, 4326, always_xy=True).transform
    geometries = [transform(project, shape(f['geometry'])) for f in source['features']]
    if any(not g.is_valid for g in geometries):
        raise ValueError('Invalid municipal source geometry')
    city = unary_union(geometries)
    geofence = display_geofence(city, config)
    for name, geometry, role in [('dhaka_city_boundary.geojson', city, 'analytical DNCC + DSCC union'),
                                 ('dhaka_city_geofence.geojson', geofence, 'generalized display geofence only')]:
        write(DAY / name, {'type': 'FeatureCollection', 'features': [{'type': 'Feature',
              'properties': {'name': 'Dhaka city', 'definition': 'DNCC + DSCC', 'role': role,
                             'source': config['city_source'], 'area_km2': geometry.area/1e6},
              'geometry': mapping(transform(inverse, geometry))}]})
    iso = shape(json.loads((DAY / 'farmgate_45min.geojson').read_text())['features'][0]['geometry'])
    intersection = city.intersection(transform(project, iso))
    percentage = intersection.area / city.area * 100
    labels_file = DAY / 'dhaka_labels.geojson'
    if not labels_file.exists():
        places_path = CACHE / 'place-nodes.json'
        if not places_path.exists():
            # Filtering in C++ avoids iterating every OSM node in Python.
            import osmium
            class Places(osmium.SimpleHandler):
                def __init__(self):
                    super().__init__()
                    self.records = []
                def node(self, n):
                    if n.id in config['label_osm_nodes'].values():
                        self.records.append({'id': n.id, 'coordinates': [n.location.lon, n.location.lat], 'tags': dict(n.tags)})
            handler = Places()
            with osmium.io.Reader(str(CACHE / 'bangladesh-20261102.osm.pbf'), osmium.osm.NODE) as reader:
                osmium.apply(reader, osmium.filter.KeyFilter('place'), handler)
            write(places_path, handler.records)
        places = {p['id']: p for p in json.loads(places_path.read_text())}
        labels = []
        for name, identifier in config['label_osm_nodes'].items():
            record = places[identifier]
            if record['tags'].get('name:en') != name:
                raise ValueError('Label name/coordinate source mismatch')
            labels.append({'type': 'Feature', 'properties': {'name': name,
                           'source': f'https://www.openstreetmap.org/node/{identifier}'},
                           'geometry': mapping(Point(*record['coordinates']))})
        # Farmgate is anchored to the verified MRT station, not a suburb centroid.
        station = next(f for f in json.loads((DAY / 'dhaka_mrt6_stations.geojson').read_text())['features'] if f['properties']['station_name'] == 'Farmgate')
        labels.append({'type': 'Feature', 'properties': {'name': 'Farmgate', 'source': station['properties']['source']}, 'geometry': station['geometry']})
        write(labels_file, {'type': 'FeatureCollection', 'features': labels})
    qa = {'city_definition': 'Dhaka North City Corporation + Dhaka South City Corporation',
          'city_source': provenance, 'area_crs': 'EPSG:32646',
          'city_area_km2': city.area/1e6, 'intersection_45min_km2': intersection.area/1e6,
          'percentage_45min': percentage, 'percentage_claim': 'Modeled street-envelope overlap with mapped municipal area, not population or verified parcel reachability',
          'denominator_includes': 'Entire original municipal union, including water and restricted land',
          'display_geofence_area_km2': geofence.area/1e6,
          'display_geofence_hausdorff_m': city.hausdorff_distance(geofence),
          'display_geofence_statistics_used': False, 'context_config': config,
          'routing_model_modified': False,
          'context_config_sha256': hashlib.sha256((DAY / 'context-config.json').read_bytes()).hexdigest(),
          'cumulative_isochrone_sha256': hashlib.sha256((DAY / 'farmgate_accessibility.geojson').read_bytes()).hexdigest()}
    write(DAY / 'context.qa.json', qa)
    print(f'Original municipal union: {city.area/1e6:.4f} km²; overlap {intersection.area/1e6:.4f} km²; {percentage:.4f}%')


if __name__ == '__main__':
    main()
