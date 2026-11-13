# Day 24 — Network · The Great American Road Trip

**1,000 miles. How many states can you visit?**

One browser-only strategy game, presented as a retro American highway atlas.
Choose a starting highway, add destinations, and collect states along the shortest
permitted route. More distinct states wins; fewer highway miles breaks a tie.

## Play locally

From the repository root:

```sh
python3 scripts/preview_map.py --directory maps/day24-network --port 8016
```

Open **http://127.0.0.1:8016/map.html**. No runtime routing API, external tile service,
backend, database, account or API key is needed. The graph, map assets, libraries
and fonts are local. A modern browser with WebGL2, Web Workers and gzip
`DecompressionStream` support is required.

- Click a highway to start; click another to drive. A starting pin alone counts
  **zero miles and zero states**.
- Drag pins, reorder/delete stops in **Your Stops**, or use **＋** there to insert
  an intermediate stop. Arrow keys move a focused pin; **Add Stop**, then Enter
  on the focused map, adds near the map center.
- Every edit is routed and checked **before acceptance**. The exact limit is
  **1,609,344 meters**. An over-budget or unroutable proposal leaves the accepted
  route, pins, state count, remaining miles, undo history and personal best intact.
- Undo restores an accepted snapshot; during validation it cancels the proposal.
  Clear cancels in-flight work and starts an empty trip. Rejected edits never
  appear in undo history. Up to 64 stops and 60 undo snapshots are supported.
- **State Passport** shows the same 48-state set used by the score. DC does not count.
- Your best updates automatically after a better accepted trip and stays in
  localStorage. Only compatible legacy 1,000-mile scores migrate; old sprint and
  nationwide-tour scores do not. A small reset option is inside How to Play.

Counters round distances for display; validation and ranking use the graph’s
centimeter distances. This is a route-planning puzzle, not a daily driving target
or real-time navigation distance.

## Architecture

MapLibre GL JS 5.6.0, Turf 7.2.0, vanilla JavaScript and locally hosted Barlow fonts.
`core.js` preserves the directed routing engine and precomputed state intervals.
`routing-worker.js` performs snapping and A* routing outside the UI thread.
`session.js` validates candidate edits atomically and rejects stale responses.
`app.js` updates the existing map sources and the four-metric scoreboard only
when an edit is accepted. The passport does not implement separate state analysis.

The OSM graph has **241,536 nodes**, **377,956 directed edges**, and reaches all
48 contiguous states. It enforces **17,873 node-based turn prohibitions**.
The compressed routing graph is about **20 MB** and the grouped highway display
about **5 MB** on first load; normal browser caching applies. Grouping display
features reduces rendering overhead without changing road coordinates or routing.
The interface initially renders Census state geography while highway assets load.

## Sources and limitations

See [DATA_SOURCES.md](DATA_SOURCES.md) and `data/sources.json` for provenance,
checksums, coverage and processing details. The OSM source is dated November 11,
2026; state geography is the official Census 2024 1:500,000 cartographic release.
OSM-derived highway/graph data use ODbL 1.0, with visible contributor attribution.

The intentionally restricted motorway/trunk network omits ordinary local streets.
Only source OSM node IDs create junctions. Conditional and via-way turn relations
are documented but not enforced; this is **not** a complete vehicle-navigation
model. Source access restrictions, carriageways, ramps and mapped one-way travel
are retained. No disconnected road is joined merely because two lines cross.

## Checks

```sh
node maps/day24-network/test_core.js
node maps/day24-network/test_session.js
node maps/day24-network/test_router.js
python3 scripts/build_pages.py
```

Core tests cover shortest paths, node-turn prohibitions, disconnected roads,
partial directed edges, repeated states/DC exclusion and scoring. Session tests
cover the exact budget, rejected adds/moves/reorders, route failures, undo/clear,
late responses and legacy-record migration. Nationwide tests compare A* with
Dijkstra and route CA–NY, FL–ME, WA–FL and CO–MA. A 48-state route tests network
coverage; it is deliberately **ineligible** for this 1,000-mile game.

For local browser checks, run the preview plus `python3 maps/day24-network/qa_server.py`
and open `/qa-browser.html`. The collector writes to `/tmp/day24-game-browser-report.json`.
It is a test utility, not a gameplay backend, and is excluded from the Pages package.
Browser results are recorded in `qa-review.json`.

## Offline rebuilding

The existing processed dataset is included; gameplay revisions do not require a rebuild.
To reproduce it, use a separate Python environment with `requests`, `ijson`,
`numpy`, `scipy`, `geopandas`, `shapely` and `pyproj`:

```sh
python maps/day24-network/download_data.py
# Official Census source: data/raw/day24/states-2024.zip; URL in data/census-source.json
python maps/day24-network/prepare_states.py
python maps/day24-network/prepare_graph.py
```

The download script caches bounded Overpass responses under ignored `data/raw/day24/highways`.
The builder measures full source geometry, preserves ordered Census intersections,
contracts degree-two chains, groups display geometry and prepares verified route
shields. `refresh_turns.py` is a diagnostic tool for turn-rule fixes, not needed for
normal rebuilding. Raw caches, temporary files and test previews are not packaged.

**Not deployed. Previous challenge days remain unchanged.**
