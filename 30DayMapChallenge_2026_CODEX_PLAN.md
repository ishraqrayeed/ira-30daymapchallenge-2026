# 30DayMapChallenge 2026 --- Codex Project Plan

## Mission

Build a public, reproducible **#30DayMapChallenge 2026** portfolio
centered on geospatial data science, transportation/mobility analytics,
GPS/location intelligence, spatial data engineering, network analysis,
and high-quality cartography.

The final repository should demonstrate professional-level Python,
SQL/spatial concepts, GeoPandas, OSMnx, H3, scikit-learn, raster
processing, GTFS, graph analytics, and scalable geospatial workflows.

Use only public/open or synthetic data. Never use proprietary employer
data, code, credentials, or intellectual property.

## Operating principles

1.  Follow the official 2026 prompts exactly.
2.  Every map should answer a question or tell a story.
3.  Prefer transportation, mobility, GIS, location intelligence, and
    spatial engineering topics.
4.  Reuse datasets when useful rather than finding 30 unrelated
    datasets.
5.  Give every published dataset proper attribution.
6.  Never commit secrets, huge raw datasets, or proprietary material.
7.  Prefer reproducible download scripts.
8.  Export a publication-quality PNG for every digital day.
9.  Document methods and limitations honestly.
10. Spend extra effort only on designated flagship days.
11. AI assistance should be disclosed. Day 10 is explicitly the
    prompting-only day.

## Repository structure

``` text
30DayMapChallenge-2026/
├── README.md
├── PLAN.md
├── requirements.txt
├── environment.yml
├── .gitignore
├── LICENSE
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── src/
│   ├── data/
│   ├── analysis/
│   ├── mobility/
│   ├── routing/
│   ├── visualization/
│   └── utils/
├── maps/
│   ├── day01-points/
│   ├── day02-lines/
│   ├── day03-polygons/
│   ├── day04-clusters/
│   ├── day05-sight/
│   ├── day06-vintage/
│   ├── day07-10-minute/
│   ├── day08-utopia/
│   ├── day09-urban-rural/
│   ├── day10-prompting-only/
│   ├── day11-sound/
│   ├── day12-power/
│   ├── day13-interactions/
│   ├── day14-borgesian/
│   ├── day15-inside-out/
│   ├── day16-collaborative/
│   ├── day17-light-dark/
│   ├── day18-null/
│   ├── day19-smell/
│   ├── day20-hexagons/
│   ├── day21-openstreetmap/
│   ├── day22-projections/
│   ├── day23-taste/
│   ├── day24-network/
│   ├── day25-is-this-a-map/
│   ├── day26-water/
│   ├── day27-new-tool/
│   ├── day28-feeling/
│   ├── day29-raster/
│   └── day30-pen-paper/
└── flagship/
    ├── mobility-intelligence/
    ├── transportation-network/
    └── spatial-big-data/
```

Each digital day should normally contain `README.md`, `map.png`,
`analysis.ipynb` or `main.py`, and `download_data.py` when appropriate.

## Core stack

Start with:

``` text
pandas
numpy
geopandas
shapely
pyproj
matplotlib
contextily
osmnx
networkx
scikit-learn
h3
rasterio
rioxarray
xarray
requests
pyarrow
duckdb
jupyter
```

Add specialized libraries only when needed.

## Core reusable public data

-   **OpenStreetMap:** roads, buildings, POIs, paths and network
    topology.
-   **RTD Denver GTFS/GTFS-RT:** transit stops, routes, schedules and
    vehicle positions. Respect RTD terms.
-   **Denver/Colorado open data:** crashes, streets, neighborhoods and
    infrastructure.
-   **DRCOG/CDOT:** regional transportation, traffic, bike corridors and
    planning datasets.
-   **US Census ACS + TIGER/Line:** population, commuting, demographics
    and boundaries.
-   **Microsoft T-Drive:** one week of trajectories from 10,357 Beijing
    taxis, roughly 15 million GPS observations. Use this as the main
    large GPS dataset.
-   **USGS/Landsat/public DEM:** elevation, terrain, imagery and raster
    analysis.
-   **DOE Alternative Fuels Data Center:** EV charging infrastructure.

