"""Build the static Day 18 GIS layers from cached OpenStreetMap and Census data."""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import urlencode

import geopandas as gpd
import networkx as nx
import numpy as np
import osmium
import osmnx as ox
from pyproj import Geod, Transformer
from shapely import STRtree, intersects_xy, make_valid, prepare
from shapely.geometry import LineString, Point, Polygon, box, mapping, shape

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "assets"
CACHE = ROOT.parent / "data/raw/day18"
STATES = ("missouri", "kansas", "colorado")
GEOD = Geod(ellps="WGS84")
PROJECT = Transformer.from_crs(4326, 5070, always_xy=True)
UNPROJECT = Transformer.from_crs(5070, 4326, always_xy=True)
MILE = 1609.344
ENDPOINTS = ((-90.188, 38.635), (-104.987, 39.781))
CENSUS = "https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/Tracts_Blocks/MapServer/0/query"
PLACES = {
    "St. Louis, MO": (-90.1994, 38.6270),
    "Wentzville, MO": (-90.8529, 38.8114),
    "Columbia, MO": (-92.3341, 38.9517),
    "Boonville, MO": (-92.7432, 38.9736),
    "Marshall Junction, MO": (-93.206, 38.963),
    "Kansas City, MO–KS": (-94.5786, 39.0997),
    "Lawrence, KS": (-95.2353, 38.9717),
    "Topeka, KS": (-95.6752, 39.0473),
    "Junction City, KS": (-96.8314, 39.0286),
    "Abilene, KS": (-97.2140, 38.9172),
    "Salina, KS": (-97.6114, 38.8403),
    "Russell, KS": (-98.8598, 38.8953),
    "Hays, KS": (-99.3268, 38.8792),
    "WaKeeney, KS": (-99.8796, 39.0250),
    "Oakley, KS": (-100.8550, 39.1333),
    "Colby, KS": (-101.0524, 39.3958),
    "Goodland, KS": (-101.7102, 39.3508),
    "Burlington, CO": (-102.2694, 39.3061),
    "Stratton, CO": (-102.6046, 39.3033),
    "Flagler, CO": (-103.0671, 39.2931),
    "Limon, CO": (-103.6922, 39.2639),
    "Deer Trail, CO": (-104.0444, 39.6147),
    "Byers, CO": (-104.2277, 39.7114),
    "Bennett, CO": (-104.4275, 39.7589),
    "Denver, CO": (-104.9903, 39.7392),
}
ROAD_TYPES = set("""
motorway motorway_link trunk trunk_link primary primary_link secondary secondary_link
tertiary tertiary_link unclassified residential living_street service
""".split())
MAJOR = {"motorway", "trunk", "primary", "secondary"}


def download(url, path, params=None):
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    url += ("?" + urlencode(params)) if params else ""
    temporary = path.with_suffix(".part")
    subprocess.run(["curl", "-fsSL", "--retry", "2", "--max-time", "300",
                    url, "-o", str(temporary)], check=True)
    temporary.replace(path)


def census_tiles():
    def tile(west):
        path = CACHE / f"tracts-{abs(west)}.geojson"
        download(CENSUS, path, {
            "geometry": f"{west},38.45,{west + 1},40.05", "inSR": 4326,
            "geometryType": "esriGeometryEnvelope", "spatialRel": "esriSpatialRelIntersects",
            "outFields": "GEOID,POP100,AREALAND,AREAWATER", "outSR": 4326,
            "returnGeometry": "true", "resultRecordCount": 4000,
            "geometryPrecision": 5, "f": "geojson",
        })
        result = json.loads(path.read_text())
        if "features" not in result or result.get("properties", {}).get("exceededTransferLimit"):
            raise ValueError(f"Incomplete Census response in {path}")
        return result["features"]

    with ThreadPoolExecutor(max_workers=5) as pool:
        records = {f["properties"]["GEOID"]: f for batch in pool.map(tile, range(-106, -90))
                   for f in batch}
    tracts = gpd.GeoDataFrame.from_features(list(records.values()), crs=4326).to_crs(5070)
    tracts.geometry = tracts.geometry.map(make_valid)
    # Land plus water gives gross density and a denominator consistent with intersections.
    tracts["density"] = tracts.POP100 / (tracts.AREALAND + tracts.AREAWATER) * MILE**2
    return tracts


def highway_ref(ref):
    return "I 70" in re.split(r";\s*", ref)


def road_directions(tags):
    value = tags.get("oneway")
    if value == "-1":
        return (-1,)
    if value in {"no", "0", "false"}:
        return (1, -1)
    if (value in {"yes", "1", "true", "reversible", "alternating"}
            or tags.get("highway") == "motorway" or tags.get("junction") in {"roundabout", "circular"}):
        return () if value in {"reversible", "alternating"} else (1,)
    return (1, -1)


