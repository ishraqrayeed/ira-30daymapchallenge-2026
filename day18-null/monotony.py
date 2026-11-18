"""Build the Driving Monotony Index and geographic reveal polygons."""
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import urlencode

import geopandas as gpd
import numpy as np
from PIL import Image
import rasterio
from rasterio.features import geometry_mask, shapes
from rasterio.transform import from_bounds, rowcol
from pyproj import Transformer
from scipy.ndimage import uniform_filter
from scipy.spatial import cKDTree
from shapely import union_all
from shapely.geometry import LineString, Polygon, mapping, shape
from shapely.ops import substring

ROOT = Path(__file__).resolve().parent
CACHE = ROOT.parent / "data/raw/day18"
BOUNDS = (-795000, 1720000, 530000, 1930000)
WIDTH, HEIGHT = 2650, 420
MILE = 1609.344
HIGH, MIN_RUN = 80, 15
DISPLAY_MIN = 10
BANDS = {"moderate": (55, 70), "high": (70, 85), "extreme": (85, 101)}
WEIGHTS = np.array([.15, .30, .40, .15])
WINDOWS = (1, 3, 5, 9)
SCENIC_WINDOW = 3
# Published MRLC palette. Unexpected or transparent pixels are missing observations.
COLORS = {(71,107,160), (219,216,61), (221,201,201), (216,147,130), (237,0,0),
          (170,0,0), (178,173,163), (104,170,99), (28,99,48), (181,201,142),
          (204,186,124), (226,226,193), (186,216,234), (170,112,40), (112,163,186)}
COVER_URL = "https://www.mrlc.gov/geoserver/mrlc_display/wms"
DEM_URL = "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage"


def fetch(url, params, filename):
    path = CACHE / filename
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        pending = path.with_suffix(".part")
        subprocess.run(["curl", "-fsSL", "--retry", "2", "--max-time", "90",
                        url + "?" + urlencode(params), "-o", str(pending)], check=True)
        pending.replace(path)
    return path


def clean_patch(geometry):
    """Generalize the lens-scale land-cover silhouette in equal-area meters."""
    geometry = geometry.simplify(850, preserve_topology=True)
    parts = [geometry] if geometry.geom_type == "Polygon" else list(geometry.geoms)
    retained = [Polygon(p.exterior, [ring for ring in p.interiors if Polygon(ring).area >= 1.5e6])
                for p in parts if p.geom_type == "Polygon" and p.area >= 3e6]
    return union_all(retained)


