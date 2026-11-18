"""Cross-check Day 18 browser data against source QA and agency mileages."""
import gzip
import json
from pathlib import Path

import numpy as np
from pyproj import Geod
from shapely.geometry import LineString, Point, shape

ROOT = Path(__file__).resolve().parent
MILE = 1609.344


def load(name):
    path = ROOT / "assets" / name
    if name.endswith(".gz"):
        return json.loads(gzip.decompress(path.read_bytes()))
    return json.loads(path.read_text())


def validate():
    journey = load("journey.json")
    qa = load("qa.json")
    coords = np.array(journey["route"])
    geod = Geod(ellps="WGS84")
    expected = np.r_[0, np.cumsum(geod.inv(
        *coords[:-1, :2].T, *coords[1:, :2].T)[2]) / MILE]
    assert np.all(np.diff(coords[:, 2]) > 0)
    assert np.max(np.abs(expected - coords[:, 2])) < .001
    assert len(coords) == qa["routeVertices"]
    assert abs(expected[-1] - qa["lengthMiles"]) < .001
    assert abs(expected[-1] - journey["miles"]) < .001
    assert np.allclose(coords[[0, -1], :2], qa["routeEndpoints"], atol=1e-7, rtol=0)
    assert coords[0, 0] > -90.25 and coords[-1, 0] < -104.95
    assert all(a["mile"] < b["mile"] for a, b in zip(journey["places"], journey["places"][1:]))

    highway = LineString(coords[:, :2])
    states = load("states.geojson")["features"]
    kansas = next(shape(s["geometry"]) for s in states if s["properties"]["state"] == "KS")
    crossings = highway.intersection(kansas)
    assert crossings.geom_type == "MultiPoint" and len(crossings.geoms) == 2
    planar = np.r_[0, np.cumsum(np.linalg.norm(np.diff(coords[:, :2], axis=0), axis=1))]
    ks_east, ks_west = sorted(np.interp(highway.project(p), planar, expected) for p in crossings.geoms)
    # Independent reference: FHWA I-70 route log (2002) and CDOT MP 449.59 and 274.
    # Missouri starts a little west of the state line. The Denver finish is east of MP 274.
    measured = [float(ks_east), float(ks_west - ks_east), float(expected[-1] - ks_west)]
    reference = [251.66, 424.15, 449.59 - 274]
    tolerance = [4, 1, 3]
    for state, model, agency, limit in zip(("MO", "KS", "CO"), measured, reference, tolerance):
        assert abs(model - agency) < limit, (state, model, agency)
        print(f"{state}: {model:.2f} measured mi / {agency:.2f} agency-reference mi")

    services = journey["services"]
    assert len(services) == qa["serviceAccessPoints"]
    assert all(a["mile"] < b["mile"] for a, b in zip(services, services[1:]))
    positions = coords[:, 2]
    for service in services:
        assert 0 <= service["snapMeters"] <= 90
        assert 0 < service["toFuelMiles"] <= 2
        assert 0 < service["toInterstateMiles"] <= 2
        assert 0 < service["mergeMile"] - service["mile"] < 4
        for key in ("mile", "mergeMile"):
            assert np.min(np.abs(positions - service[key])) <= .000006
        assert highway.distance(Point(service["coordinates"])) < .055
    gaps = [(b["mile"] - a["mile"], a, b) for a, b in zip(services, services[1:])]
    observed, start, end = max(gaps, key=lambda g: g[0])
    assert abs(observed - journey["gap"]["miles"]) <= .000011
    assert journey["gap"]["from"] == start and journey["gap"]["to"] == end
    assert len(journey["density"]) == qa["populationSamples"]
    assert journey["density"][0][0] == 0
    assert abs(journey["density"][-1][0] - journey["miles"]) < .00001
    assert all(a[0] < b[0] and a[1] >= 0 and b[1] >= 0
               for a, b in zip(journey["density"], journey["density"][1:]))
    for asset, key in (("roads.geojson.gz", "roads"), ("buildings.geojson.gz", "footprints"),
                       ("lights.geojson", "censusLightCells")):
        if (ROOT / "assets" / asset).is_file():
            assert len(load(asset)["features"]) == qa[key]

    index = load("monotony.json")
    segments = index["segments"]
    assert segments[0]["start"] == 0 and segments[-1]["end"] == journey["miles"]
    assert all(a["end"] == b["start"] for a, b in zip(segments, segments[1:]))
    weights = np.array([.15, .30, .40, .15])
    runs = []
    current = []
    for segment in segments:
        if segment["score"] is not None:
            assert abs(weights @ segment["components"] - segment["score"]) < .001
        if segment["score"] is not None and segment["score"] >= index["high"]:
            current.append(segment)
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    eligible = [r for r in runs if r[-1]["end"] - r[0]["start"] >= index["minimumMiles"]]
    expected_headline = max(eligible, key=lambda run: run[-1]["end"] - run[0]["start"], default=None)
    headline = index["longest"]
    if expected_headline:
        assert headline["segmentIds"] == [s["id"] for s in expected_headline]
        assert headline["miles"] == expected_headline[-1]["end"] - expected_headline[0]["start"]
    else:
        assert headline is None

    regions = index["regions"]
    expected_display = []
    for band, (lo, hi) in index["displayBands"].items():
        current = []
        band_regions = []
        for segment in segments + [{"score": None}]:
            if segment["score"] is not None and lo <= segment["score"] < hi:
                current.append(segment)
            elif current:
                if current[-1]["end"] - current[0]["start"] >= index["displayMinimumMiles"]:
                    band_regions.append(current)
                current = []
        expected_display.extend((band, r) for r in band_regions)
        assert len(band_regions) == index["displayStats"][band]["stretches"]
    expected_display.sort(key=lambda pair: pair[1][0]["start"])
    assert len(regions) == len(expected_display)
    polygons = {f["id"]: f for f in load("monotony.geojson")["features"]}
    assert set(polygons) == {r["id"] for r in regions}
    geometries = []
    for region, (band, run) in zip(regions, expected_display):
        assert region["band"] == polygons[region["id"]]["properties"]["band"] == band
        assert region["start"] == run[0]["start"] and region["end"] == run[-1]["end"]
        assert region["segmentIds"] == [s["id"] for s in run]
        geom = shape(polygons[region["id"]]["geometry"])
        assert geom.is_valid and not geom.is_empty
        road_piece = LineString(coords[(positions >= region["start"]) & (positions <= region["end"]), :2])
        assert geom.intersects(road_piece.buffer(.15))
        geometries.append(geom)
    assert all(a.intersection(b).area < 1e-7 for i, a in enumerate(geometries) for b in geometries[i+1:])
    extremes = [r for r in regions if r["band"] == "extreme"]
    assert (index["longestExtreme"] or {}).get("miles", 0) == max((r["miles"] for r in extremes), default=0)
    print(f"Monotony: {len(segments)} segments, {len(polygons)} mapped regions, "
          f"{(index['longest'] or {}).get('miles', 0):.1f} mi longest")

    print(f"Route: {expected[-1]:.2f} mi, {len(coords):,} directed vertices")
    print(f"Gap: {observed:.2f} mi, {start['name']} → {end['name']}, among {len(services)} exits")


if __name__ == "__main__":
    validate()