# 30-Day Plan

## Day 1 --- Points

**Question:** Where are serious traffic crashes concentrated in Denver?\
**Data:** Denver/Colorado public crash data.\
**Methods:** pandas, GeoPandas, severity filtering, point
visualization.\
**Output:** Crash map emphasizing serious/fatal crashes.\
**Value:** Transportation safety + spatial analytics.\
**Effort:** 1--2 hours.

## Day 2 --- Lines

**Question:** What does Denver's road hierarchy look like?\
**Data:** OpenStreetMap.\
**Methods:** OSMnx, road classification, line styling.\
**Output:** Minimal road-network hierarchy map.\
**Value:** OSM + transportation networks.

## Day 3 --- Polygons

**Question:** How does population density vary across Denver metro?\
**Data:** Census ACS + TIGER/Line.\
**Methods:** polygon joins, density calculation, choropleth.\
**Value:** Census + location intelligence.

## Day 4 --- Clusters ⭐ FLAGSHIP

**Question:** Can activity locations be discovered automatically from
raw GPS trajectories?\
**Data:** Microsoft T-Drive.\
**Methods:** GPS cleaning, projected coordinates, DBSCAN, cluster
statistics.\
**Output:** Raw GPS observations plus inferred clusters.\
**Value:** GPS analytics + unsupervised ML.\
**Reuse:** Save outputs for Days 13, 18, 20 and 21.

## Day 5 --- Senses: Sight

**Question:** What terrain is visible from a selected Colorado
viewpoint?\
**Data:** Public DEM/elevation data.\
**Methods:** raster processing, elevation, viewshed if practical.\
**Output:** Viewshed/elevation map.\
If a true viewshed becomes disproportionately difficult, simplify
without losing the day.

## Day 6 --- Vintage

Create a vintage-style Denver transportation map using appropriately
licensed public geography. Focus on cartographic styling and typography.

## Day 7 --- 10 Minute Map

Create an RTD transit-stop map from GTFS. Time-box actual map creation
to 10 minutes once data is ready.

## Day 8 --- Utopia

Design an idealized Denver regional rail/transit network. Use existing
geography as context but make the proposed network clearly hypothetical.

## Day 9 --- Urban-Rural

Compare road-network structure between dense Denver and rural Colorado
using OSMnx metrics such as road density and intersection density.

## Day 10 --- Prompting Only ⭐

Complete a transportation/geospatial map through AI
prompting/command-line interaction. Document initial prompt, follow-ups,
failures, corrections, final output, and what still required human
judgment.

## Day 11 --- Senses: Sound

Map transportation noise exposure using credible public noise data or
clearly labeled proxies such as airport/highway proximity. Never
represent proxies as measured noise.

## Day 12 --- Power

Map EV charging accessibility in Colorado/Denver using public
charging-station data.

## Day 13 --- Interactions ⭐ FLAGSHIP

**Question:** How do movements connect origins and destinations?\
**Data:** T-Drive.\
**Methods:** trajectory segmentation, origin/destination extraction,
aggregation and flow visualization.\
**Output:** OD-flow map.\
**Value:** Mobility analytics.

## Day 14 --- Borgesian Map

Create an intentionally hyper-detailed map of a tiny Denver/Boulder area
using rich OpenStreetMap feature classes.

## Day 15 --- Inside Out

Invert normal cartographic conventions---for example, show
infrastructure while removing ordinary land context. Keep this
experimental and lightweight.

## Day 16 --- Collaborative Map

Collaborate with a real person. A family member or friend can sketch an
imaginary transit network or meaningful places; convert that
collaboration into a polished map. AI does not count as the
collaborator.

## Day 17 --- Light & Dark

Create a dark-background Denver road/network visualization using line
hierarchy and luminance.

## Day 18 --- NULL

**Question:** Where and how does GPS data quality fail?\
**Data:** T-Drive.\
Analyze missing/irregular timestamps, impossible jumps, observation
gaps, suspicious coordinates, sparse trajectories and speed anomalies.\
**Value:** Spatial data QA.

## Day 19 --- Senses: Smell

Map a smell-related phenomenon such as coffee shops, bakeries or another
defensible POI category using OSM/local open data. Keep it fun and
quick.