def routable(tags):
    access = next((tags[k] for k in ("motorcar", "motor_vehicle", "vehicle", "access") if k in tags), "")
    return access not in {"no", "private", "agricultural", "forestry", "emergency", "delivery"}


def node_coords(way):
    return [(n.ref, n.lon, n.lat) for n in way.nodes if n.location.valid()]


def route_graph(ways):
    graph = nx.DiGraph()
    for nodes, tags in ways:
        pos = np.array([p[1:] for p in nodes])
        if len(pos) < 2:
            continue
        for node, lon, lat in nodes:
            graph.add_node(node, x=lon, y=lat)
        lengths = ox.distance.great_circle(pos[:-1, 1], pos[:-1, 0], pos[1:, 1], pos[1:, 0])
        for (a, *_), (b, *_), length in zip(nodes, nodes[1:], lengths):
            for direction in road_directions(tags):
                u, v = (a, b) if direction == 1 else (b, a)
                graph.add_edge(u, v, weight=float(length))
    return graph


def locate_route(graph):
    nodes = sorted(graph)
    xy = np.array([(graph.nodes[n]["x"], graph.nodes[n]["y"]) for n in nodes])
    picks = []
    for lon, lat in ENDPOINTS:
        dx = (xy[:, 0] - lon) * math.cos(math.radians(lat))
        near = np.argsort(dx**2 + (xy[:, 1] - lat)**2)
        # Westbound and eastbound are close. Accept only west-facing mainline anchors.
        picks.append([nodes[i] for i in near[:50] if any(
            graph.nodes[v]["x"] < graph.nodes[nodes[i]]["x"]
            for v in graph.successors(nodes[i]))])
    if not all(picks):
        raise ValueError("No west-facing endpoint candidate")
    route = nx.shortest_path(graph, picks[0][0], picks[1][0], weight="weight")
    lonlat = np.array([(graph.nodes[n]["x"], graph.nodes[n]["y"]) for n in route])
    meters = GEOD.inv(*lonlat[:-1].T, *lonlat[1:].T)[2]
    if min(meters) <= 0 or max(meters) > 6500 or not 830 < sum(meters) / MILE < 870:
        raise ValueError("Route continuity or total distance check failed")
    return route, lonlat, np.r_[0, np.cumsum(meters)]



def pbf_ways(paths):
    seen = set()
    for path in paths:
        for item in osmium.FileProcessor(path).with_locations().with_filter(osmium.filter.KeyFilter("highway")):
            if not item.is_way() or item.id in seen:
                continue
            if item.tags.get("highway") not in {"motorway", "motorway_link", "trunk", "trunk_link"}:
                continue
            tags = dict(item.tags)
            if not routable(tags):
                continue
            # This Columbia mainline segment is missing the route ref.
            if not highway_ref(tags.get("ref", "")) and item.id != 1524427900:
                continue
            nodes = node_coords(item)
            if len(nodes) == len(item.nodes):
                seen.add(item.id)
                yield nodes, tags


def route_with_archived_topeka(paths):
    graph = route_graph(pbf_ways(paths))
    try:
        return (*locate_route(graph), None, set())
    except nx.NetworkXNoPath:
        archived = json.loads((ROOT / "source/topeka-preclosure.json").read_text())
        nodes = archived["nodes"]
        for i in (0, -1):
            key, lon, lat = nodes[i]
            if key not in graph:
                raise ValueError("Topeka archival endpoint is missing from the current I-70 graph")
            current = graph.nodes[key]
            if GEOD.inv(lon, lat, current["x"], current["y"])[2] > 25:
                raise ValueError("Topeka archival endpoint moved more than 25 meters")
            nodes[i] = (key, current["x"], current["y"])
        backup = route_graph([(nodes, {"highway": "motorway", "oneway": "yes"})])
        graph.update(backup)
        route, lonlat, meters = locate_route(graph)
        if any(n not in route for n, *_ in nodes):
            raise ValueError("Topeka archival trace was not incorporated in order")
        return route, lonlat, meters, archived["timestamp"], {n for n, *_ in nodes}


def feature(geometry, **properties):
    return {"type": "Feature", "geometry": geometry, "properties": properties}


def geo_line(coords):
    return {"type": "LineString", "coordinates": [[round(x, 6), round(y, 6)] for x, y in coords]}


