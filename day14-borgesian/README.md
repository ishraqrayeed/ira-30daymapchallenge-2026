# Day 14 — Denver, City of 280+ Parks

**Borgesian Map.** How much of a city fits inside one place to sit?
Follow a continuous aerial circuit from Denver into Washington Park: Smith Lake,
the mapped north and south playgrounds, Grasmere Lake, the south tennis courts,
and a western view of the lake before returning to the original bench among
nine mapped trees. The park circuit takes **50 seconds**, plus the approximately
8.6-second Denver approach. There are no intermediate pauses; the final zoom
slows smoothly toward the bench. The flight starts automatically once the map is ready; reload the page to replay it.
The bottom panel and legend are removed. Compact +/− buttons, wheel, pinch,
double-click and keyboard zoom support free exploration; manual zoom pauses
the flight. Reload replays it.

The map opens top-down; park and bench stops tilt to 50–52°. 2D/3D preserves
location and zoom. Reset returns to the full Denver boundary, including DIA.
Reduced-motion preferences make camera changes immediate.

## Data and selection

Retrieved **2026-11-14**. The [official Parkland layer](https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/ArcGIS/rest/services/ODC_PARK_PARKLAND_A/FeatureServer/87)
contains **376 polygon records**, last edited **2026-10-30**. Schema and REST
count are checked before filtering; transfer-limit or count mismatches fail.

- Include `PARK_TYPE` = `Park` or `Open Space`.
- Exclude `PARK_CLASS` = `Mountain` or `Undeveloped`, and mountain maintenance districts.
- Intersect with the [official city jurisdiction layer](https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/ArcGIS/rest/services/ODC_ENG_SRVCCDBOUNDARY_A/FeatureServer/40), selecting `COUNTY = Denver`. Its neighboring-county enclave polygons are excluded.
- Dissolve by `LOC_CODE`, preserving multipart geometry and holes. All 302 selected codes are unique in this snapshot; there are no selected name collisions. Names are display labels, never grouping keys.

**302 parks mapped**, from 302 selected source records. Excluded: 46 mountain
records and 28 other-type/undeveloped records (including 7 golf and 8 standalone
recreation-center records). Facilities inside included park boundaries remain.
Urban open spaces, athletic complexes, and linear parks are included. This
explicit GIS subset differs from DPR’s administrative inventory.