## Day 20 --- Hexagons ⭐ FLAGSHIP

**Question:** What mobility patterns emerge when millions of GPS
observations are aggregated spatially?\
**Data:** T-Drive.\
**Methods:** H3 conversion, aggregation, optional time-of-day
comparison.\
**Output:** H3 mobility-density map.\
**Stretch:** Compare raw-point visualization with H3 aggregation.

## Day 21 --- OpenStreetMap ⭐ FLAGSHIP

**Question:** Can raw GPS trajectories be reconstructed against the
street network?\
**Data:** T-Drive + OSM.\
**Methods:** OSMnx, trajectory cleanup, nearest edge/node or defensible
map-matching method.\
**Output:** Raw GPS versus reconstructed route.\
Describe the actual method accurately; do not call nearest-edge snapping
sophisticated probabilistic map matching.

## Day 22 --- Projections

Demonstrate how projection choice affects transportation distance/area
perception using several CRS choices.

## Day 23 --- Senses: Taste

Map South Asian/international food geography in Denver metro using
appropriately licensed POI data. Do not label a restaurant halal unless
a reliable source supports that classification.

## Day 24 --- Network ⭐ FLAGSHIP

**Question:** Which intersections or road segments are structurally
important?\
**Data:** OSM.\
**Methods:** OSMnx + NetworkX centrality metrics.\
**Output:** Network-centrality map.\
If full metro betweenness is too expensive, use a representative
subnetwork or approximation and document it.

## Day 25 --- Is This a Map?

Blend transportation geography with abstract data visualization while
retaining some geographic structure.

## Day 26 --- Water

Overlay transportation infrastructure with credible public flood/water
data. Present it as exploratory exposure analysis unless the methodology
supports formal risk assessment.

## Day 27 --- New Tool ⭐

Prefer **DuckDB Spatial** if genuinely new. Load a moderately large
spatial dataset and demonstrate filtering, spatial joins and
aggregation. Include a small performance note.

## Day 28 --- Senses: Feeling

Build a clearly labeled proxy for urban calm/peacefulness using factors
such as green-space access, major-road distance, traffic intensity and
water proximity. Never claim this objectively measures emotion.

## Day 29 --- Raster

Use Landsat or another public raster source to show Front Range/Denver
land cover, urban growth or change. Use rasterio/rioxarray.

## Day 30 --- Pen & Paper

No digital map creation. Draw a transportation map from memory or an
ideal transit network by hand. Photograph/scan it for the repository and
discuss what the mental map emphasizes or omits.

# Flagship Portfolio Stories

## 1. From Raw GPS Pings to Mobility Intelligence

Combine Days 4, 13, 18, 20 and 21:

``` text
raw GPS
→ validation
→ cleaning
→ activity clustering
→ OD inference
→ H3 mobility patterns
→ OSM snapping / route reconstruction
```

This should become the strongest portfolio case study.

## 2. Transportation Network Intelligence

Combine Days 2, 9, 21 and 24:

``` text
OpenStreetMap
→ road graph
→ network statistics
→ urban/rural comparison
→ GPS/network integration
→ centrality analysis
```

## 3. Spatial Data Engineering

Combine Day 20, Day 27 and selected large-data workflows.

A later optional benchmark can compare GeoPandas, DuckDB Spatial,
PostGIS and Apache Sedona. Do not let this benchmark derail the November
challenge.

# Standard Daily Workflow

For each day:

1.  Read the official theme and this plan.
2.  Verify the intended dataset is accessible.
3.  Read/document licensing and attribution requirements.
4.  Download/cache data when permitted.
5.  Inspect schema and perform QA.
6.  Implement the analysis.
7.  Generate the map.
8.  Export a high-resolution PNG.
9.  Complete the day's README.
10. Record question, source, method, tools, finding and limitations.
11. Add the map to the root README gallery.
12. Run basic code-quality checks.
13. Commit with a descriptive message.
14. Do not automatically publish to social media.

# Daily README Template

