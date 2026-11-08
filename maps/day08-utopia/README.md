# Day 8 — Utopia

## What If Dallas–Fort Worth Had NYC’s Subway?

*An alternate reality where the Metroplex runs on rails.*

What would a connected Metroplex look like if Arlington, the airports, both
downtowns and the northern cities shared a subway map?

[Interactive geographic map](map.html) · [Benchmark](benchmark.json) · [QA](web.qa.json)

The current deliverable is the interactive web map. Earlier static exports are
retained as archived assets; they are not required to use the map.

**Conceptual transit network. Not an existing or officially proposed transit system.**
All ten services are fictional, including those that follow existing rail.
Stations are sourced geographic anchors, not surveyed entrances or engineering sites.

### Interactive explorer

Open `map.html`. The explorer has a **1:1 square frame** for LinkedIn browser
screenshots, with larger service badges and text. All ten services appear in two
compact rows on desktop; the mobile legend scrolls horizontally and remains
outside the geographic viewport. “All services” clears the filter. Selecting a
badge highlights its route and stopping stations, dims other services to 20%,
and synchronizes the optional dropdown under “Service list.” Select it again to
restore the whole network.

At the opening view, labels prioritize eight major destinations. Terminals,
transfer stations and then ordinary station names become eligible as zoom
increases. Labels are positioned in screen pixels, checked against other labels
and station markers, and recalculated after zoom, pan, resize and filtering.
Unlabeled markers always remain present. Every original name remains in the data
and station popup.

Tap/click a station or press Enter/Space when focused for its exact name, colored
service badges, transfer designation and explicit conceptual-network note. The
popup derives memberships from the route station lists, not geometric crossings.
There are 74 unique locations, of which 37 have two or more stopping services.
Popup badges can also select a service. Close with × or Escape.

Scroll-wheel, trackpad pinch, two-finger touch pinch, +/− and keyboard +/− zoom
only the map. The opening extent stays fitted; pan after zooming, with bounds
preventing the network from being dragged out of view. Reset view restores the
camera. Existing rail uses thin dashed gray lines; enabling it displays a short
explanation distinguishing real DART/TRE, TEXRail and DCTA rail from the colored
fictional network. It does not create transfers at crossings.

The basemap retains the countywide Census TIGER/Line 2025 primary roads (MTFCC
S1100) and areal water from Dallas, Tarrant, Denton and Collin. Water polygons of
at least 0.25 km², plus named Trinity River pieces of at least 0.005 km², are
simplified by 25 m in UTM 14N. Lake-name abbreviations are expanded for display.
No residential grid, live tiles, API keys or paid service is required.

`download_basemap.py` reproduces [water](basemap-water.geojson) and
[highways](basemap-highways.geojson). The manifest records these public-domain
Census sources. `render.py --web-only` embeds `explorer.js` in the HTML, without
regenerating static exports. The existing poster, basemap geometries, route
coordinates, service definitions and marker positions are unchanged.
`validate_web.py` runs data/artifact checks and the desktop/mobile interaction
suite in `test_controls.js`, including every service and every station popup.

### Data and terms

Retrieved November 6–7, 2026 UTC; exact retrieval times, URLs, bytes and SHA-256
checksums appear in [source-manifest.json](source-manifest.json). Raw snapshots
stay in ignored `data/raw/day08-utopia/`; derived geographic files are published.

