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
