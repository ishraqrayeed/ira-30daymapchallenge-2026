# Day 1 — Points

## Someone Was Walking Here.

[Interactive map](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day01-points/) ·
[Annual results](map.results.md) · [QA summary](map.qa.json)

**126 mapped fatal crashes involving pedestrians · City & County of Denver · 2021–2025.**

Each walking-person symbol marks one crash. The dataset identifies pedestrian
involvement; it does not establish that the person killed was the pedestrian.
The map subtitle uses “fatal pedestrian crashes” as shorthand for this selection.

## Data

- Provider: City and County of Denver / Denver Police Department.
- [Traffic Accidents (Offenses), layer 325](https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/ArcGIS/rest/services/ODC_CRIME_TRAFFICACCIDENTS5YR_P/FeatureServer/325).
- Attribution: [City of Denver Open Data Catalog](https://opendata-geospatialdenver.hub.arcgis.com/),
  [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/).
- Retrieved: October 31, 2026 UTC. Download manifests record timestamps and checksums.
- Basemap: © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright).

## Method

1. Download 2021–2025 crashes with pedestrian or bicycle involvement and positive
   injury counts or an explicit fatal/SBI offense label.
2. Validate IDs, dates, severity, mode flags, coordinates, and the declared CRS.
   Collapse duplicate incident rows and reject conflicting locations or years.
3. Select fatal events with `pedestrian_ind = 1`. Fatal classification uses a
   positive `FATALITIES` count or a `TRAF - ACCIDENT - FATAL` offense label.
4. Embed one original walking-person SVG per crash in a deck.gl HTML map.

The base download contains 731 rows. Of these, 716 pass coordinate validation;
15 lack geometry. The story filter retains 126 events. The 15 location exclusions
apply to the base download, not solely to the final story subset.

Numeric injury counts were incomplete in the source, so explicit offense labels
also support the severity filter. Person-specific fatality modes are not available
in the current cache. Checksums and exclusions are recorded in `map.qa.json`.

| Year | Mapped fatal crashes involving pedestrians |
| --- | ---: |
| 2021 | 21 |
| 2022 | 25 |
| 2023 | 33 |
| 2024 | 20 |
| 2025 | 27 |

## Reproduce

From the repository root, after installing `requirements.txt`:

```sh
python3 maps/day01-points/download_data.py --start-year 2021 --end-year 2025
python3 maps/day01-points/main.py --start-year 2021 --end-year 2025
python3 scripts/preview_map.py
```

Open `http://127.0.0.1:8000/map.html`, keeping the preview terminal running.
Use the HTTP preview rather than opening the file directly, so OSM tile requests
include the browser referrer. Screenshots are taken from the browser.

## Reading the map

The data covers City and County of Denver reports, not the full metropolitan
area. The opening view focuses on urban Denver; all 126 records remain available
by panning. Symbols stay at the reported coordinates. Tooltips show occurrence
date and time in `America/Denver`, with MST/MDT labels. Source-year selection
continues to use the service's UTC dates.

## Limitations

These are reported crash events, not a count of pedestrian deaths or a measure
of exposure-adjusted risk. Missing locations, unreported events, and changing
classifications affect coverage. Overlapping symbols can hide multiple crashes.
Current basemap streets may differ from those at the time of the crash.

The [pedestrian SVG](../../assets/pedestrian.svg) is lightweight vector artwork
recreated from `assets/pedestrian_v2.png`: a front-facing neutral silhouette,
muted dark red fill, and thin cream halo. The reference raster is not embedded.
The 64 × 80 SVG works with the current deck.gl atlas or a Leaflet `L.icon`:

```js
const pedestrianIcon = L.icon({
  iconUrl: 'assets/pedestrian.svg',
  iconSize: [17.6, 22],
  iconAnchor: [8.8, 11], // Center on the crash coordinate, matching Day 1.
  popupAnchor: [0, -11],
});
```

Code, artwork, and styling were developed with Codex assistance and reviewed by
the author.