def main():
    bbox = ",".join(map(str, BOUNDS))
    cover_path = fetch(COVER_URL, {
        "service": "WMS", "version": "1.1.1", "request": "GetMap",
        "layers": "NLCD_2021_Land_Cover_L48", "styles": "", "srs": "EPSG:5070",
        "bbox": bbox, "width": WIDTH, "height": HEIGHT, "format": "image/png",
    }, "nlcd-2021.png")
    dem_path = fetch(DEM_URL, {
        "bbox": bbox, "bboxSR": 5070, "imageSR": 5070, "size": f"{WIDTH},{HEIGHT}",
        "format": "tiff", "pixelType": "F32", "interpolation": "RSP_BilinearInterpolation", "f": "image",
    }, "elevation-3dep.tif")
    transform = from_bounds(*BOUNDS, WIDTH, HEIGHT)
    with Image.open(cover_path) as image:
        rgba = np.asarray(image.convert("RGBA"))
        rgb = rgba[:, :, :3]
    palette, cover = np.unique(rgb.reshape(-1, 3), axis=0, return_inverse=True)
    cover = cover.reshape(HEIGHT, WIDTH)
    known = np.array([tuple(c) in COLORS for c in palette])[cover] & (rgba[:, :, 3] == 255)
    with rasterio.open(dem_path) as raster:
        assert raster.crs.to_epsg() == 5070 and raster.transform.almost_equals(transform)
        dem = raster.read(1, masked=True).filled(np.nan)

    slope = np.hypot(*np.gradient(dem, 500)) * 100
    layers = [(known & (cover == i)).astype(np.float32) for i in range(len(palette))]
    modes = {}
    for size in WINDOWS:
        votes = np.stack([uniform_filter(layer, size=size) for layer in layers])
        modes[size] = np.where(known & (votes.sum(axis=0) >= .995), np.argmax(votes, axis=0), -1)
    journey = json.loads((ROOT / "assets/journey.json").read_text())
    route = np.asarray(journey["route"])
    projector = Transformer.from_crs(4326, 5070, always_xy=True)
    xy = np.column_stack(projector.transform(*route[:, :2].T))
    planar = np.r_[0, np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))]
    line = LineString(xy)
    stations = np.r_[np.arange(0, journey["miles"], 8), journey["miles"]]
    scenarios = {f"{model}-{w}": [] for model in ("original", "weighted") for w in WINDOWS}
    dominant_classes = {}
    for idx, (a, b) in enumerate(zip(stations, stations[1:])):
        start, end = np.interp([a, b], route[:, 2], planar)
        piece = substring(line, start, end)
        corridor = piece.buffer(7 * MILE, quad_segs=8)
        inside = geometry_mask([mapping(corridor)], cover.shape, transform, invert=True)
        counts = np.bincount(cover[inside & known], minlength=len(palette))
        dominant_classes[idx] = int(np.argmax(counts))
        samples = np.linspace(start, end, max(3, int((end - start) / 500)))
        sample_xy = np.array([piece.interpolate(m - start).coords[0] for m in samples])
        rows, cols = rowcol(transform, *sample_xy.T)
        endpoint_a, endpoint_b = piece.boundary.geoms
        common = [
            np.clip((endpoint_a.distance(endpoint_b) / piece.length - .82) / .18, 0, 1),
            1 - np.clip(np.nanpercentile(slope[inside], 75) / 6, 0, 1),
            counts.max() / max(counts.sum(), 1),
        ]
        for size, mode in modes.items():
            classes = mode[rows, cols]
            complete = (known[inside].mean() >= .995 and np.isfinite(slope[inside]).mean() >= .995
                        and bool(np.all(classes >= 0)))
            components = np.array([*common, np.mean(classes[1:] == classes[:-1])]) * 100
            for model, weights in (("original", np.full(4, .25)), ("weighted", WEIGHTS)):
                score = round(float(components @ weights), 3) if complete else None
                scenarios[f"{model}-{size}"].append({
                    "id": idx, "start": round(float(a), 6), "end": round(float(b), 6),
                    "score": score, "components": np.round(components, 3).tolist() if complete else None,
                })

    scores = scenarios[f"weighted-{SCENIC_WINDOW}"]
    # Use the exact archived formula as the baseline, including the original tie handling.
    baseline = scenarios["original-5"]
    for window in WINDOWS:
        # Record each scenario whether or not it produces a qualifying run.
        assert len(scenarios[f"weighted-{window}"]) == len(baseline)
    diagnostics = {name: summarize(items) for name, items in scenarios.items()}
    (ROOT / "assets/monotony-diagnostics.json").write_text(json.dumps(diagnostics, indent=2, allow_nan=False))
    def describe_run(run):
        a, b = run[0]["start"], run[-1]["end"]
        return {"start": a, "end": b, "miles": round(b - a, 6),
                "startPlace": describe(a, journey), "endPlace": describe(b, journey),
                "segmentIds": [s["id"] for s in run]}

    headline = qualifying_runs(scores, HIGH, MIN_RUN)
    longest = max(map(describe_run, headline), key=lambda r: r["miles"], default=None)
    band_runs = {band: qualifying_runs(scores, low, DISPLAY_MIN, high)
                 for band, (low, high) in BANDS.items()}
    runs = sorted(((run, band) for band, items in band_runs.items() for run in items),
                  key=lambda pair: pair[0][0]["start"])
    samples = np.linspace(0, line.length, int(line.length / 500) + 1)
    tree = cKDTree([line.interpolate(m).coords[0] for m in samples])
    cols, rows = np.meshgrid(np.arange(WIDTH) + .5, np.arange(HEIGHT) + .5)
    east, north = transform * (cols, rows)
    distance, nearest = tree.query(np.column_stack((east.ravel(), north.ravel())))
    nearest_mile = np.interp(samples[nearest], planar, route[:, 2]).reshape(cover.shape)
    within_search = distance.reshape(cover.shape) <= 20 * MILE
    covered = union_all([])
    regions, records = [], []
    for run, band in runs:
        a, b = run[0]["start"], run[-1]["end"]
        start, end = np.interp([a, b], route[:, 2], planar)
        piece = substring(line, start, end)
        seed = piece.buffer(7 * MILE, quad_segs=8)
        extent = within_search & (nearest_mile >= a) & (nearest_mile < b)
        classes = {dominant_classes[s["id"]] for s in run}
        parts = []
        for category in classes:
            selected = extent & (modes[9] == category)
            for geometry, _ in shapes(selected.astype(np.uint8), mask=selected, transform=transform):
                patch = shape(geometry).buffer(0)
                if patch.area >= 12e6 and patch.intersection(seed).area >= 4e6:
                    parts.append(patch)
        patch = clean_patch(union_all(parts)).difference(covered).buffer(0)
        if patch.is_empty:
            raise ValueError(f"No distinctive cover region for qualifying run at mile {a}")
        covered = covered.union(patch)
        region = {"id": len(regions), "band": band, **describe_run(run)}
        regions.append(region)
        records.append({"id": region["id"], "band": band, "geometry": patch})
    frame = gpd.GeoDataFrame(records, geometry="geometry", crs=5070).to_crs(4326)
    rounded = []
    covered_wgs84 = union_all([])
    for geom in frame.geometry:
        clipped = geom.difference(covered_wgs84)
        rounded.append(clipped)
        covered_wgs84 = covered_wgs84.union(clipped)
    frame.geometry = rounded
    out = json.loads(frame.to_json(drop_id=True))
    for feature in out["features"]:
        feature["id"] = feature["properties"]["id"]
    stats = {}
    for band, (low, high) in BANDS.items():
        raw = qualifying_runs(scores, low, maximum=high)
        raw_miles = sum(run[-1]["end"] - run[0]["start"] for run in raw)
        stats[band] = {"classifiedMiles": round(raw_miles, 6),
                       "classifiedPercent": round(raw_miles / journey["miles"] * 100, 2),
                       "min8": {"count": sum(run[-1]["end"] - run[0]["start"] >= 8 for run in raw),
                                "miles": round(sum(run[-1]["end"] - run[0]["start"] for run in raw
                                                   if run[-1]["end"] - run[0]["start"] >= 8), 6)},
                       "shownMiles": round(sum(r["miles"] for r in regions if r["band"] == band), 6),
                       "stretches": len(band_runs[band])}
    payload = {"segments": scores, "regions": regions, "longest": longest,
               "longestExtreme": max(map(describe_run, band_runs["extreme"]),
                                     key=lambda r: r["miles"], default=None),
               "displayBands": BANDS, "displayMinimumMiles": DISPLAY_MIN, "displayStats": stats,
               "high": HIGH, "minimumMiles": MIN_RUN, "corridorHalfWidthMiles": 7,
               "sources": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (cover_path, dem_path)}}
    for name, contents in (("monotony.geojson", out), ("monotony.json", payload)):
        (ROOT / "assets" / name).write_text(json.dumps(contents, separators=(",", ":"), allow_nan=False))
    print(stats)