``` markdown
# Day XX — [Prompt]

## [Map title]

### Question
What are we trying to understand?

### Map
![Map](map.png)

### Key finding
One to three sentences.

### Data
- Dataset:
- Provider:
- Source:
- License/terms:
- Date accessed:

### Method
Brief processing/analysis explanation.

### Tools
Python · GeoPandas · ...

### Reproduce
Instructions.

### Limitations
Be explicit.

### #30DayMapChallenge
Day XX of #30DayMapChallenge 2026.
```

# Visual Standards

Maps should generally have a clear title, concise subtitle when useful,
readable legend when needed, source attribution, restrained annotation
and sensible extent.

Avoid unstyled default plots when modest styling materially improves the
map.

Export `map.png` at roughly 2000--3000 px wide where practical. Never
fabricate data.

# Git / Data Rules

Suggested `.gitignore`:

``` text
.env
.venv/
__pycache__/
.ipynb_checkpoints/
.DS_Store
data/raw/*
data/interim/*
*.parquet
*.gpkg
*.tif
*.tiff
```

Never commit credentials, employer data, proprietary code or huge raw
datasets.

# Code Quality

Prefer reusable functions over giant notebook cells. Use explicit CRS
handling and a suitable projected CRS for distance-based operations.
Validate geometry/coordinates instead of silently ignoring problems. Use
docstrings/type hints for reusable modules where useful.

# Time Budget

-   Normal day: 60--90 minutes.
-   Technical day: up to \~2 hours.
-   Flagship day: up to \~3--4 hours.
-   Flagships: Days 4, 10, 13, 20, 21, 24 and 27.

If a normal day becomes a rabbit hole, simplify it.

# Consulting/Portfolio Goal

The completed work should demonstrate ability to solve commercial
problems involving GPS trajectories, routing, mobility analytics,
location intelligence, transportation networks, spatial ETL, geospatial
automation, clustering, large spatial datasets, data QA and
demographic/location analysis.

Do not make every README a sales pitch. Let the work prove the skill.

# Initial Codex Task

Start by scaffolding the repository.

1.  Create the directory structure above.
2.  Create `.gitignore`.
3.  Create `requirements.txt`.
4.  Create `environment.yml`.
5.  Create the root `README.md`.
6.  Create all 30 day directories.
7.  Add the README template to each day.
8.  Create the `src/` package structure.
9.  Create a small reusable plotting utility.
10. Create a reusable data-download utility.
11. Do **not** download all datasets.
12. Do **not** attempt all 30 maps.
13. After scaffolding, begin only **Day 1 --- Points**.

For Day 1:

1.  Locate an authoritative Denver/Colorado traffic-crash public
    dataset.
2.  Document its source and terms.
3.  Download programmatically if practical.
4.  Inspect columns and coordinate information.
5.  Validate coordinates and CRS.
6.  Identify severity fields if available.
7.  Produce a clean point map focused on serious/fatal crashes.
8.  Add context/basemap only when licensing and readability permit.
9.  Export `maps/day01-points/map.png`.
10. Complete `maps/day01-points/README.md`.
11. Update the root gallery.
12. Report what was created, assumptions, limitations and possible
    improvements.
13. **Stop after Day 1 unless explicitly instructed to continue.**

# Official 2026 Prompts

1.  Points
2.  Lines
3.  Polygons
4.  Clusters
5.  Senses: Sight
6.  Vintage
7.  10 minute map
8.  Utopia
9.  Urban-rural
10. Prompting only
11. Senses: Sound
12. Power
13. Interactions
14. Borgesian map
15. Inside out
16. Collaborative map
17. Light & dark
18. NULL
19. Senses: Smell
20. Hexagons
21. OpenStreetMap
22. Projections
23. Senses: Taste
24. Network
25. Is this a map?
26. Water
27. New tool
28. Senses: Feeling
29. Raster
30. Pen & paper

# Definition of Success

Success is not merely producing 30 maps. By November 30 the repository
should contain:

-   a coherent geospatial portfolio
-   several strong transportation/mobility analyses
-   reproducible public-data workflows
-   strong cartography
-   a substantial GPS/mobility case study
-   network-analysis work
-   spatial data-engineering evidence
-   clean GitHub documentation
-   work that can be linked directly in consulting proposals and job
    applications

Quality and coherence matter more than checking every box.
