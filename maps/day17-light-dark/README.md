# Day 17 — Light & Dark

## The First 5, the Last 5

A flight home to Colorado: Delta DL424, JFK → DEN, October 15, 2025.
[Open replay](map.html). Fixed north-up Three.js maps compare equal horizontal
route distance, with synchronized controls and a completed still for reduced motion.
The latest revision uses **5 statute miles** at each end, replacing the initial 50.

### Flight and sampling

[adsb.aero trajectory](https://adsb.aero/api/v1/flights/a6bbef%3A2025-10-15T23%3A57%3A13Z)
confirms DAL424, N533DT, a6bbef, KJFK → KDEN. Its 168 simplified vertices derive
from 1,541 raw positions. Original extent: 2025-10-15 23:57:13.760 UTC through
2025-10-16 03:49:34.540 UTC, matching the reference 7:57 p.m. EDT / 9:49 p.m. MDT
minutes. A 63.6-second coverage gap at 03:11–03:12 UTC lies outside both windows.
Long intervals between simplified vertices alone are not additional coverage gaps.

Exact liftoff/touchdown flags are unavailable in this response. Windows anchor to
the first/last recorded positions, not invented runway endpoints. The first point
is approximately 0.99 km from JFK's airport reference point; the last is 2.94 km
from DEN's reference point. Airport reference points are not runway thresholds.
Pressure altitudes of 50 ft and 5,425 ft do not establish precise ground contact.
See `data/validation.json` for exact clipped timestamps.

WGS84 geodesic cumulative distance clips exactly 5 × 1,609.344 m per window.
Intermediate positions follow geodesic legs between recorded vertices; original
timestamps interpolate along each leg. Replay is by normalized distance, not
simultaneous clock time or actual flight speed. No cruise gap is bridged here.

[VIIRS annual 2024, OpenLandMap v0.4](https://zenodo.org/records/17294744),
`nightlights.average_viirs.v21_m_500m_s_20240101_20241231_go_epsg4326_v20250904.tif`,
is the sole analytical raster. Its MD5 is `0b976892d40c2d0d99177c727289eaf2`.
The 15-arcsecond grid is approximately 500 m, with stored values scaled 10× from
original VNL radiance. At miles 0–5 inclusive (six samples), take the median of
valid native pixel centers within a 3-statute-mile geodesic radius. Include valid
zeros and water; exclude nodata/negative values. Overlapping samples are not
independent. The medians of these profiles are **25.5 / 2.0 = 12.75×**. Display
rounds to 12.8×. This compares typical ground brightness along these two windows,
not passenger visibility, photographic exposure or brightness on the flight night.

### Display composite

Free [NASA georeferenced ISS imagery](https://eol.jsc.nasa.gov/ExplorePhotos/):
JFK **ISS072-E-184896**, October 27, 2024; DEN **ISS070-E-103355**, February 28,
2024. NASA's catalog estimates source resolutions of 11.98 / 24.19 m. The public
z12 Web Mercator map tiles actually used have approximately 29 m ground spacing
at these latitudes; the 25 m output grid adds no new observed detail. GeoTIFF
endpoint requests returned HTTP 502, so preprocessing mosaics NASA's published
georeferenced tiles. No manually positioned or fabricated aerial image is used.
NASA georeferences are not survey control; airport and street patterns were
visually reviewed, and alpha coverage is tested along both routes.

The hybrid is **VIIRS brightness · ISS detail · Contrast enhanced**. GDAL bilinear
resampling and a mask-normalized 120 m Gaussian create the continuous display
brightness envelope. ISS detail is normalized against a continuous 350 m local
mean, clipped to 0.15–3, and blended at 0.75 gain. This replaces the previous
nearest-neighbor envelope and per-VIIRS-cell normalization, whose abrupt cell
transitions created rectangular patches. The checked 20 km squares have no VIIRS
NoData or missing ISS coverage; DEN has genuinely low/zero source pixels.

Missing photography feathers to valid VIIRS-only coverage rather than black.
Truly missing VIIRS is hatched slate; valid zero terrain/water stays dark.
Source alpha and analytical NoData are separate masks. The hybrid is a cartographic
composite, **not calibrated high-resolution radiance**. No cell-mean conservation
is claimed for the display. Fine detail comes from different dates; all statistics
still come from untouched native VIIRS pixels, not the hybrid proxy or PNGs.

Both panels use identical local metric ground scale, navy-to-warm-gold palette and
`[log1p(clip(proxy, 0, 600)) / log1p(600)]^1.15`. Bloom starts at proxy value 80,
with restrained 75/175 m blur and warm RGB gain [8,6,3]. Parameters never vary by panel
or frame. The nonlinear styling is not a literal screen-luminance ratio of 12.75.
64 km padding crops support responsive framing; the actual view zooms to the
5-mile trails with a common scale and sufficient endpoint margin. Aircraft and
trails animate; ground textures remain fixed.

### Reproduce

```sh
python3 -m pip install -r maps/day17-light-dark/requirements.txt
python3 maps/day17-light-dark/scripts/prepare.py
python3 maps/day17-light-dark/scripts/prepare_nasa.py
python3 maps/day17-light-dark/scripts/prepare_hybrid.py
python3 maps/day17-light-dark/scripts/validate.py
python3 scripts/preview_map.py --directory maps/day17-light-dark --port 8017
```

Python Rasterio uses GDAL for reprojection. Raw source caches stay under ignored
`data/raw/day17/`. Exported GeoTIFFs carry CRS/transforms; `data/bounds.json` gives
crop bounds; `routes.geojson`, `profiles.csv` and manifests preserve public outputs.
Hybrid QA tests missing-photo fallback, dark-field preservation, source coverage,
and identical curve/bloom parameters. The chart uses distance flown from 0–5 miles
within each window; DEN runs from five miles out toward the recorded endpoint.
Its scaled source values are labelled Relative brightness.

With Playwright and its Chromium/WebKit browsers installed, run `scripts/review.cjs`
and `scripts/review_frames.cjs` using Node. Set `DAY17_NODE_MODULES` to the module
path, `PLAYWRIGHT_BROWSERS_PATH` to Chromium's installation, and
`DAY17_WEBKIT_PATH` to WebKit's installation. The user captures screenshots or
records directly from the page; no video is exported in the release.

Opening hold 1.3 s (aircraft already visible); movement 11 s; final hold 2.7 s.
Small teal/amber chart planes follow the same mileage as the map aircraft.
A single icon toggles Play/Pause and replays from the beginning after the end.
Drag either map plane along its recorded route, or either chart plane horizontally,
to pause and synchronize all four markers by distance. Chart markers also accept
Left/Right, Home and End keys. Both map readouts show miles flown within the selected segment, from 0.0 / 5 mi
to 5.0 / 5 mi; DEN advances toward the recorded endpoint. No animation tracker is displayed. The expanded chart retains synchronized
plane symbols and distance/brightness axes. Reports record checks.

Sources: EOG Annual VNL V2 (Elvidge et al., 2021), redistributed by Tomislav Hengl /
OpenLandMap under CC BY 4.0; NASA Earth Science and Remote Sensing Unit, NASA
Johnson Space Center; adsb.lol historical data via adsb.aero under ODbL 1.0.
Derived trajectory portions of the public JSON/GeoJSON/CSV remain available under
ODbL; independent raster/photographic layers retain their source terms. No SDGSAT
imagery, simulated road lighting, OSM tiles or source credentials are included.
