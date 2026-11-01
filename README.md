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

[Data and methods](maps/day02-lines/README.md)

Local preview: `python3 scripts/preview_map.py --directory maps/day02-lines --port 8002`

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
