# Daily mapping workflow

## Start with the story

Read the day's official theme in `PLAN.md`. Choose one question, geography, and
time period, then a visual idea suited to them. The goal is an interesting map,
not a dashboard of every available field. A memorable title and purposeful
symbols worked well for Day 1. Humor should suit the subject.

## Build and validate

1. Work in `maps/dayXX-theme/`. Keep reusable code in `src/` and artwork in `assets/`.
2. Check the authoritative source, terms, schema, dates, units, and CRS. Download
   programmatically and cache under ignored `data/` directories. Record retrieval
   dates and checksums when practical.
3. Validate the data before selecting the story subset. Record exclusions, counts,
   and limitations. Label the quantity actually supported by the source.
4. Generate `map.html`, a QA summary, and concise results. Start the day's README
   from `templates/day-readme.md`, filling it with findings rather than placeholders.

Day 1's source is a useful reference for ArcGIS object-ID batching with POST
requests, severity-label fallback, timestamp conversion, and geometry checks.
Those are dataset-specific methods, not requirements for every day.

## Review in the browser

```sh
python3 scripts/preview_map.py --directory maps/dayXX-theme
```

Replace `dayXX-theme` with the actual folder. If the server is already running for
another day, stop it or pass a different `--port`. Open the printed HTTP URL.

Review the title, scope, legend, source credits, default extent, visual hierarchy,
and tooltips. Inspect the intended screenshot size and a narrow mobile viewport.
Confirm symbols and basemap tiles actually appear. Keep overlays small; put
methods and detailed limitations in the README.

The final deliverable is HTML. The user captures a screenshot after tiles load,
with the cursor off the features and source credits visible.

## Publish and share

Add the finished day to `templates/portfolio-index.html` and extend
`scripts/build_pages.py` to package its named route and reports. The packager
  supports **Days 1–5**; it does not automatically discover new days.

Run checks appropriate to the new code. Existing checks are:

```sh
python3 -m unittest discover -s tests -v
node tests/test_map_controls.js
python3 scripts/build_pages.py
```

When publication is requested:

```sh
bash scripts/publish_github.sh
```

Verify the deployed map before posting. A LinkedIn draft can include the daily
theme, a personal connection or question, the main finding, map and repository
links, and `#30DayMapChallenge`. Social posting is manual.

## Resume with Day 2

- Theme: **Lines**. Folder: `maps/day02-lines/`.
- Implemented story: **Every Line a Climb**, Rocky Mountain National Park hiking
  trails colored by elevation, with a centered circular USGS terrain map.
  NPS's park-wide summary is 350+ miles; the cleaned map contains approximately
  349.2 miles. User approved publication; future edits should preserve this map.
- Day 1 is complete: 126 fatal crashes involving pedestrians, City and County of
  Denver, 2021–2025. One walking-person symbol equals one crash, not one person.
- Keep `/day01-points/` and the `/day01/` redirect. Day 2's route should be
  `/day02-lines/`, linked from the root portfolio index.
- The approved Day 1 style lives in `templates/story-panel.html`,
  `src/visualization/interactive.py`, and `src/visualization/basemap.py`. The latter
  uses 60% OSM opacity. Adapt the visual language to lines without redesigning or
  regenerating the finished Day 1 map unnecessarily.
- The root README and daily documentation were deliberately shortened. Keep new
  documentation factual and concise; avoid process logs and repetitive disclaimers.

Repository: `ishraqrayeed/ira-30daymapchallenge-2026`.
Live portfolio: https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/
