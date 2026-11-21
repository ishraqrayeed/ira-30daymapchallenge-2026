# 30DayMapChallenge 2026

A month of maps about transportation, mobility, and the places we live.

[Explore the maps](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/) ·
[Challenge themes](https://30daymapchallenge.com/) · [Project plan](PLAN.md)

## Day 1 — Points

### Someone Was Walking Here.

126 mapped fatal crashes involving pedestrians in the City and County of Denver,
2021–2025. One walking-person symbol represents one crash event.

[Open the map](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day01-points/) ·
[Data and methods](maps/day01-points/README.md)

## Day 2 — Lines

### Every Line a Climb

Rocky Mountain National Park's hiking trails, colored by elevation, in a circular
terrain map. Click or tap a trail segment to explore its elevation profile.

[Open the map](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day02-lines/) ·
[Data and methods](maps/day02-lines/README.md)

## Day 3 — Polygons

### Dhaka in 45 Minutes

Modeled metro + walking accessibility from Farmgate, Dhaka, Bangladesh.

[Open the map](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day03-polygons/) ·
[Data and methods](maps/day03-polygons/README.md)

## Day 4 — Clusters

### Halal in Manhattan

121 identifiable halal food locations compiled from public sources. DBSCAN groups
92 locations into fourteen spatial clusters; 29 remain unclustered. Not a census.

[Open the map](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day04-clusters/) ·
[Data and methods](maps/day04-clusters/README.md)

## Day 5 — Sight

### What Messi Saw

The geometric goal opening from Lionel Messi's 35 recorded 2026 World Cup shots.

[Open the map](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day05-sight/) ·
[Data and methods](maps/day05-sight/README.md)

## Day 6 — Vintage

### TELLURIDE

*Echoes of a Mining Town* — 293 footprints with historic ratings over fine USGS
terrain contours. Preservation ratings do not imply construction dates.

[Open the map](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day06-vintage/) ·
[Data, QGIS project and reproduction](maps/day06-vintage/README.md)

## Day 7 — Accessibility

### Same city. Quite the journey.

Denver Union Station to Denver International Airport: the supplied map, unchanged.

[Open the map](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day07-10-minute/) ·
[Map notes](maps/day07-10-minute/README.md)

## Day 8 — Utopia

### What If DFW Had NYC’s Subway?

An alternate reality where the Metroplex runs on rails. Ten fictional services
connect real locations across Dallas–Fort Worth.

[Open the map](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day08-utopia/) ·
[Data, methods and poster](maps/day08-utopia/README.md)

## Day 9 — Urban–Rural

### Las Vegas — The Desert That Became a City

Compare and animate ten GHSL estimates of the valley’s developed footprint,
1975–2020, over contemporary satellite imagery.

[Open the map](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day09-urban-rural/) ·
[Data and methods](maps/day09-urban-rural/README.md)

## Day 10 — Prompt Only

### The Other Side of Earth

Choose a city or any point on Earth, then travel through a schematic planetary
cross-section to its calculated antipode.

[Open the map](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day10-prompting-only/) ·
[Sources and method](maps/day10-prompting-only/README.md)

## Day 11 — Sound

### The World in Traffic

Twelve circular OpenStreetMap street networks paired with authentic traffic
recordings from cities around the world. Choose a city to hear its streets.

[Open the map](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day11-sound/) ·
[Sources and methods](maps/day11-sound/README.md)

## Run locally

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python maps/day01-points/download_data.py --start-year 2021 --end-year 2025
python maps/day01-points/main.py --start-year 2021 --end-year 2025
python scripts/preview_map.py
```

The preview opens at `http://127.0.0.1:8000/map.html`. Basemap tiles load in the
browser. Capture screenshots there for social posts.

## Day 12 — Power

**The Pulse of Hoover Dam** lights archived transmission corridors across the
Southwest with an artistic electric pulse.
[Open the map](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day12-power/) ·
[Sources and methods](maps/day12-power/README.md).

## Day 13 — Interactions

**The Great American Road Trip** — a browser-only route-planning game:
1,000 miles. How many states can you visit?
[Open the map](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day13-interactions/) ·
[Map and methods](maps/day13-interactions/README.md).

## Day 14 — Borgesian Map

**Denver, City of 280+ Parks** — follow the map from Denver’s park system to
Washington Park and a real mapped bench.
[Open the map](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day14-borgesian/) ·
[Data and reproduction](day14-borgesian/README.md).

## Day 15 — Inside Out

**The Road Carved Into the Mountains** — Switchbacks of the Million Dollar Highway.
Compare a credited photograph, the GIS alignment, and a rotatable 3D road ribbon.
[Open the map](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day15-inside-out/) ·
[Data and reproduction](maps/day15-inside-out/README.md).

## Day 17 — Light & Dark

**The First 5, the Last 5** — A flight home from JFK to Denver. Replay the first
and last five recorded miles, with VIIRS brightness and ISS photographic detail.
[Open the map](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day17-light-dark/) ·
[Data and methods](maps/day17-light-dark/README.md).

## Day 18 — NULL

**The Great American Nothing** — Follow westbound I-70 from St. Louis to Denver
and reveal stretches of repetitive landscape.
[Open the map](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day18-null/) ·
[Data and methods](day18-null/README.md).

## Day 19 — Smell

**Where Cinnamon Grows** follows the curls of cinnamon bark into the terrain of
Sumatra’s Kerinci Highlands.
[View the poster](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day19-smell/) ·
[Sources and reproduction](maps/day19-smell/README.md).

## Project layout

- `maps/`: daily maps, code, and methods.
- `src/`: shared data processing and rendering.
- `assets/` and `templates/`: symbols and HTML layouts.
- `data/`: local source caches, excluded from Git.
- `scripts/`: local preview and publishing.

## Checks and publishing

```sh
python -m unittest discover -s tests -v
node tests/test_map_controls.js
node tests/test_trail_controls.js
python scripts/build_pages.py
bash scripts/publish_github.sh
```

See [hosting instructions](docs/HOSTING.md) for the GitHub connection and deployment.
Source attribution and limitations are documented with each map.

[Daily workflow and next-day notes](docs/WORKFLOW.md) · [Design reference](docs/DESIGN.md)

## Day 20 — Hexagons

**Where America Learns to Play Soccer** maps 2,307 US Club Soccer directory locations
across all 50 states and D.C. Select a hex to see the clubs listed there.

[Open the atlas](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day20-hexagons/) ·
[Data and methods](maps/day20-hexagons/CLUBS.md)
