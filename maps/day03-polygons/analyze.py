"""Approximate rail + pedestrian accessibility from a fixed OSM snapshot.

Rail times are distance-weighted estimates calibrated to a published whole-line
time. Walking is routed on real OSM links, with partial boundary edges retained.
The area geometry is a street catchment envelope, not a parcel-access inventory.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
os.environ.setdefault('MPLCONFIGDIR', '/tmp/day3-dhaka-mpl')
import geopandas as gpd
import pandas as pd
import networkx as nx
import numpy as np
import osmnx as ox
from pyproj import Transformer
from shapely.geometry import Point, LineString, Polygon, shape, mapping, box
from shapely.ops import transform, unary_union, substring

DAY = Path(__file__).resolve().parent
CACHE = DAY.parents[1] / 'data/raw/day03-polygons'


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def polygon_parts(geometry):
    if geometry.geom_type == 'Polygon':
        yield geometry
    elif hasattr(geometry, 'geoms'):
        for part in geometry.geoms:
            yield from polygon_parts(part)


def normalize(name):
    return name.lower().replace('kawran', 'karwan').replace('centre', 'center').replace(' ', '')


def stations_from_osm(context, config, project):
    crosscheck = json.loads((CACHE / 'citylines-stations.geojson').read_text())['features']
    crosscheck = {normalize(f['properties']['name']): Point(project(*f['geometry']['coordinates'])) for f in crosscheck}
    candidates = []
    for record in context['stations']:
        coords = record['coordinates']
        location = Point(*project(*coords)) if record['type'] == 'node' else transform(project, Polygon(coords)).centroid
        tags = record['tags']
        candidates.append((record, location, ' / '.join(tags.get(k, '') for k in ['name', 'name:en', 'alt_name', 'alt_name:en'])))
    records = []
    inverse = Transformer.from_crs(config['crs'], 4326, always_xy=True).transform
    for order, name in enumerate(config['stations_north_to_south'], start=1):
        reference = crosscheck[normalize(name)]
        nearby = [(record, location, names) for record, location, names in candidates if location.distance(reference) < 400]
        if not nearby:
            raise ValueError(f'No independently cross-checked OSM station for {name}')
        nearby.sort(key=lambda r: (r[0]['type'] != 'way', r[1].distance(reference)))
        record, location, names = nearby[0]
        if normalize(name) not in normalize(names):
            raise ValueError(f'Station name mismatch for {name}: {names}')
        lon, lat = inverse(location.x, location.y)
        records.append({'station_name': name, 'latitude': lat, 'longitude': lon,
                        'station_order': order, 'x': location.x, 'y': location.y,
                        'source': f'https://www.openstreetmap.org/{record["type"]}/{record["id"]}',
                        'coordinate_definition': 'station building centroid' if record['type'] == 'way' else 'mapped station node',
                        'coordinate_crosscheck_source': 'https://www.citylines.co/api/dhaka/raw_source/stations',
                        'coordinate_crosscheck_distance_m': location.distance(reference)})
    return records


def rail_model(context, stations, config, project):
    # Prefer a mapped directional passenger route to avoid depot tracks and
    # alternating snaps between parallel tracks. Never draw a chord as rail data.
    route = next((r for r in context['relations']
                  if ('uttara' in str(r['tags'].get('from', '')).lower() or 'উত্তরা' in r['tags'].get('from', ''))
                  and ('motijheel' in str(r['tags'].get('to', '')).lower() or 'মতিঝিল' in r['tags'].get('to', ''))), None)
    allowed = {m['ref'] for m in route['members'] if m['type'] == 'w'} if route else None
    graph = nx.Graph()
    for way in context['metro']:
        if allowed is not None and way['id'] not in allowed:
            continue
        if len(way['nodes']) != len(way['coordinates']):
            continue
        coords = [project(*xy) for xy in way['coordinates']]
        for identifier, (x, y) in zip(way['nodes'], coords):
            graph.add_node(identifier, x=x, y=y)
        for u, v, a, b in zip(way['nodes'][:-1], way['nodes'][1:], coords[:-1], coords[1:]):
            graph.add_edge(u, v, length=Point(a).distance(Point(b)))
    if not graph:
        raise ValueError('No mapped operating railway geometry')
    component = max(nx.connected_components(graph), key=len)
    graph = graph.subgraph(component).copy()
    if route:
        stops = [m['ref'] for m in route['members'] if m['role'] == 'stop' and m['type'] == 'n']
        if len(stops) != len(stations) or any(n not in graph for n in stops):
            raise ValueError('Mapped route stop sequence is incomplete')
        for station, node in zip(stations, stops):
            stop = Point(graph.nodes[node]['x'], graph.nodes[node]['y'])
            nearest = min(stations, key=lambda s: stop.distance(Point(s['x'], s['y'])))
            if nearest['station_order'] != station['station_order'] or stop.distance(Point(station['x'], station['y'])) > 300:
                raise ValueError('Station order disagrees with mapped passenger route')
    ids = list(graph)
    coords = np.array([[graph.nodes[n]['x'], graph.nodes[n]['y']] for n in ids])
    snapped = []
    for station in stations:
        distances = np.linalg.norm(coords - [station['x'], station['y']], axis=1)
        i = int(distances.argmin())
        if distances[i] > 250:
            raise ValueError(f'Rail snap too distant: {station["station_name"]}, {distances[i]}')
        snapped.append(ids[i])
        station['rail_snap_m'] = float(distances[i])
    paths, lengths = [], []
    for i, (u, v) in enumerate(zip(snapped[:-1], snapped[1:])):
        path = nx.shortest_path(graph, u, v, weight='length')
        line = LineString([(graph.nodes[n]['x'], graph.nodes[n]['y']) for n in path])
        direct = Point(stations[i]['x'], stations[i]['y']).distance(Point(stations[i+1]['x'], stations[i+1]['y']))
        if line.length < direct * .75 or line.length > direct * 2:
            raise ValueError(f'Implausible rail alignment between stations {i+1} and {i+2}')
        paths.append(line)
        lengths.append(line.length)
    running_total = config['full_line_minutes'] - (len(stations) - 2) * config['intermediate_dwell_minutes']
    running = np.array(lengths) / sum(lengths) * running_total
    origin = next(i for i, s in enumerate(stations) if s['station_name'] == config['origin'])
    for i, station in enumerate(stations):
        a, b = sorted([origin, i])
        hops = b - a
        station['metro_minutes_from_farmgate'] = float(sum(running[a:b]) + max(0, hops - 1) * config['intermediate_dwell_minutes'])
    segments = [{'from': stations[i]['station_name'], 'to': stations[i+1]['station_name'],
                 'mapped_track_metres': lengths[i], 'estimated_running_minutes': float(running[i])}
                for i in range(len(paths))]
    return paths, segments, {'osm_relation': route['id'] if route else None,
                             'track_length_m': sum(lengths), 'calibration_minutes': config['full_line_minutes'],
                             'running_minutes': running_total,
                             'dwell_minutes_per_intermediate_station': config['intermediate_dwell_minutes'],
                             'station_order_verified_against_route_stops': bool(route)}


def reachable_edge(line, from_u, from_v, threshold, speed_m_min):
    """Union the reachable intervals from both ends, including partial edges."""
    length = line.length
    a = min(length, max(0., (threshold - from_u) * speed_m_min))
    b = min(length, max(0., (threshold - from_v) * speed_m_min))
    if a + b >= length and (a > 0 or b > 0):
        return [line]
    parts = []
    if a > 0:
        parts.append(substring(line, 0, a))
    if b > 0:
        parts.append(substring(line, length - b, length))
    return parts


def network_model(stations, context, config, project):
    graphfile = CACHE / 'walk.graphml'
    source_hash = hashlib.sha256((CACHE / 'walk.osm').read_bytes()).hexdigest()
    cache_meta = CACHE / 'walk-graph-source.json'
    if graphfile.exists() and cache_meta.exists() and json.loads(cache_meta.read_text())['xml_sha256'] == source_hash:
        graph = ox.load_graphml(graphfile)
    else:
        graph = ox.graph_from_xml(CACHE / 'walk.osm', bidirectional=True, simplify=False, retain_all=True)
        graph = ox.project_graph(graph, to_crs=config['crs'])
        # Metric segment geometry and time come from the same projected endpoints.
        for u, v, key, edge in graph.edges(keys=True, data=True):
            a, b = graph.nodes[u], graph.nodes[v]
            edge['length'] = Point(a['x'], a['y']).distance(Point(b['x'], b['y']))
        ox.save_graphml(graph, graphfile)
        dump(cache_meta, {'xml_sha256': source_hash})
    component = max(nx.weakly_connected_components(graph), key=len)
    graph = graph.subgraph(component).copy()
    speed = config['walking_kph'] * 1000 / 60
    for _, _, _, edge in graph.edges(keys=True, data=True):
        edge['minutes'] = edge['length'] / speed
    ids = list(graph)
    coordinates = np.array([[graph.nodes[n]['x'], graph.nodes[n]['y']] for n in ids])
    entrances = [(e, Point(*project(*e['coordinates']))) for e in context['entrances']]
    seed = '__metro_seeds__'
    graph.add_node(seed)
    for station in stations:
        point = Point(station['x'], station['y'])
        nearby = [(e, p) for e, p in entrances if p.distance(point) < 300
                  and e['tags'].get('access') not in ['no', 'private']]
        accesses = nearby or [({'id': None}, point)]
        station['walking_access_points'] = []
        for entrance, location in accesses:
            distances = np.linalg.norm(coordinates - [location.x, location.y], axis=1)
            i = int(distances.argmin())
            if distances[i] > 180:
                raise ValueError(f'Pedestrian snap too distant: {station["station_name"]}, {distances[i]}')
            cost = station['metro_minutes_from_farmgate'] + config['station_exit_minutes'] + distances[i] / speed
            node = ids[i]
            if not graph.has_edge(seed, node) or cost < graph[seed][node][0]['minutes']:
                graph.add_edge(seed, node, minutes=float(cost), length=0)
            station['walking_access_points'].append({'osm_entrance_node': entrance['id'], 'network_node': node,
                                                     'snap_distance_m': float(distances[i]),
                                                     'station_center_fallback': not bool(nearby)})
    distances = nx.single_source_dijkstra_path_length(graph, seed, cutoff=max(config['thresholds_minutes']), weight='minutes')
    graph.remove_node(seed)
    # Simplification is intentionally postponed: unsimplified links make partial
    # edge interpolation exact for the geometry used by the travel-time weights.
    edges = []
    for u, v, key, edge in graph.edges(keys=True, data=True):
        if u > v:
            continue
        a, b = graph.nodes[u], graph.nodes[v]
        line = LineString([(a['x'], a['y']), (b['x'], b['y'])])
        edges.append((u, v, line))
    water_parts = []
    for feature in context['water']:
        xy = feature['coordinates']
        if len(xy) > 3 and xy[0] == xy[-1]:
            g = transform(project, Polygon(xy))
            if g.is_valid:
                water_parts.append(g)
    water = unary_union(water_parts)
    polygons, stats = {}, {}
    for threshold in config['thresholds_minutes']:
        lines = [piece for u, v, line in edges
                 for piece in reachable_edge(line, distances.get(u, float('inf')), distances.get(v, float('inf')), threshold, speed)]
        if not lines:
            raise ValueError('No reachable pedestrian links')
        buffers = [line.buffer(config['street_envelope_metres'], resolution=4) for line in lines]
        footprint = unary_union(buffers).difference(water)
        footprint = unary_union([p for p in polygon_parts(footprint) if p.area >= config['minimum_component_m2']])
        if not footprint.is_valid:
            raise ValueError('Invalid catchment geometry')
        polygons[threshold] = footprint
        stats[threshold] = {'minutes': threshold, 'area_km2': footprint.area / 1e6,
                            'reachable_stations': sum(s['metro_minutes_from_farmgate'] < threshold for s in stations),
                            'reachable_walk_nodes': sum(t <= threshold for t in distances.values()),
                            'reachable_link_metres': sum(line.length for line in lines),
                            'polygon_parts': len(list(polygon_parts(footprint)))}
        print(f'{threshold} minutes: {stats[threshold]}', flush=True)
    for lower, upper in zip(config['thresholds_minutes'][:-1], config['thresholds_minutes'][1:]):
        outside = polygons[lower].difference(polygons[upper]).area
        if outside > .01:
            raise ValueError(f'Catchments not nested: {outside} m²')
    boundary = transform(project, box(*config['extraction_bbox_wgs84'])).boundary
    if polygons[max(polygons)].distance(boundary) < 200:
        raise ValueError('Catchment approaches network extraction boundary; enlarge source crop')
    return polygons, stats, water, {'walking_graph_nodes': len(graph), 'walking_graph_edges': graph.number_of_edges(),
                                  'reachable_node_count': len(distances) - 1,
                                  'network_boundary_clearance_m': polygons[max(polygons)].distance(boundary)}


def main():
    config = json.loads((DAY / 'config.json').read_text())
    manifest = json.loads((CACHE / 'manifest.json').read_text())
    if hashlib.sha256((CACHE / 'walk.osm').read_bytes()).hexdigest() != manifest['walk_xml_sha256']:
        raise ValueError('Walking source checksum changed')
    context = json.loads((CACHE / 'context.json').read_text())
    project = Transformer.from_crs(4326, config['crs'], always_xy=True).transform
    inverse = Transformer.from_crs(config['crs'], 4326, always_xy=True).transform
    stations = stations_from_osm(context, config, project)
    rail, segments, rail_qa = rail_model(context, stations, config, project)
    polygons, statistics, water, network_qa = network_model(stations, context, config, project)
    features = []
    for threshold in config['thresholds_minutes']:
        feature = {'type': 'Feature', 'properties': {**statistics[threshold],
                   'model': 'Estimated metro + network walking; 60 m street envelope'},
                   'geometry': mapping(transform(inverse, polygons[threshold]))}
        features.append(feature)
        dump(DAY / f'farmgate_{threshold}min.geojson', {'type': 'FeatureCollection', 'features': [feature]})
    dump(DAY / 'farmgate_accessibility.geojson', {'type': 'FeatureCollection', 'features': features})
    station_features = [{'type': 'Feature', 'properties': {k: v for k, v in s.items() if k not in ['x', 'y']},
                         'geometry': mapping(Point(s['longitude'], s['latitude']))} for s in stations]
    dump(DAY / 'dhaka_mrt6_stations.geojson', {'type': 'FeatureCollection', 'features': station_features})
    pd.DataFrame([{k: v for k, v in s.items() if k not in ['x', 'y', 'walking_access_points']} for s in stations]).to_csv(DAY / 'dhaka_mrt6_stations.csv', index=False)
    pd.DataFrame(segments).to_csv(DAY / 'estimated_rail_segments.csv', index=False)
    # Export only quiet map context, not the full source walking network.
    context_features = [{'type': 'Feature', 'properties': {'kind': 'metro'}, 'geometry': mapping(transform(inverse, unary_union(rail)))},
                        {'type': 'Feature', 'properties': {'kind': 'water'}, 'geometry': mapping(transform(inverse, water))}]
    dump(DAY / 'map-context.geojson', {'type': 'FeatureCollection', 'features': context_features})
    report = {'title': 'Dhaka in 45 Minutes', 'origin': config['origin'], 'config': config,
              'config_sha256': hashlib.sha256((DAY / 'config.json').read_bytes()).hexdigest(),
              'statistics': list(statistics.values()), 'rail': rail_qa, 'network': network_qa,
              'source': manifest, 'nested': True, 'valid_geometries': True,
              'farmgate_verified': next(s for s in stations if s['station_name'] == 'Farmgate')}
    dump(DAY / 'map.qa.json', report)
    print('Wrote independently calculated service areas and station dataset.')
    return report


if __name__ == '__main__':
    main()
