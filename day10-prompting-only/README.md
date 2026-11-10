# Day 10 — The Other Side of Earth

**Prompt only.** Select a city or click Earth, then follow a straight, schematic
journey through the center to its calculated antipode. No backend or token.

```sh
python3 scripts/preview_map.py --directory maps/day10-prompting-only --port 8010 --no-browser
node maps/day10-prompting-only/test_geo.js
```

Open http://127.0.0.1:8010/map.html. `qa.html#run` runs real Cesium checks for
Dhaka, Denver, displayed coordinates, actual marker positions and occlusion,
camera target, replay, inspection and reset. Requires a WebGL browser.

## Geography

Latitude changes sign; longitude shifts 180° and normalizes to [−180°, 180°).
The app calculates one destination shared by the marker, camera, section labels
and polygon lookup. Coordinates are WGS84 degrees; Cesium receives longitude
before latitude. The cross-section projects the origin-aligned diameter of a
6,371 km sphere: length approximately **12,742 km**, center reached halfway.
Layer radii are simplified; crust exaggerated. This is not a gravity simulation.

Dhaka (24.0057° N, 90.3911° E) → 24.0057° S, 89.6089° W, South Pacific Ocean.
Denver (39.7392° N, 104.9903° W) → 39.7392° S, 75.0097° E, Indian Ocean.
Preset city centers and searched coordinates can differ; the actual selected
coordinates determine the destination. Manually selected points receive no
unverified place name.

## Assets and terms

- Local [NASA GIBS Blue Marble](https://gibs.earthdata.nasa.gov/) global composite:
  2048 × 1024 JPEG, inherited unchanged from the repository's Day 9 asset.
  Illustrative contemporary world backdrop, not city-scale imagery.
- [Esri World Imagery](https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer):
  detailed satellite tiles fade in between camera heights of 12,000 and 4,000 km.
  Streamed, with visible provider attribution; not redistributed. Regional dates
  and resolution vary by contributor. Subject to Esri service terms and contributor
  licensing. Network access is required for detailed imagery; local NASA imagery
  remains underneath when tiles fail. No paid API or Cesium ion token configured.
- [Natural Earth 5.1.2](https://www.naturalearthdata.com/about/terms-of-use/), public
  domain: local 1:110m countries and named marine polygons. Source URLs, retrieval
  date and SHA-256 digests in `data/sources.json`. Polygon containment uses the
  antipode, not the origin. These are generalized cartographic boundaries, not
  surveyed shorelines or a claim of current political boundaries. Small islands,
  inland waters and near-coastal points can be omitted or uncertain. Unknown
  polygons remain unclassified; no ocean names are guessed from longitude.
- CesiumJS 1.127.0 is bundled locally under `vendor/Cesium/`; Apache 2.0 and
  third-party notices are retained in `vendor/`.
- Optional city search: [Open-Meteo Geocoding API](https://open-meteo.com/en/docs/geocoding-api)
  (GeoNames place data). Its results supply names and coordinates; search failure
  leaves presets and manual selection available.

The style, title, imagery composite and layout are preserved. Nothing in this
folder deploys the site. Browser screenshots are the presentation output; there
is no separate PNG export.