def qualifying_runs(segments, threshold, minimum=0, maximum=101):
    runs = []
    current = []
    for s in segments:
        if s["score"] is not None and threshold <= s["score"] < maximum:
            current.append(s)
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    return [r for r in runs if r[-1]["end"] - r[0]["start"] >= minimum]


def summarize(segments):
    total = segments[-1]["end"]
    valid = [s for s in segments if s["score"] is not None]
    scores = np.array([s["score"] for s in valid])
    components = np.array([s["components"] for s in valid])
    def stats(values):
        return np.round(np.percentile(values, [0, 10, 25, 50, 75, 90, 100], axis=0), 2).tolist()
    categories = {}
    for lo, hi in zip([0, 70, 75, 80, 83, 85, 90], [70, 75, 80, 83, 85, 90, 101]):
        categories[f"{lo}–{hi}"] = round(sum(s["end"] - s["start"] for s in valid if lo <= s["score"] < hi) / total * 100, 2)
    thresholds = {}
    for t in (70, 75, 80, 83, 85, 90):
        runs = qualifying_runs(segments, t)
        intervals = sorted(([r[0]["start"], r[-1]["end"]] for r in runs), key=lambda p: p[1]-p[0], reverse=True)
        lengths = [b-a for a,b in intervals]
        thresholds[t] = {"anyPct": round(sum(lengths)/total*100, 2),
                         "min15Pct": round(sum(v for v in lengths if v >= 15)/total*100, 2),
                         "runs": [[a, b, round(b-a, 3)] for a,b in intervals]}
    return {"scoreQuantiles": stats(scores), "componentQuantiles": stats(components),
            "pearson": np.round(np.corrcoef(components.T), 3).tolist(), "categoriesPct": categories,
            "missingMiles": round(sum(s["end"] - s["start"] for s in segments if s["score"] is None), 3),
            "thresholds": thresholds}


def describe(mile, journey):
    near = min(journey["places"], key=lambda p: abs(mile - p["mile"]))
    delta = mile - near["mile"]
    return (f"{abs(delta):.1f} mi {'west' if delta >= 0 else 'east'} of {near['name']}"
            if abs(delta) >= 1 else f"Near {near['name']}")


if __name__ == "__main__":
    main()
