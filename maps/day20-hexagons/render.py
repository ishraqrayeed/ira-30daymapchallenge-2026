"""Draw a land-clipped, projected H3 overview of listed club locations."""
import json
from xml.sax.saxutils import quoteattr

import fiona
from fiona.io import ZipMemoryFile
import h3
from pyproj import Transformer
from shapely.geometry import Point, Polygon, shape
from shapely.ops import transform, unary_union
from shapely.prepared import prep

from download_data import CACHE
from clubs import OUT

LAND = "#EDE7D8"
STYLES = ((1, "1", "#B8C8A6"), (2, "2–4", "#96B38A"),
          (5, "5–9", "#6E9671"), (10, "10–24", "#427559"),
          (25, "25+", "#1D503D"))
REGIONS = {
    "us": (5070, (10, 5, 811, 516), lambda lat, lon: 20 < lat < 56 and -133 < lon < -60),
    "ak": (3338, (871, 165, 188, 122), lambda lat, lon: lat > 48 and (lon < -124 or lon > 161)),
    "hi": (3759, (877, 357, 176, 117), lambda lat, lon: 14 < lat < 35 and -180 <= lon < -150),
}


def polygons(geometry):
    if geometry.geom_type == "Polygon":
        if not geometry.is_empty:
            yield geometry
    elif hasattr(geometry, "geoms"):
        for child in geometry.geoms:
            yield from polygons(child)


def get_states():
    with ZipMemoryFile((CACHE / "nat-boundaries").read_bytes()) as archive:
        name = next(n for n in archive.listdir() if n.endswith(".shp"))
        with archive.open(name) as source:
            features = list(source)
    return ({f["properties"]["STUSPS"]: shape(f["geometry"]) for f in features},
            {f["properties"]["STUSPS"]: f["properties"]["NAME"] for f in features})


def view(bounds, box):
    x1, y1, x2, y2 = bounds
    left, top, w, h = box
    scale = min(w/(x2-x1), h/(y2-y1))
    return lambda x, y: (left+(w-(x2-x1)*scale)/2+(x-x1)*scale,
                         top+(h-(y2-y1)*scale)/2+(y2-y)*scale)


def path(geometry, place):
    parts = []
    for polygon in polygons(geometry):
        for ring in (polygon.exterior, *polygon.interiors):
            points = [place(*p[:2]) for p in ring.coords]
            parts.append("M" + " ".join(f"{x:.2f},{y:.2f}" for x, y in points) + "Z")
    return "".join(parts)


def cell_polygon(cell, project):
    return Polygon([project(*p) for p in h3.h3_to_geo_boundary(cell, geo_json=True)])


def grid(region, land, project, resolution):
    include = REGIONS[region][2]
    prepared = prep(land)
    for root in h3.get_res0_indexes():
        for cell in h3.h3_to_children(root, resolution):
            if not include(*h3.h3_to_geo(cell)):
                continue
            full = cell_polygon(cell, project)
            if prepared.intersects(full):
                intersection = land.intersection(full)
                if intersection.area > 0:
                    yield cell, full, intersection


def reveal_order(counts):
    """Seed waves at separate local maxima, then fill lower-count neighboring cells."""
    ordered = sorted(counts, key=lambda cell: (-counts[cell], cell))
    peaks = []
    for cell in ordered:
        if counts[cell] < 4:
            break
        neighbors = h3.k_ring(cell, 1) - {cell}
        if any((counts.get(n, 0), n) > (counts[cell], cell) for n in neighbors):
            continue
        if any(cell in h3.k_ring(peak, 2) for peak in peaks):
            continue
        peaks.append(cell)
        if len(peaks) == 10:
            break
    timing = {peak: (i*17, 475, "peak") for i, peak in enumerate(peaks)}
    neighbors = {peak: h3.k_ring(peak, 3) for peak in peaks}
    centers = {cell: h3.h3_to_geo(cell) for cell in counts}
    waves = []
    isolated = []
    for cell in ordered:
        if cell in timing:
            continue
        candidates = [h3.point_dist(centers[cell], centers[peak], unit="km") for peak in peaks
                      if cell in neighbors[peak] and counts[cell] <= counts[peak]]
        if candidates:
            waves.append((int(min(candidates)/75), -counts[cell], cell))
        else:
            isolated.append(cell)
    sequence = [(cell, "wave") for _, _, cell in sorted(waves)]
    sequence.extend((cell, "isolated") for cell in isolated)
    # Distribute starts continuously across the sorted sequence, including the
    # transition between the last regional wave and the first isolated cell.
    for i, (cell, phase) in enumerate(sequence):
        start = 170 + round(1940*i/max(1, len(sequence)-1))
        timing[cell] = (start, 390, phase)
    return timing, peaks