def point_feature(lon, lat, **properties):
    return feature({"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]}, **properties)


def height(tags):
    value = re.fullmatch(r"([0-9.]+)\s*(m|ft)?", tags.get("height", "").strip())
    try:
        if value:
            return max(2.5, min(350, float(value[1]) * (0.3048 if value[2] == "ft" else 1))), True
        if tags.get("building:levels"):
            return max(2.5, min(350, 3.2 * float(tags["building:levels"]))), False
    except ValueError:
        pass
    return (7 if tags.get("building") in {"industrial", "commercial", "retail"} else 4.6), False


def collect_detail(paths, route, xy, archived_nodes):
    line = LineString(xy)
    outer = line.buffer(28000, quad_segs=4)
    inner = line.buffer(4750, quad_segs=4)
    building_zone = line.buffer(2450, quad_segs=4)
    for geom in (outer, inner, building_zone):
        prepare(geom)
    route_index = {key: i for i, key in enumerate(route)}
    seen = set()
    roads, fuels = [], []
    buildings = defaultdict(list)
    graph = nx.DiGraph()
    exit_nodes, entry_nodes = set(), set()
    snap_edges = {}
    for path in paths:
        processor = (osmium.FileProcessor(path).with_locations()
                     .with_filter(osmium.filter.KeyFilter("amenity", "building", "highway")))
        for item in processor:
            if item.tags.get("amenity") == "fuel" and routable(item.tags):
                if item.is_node() and item.location.valid():
                    lon, lat = item.lon, item.lat
                elif item.is_way():
                    nodes = node_coords(item)
                    if len(nodes) < 3:
                        continue
                    lon, lat = Polygon([n[1:] for n in nodes]).representative_point().coords[0]
                else:
                    continue
                p = Point(PROJECT.transform(lon, lat))
                token = ("fuel", item.is_node(), item.id)
                if token not in seen and inner.intersects(p):
                    fuels.append((p, item.tags.get("name") or item.tags.get("brand") or "Mapped fuel station"))
                    seen.add(token)
            if not item.is_way() or item.id in seen:
                continue
            highway = item.tags.get("highway")
            is_building = "building" in item.tags and item.tags["building"] != "no"
            if highway not in ROAD_TYPES and not is_building:
                continue
            first = item.nodes[0].location
            if not first.valid():
                continue
            x, y = PROJECT.transform(first.lon, first.lat)
            # Building footprints have a different selection window from the road graph.
            if is_building and highway not in ROAD_TYPES:
                if not intersects_xy(building_zone, x, y):
                    continue
                nodes = node_coords(item)
                if len(nodes) < 4 or nodes[0][0] != nodes[-1][0]:
                    continue
                lons, lats = np.array([p[1:] for p in nodes]).T
                polygon = Polygon(np.column_stack(PROJECT.transform(lons, lats)))
                simple = polygon.simplify(2.0)
                if simple.geom_type != "Polygon" or not simple.is_valid or simple.area < 42:
                    continue
                h, measured = height(item.tags)
                cell = (int(x // 260), int(y // 260))
                buildings[cell].append((simple, h, measured))
                seen.add(item.id)
                continue

            tags = dict(item.tags)
            if highway not in MAJOR and not intersects_xy(outer, x, y):
                continue
            nodes = node_coords(item)
            if len(nodes) < 2 or len(nodes) != len(item.nodes):
                continue
            lons, lats = np.array([p[1:] for p in nodes]).T
            coords = np.column_stack(PROJECT.transform(lons, lats))
            road = LineString(coords)
            if not outer.intersects(road):
                continue
            seen.add(item.id)
            near = inner.intersects(road)
            if highway in MAJOR or (near and highway in {"motorway_link", "trunk_link", "tertiary", "residential", "unclassified", "secondary_link", "primary_link"}):
                simple = road.simplify(15 if highway in MAJOR else 9)
                roads.append((simple, highway in MAJOR))
            # Never traverse any motorway between exit and merge, in either direction.
            if not near or highway == "motorway" or not routable(tags):
                continue
            for (a, *_), (b, *_), p, q in zip(nodes, nodes[1:], coords, coords[1:]):
                weight = float(np.linalg.norm(q - p))
                if not weight:
                    continue
                # Exclude I-70 mainline segments in case a short section has another highway tag.
                if a in route_index and b in route_index:
                    continue
                for direction in road_directions(tags):
                    u, v = (a, b) if direction == 1 else (b, a)
                    graph.add_edge(u, v, weight=weight)
                    if highway == "motorway_link" and u in route_index and u not in archived_nodes:
                        exit_nodes.add(u)
                    if highway == "motorway_link" and v in route_index and v not in archived_nodes:
                        entry_nodes.add(v)
                if a not in route_index and b not in route_index and highway not in {"motorway_link", "trunk_link"}:
                    snap_edges.setdefault((a, b), LineString((p, q)))
    return roads, buildings, fuels, graph, snap_edges, exit_nodes, entry_nodes


def qualify_services(detail, route, meters):
    _, _, fuels, graph, snap_edges, exits, entries = detail
    index = {key: i for i, key in enumerate(route)}
    edges = list(snap_edges)
    lines = list(snap_edges.values())
    tree = STRtree(lines)
    reverse = graph.reverse(copy=False)
    records = {}
    cutoff = 2 * MILE

    def paths_from(start, cost, network, targets):
        if start not in network or cost > cutoff:
            return {}
        found = nx.single_source_dijkstra_path_length(network, start, cutoff - cost, weight="weight")
        return {n: length + cost for n, length in found.items() if n in targets}

    for p, name in fuels:
        hits = tree.query(p, predicate="dwithin", distance=90)
        if not len(hits):
            continue
        # Use the closest mapped road, preferring a mapped driveway when it actually is closest.
        i = min(hits, key=lambda j: (lines[j].distance(p), edges[j]))
        line = lines[i]
        along = line.project(p)
        spur = line.distance(p)
        a, b = edges[i]
        inbound, outbound = {}, {}
        for u, v, fraction in ((a, b, along), (b, a, line.length - along)):
            if not graph.has_edge(u, v):
                continue
            for target, length in paths_from(u, fraction + spur, reverse, exits).items():
                inbound[target] = min(inbound.get(target, math.inf), length)
            for target, length in paths_from(v, line.length - fraction + spur, graph, entries).items():
                outbound[target] = min(outbound.get(target, math.inf), length)
        pairs = [(arrival + departure, index[exit], index[merge], arrival, departure)
                 for exit, arrival in inbound.items() for merge, departure in outbound.items()
                 if 0 < meters[index[merge]] - meters[index[exit]] < 4 * MILE]
        if not pairs:
            continue
        detour, start, end, arrival, departure = min(pairs)
        lon, lat = UNPROJECT.transform(p.x, p.y)
        candidate = {"name": name, "coordinates": [round(lon, 6), round(lat, 6)],
                     "mile": round(float(meters[start] / MILE), 5),
                     "mergeMile": round(float(meters[end] / MILE), 5),
                     "exitNode": route[start], "mergeNode": route[end],
                     "toFuelMiles": round(arrival / MILE, 4), "toInterstateMiles": round(departure / MILE, 4),
                     "snapMeters": round(spur, 2)}
        if start not in records or detour < records[start][0]:
            records[start] = detour, candidate
    return [records[i][1] for i in sorted(records)]


def population(tracts, line, xy, meters):
    geometry = tracts.geometry.to_numpy()
    tree = STRtree(geometry)
    density = tracts.density.to_numpy()
    radius = 8000
    samples = []
    for station in np.append(np.arange(0, meters[-1], 4000), meters[-1]):
        location = Point(np.interp(station, meters, xy[:, 0]), np.interp(station, meters, xy[:, 1]))
        window = location.buffer(radius, quad_segs=24)
        indices = tree.query(window, predicate="intersects")
        areas = np.array([window.intersection(geometry[i]).area for i in indices])
        coverage = areas.sum() / window.area
        if not .985 < coverage < 1.015:
            raise ValueError(f"Census coverage {coverage:.3f} at mile {station / MILE:.2f}")
        samples.append([round(station / MILE, 5), round(float(density[indices] @ areas / window.area), 2)])
    clipped = tracts.iloc[tree.query(line.buffer(27000), predicate="intersects")]
    lights = []
    # Display one light per fixed-area grid cell, never a fictitious town marker.
    band = line.buffer(25000, quad_segs=4)
    prepare(band)
    lo_x, lo_y, hi_x, hi_y = band.bounds
    for x in np.arange(math.floor(lo_x / 3300) * 3300, hi_x, 3300):
        for y in np.arange(math.floor(lo_y / 3300) * 3300, hi_y, 3300):
            if not intersects_xy(band, x, y):
                continue
            p = Point(x, y)
            indices = tree.query(p, predicate="within")
            if len(indices) != 1 or density[indices[0]] < 1:
                continue
            lon, lat = UNPROJECT.transform(x, y)
            lights.append(point_feature(lon, lat, density=round(float(density[indices[0]]), 1)))
    return samples, lights, len(clipped)


def output_json(name, payload):
    payload_bytes = json.dumps(payload, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    if name.endswith(".gz"):
        payload_bytes = gzip.compress(payload_bytes, compresslevel=6, mtime=0)
    with tempfile.NamedTemporaryFile(dir=OUTPUT, delete=False) as stream:
        stream.write(payload_bytes)
        temporary = Path(stream.name)
    temporary.chmod(0o644)
    temporary.replace(OUTPUT / name)


def collection(features):
    return {"type": "FeatureCollection", "features": features}


def build(paths, tracts):
    route, lonlat, meters, topeka_archive, archived_nodes = route_with_archived_topeka(paths)
    print(f"Continuous route: {meters[-1] / MILE:.3f} mi, {len(route):,} vertices", flush=True)
    xy = np.column_stack(PROJECT.transform(*lonlat.T))
    line = LineString(xy)
    detail = collect_detail(paths, route, xy, archived_nodes)
    roads, buildings, fuels, graph, _, exits, entries = detail
    print(f"{len(fuels)} fuel candidates, {len(exits)} westbound exits, "
          f"{len(entries)} westbound merges, {graph.number_of_edges():,} street edges", flush=True)
    services = qualify_services(detail, route, meters)
    if len(services) < 2:
        raise ValueError("Insufficient network-qualified fuel access points")
    start, end = max(zip(services, services[1:]), key=lambda pair: pair[1]["mile"] - pair[0]["mile"])
    station = lambda p: int(np.argmin(np.linalg.norm(xy - PROJECT.transform(*p), axis=1)))
    places = []
    for name, p in PLACES.items():
        idx = station(p)
        distance = np.linalg.norm(xy[idx] - PROJECT.transform(*p))
        if distance > 16000:
            raise ValueError(f"I-70 missed validation place {name}")
        places.append({"name": name, "mile": round(meters[idx] / MILE, 5), "coordinates": list(p),
                       "offsetMiles": round(float(distance) / MILE, 2)})
    samples, lights, tract_count = population(tracts, line, xy, meters)
    revisions = {}
    for path in paths:
        with osmium.io.Reader(str(path)) as reader:
            timestamp = reader.header().get("osmosis_replication_timestamp")
        with path.open("rb") as stream:
            sha = hashlib.file_digest(stream, "sha256").hexdigest()
        revisions[path.stem.split(".")[0]] = {"timestamp": timestamp, "sha256": sha}

    a, b = route.index(start["exitNode"]), route.index(end["exitNode"])
    output_json("journey.json", {
        "route": [[round(x, 7), round(y, 7), round(m / MILE, 6)] for (x, y), m in zip(lonlat, meters)],
        "miles": round(meters[-1] / MILE, 6), "places": places, "services": services,
        "density": samples,
        "gap": {"from": start, "to": end, "miles": round((meters[b] - meters[a]) / MILE, 5)},
    })
    output_json("roads.geojson.gz", collection([
        feature(geo_line(zip(*UNPROJECT.transform(*np.asarray(road.coords).T))), major=int(major))
        for road, major in roads
    ]))
    footprints = []
    for cell in buildings.values():
        for poly, h, measured in sorted(cell, key=lambda item: item[0].area, reverse=True)[:5]:
            ring = geo_line(zip(*UNPROJECT.transform(*np.asarray(poly.exterior.coords).T)))["coordinates"]
            footprints.append(feature({"type": "Polygon", "coordinates": [ring]}, h=round(h, 1), measured=measured))
    output_json("buildings.geojson.gz", collection(footprints))
    output_json("lights.geojson", collection(lights))
    output_json("qa.json", {
        "osm": revisions, "topekaArchive": topeka_archive, "tracts": tract_count, "populationSamples": len(samples),
        "routeVertices": len(route), "lengthMiles": round(meters[-1] / MILE, 5),
        "routeEndpoints": lonlat[[0, -1]].tolist(),
        "maxRouteEdgeMeters": round(float(np.diff(meters).max()), 2),
        "fuelCandidates": len(fuels), "serviceAccessPoints": len(services),
        "westboundExitNodes": len(exits), "westboundMergeNodes": len(entries),
        "footprints": len(footprints), "taggedHeights": sum(f["properties"]["measured"] for f in footprints),
        "roads": len(roads), "censusLightCells": len(lights),
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Download missing Geofabrik extracts")
    args = parser.parse_args()
    paths = [CACHE / f"{state}.osm.pbf" for state in STATES]
    if args.fetch:
        for state, path in zip(STATES, paths):
            download(f"https://download.geofabrik.de/north-america/us/{state}-latest.osm.pbf", path)
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        parser.error("Missing extracts. Run with --fetch. " + ", ".join(missing))
    OUTPUT.mkdir(exist_ok=True)
    build(paths, census_tiles())


if __name__ == "__main__":
    main()
