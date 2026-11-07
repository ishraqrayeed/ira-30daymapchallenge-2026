# Day 8 — Utopia

## What If Dallas–Fort Worth Had NYC’s Subway?

*An alternate reality where the Metroplex runs on rails.*

What would a connected Metroplex look like if Arlington, the airports, both
downtowns and the northern cities shared a subway map?

[Interactive map](map.html) · [LinkedIn poster, 2400 × 3000](poster.png) ·
[Vector poster](poster.svg) · [Benchmark](benchmark.json) · [QA](map.qa.json)

**Conceptual transit network. Not an existing or officially proposed transit system.**
All ten services are fictional, including those that follow existing rail.
Stations are sourced geographic anchors, not surveyed entrances or engineering sites.

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
- Census 2024 Texas place boundaries and [Census 2024 cartographic counties](https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html):
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
places within the Dallas extract; Census 2024 place polygons supply interior
representative points for outer cities. These interior points can be distant
from historic downtowns. Love Field uses the OurAirports KDAL airport reference
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
avoids text collisions; crowded labels appear after zooming. The poster selects
labels for space while retaining every station symbol.

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
python3 maps/day08-utopia/main.py
python3 maps/day08-utopia/render.py
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
Local HTTP opened in Chrome; repeated native browser-control interruptions
prevented completing desktop/mobile visual interaction review. Treat that browser
review as outstanding, rather than a passed check.