def map_region(region, states, data, timing):
    epsg, box, _ = REGIONS[region]
    project = Transformer.from_crs(4326, epsg, always_xy=True).transform
    ids = ([k for k in states if k not in {"AK", "HI", "PR", "GU", "VI", "MP", "AS"}]
           if region == "us" else [region.upper()])
    geoms = [transform(project, states[k]) for k in ids]
    land = unary_union(geoms)
    hits = list(grid(region, land, project, 3))
    place = view(land.bounds, box)
    background = [f'<path d="{path(land,place)}" fill="{LAND}"/>']
    boundaries = [f'<path d="{path(p,place)}" fill="none" stroke="#C5BEAD" '
                  'stroke-width=".55" vector-effect="non-scaling-stroke" pointer-events="none"/>' for p in geoms]
    outline = (f'<path d="{path(land,place)}" fill="none" stroke="#A69F8D" stroke-width="1.1" '
               'vector-effect="non-scaling-stroke" stroke-linejoin="round" pointer-events="none"/>')
    tiled = unary_union([p for _, _, p in hits])
    uncovered_share = land.difference(tiled).area / land.area
    assert uncovered_share < 1e-7, (region, uncovered_share)
    fills, occupied = [], set()
    offshore = 0
    for cell, full, clipped in sorted(hits, key=lambda hit:hit[0]):
        lat, lon = h3.h3_to_geo(cell)
        offshore += not clipped.covers(Point(project(lon, lat)))
        count = data.get(cell, 0)
        if not count:
            continue
        occupied.add(cell)
        start, duration, phase = timing[cell]
        _, _, fill = next(style for style in reversed(STYLES) if count >= style[0])
        land_path = path(clipped, place)
        fills.append(f'<g class="cell"><path class="club-cell" data-phase="{phase}" data-start="{start}" '
                     f'data-duration="{duration}" style="--final:{fill}" d="{land_path}" fill="{fill}" '
                     f'fill-rule="evenodd" pointer-events="none"/>'
                     f'<path class="hex-hit" data-h3="{cell}" data-count="{count}" '
                     f'aria-label="{count} listed {"club" if count == 1 else "clubs"}" '
                     f'd="{path(full,place)}" fill="transparent"/>'
                     f'<path class="cell-outline" d="{land_path}" fill="none" pointer-events="none"/></g>')
    label = {"ak":"Alaska", "hi":"Hawaii"}.get(region)
    if label:
        background.insert(0, f'<text x="{box[0]+box[2]/2}" y="{box[1]-11}" text-anchor="middle">{label}</text>')
    return "".join(background+fills+boundaries+[outline]), occupied, dict(cells=len(hits), occupied=len(occupied),
            offshore_center_cells=offshore, uncovered_land_share=uncovered_share)


def render():
    data = json.loads((OUT / "h3-r3-panel.json").read_text())["hexes"]
    counts = {cell:row["provider_count"] for cell, row in data.items()}
    timing, peaks = reveal_order(counts)
    states, names = get_states()
    state_names = quoteattr(json.dumps(names))
    legend = quoteattr(json.dumps([[label, color] for _, label, color in STYLES]))
    pieces = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1068 528" role="group" '
              'aria-label="Map of US Club Soccer listed locations" '
              f'font-family="system-ui,sans-serif" font-size="15" fill="#193B30" data-land="{LAND}" data-legend={legend} data-state-names={state_names}>']
    found, summary = set(), {}
    for region in REGIONS:
        block, cells, metrics = map_region(region, states, counts, timing)
        pieces.append(f'<g data-region="{region}">{block}</g>')
        found.update(cells)
        summary[region] = metrics
    assert found == set(data), set(data)-found
    pieces.append("</svg>")
    (OUT / "national-r3.svg").write_text("\n".join(pieces))
    audit = dict(resolution=3, regions=summary, peaks=[dict(h3=k, listed_clubs=counts[k]) for k in peaks],
                 occupied_cells=len(found), mapped_clubs=sum(counts.values()),
                 intro_end_ms=max(start+duration for start,duration,_ in timing.values()))
    (OUT / "land-grid-qa.json").write_text(json.dumps(audit, indent=2)+"\n")
    print(json.dumps(audit))


if __name__ == "__main__":
    render()
