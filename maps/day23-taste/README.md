# Day 23 — Taste · A Taste of Old Dhaka

A culinary journey through the streets of Puran Dhaka. Twenty-two source-checked
food destinations, eight bilingual categories, and walking trails through the
historic street network. Bright monochrome cartography with a restrained teal accent.

## Preview

From the repository root:

```sh
python3 scripts/preview_map.py --directory maps/day23-taste --port 8014
```

Open **http://127.0.0.1:8014/map.html**. No backend, API keys, live routing service,
external tiles, or paid services are needed. WebGL and a local HTTP server are required.

Choose a food category, dish or neighborhood. Hover a marker or use **Find a place**
with the keyboard to open its description. Add 2–5 restaurants to **Your food trail**;
reorder or remove stops, see the walk, or reset the experience. Mobile categories
scroll horizontally and restaurant cards become bottom sheets. Escape closes details.

## Data and rebuilding

See [DATA_SOURCES.md](DATA_SOURCES.md) and [RESEARCH_NOTES.md](RESEARCH_NOTES.md).
Each point in `data/restaurants.geojson` includes branch identity, coordinates,
food tags, provenance, operating-status limitations, and street-access offset.
`curated.json` is the editable research input. Photos are intentionally absent:
no relevant food photograph has yet been verified for reusable licensing.

Public GIS assets are already included. To reproduce them with the repository’s
cached **2026-11-02 Bangladesh OSM PBF** and validated pedestrian XML:

```sh
python3 -m venv /tmp/day23-gis
/tmp/day23-gis/bin/pip install osmium shapely
/tmp/day23-gis/bin/python maps/day23-taste/extract_osm.py
/tmp/day23-gis/bin/python maps/day23-taste/extract_water.py
/tmp/day23-gis/bin/python maps/day23-taste/prepare_data.py
node maps/day23-taste/test_core.js
```

The default snapshot and walking XML are the existing ignored caches under
`data/raw/day03-polygons/`; Day 23 reads them without changing earlier maps.
`extract_osm.py` also accepts a PBF path as its first argument. The walking XML was
produced by the repository’s public-access OSM extraction; its checksum and the PBF
checksum are recorded in `data/sources.json`. `extract_water.py` assembles actual
water multipolygons, including Buriganga relation **5347205**. Raw caches stay out of Git.

## Routing and limits

A worker runs Dijkstra shortest paths over **21,759 mapped street nodes** and
**47,140 directed edges**. Shared OSM node IDs define connections; crossings do not
create connections merely because lines intersect. Access restrictions, restricted
barriers and mapped pedestrian one-way rules are respected by the extraction.
Car one-way rules do not restrict pedestrians. Missing geometry is never bridged.
Turf supplies filter extents and an independent geometry-length calculation.

Times assume **4 km/h**, excluding meals, queues, entrance approaches and crossings.
Street access is at the nearest mapped node, within **23.7 m** of each restaurant.
Adjacent restaurants can share an access node; the UI identifies this instead of
inventing a path. The network is an OSM model, not a field-surveyed accessibility or
safety guarantee. There is no live opening-hours claim. Two historic businesses
have explicitly uncertain operating status. No fabricated neighborhood polygons,
straight-line walking routes, menu claims, founding dates or substitute photos.

## Checks

```sh
python3 maps/day23-taste/prepare_data.py
node maps/day23-taste/test_core.js
python3 maps/day23-taste/qa_server.py
# With the preview server running, open:
# http://127.0.0.1:8014/qa-browser.html
```

`data/qa.json` records extraction checks. Unit checks validate **462 directed
restaurant pairs** against real graph edges, disconnected graphs and filter logic.
The browser harness checks rendered circles, category/dish/neighborhood filters,
cards, worker routing, trail order/removal/reset and mobile layout. Its optional
collector writes only to `/tmp/day23-browser-report.json`; test tools are excluded
from the Pages package. The final review is recorded in `qa-review.json`.

MapLibre GL JS 5.6.0, Turf 7.2.0 and Noto Sans Bengali are vendored with licenses.
No previous challenge day is edited. **Not deployed.**
