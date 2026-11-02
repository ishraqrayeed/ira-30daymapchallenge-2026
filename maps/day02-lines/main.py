"""Build the self-contained circular trail map from cached NPS/USGS data."""

import base64
import hashlib
from collections import Counter, defaultdict
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
from matplotlib.colors import LightSource
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw
from pyproj import Transformer
import rasterio
from shapely.geometry import LineString, shape
from shapely.ops import transform, unary_union
from shapely import line_merge, union_all

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data.download import write_json

DAY = Path(__file__).resolve().parent
CACHE = ROOT / "data/raw/day02-lines"
MIN_SEGMENT_METRES = 0.5 * 1609.344
PALETTE = [[7500, "#38694D"], [9000, "#697B48"], [10500, "#B58A45"],
           [12000, "#B65D40"], [14000, "#76546F"]]


def hiking_feature(properties):
    return ("Hiker/Pedestrian" in (properties.get("TRLUSE") or "")
            and properties.get("TRLSTATUS") == "Existing"
            and str(properties.get("ISEXTANT")).lower() != "false"
            and str(properties.get("OPENTOPUBLIC")).lower() not in {"false", "no"})


def dissolve_named_parts(parts):
    """Remove exact overlap and join touching lines; preserve separate branches."""
    return list(line_parts(line_merge(union_all(parts))))


def line_parts(geometry):
    if geometry.geom_type == "LineString":
        yield geometry
    elif hasattr(geometry, "geoms"):
        for part in geometry.geoms:
            yield from line_parts(part)


def remove_isolated_compact_segments(mapped, metres_per_unit):
    """Omit tiny detached footprints; retain connected paths and genuine loops."""
    geometries = [LineString([p[:2] for p in t["points"]]) for t in mapped]
    keep, omitted = [], []
    for i, (trail, geometry) in enumerate(zip(mapped, geometries)):
        xmin, ymin, xmax, ymax = geometry.bounds
        footprint = max(xmax - xmin, ymax - ymin) * metres_per_unit
        isolated = all(geometry.distance(other) * metres_per_unit > 100
                       for j, other in enumerate(geometries) if j != i)
        (omitted if footprint < 600 and isolated else keep).append(trail)
    return keep, omitted


def bilinear(grid, affine, xy):
    """Sample pixel centers; fail rather than silently extrapolate beyond coverage."""
    x, y = xy[:, 0], xy[:, 1]
    col = (x - affine.c) / affine.a - .5
    row = (y - affine.f) / affine.e - .5
    if np.any(col < 0) or np.any(row < 0) or np.any(col >= grid.shape[1] - 1) or np.any(row >= grid.shape[0] - 1):
        raise ValueError("Trail sample lies outside elevation coverage")
    c, r = col.astype(int), row.astype(int)
    dc, dr = col - c, row - r
    result = ((1 - dc) * (1 - dr) * grid[r, c] + dc * (1 - dr) * grid[r, c + 1]
              + (1 - dc) * dr * grid[r + 1, c] + dc * dr * grid[r + 1, c + 1])
    if not np.all(np.isfinite(result)) or np.any(result < 1500) or np.any(result > 5000):
        raise ValueError("Missing or implausible trail elevations")
    return result