- [DART official GTFS](https://www.dart.org/about/about-dart/fixed-route-schedule):
  light rail, Silver Line and TRE. Use rail route types 0/1/2; remove yard-limit
  and pocket-track operating points. Feed date ranges are in `benchmark.json`.
- [Trinity Metro official GTFS](https://ridetrinitymetro.org/gtfs-data/): TEXRail.
  **Data provided by Trinity Metro is not warranted by Trinity Metro for accuracy
  or completeness and data is subject to change without notice.** This is an
  archived artistic snapshot, not a live journey planner. The notice is also on
  the interactive page. Agency data remain subject to their respective terms;
  no blanket open license is asserted for transit feeds.
- [DCTA open data](https://www.dcta.net/resources/open-data): A-train GTFS.
- [MTA subway stations](https://data.ny.gov/Transportation/MTA-Subway-Stations/39hk-dx4f)
  and [MTA service lines](https://data.ny.gov/Transportation/MTA-Subway-Service-Lines/s692-irgq):
  official NY Open Data snapshots. Exclude Staten Island Railway; retain
  stations and station complexes as different quantities. See
  [NY Open Data terms](https://data.ny.gov/terms-of-use).
- [US Census TIGER/Line 2025 roads](https://www2.census.gov/geo/tiger/TIGER2025/ROADS/):
  Dallas (48113), Tarrant (48439), Denton (48121), Collin (48085).
  Public domain. Download URLs and checksums are in the manifest.
- [USGS GNIS Texas domestic names](https://www.usgs.gov/us-board-on-geographic-names/download-gnis-data):
  official Populated Place records in Dallas, Tarrant, Denton and Collin counties.
  Federal public domain. Feature IDs accompany every GNIS station.
- [Census 2024 cartographic counties](https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html):
  Dallas, Tarrant, Denton and Collin counties. Federal public domain;
  ALAND is land area in square metres. This four-county study region is **not**
  the full official metropolitan statistical area.
- [NYC borough shoreline boundaries](https://data.cityofnewyork.us/City-Government/Borough-Boundaries/gthc-hcne):
  all five boroughs. Polygon area is calculated in UTM 18N; boundaries are
  shoreline geography, not a subway catchment.
- [BBBike Dallas OSM extract](https://download.bbbike.org/osm/bbbike/Dallas/):
  snapshot last modified October 31, 2026. © OpenStreetMap contributors,
  [ODbL 1.0](https://www.openstreetmap.org/copyright). Extract place nodes,
  airports, motorways, rivers and reservoir ways. Derived combined geographic
  data are offered under ODbL; retain attribution and source provenance.

### Design and method

Existing GTFS stops anchor the core. OSM city and neighborhood nodes anchor new
places within the Dallas extract; USGS GNIS populated-place reference points
anchor the outer cities. The refinement replaces Census polygon interior points,
which placed Arlington and several other cities away from their named centers. Love Field uses the OurAirports KDAL airport reference
point ([public-domain data](https://ourairports.com/data/)).
Every station carries its source ID. Shared station IDs define transfers exactly.
No manual coordinate fabrication or geocoding is used. City nodes represent a
central named location, not a claim about the best station site.

Ten service identities form a connected graph. The red Metroplex corridor brings
Arlington and Grand Prairie into the east–west spine; airport and northern arcs
create cross-connections instead of independent downtown spokes. Services are
inspired by NYC colors and interchanges, not copied from its routes or schedules.
There is no frequency, travel-time, ridership, feasibility or funding model.
Long suburban gaps remain: this is not NYC-equivalent stop spacing or coverage.

The local equirectangular frame uses a constant metric aspect at approximately
33°N. Geographic station positions are fixed; corridors have shallow Bezier
curves, with parallel lanes where services share an edge. Curves are display
geometry, while GeoJSON preserves geographic anchor-to-anchor lines. Alignments
cross real properties and water without engineering analysis. Nearby crossings
are not transfers unless they share a station ID. Automatic label placement
avoids text collisions; crowded labels appear after zooming. A geographic
Dallas inset separates downtown labels, with interactive station circles. All
route casings render before colored lanes, preventing shared services from
erasing each other. The Eastern Arc omits its former McKinney backtrack. The poster selects
labels for space while retaining every station symbol.

The basemap shows a solid outline and light fill for the dissolved union of
Dallas, Tarrant, Denton and Collin county boundaries. The entire exterior fits
the opening view; internal dotted county lines are omitted. This is the
four-county study region, not the official metropolitan statistical area.
[Download the outline](study-region.geojson). Census TIGER/Line 2025 roads provide consistent street coverage across all four
counties: highways, secondary roads and local streets (MTFCC S1100/S1200/S1400).
Local fragments under 100 m are omitted; geometry is simplified by 20 m in UTM
14N for regional display. The street layer is clipped to the study-region outline.
The older partial eastern OSM road/creek mesh remains available in `context.geojson`
but is not drawn. [Street geometry](streets.geojson) is public-domain Census data. Existing rail retains its separate dashed comparison toggle.

### Final poster polish

[Final PNG, 2400 × 3000](day08-utopia-final.png) · [Poster preview](poster.html) ·
[Vector artwork](poster.svg). `poster.png` remains an identical compatibility copy.
The title, subtitle, colors, type hierarchy, dimensions and ten-service legend
are preserved. No outline fragments, streets or other geographic layers are
drawn on the poster; the background is uniform off-white.

Twelve Dallas-area station symbols use small, documented display offsets in
[poster-offsets.json](poster-offsets.json), at most about 26 SVG units. Every
service connects to the same displaced point for a given station ID. Geographic
coordinates, station IDs, service sequences and transfer relationships are
unchanged. These offsets are cartographic display choices, not new infrastructure.
Labels avoid route strokes, markers and other labels; callout leaders avoid
other station symbols. Intermediate downtown labels remain hidden at poster scale.

All **15 distinct service endpoints** are labeled using exact station names from
the existing dataset, including Cedar Hill, Westmoreland, Keller, Southlake and
Buckner. The footer remains **10 services · 74 real-world locations · 37 imagined
interchanges**. Counts are independently verified after deduplicating station
IDs: all 74 geographic positions are also unique, and each of 37 transfer IDs
has two or more distinct stopping services. Geometric crossings do not qualify.
The complete terminal and transfer lists are in [layout QA](poster-layout.qa.json).

`render.py` regenerates both PNG filenames, the SVG and versioned preview.
The interactive HTML remains unchanged unless `--update-interactive` is explicitly
passed. `validate_poster.py` checks source hashes, documented display positions,
edge endpoints and service topology, terminal text, label bounds/collisions,
all ten legend identities, counts and named-export equality. Full-resolution
crops and the 800 × 1000 feed preview were visually inspected. The Pages packager
includes the final named PNG and QA assets; no publication was performed.

The final minor adjustment adds **DOWNTOWN DALLAS** as an area annotation, not a
station, using the major-destination type style. **North Side** and **T&P** are
labeled from existing station records. The unchanged-size header is translated
18 artboard units (36 export pixels) downward. Map projection, display offsets,
route widths, markers and network data are unchanged. All new labels are checked
against the existing labels, and the final export is reviewed at full resolution
and 800 pixels wide. Counts remain independently verified at 74 and 37.

### Export and preview audit

The static renderer is `render.py`, which writes `poster.svg` and invokes
`rsvg-convert` for the 2400 × 3000 `poster.png`. It renders to a fresh temporary
file and atomically replaces the output only after checking image dimensions.
[Export audit](poster-export.json) records generation time, resolved output path,
size and SHA-256. [Poster preview](poster.html) uses a versioned image URL.

The November 7 UTC audit found the requested styling already in the renderer
and PNG. Port 8008 returned exactly the disk PNG; an older `_site` HTML artboard
was found and repackaged. The fresh PNG matched the previous refined PNG hash,
confirming deterministic rendering rather than a skipped export. Browser caching
was not independently established as the cause of the user's stale view.

### Benchmark definitions

`benchmark.json` calculates station records, physical complexes, approximate
service mileage and density. DFW complexes merge rail platform coordinates
within 250 m, including cross-agency records; this can merge nearby but operationally
separate stops. NYC uses official complex IDs. These are approximate comparators,
not identically defined operational units.

For each DFW existing rail service, take the longest available GTFS shape once;
short turns and opposite directions are not summed. MTA mileage sums the published
service geometries once per record. Both are **service miles**, so overlapping
services count repeatedly; neither is physical track mileage. The DFW snapshot
covers DART/TRE, TEXRail and A-train, excluding streetcars and heritage operations.
No calendar-day service availability is inferred from a feed's presence.

DFW density is complexes per 100 km² of four-county Census land area. NYC density
is complexes per 100 km² of five-borough shoreline polygons, including Staten
Island land but excluding SIR stations. Their different footprints and residual
water treatments limit comparison. No population adjustment is made. Fictional
mileage uses projected straight station-to-station edges (UTM 14N), separately
reporting summed service miles and unique undirected corridor miles. These are
conceptual lengths, not engineered subway mileage. No NYC-equivalent coverage claim.

### Reproduce

Python 3 with `geopandas`, `shapely`, `pyproj`, `osmium`; `rsvg-convert` for PNG.
The other packages are already used in the repository; osmium is the PBF reader.

```sh
python3 maps/day08-utopia/download_data.py
python3 maps/day08-utopia/download_osm.py
python3 maps/day08-utopia/download_streets.py
python3 maps/day08-utopia/download_basemap.py
python3 maps/day08-utopia/main.py
python3 maps/day08-utopia/render.py --web-only
python3 maps/day08-utopia/validate.py
node maps/day08-utopia/test_controls.js
python3 scripts/preview_map.py --directory maps/day08-utopia --port 8008
python3 scripts/build_pages.py
```

Pan by dragging. Zoom with buttons or keyboard +/−. Home resets; Escape clears
selection. Select a service from the menu or route legend. Hover, tap or focus a
station for provenance and services. Existing rail is a dashed gray comparison;
it does not imply the colored concepts exist. Data are embedded; no API key,
paid service, live tiles, CDN or runtime network dependency is required.

NYC source QA: 475 non-SIR rows represent **472 unique station IDs**; three
stations have repeated source records. Count unique IDs when quoting stations.

### Validation and review

Independent QA verifies finite coordinates, provenance, station/route agreement,
shared interchange IDs and one connected component. Poster dimensions and SVG
symbol counts agree with the generated data. Node interaction checks exercise
route highlighting, existing-rail toggling, station details, zoom/reset, pan and
Escape at desktop and 390 px widths using a DOM harness. These do not replace
real browser interaction tests. The PNG was visually reviewed at 800 × 1000.
Refined local HTTP was visually reviewed in Chrome at desktop and a 390 × 844
emulated mobile viewport. Browser checks confirmed A-service highlighting,
existing-rail overlay, desktop and mobile DFW station details, and mobile zoom.
Circular service identifiers repeat on open stretches of the main network. Full-network labels are small at
mobile overview scale; zoom is necessary for station-level reading.

### Transit styling and network modes

The web map uses rounded colored lanes with white casings and retains the existing
shared-corridor offsets. Local stops use small circles, transfers larger circles,
and hubs served by at least four distinct fictional services use white capsules.
Memberships come from route station IDs, never geometric crossings.

Reality hides fictional routes, markers and labels and displays the available
official existing-rail snapshot geometries. This is source-dependent coverage,
not a comprehensive or live service map. Utopia restores the ten fictional
services; switching modes clears selection and popups without changing the camera.
Compare rail remains available in Utopia. Reduced-motion preferences suppress
opacity transitions and smooth legend scrolling. Static poster assets are untouched.
