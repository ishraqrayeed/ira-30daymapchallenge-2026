# 30DayMapChallenge 2026

A reproducible geospatial portfolio exploring transportation, mobility, GPS data,
spatial engineering, and cartography using public or synthetic data.

## Current milestone

Repository scaffold and the Day 1 five-year maps are available. All five source
snapshots for **2021–2025** match their checksums. Of 731 downloaded records,
716 unique events can be mapped; 15 lack geometry. The mapped subset includes
137 fatal and 579 serious-injury crashes involving pedestrians or bicyclists.
The corrected severity filter uses positive injury counts or explicit fatal/SBI
offense labels. The OSM basemap and minimal headline/legend overlay are in place. Optional detail enrichment and final
storytelling remain before publication.
Days 2–30 remain planned.

## Setup

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Alternatively: `conda env create -f environment.yml`.
Dependencies use compatibility ranges; a fully resolved lockfile is still pending.

## Day 1

Focus: Denver pedestrian- or bicycle-involved fatal/serious-injury crashes
across five complete years, 2021–2025. Involvement does not identify which person was injured.

Run from the repository root on a machine with internet access:

```sh
python maps/day01-points/download_data.py --start-year 2021 --end-year 2025 --details
python maps/day01-points/main.py --start-year 2021 --end-year 2025
python -m unittest discover -s tests -v
```

The downloader caches a dated-source manifest and SHA-256 checksum. The map script
writes the interactive `map.html`, a QA summary, and annual results. Capture
LinkedIn screenshots directly from the browser; no separate PNG is generated.
See [Day 1](maps/day01-points/README.md) for source details and limitations.

## Shared design

Open [the local visual preview](docs/template-preview.html) in a browser.
The initial preview uses synthetic data. Its layout was approved; the live Day 1
map now uses a full-screen map with a minimal headline, legend, and source credits.
See [the draft specification](docs/TEMPLATE_DRAFT.md).

Interactive maps use pydeck/deck.gl HTML exports, with browser screenshots for
social posts. HTML loads JavaScript and OSM tiles online. GitHub Pages is the
selected host; the new repository will be `ishraqrayeed/ira-30daymapchallenge-2026`.
The [publish script and hosting instructions](docs/HOSTING.md) are prepared;
creation and initial deployment still require the internet-connected terminal.

## Gallery / progress

Day 1 provisional output (presentation and source-completeness review remain):

[Day 1 — pedestrian- and bicycle-involved severe crashes](maps/day01-points/README.md)

[Explore the interactive map](maps/day01-points/map.html). Pending entries are not completed work.

| Day | Theme | Status |
| --- | --- | --- |
| 01 | [Points](maps/day01-points/README.md) | Maps generated; presentation review pending |
| 02 | [Lines](maps/day02-lines/README.md) | Planned |
| 03 | [Polygons](maps/day03-polygons/README.md) | Planned |
| 04 | [Clusters](maps/day04-clusters/README.md) | Planned |
| 05 | [Sight](maps/day05-sight/README.md) | Planned |
| 06 | [Vintage](maps/day06-vintage/README.md) | Planned |
| 07 | [10 Minute](maps/day07-10-minute/README.md) | Planned |
| 08 | [Utopia](maps/day08-utopia/README.md) | Planned |
| 09 | [Urban Rural](maps/day09-urban-rural/README.md) | Planned |
| 10 | [Prompting Only](maps/day10-prompting-only/README.md) | Planned |
| 11 | [Sound](maps/day11-sound/README.md) | Planned |
| 12 | [Power](maps/day12-power/README.md) | Planned |
| 13 | [Interactions](maps/day13-interactions/README.md) | Planned |
| 14 | [Borgesian](maps/day14-borgesian/README.md) | Planned |
| 15 | [Inside Out](maps/day15-inside-out/README.md) | Planned |
| 16 | [Collaborative](maps/day16-collaborative/README.md) | Planned |
| 17 | [Light Dark](maps/day17-light-dark/README.md) | Planned |
| 18 | [Null](maps/day18-null/README.md) | Planned |
| 19 | [Smell](maps/day19-smell/README.md) | Planned |
| 20 | [Hexagons](maps/day20-hexagons/README.md) | Planned |
| 21 | [Openstreetmap](maps/day21-openstreetmap/README.md) | Planned |
| 22 | [Projections](maps/day22-projections/README.md) | Planned |
| 23 | [Taste](maps/day23-taste/README.md) | Planned |
| 24 | [Network](maps/day24-network/README.md) | Planned |
| 25 | [Is This A Map](maps/day25-is-this-a-map/README.md) | Planned |
| 26 | [Water](maps/day26-water/README.md) | Planned |
| 27 | [New Tool](maps/day27-new-tool/README.md) | Planned |
| 28 | [Feeling](maps/day28-feeling/README.md) | Planned |
| 29 | [Raster](maps/day29-raster/README.md) | Planned |
| 30 | [Pen Paper](maps/day30-pen-paper/README.md) | Planned |

## Portfolio case studies

- [Mobility intelligence](flagship/mobility-intelligence/README.md)
- [Transportation networks](flagship/transportation-network/README.md)
- [Spatial data engineering](flagship/spatial-big-data/README.md)

## Working principles

Use public/open or clearly labeled synthetic data; document attribution, CRS,
methods, and limitations. Raw data stays out of version control. AI assistance
is disclosed in daily documentation. Day 16 requires a real collaborator and
Day 30 requires a hand-drawn map. No social posting or hosting is automated.

The [original plan](30DayMapChallenge_2026_CODEX_PLAN.md) defines the scope.
The supplied 2026 theme list still needs independent official verification.
Project code and artwork licensing awaits an owner-selected license; third-party
licenses apply separately. See [LICENSE](LICENSE).