def main():
    trails = json.loads((CACHE / "trails.geojson").read_text())["features"]
    boundaries = json.loads((CACHE / "boundary.geojson").read_text())["features"]
    manifest = json.loads((CACHE / "manifest.json").read_text())
    for name, filename in [("trails", "trails.geojson"), ("boundary", "boundary.geojson"),
                           ("elevation", "elevation.tif")]:
        actual = hashlib.sha256((CACHE / filename).read_bytes()).hexdigest()
        if actual != manifest["sources"][name]["sha256"]:
            raise ValueError(f"Cached {name} disagrees with provenance manifest")
    projection = Transformer.from_crs(4326, 26913, always_xy=True).transform
    park = transform(projection, unary_union([shape(f["geometry"]) for f in boundaries]))
    if park.is_empty or not park.is_valid:
        raise ValueError("Invalid park boundary")
    with rasterio.open(CACHE / "elevation.tif") as dataset:
        grid = dataset.read(1, masked=True)
        if grid.count() != grid.size:
            raise ValueError("Elevation grid has missing cells")
        grid = np.asarray(grid)
        affine, bounds = dataset.transform, dataset.bounds
        resolution = affine.a
    span = bounds.right - bounds.left

    def screen(x, y):
        return [(x - bounds.left) / span * 1000, (bounds.top - y) / span * 1000]

    # Local UTM hillshade has true metre spacing; colors remain neutral so that
    # elevation is encoded only by the trails. This is a map asset, not an export.
    hill = LightSource(azdeg=315, altdeg=45).hillshade(grid, dx=resolution, dy=resolution, vert_exag=1.25)
    base = np.array([235, 230, 214], dtype=float)
    shade = .76 + hill[..., None] * .25
    rgb = np.clip(base * shade, 0, 255).astype("uint8")
    terrain = Image.fromarray(rgb)
    draw = ImageDraw.Draw(terrain)
    fig, ax = plt.subplots()
    contours = ax.contour(grid[::3, ::3], levels=np.arange(2000, 4501, 250))
    for level in contours.allsegs:
        for line in level:
            if len(line) > 10:
                points = [(float(x * 3), float(y * 3)) for x, y in line]
                draw.line(points, fill=(193, 187, 166), width=1)
    plt.close(fig)
    buffer = io.BytesIO()
    terrain.save(buffer, format="WEBP", quality=88)

    exclusions = Counter()
    seen = set()
    mapped = []
    grouped = defaultdict(list)
    source_members = defaultdict(set)
    names = {}
    dates = []
    clipped_sources = set()
    for feature in trails:
        props = feature["properties"]
        if not hiking_feature(props):
            exclusions["not_existing_hiking_use"] += 1
            continue
        if not feature.get("geometry"):
            exclusions["missing_geometry"] += 1
            continue
        original = transform(projection, shape(feature["geometry"]))
        if not original.is_valid or original.is_empty:
            exclusions["invalid_geometry"] += 1
            continue
        clipped = original.intersection(park)
        if clipped.is_empty:
            exclusions["outside_boundary"] += 1
            continue
        if original.difference(park).length > .1:
            clipped_sources.add(props["OBJECTID"])
        name = " ".join((props.get("TRLNAME") or "Unnamed trail").split())
        key = name.casefold()
        names.setdefault(key, name)
        grouped[key].extend(line_parts(clipped))
        source_members[key].add(props["OBJECTID"])
        if props.get("EDITDATE"):
            dates.append(props["EDITDATE"])
    raw_piece_count = sum(len(parts) for parts in grouped.values())
    omitted_metres = 0
    pre_dissolve_metres = sum(p.length for parts in grouped.values() for p in parts)
    post_dissolve_metres = 0
    retained_source_ids = set()
    for group_number, key in enumerate(sorted(grouped)):
        # Same-name records commonly divide a single trail into many tiny GIS
        # pieces. Dissolve overlaps and merge touching pieces before filtering.
        # Preserve original coordinates: rounding dense source vertices onto a
        # grid artificially lengthens some paths. Only exact overlaps dissolve;
        # close parallel paths remain distinct. Branches keep separate profiles.
        for part_number, part in enumerate(dissolve_named_parts(grouped[key])):
            post_dissolve_metres += part.length
            part = part.simplify(2, preserve_topology=True)
            if part.length < MIN_SEGMENT_METRES:
                exclusions["merged_pieces_shorter_than_half_mile"] += 1
                omitted_metres += part.length
                continue
            fingerprint = part.normalize().wkb
            if fingerprint in seen:
                exclusions["duplicate_geometry_pieces"] += 1
                continue
            seen.add(fingerprint)
            # Densify the actual line, retaining its vertices so switchbacks and
            # corners are not shortened by regularly spaced interpolation alone.
            dense = part.segmentize(35)
            xy = np.asarray(dense.coords)[:, :2]
            heights = bilinear(grid, affine, xy) / .3048
            distances = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))]) / 1609.344
            points = [[round(v, 3) for v in [*screen(x, y), float(h), float(d)]]
                      for (x, y), h, d in zip(xy, heights, distances)]
            retained_source_ids.update(source_members[key])
            mapped.append({"id": f'{group_number}-{part_number}',
                           "name": names[key],
                           "points": points, "miles": round(float(distances[-1]), 3),
                           "min": round(float(heights.min())), "max": round(float(heights.max()))})
    mapped, isolated_pieces = remove_isolated_compact_segments(mapped, span / 1000)
    exclusions["isolated_compact_segments"] = len(isolated_pieces)
    if not mapped:
        raise ValueError("No hiking segments mapped")
    rings = []
    for polygon in park.geoms if hasattr(park, "geoms") else [park]:
        for ring in [polygon.exterior, *polygon.interiors]:
            rings.append([[round(v, 3) for v in screen(x, y)]
                          for x, y in ring.simplify(15).coords])
    totals = {"segments": len(mapped), "miles": round(sum(t["miles"] for t in mapped), 1),
              "min": min(t["min"] for t in mapped), "max": max(t["max"] for t in mapped)}
    peak_source = json.loads((DAY / "peaks.json").read_text())
    peaks = []
    for peak in peak_source["peaks"]:
        point = screen(*projection(peak["lon"], peak["lat"]))
        if not all(0 < v < 1000 for v in point) or sum((v-500)**2 for v in point) >= 500**2:
            raise ValueError(f"Peak outside circular map: {peak['name']}")
        peaks.append({**peak, "point": [round(v, 3) for v in point]})
    data = {"peaks": peaks, "trails": mapped, "boundary": rings, "palette": PALETTE,
            "metresPerUnit": span / 1000, "totals": totals}
    html = (DAY / "template.html").read_text()
    html = html.replace("__MAP_DATA__", json.dumps(data, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c"))
    html = html.replace("__TERRAIN__", base64.b64encode(buffer.getvalue()).decode())
    html = html.replace("__MILES__", f'{totals["miles"]:,.0f}')
    (DAY / "map.html").write_text(html)
    qa = {"peak_landmarks": peaks, "peak_source": peak_source, "source_features": len(trails), "mapped_segments": len(mapped),
          "source_features_in_retained_name_groups": len(retained_source_ids),
          "cleanup": {"input_clipped_pieces": raw_piece_count,
                      "minimum_segment_length_metres": MIN_SEGMENT_METRES,
                      "minimum_segment_length_miles": 0.5,
                      "precision_grid_metres": None,
                      "isolated_piece_rule": "footprint max width/height < 600 m and distance to every other retained-length segment > 100 m",
                      "isolated_pieces": [{"id": t["id"], "name": t["name"], "miles": t["miles"]} for t in isolated_pieces],
                      "omitted_isolated_piece_miles": round(sum(t["miles"] for t in isolated_pieces), 3),
                      "omitted_short_piece_miles": round(omitted_metres / 1609.344, 3),
                      "length_change_after_dissolve_miles": round((pre_dissolve_metres-post_dissolve_metres)/1609.344, 3)},
          "exclusions": dict(exclusions), "source_features_clipped": len(clipped_sources),
          "totals": totals, "elevation_samples": sum(len(t["points"]) for t in mapped),
          "missing_elevation_samples": 0, "crs": "EPSG:26913", "dem_grid_spacing_metres": resolution,
          "trail_edit_date_range": [datetime.fromtimestamp(v / 1000, timezone.utc).isoformat()
                                    for v in [min(dates), max(dates)]],
          "source_manifest": manifest}
    write_json(DAY / "map.qa.json", qa)
    (DAY / "map.results.md").write_text(
        f'# Every Line a Climb\n\n[Open the map](map.html)\n\n'
        f'{totals["segments"]} mapped trail segments; approximately {totals["miles"]:,.1f} miles '
        f'of selected linework inside the NPS boundary. Sampled elevations span '
        f'{totals["min"]:,}–{totals["max"]:,} feet.\n\n'
        'Only segments at least 0.5 miles long are shown. Segments are dataset pieces, not complete hikes. Distances describe linework; '
        'no route completion, current access, or difficulty is inferred. '
        '[Sources and methods](README.md).\n')
    print(json.dumps({**totals, "grid_spacing_m": resolution, "exclusions": dict(exclusions)}, indent=2))


if __name__ == "__main__":
    main()