The title’s **280+** is [DPR’s published urban park figure](https://www.denvergov.org/Government/Agencies-Departments-Offices/Agencies-Departments-Offices-Directory/Parks-Recreation/Urban-Parks-Trails),
not a count calculated from these polygons.

## The map inside the map

OpenStreetMap interiors come from the [Geofabrik Colorado extract](https://download.geofabrik.de/north-america/us/colorado.html),
snapshot **2026-11-13 21:22:20 UTC**. Regional PBF processing replaced unavailable
Overpass endpoints. No runtime Overpass or ArcGIS requests are made.

| Kind | Source features mapped |
|---|---:|
| Individually mapped trees | 16,421 |
| Benches | 638 |
| Paths | 6,118 |
| Water | 609 |
| Playgrounds | 196 |
| Pitches | 501 |

These are OSM feature counts, not a complete amenity inventory. Paths include
footways, cycleways, paths, tracks, pedestrian ways and steps. Water includes
`natural=water` and waterways. Playgrounds/pitches include point or area geometry.
Soccer is labeled only when `sport=soccer`; untagged pitches remain “Sports pitch.”
Multipolygon water retains inner rings. Geographic selection uses the union of
included parks; lines and areas crossing edges are clipped, with original
interior coordinates retained and only intersection vertices added. Point
coordinates are unchanged. Edge-clipped source features: 2,281 paths, 229 water,
20 pitches and 11 playgrounds. The validator checks the results against parkland,
allowing only floating-point overlay tolerance below 0.02 mm.

Washington Park has **51 mapped point benches** and **297 individually mapped trees**.
The final stop maximizes the number of mapped trees within 30 metres, then
prefers descriptive source tags and proximity to the park’s interior point.
It is [node/5711818758](https://www.openstreetmap.org/node/5711818758), at
longitude **−104.9694218**, latitude **39.6993642**: tagged backrest=yes, with no
material or direction tag. **Nine mapped trees** surround it within 30 metres.
The precise coordinate and tags are recorded in [data/qa.json](data/qa.json).
It is verified against the official Washington Park polygon.

## 3D detail and its limits

Rich green parkland, quiet streets, blue water and small park dots establish the
city view. Names appear at zoom 12.5; paths at 13; play areas/pitches at 14;
benches and trees at 17; richer crowns and seat detailing at 19. The final stop
is zoom 20.2. Symbols use actual OSM coordinates. Interiors are indexed by geometry bounds and sent to MapLibre only near the
current view. Nearby solids are generated only for the visible close-up,
avoiding a citywide 3D mesh on mobile. The matching MapLibre worker is vendored
locally; there are no worker CDN dependencies.

Trees use smooth, shaded 3D foliage with textured leaf sprays, visible trunks and
forked branches. Five illustrative forms—spreading, rounded, upright, weeping,
and evergreen—vary silhouette, foliage colour and leaf arrangement. The autumn palette uses
golden yellow, burnt orange, copper and rust red, with muted green evergreens.
These colours are seasonal art direction, not observed leaf conditions. Recorded
genus/species or leaf type guides the form where available; otherwise a stable
OSM-ID seed supplies visual variety, not a claim about species. Tree crowns
are clickable. The Three.js layer shares the map depth buffer and batches leaf
geometry on the GPU; close views use more leaf detail, with a maximum of 100
nearby tree models on narrow screens and 250 on desktop. Other mapped trees remain visible as point symbols. Bench symbols
have slatted seats and supports, enlarged 2.1× for readability. **These are illustrative dimensions and shapes,
not measured models.** Source `direction`, when present, sets the seated facing
direction; the bench long axis is perpendicular. Standard bench symbols have rectangular slatted seats, backs and legs; an explicit
`backrest=no` omits the back. Missing direction faces the closest point on a mapped path within 50 m; the
bench’s long axis lies across that facing vector. A bench directly on a path
uses the perpendicular to its local tangent. This display inference uses a local
metre approximation and never moves the bench or changes OSM tags. The direction basis is retained in the prepared GeoJSON and described in About. Without a path within 50 m, the default
display facing remains north. The generic design and inferred alignment do not
assert a surveyed appearance or orientation.
Benches have no persistent text labels. The bench popup shows only its title and a source link.

Trails have thicker cream strokes and darker outlines at close zoom. A seamless,
locally generated grass texture adds restrained grain, short blades and subtle
lawn variation above zoom 15.5. It is decorative, clipped to official parkland,
and drawn beneath water, paths and play areas. It does not identify observed
mowing, grass species or ground conditions. Ground remains flat; no elevation
model is used. Bench callouts sit beside the model on desktop and above it with
extra clearance on narrow screens, preserving the seat’s visibility.

The aerial loop’s landmarks are derived from the shipped OSM geometries and
recorded in `data/qa.json`. Tennis courts are selected only from `sport=tennis`.
The original final bench, `node/5711818758`, is retained.

The light OpenFreeMap Positron basemap supplies OpenMapTiles buildings.
Extrusions use `render_height` / `render_min_height`; missing height falls back
to an explicitly disclosed illustrative 3 m. OSM amenity coverage and basemap
building dates vary. This is not photogrammetry, terrain surveying, navigation,
or a claim that every real tree or bench is mapped.

## Reproduce

From the repository root (Python 3.11+, `curl`):

```sh
python3 -m venv .venv
.venv/bin/pip install -r day14-borgesian/requirements.txt
.venv/bin/python day14-borgesian/prepare_data.py
.venv/bin/python day14-borgesian/validate_data.py
python3 scripts/preview_map.py --directory day14-borgesian --port 8014
python3 scripts/build_pages.py
```

Cold runs fetch official layers, the basemap style and the ~370 MB Colorado PBF;
`extract_osm.py` uses pyosmium’s C++ filters, builds OSM multipolygons, and keeps
only relevant features intersecting the Denver extraction envelope. Every
selected park must fall within that envelope or the preparation fails. Raw
files remain in ignored `data/raw/day14/`. Warm runs reuse caches. Use
`prepare_data.py --refresh` for new downloads; future source updates can change
counts. The shipped snapshot is reproducible from cached inputs; hashes, source
dates, counts and exclusions are recorded in `data/qa.json` and `data/sources.json`.
For exact reprocessing, retain the PBF matching the recorded SHA-256; the
Geofabrik `latest` URL advances daily. Output GeoJSON is compact (~8 MB total).
GitHub Pages serves `/day14-borgesian/` with relative local asset URLs; only
basemap tiles, glyphs and sprites require external network access.

## Credits and terms

- Denver Parks & Recreation; Denver Public Works/Survey. Public GIS data is supplied as-is, without accuracy/completeness warranties, and is not for engineering purposes. [Parkland usage constraints](https://www.arcgis.com/sharing/rest/content/items/e752556524024fbfac700b35f33c0f2c?f=pjson), [boundary usage constraints](https://www.arcgis.com/sharing/rest/content/items/53a0ae35c018471788efe36b6f730a79?f=pjson).
- © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), ODbL 1.0; processed OSM interior data remains available here under ODbL. Extract distribution: Geofabrik.
- [OpenFreeMap](https://openfreemap.org/), [OpenMapTiles](https://openmaptiles.org/) and OSM, with linked credits always visible. [OpenFreeMap terms](https://openfreemap.org/tos/) permit the public interactive service subject to their terms; no bulk basemap downloads are included.
- MapLibre GL JS and Three.js are vendored with their licenses in `vendor/`. Leaf textures and tree models are generated locally in code; no model or texture CDN calls are required.

## Verification

```sh
python3 -m unittest tests.test_day14_orientation tests.test_day14 tests.test_pages -v
node --test tests/test_day14_camera.mjs
python3 day14-borgesian/validate_data.py
node --check day14-borgesian/app.js
```

For repeatable real-browser interaction checks, serve this folder with the preview
script and open `/test_browser.html`. It embeds the actual map at 390 × 844 and
checks the opening extent, guided feature, rendered 3D geometry, toggles, manual
exploration, reset, automatic tour, cancellation and reduced-motion branch.
`?target=/your-pages-prefix/day14-borgesian/` can target a packaged build served
on the same origin. The test harness is excluded from the public package.
Chrome desktop and iPhone-sized layout are reviewed; physical iPhone/Safari and
live GitHub Pages deployment are not verified. See `qa-review.json`.

No publication is performed by the preparation or Pages build commands.
