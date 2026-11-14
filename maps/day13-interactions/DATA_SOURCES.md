# Highway data, geography and game methodology

## Sources

**Roads:** © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright),
[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/), retrieved in 18 bounded
queries from the [North America Overpass mirror](https://ovp.dresel.systems/api-na/interpreter).
The responses include original way/node IDs, driving tags, geometries and relevant
turn-restriction relations. Exact queries, source timestamps and compressed-cache
SHA-256 values are in `data/sources.json`; source timestamps are November 11, 2026.
Only offline preparation uses this service. The browser never calls it.

**States:** [US Census Bureau 2024 cartographic boundaries, 1:500,000](https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_state_500k.zip).
Alaska, Hawaii and territories are excluded. DC remains traversable but uncounted.
The original Census polygons determine road/state intersections; the displayed
polygons are simplified by 250 m. `data/census-source.json` records the source hash.
Census geography is public US government data, not a new administrative delineation.

**Software/fonts:** MapLibre GL JS 5.6.0, Turf 7.2.0 and Barlow/Barlow Condensed are
vendored with BSD/MIT/OFL license text. Interstate-style SVGs are generated locally
only for Interstate references present in the highway attributes. Their locations
lie on those source lines; the title’s “Road Trip 48” shield is a decorative state-count graphic.

## Directed highway preparation

1. Retain `motorway`, `motorway_link`, `trunk` and `trunk_link` features intersecting
   the lower-48/DC geography. Exclude private, prohibited, destination-only,
   permit-only and time-restricted driving access, designated HOV-only roads, and
   reversible/alternating roads. Motorcar-specific permission takes precedence
   over general access. Toll roads remain eligible.
2. Split at shared **original OSM node IDs**, way ends and supported turn-via nodes.
   Separate carriageways remain separate; geometric intersections never create junctions.
   Honor mapped motorcar/motor-vehicle one-ways, reverse one-ways, and motorway/
   roundabout defaults. Missing motorway-link one-way tags are not invented.
3. Retain the largest strongly connected source-node component. Other components,
   incomplete links and foreign detours are excluded rather than connected artificially.
   Contract only unambiguous degree-two chains with consistent road references,
   classes, speed attributes and directionality. Preserve junctions and turn-via nodes.
4. Enforce applicable unconditional **node-via** `no_*`/`only_*` restrictions at
   routing time using incoming/outgoing edge IDs. A same-way no-U-turn rule blocks
   the returning edge, not legal straight continuation on that way. Restrictions
   whose only allowed destination leaves the retained network may make an approach
   unusable; the router reports failure rather than ignoring the restriction.
5. Measure complete original curves on the WGS84 ellipsoid using PyProj Geod.
   Store weights in integer centimeters. Preserve geometry with 2 m simplification
   for route display; the 100 m generalized background network is cartographic only.
   Grouping equal-style background lines does not change coordinates or connectivity.

The graph contains **241,536 nodes / 377,956 directed edges**, including
**17,873** enforced turn prohibitions. QA reports source components, discarded
nodes and unsupported relations. The graph is identical for all gameplay edits.

## Routing and snapping

The worker creates a grid spatial index and snaps to the nearest eligible physical
highway geometry, including positions inside an edge. Partial-edge fractions are
applied to measured edge lengths. Reverse options exist only for actual paired
edges on the same physical source path; proximity to a parallel carriageway never
creates a crossing. Candidate routes preserve the arrival/departure direction at
intermediate waypoints. A* tracks incoming edges so supported turns remain enforceable.
Its conservative distance heuristic is checked against Dijkstra in the real graph.

The router returns actual edge paths and geometry, never straight-line fallbacks.
Waypoints are projected onto the retained network, not on residential streets.
Country-scale clicks are approximate; zoom for precise carriageway placement.

## State counting

Full-resolution Census intersections are computed **offline**, along each original
road curve. Every edge stores ordered interval-end distances and state IDs, so
partial edges count only their traveled portion. Positive road intervals of at least
**1 m** count; point touches do not. If a road follows a shared boundary exactly,
its coincident interval is assigned once, deterministically by the lowest Census
FIPS code. This is a documented counting convention, not a survey of lane jurisdiction.

Each accepted route unions its traversed state IDs. Repeated visits count once;
DC never counts. A single unrouted starting point counts zero states. The map,
score and passport all use the same returned set. Generalized Census geography
and OSM positional error can affect fine boundary cases.

## The 1,000-mile rule and records

The exact budget is **1,609,344 meters = 160,934,400 centimeters**. A candidate add,
move, insertion or reorder is routed before acceptance. Budget and routing failures
leave the previous accepted route, pins, counters, history and record unchanged.
Generation tokens discard stale asynchronous results. Undo uses validated snapshots;
clear cancels pending work. Display rounding never determines eligibility.

Personal best ranks **most states**, then **least distance**, for accepted nonzero
trips within the budget. Records are localStorage-only and tied to the graph version.
Only compatible old 1,000-mile records migrate; old sprint/nationwide-tour scores do
not. No data is uploaded, and no global ranking is claimed.

## Limits

This is a simplified major-highway model, not live navigation or a safety/accessibility
assessment. **7,815 via-way/complex** and **270 conditional** turn relations are counted
but not enforced. Date/time restrictions, temporary closures and traffic are not modeled.
State boundary generalization and missing OSM restrictions remain limitations.
Road distances can differ from full-road-network directions. The mileage budget is
an abstract game constraint, not a recommended amount to drive in a day.

The old estimated-time edge attribute remains in the preserved dataset but is not
shown or used for scoring. The website needs only static hosting, WebGL2, workers
and browser gzip decompression. Raw responses and Python caches stay out of Git;
OSM-derived processed data are redistributed under ODbL 1.0 with attribution.
