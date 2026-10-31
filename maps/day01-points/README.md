# Day 01 — Points

## On foot, on a bike: five years of severe crashes in Denver

Scope: five complete calendar years, **2021–2025**. Include crashes involving
pedestrians or bicyclists and identified as fatal/serious injury by positive
injury counts **or explicit fatal/SBI offense labels**.

Status: all five corrected snapshots downloaded and checksum-verified. The
five-year HTML was generated from real data. The PNG export has been removed;
LinkedIn images will be captured as browser screenshots. The outputs remain
provisional while source completeness and presentation receive further review.

### Question
Where do reported severe crashes involving people walking or cycling occur,
and how do their recorded counts vary across the five years?

### Why the filter changed
The user-supplied 2025 coverage audit found 680 pedestrian/bicycle-involved source
rows, but just five with positive injury counts. It found 34 fatal-offense rows
and 88 SBI-offense rows; 119 severe-offense rows lacked positive injury counts.
These are source-row counts, not deduplicated crash totals. Filtering exclusively
on numeric injury counts omitted many explicitly severe-labeled records.

The revised filter includes either severity signal. Explicit labels classify
crash severity; they do not supply missing numbers of people injured or killed.
The `ped-bike-severe-v2` cache prefix prevents reuse of the earlier count-only
cache. All download filters are retained in source manifests.

### Map and findings

[Interactive map](map.html) · [Results and annual counts](map.results.md) · [QA report](map.qa.json)

The downloaded subset contains **731 records**, with **716 unique mapped crash
events** after excluding **15 records with missing geometry**. No other records
were excluded, and no duplicate incidents were found. Of the mapped events,
**137 are fatal crashes** and **579 are serious-injury crashes without recorded
fatal severity**. Pedestrian involvement appears in **573** events (about 80%),
and bicycle involvement in **143**; no mapped event has both flags.

These figures describe the selected, geocoded reports, not every crash or the
number of people harmed. They do not establish relative risk for walking versus
cycling. All 15 location exclusions are missing geometry, rather than coordinates
outside the plausibility envelope.

| Year | Downloaded rows | Missing geometry | Mapped crashes | Fatal | Serious injury only |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2021 | 166 | 3 | 163 | 22 | 141 |
| 2022 | 128 | 3 | 125 | 29 | 96 |
| 2023 | 168 | 4 | 164 | 35 | 129 |
| 2024 | 145 | 2 | 143 | 20 | 123 |
| 2025 | 124 | 3 | 121 | 31 | 90 |

573 validated source rows qualified solely through explicit offense labels,
confirming why numeric injury counts alone were insufficient. This count happens
to equal the pedestrian-involved total; the two quantities represent different
attributes and must not be conflated.

The point pattern suggests repeated locations and linear arrangements, but no
street-level claim or statistical hotspot result is made. The interactive basemap uses OpenStreetMap streets and place labels. A minimal headline card shows the city, period, and severity legend; source credits
remain visible. Explanatory context and AI disclosure stay in this documentation
instead of on the map. Stronger point contrast and white outlines improve separation.

### Data
- Provider: City and County of Denver / Denver Police Department.
- Dataset: Traffic Accidents (Offenses), current layer 325.
- [Source layer](https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/ArcGIS/rest/services/ODC_CRIME_TRAFFICACCIDENTS5YR_P/FeatureServer/325).
- [City of Denver Open Data Catalog and terms](https://opendata-geospatialdenver.hub.arcgis.com/).
- License: [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/).
- Metadata first inspected: 2026-10-30. Corrected snapshots retrieved on
  2026-10-31 UTC (2026-10-30 in Denver), with individual SHA-256 checksums.
- Source is mutable; historical coverage and classification consistency require
  review before interpreting annual comparisons.

### Method
Download one snapshot per year using object-ID batches and verify every requested
ID. Record batches use form-encoded POST requests so long object-ID lists do not
exceed URL length limits. Require an explicit EPSG:4326 response CRS. Check incident IDs, dates,
coordinates, mode flags, and severity signals. The broad Denver plausibility
box (-105.3 to -104.4 longitude, 39.5 to 40.1 latitude) is not a boundary filter.

Classify as fatal when `FATALITIES > 0` or the trimmed, case-normalized offense
label is `TRAF - ACCIDENT - FATAL`. Classify other retained events as serious
injury when `SERIOUSLY_INJURED > 0` or the label is `TRAF - ACCIDENT - SBI`.
Track rows recovered solely through offense labels. Reject invalid negative or
fractional injury counts for review rather than silently repairing them.

Deduplicate incident IDs, retaining fatal precedence; exclude incidents with
conflicting coordinates or years. Events involving both pedestrian and bicycle
modes count once overall, and appear in both mode totals with overlap reported.
Validated geometry uses NAD83 / UTM 13N (EPSG:26913) internally; interactive
points are converted to WGS84. Publish per-year counts beside the combined map.

### Reproduce
From the repository root, with dependencies installed and internet access:

```sh
python3 maps/day01-points/download_data.py --start-year 2021 --end-year 2025 --details
python3 maps/day01-points/main.py --start-year 2021 --end-year 2025
python3 scripts/preview_map.py
python3 -m unittest discover -s tests -v
```

Use `--refresh` to explicitly replace caches. Single-year runs still support
`--year 2025`. The range renderer requires all annual snapshots and checks each
available manifest checksum. It refuses a missing year rather than silently
rendering a shorter period. Raw source files remain outside version control.

### Story direction
Use the map to describe the recorded geography of severe walking/cycling-involved
crashes over a sustained period. Use annual counts to distinguish accumulated
locations from changes over time. Choose the headline only after reviewing the
corrected source, QA exclusions, and actual pattern.

### Limitations
- Severity is crash-level. Involvement flags do not identify who was injured.
- Counts are events, not people or exposure-adjusted risk. Repeated points overlap.
- Police reporting, missing records, and source revisions affect coverage.
- Offense labels and numeric counts can disagree; positive fatal evidence takes
  precedence. Neither field is a substitute for person-level injury records.
- The five-year map combines different dates; it cannot alone demonstrate a trend.
  Annual comparisons also require consistent reporting and coverage.
- Source metadata declares UTC date fields. Predicates use service timestamp
  semantics; local-calendar boundary effects warrant care.
- The city announced a Q4 2026 migration. Schema checks detect missing fields but
  cannot guarantee source completeness.
- The basemap shows current OpenStreetMap context, not historical street layouts
  for each crash year. The HTML loads JavaScript and tiles online; hosting is not
  configured.

### Tools and AI assistance
Python · requests · pandas · GeoPandas · pydeck / deck.gl.
Codex researched metadata, implemented downloads/QA/rendering, and ran offline
checks. The user downloaded the initial source and coverage audit. The corrected
five-year data has been validated and rendered; geographic context, narrative,
and completeness review remain before publication.

Day 01 of #30DayMapChallenge 2026.

### Richer details

The source schema includes address/intersection, neighborhood, road context and
conditions, lighting, vehicle types and movements, reported driver actions and
contributing-factor descriptions, and fatality/serious-injury mode descriptions.
The occurrence timestamp is already in the core cache and is converted from
source UTC to `America/Denver` for display, labeled MST or MDT as appropriate; it is the crash occurrence timestamp, not an independently verified time of
injury. Optional source context requires the `--details` download above.

The downloader enriches existing core caches when requested, checks optional
fields against the source schema, and records unavailable fields in the manifest.
The renderer retains distinct descriptions across duplicate offense rows and
reports per-field usable coverage in `map.qa.json`.

Tooltips distinguish **Not in snapshot** (a field has not been downloaded) from
**Not reported** (a downloaded field is blank). Source text such as “UNDER
INVESTIGATION” is retained. Vehicle-unit descriptions remain source descriptions;
they do not establish responsibility or which person was harmed.

### Browser map and screenshots

OpenStreetMap standard raster tiles provide streets and place names beneath the
deck.gl point layer. Muted colors keep the data prominent, and attribution remains
visible. No API key is needed. Tiles load in the browser; the Python renderer no
longer downloads tiles or produces a PNG. Take a screenshot after the map has
finished loading, retaining the title, legend, and source attribution.

Run `python3 scripts/preview_map.py` from the repository root. It opens
`http://127.0.0.1:8000/map.html`; keep that terminal running while viewing it.
Opening the HTML directly via `file://` can omit the required browser referrer and
lead to an OSM blocked-access tile. Normal local HTTP preview resolved the user's
reported block.

- [OpenStreetMap copyright and attribution](https://www.openstreetmap.org/copyright)
- [Standard tile usage policy](https://operations.osmfoundation.org/policies/tiles/)
- [Hosting plan](../../docs/HOSTING.md)

### Current tooltip presentation

Tooltips show only occurrence date/time (Denver time, MST/MDT), pedestrian/bicycle
involvement, and severity. Other reported context is retained in the analysis
when downloaded, but is not shown on hover. Marker radii are 4.5 pixels for
serious injury and 7.5 pixels for fatal crashes, with a 0.65-pixel light outline.
The basemap uses 60% opacity, mostly desaturated colors, and slightly reduced contrast.

### Mode filter and screenshot layout

The compact centered title card includes an All modes / Pedestrians / Bicycles
selector. Filtering uses the validated involvement flags, includes events flagged
for both in either applicable view, and does not duplicate them. The selector identifies the selected mode; the subtitle retains the shared
fatal/serious-injury scope and date range. Severity colors and sizes remain unchanged
between modes. Fatal points are ordered after serious-injury points so they are
not hidden beneath them at the same location.

The footer names Denver Open Data, the actual downloaded provider, and states
that only fatal and serious-injury events are shown. CDOT is not listed because
no CDOT dataset is used in this map. OSM attribution remains visible separately.

The JavaScript controller and exported marker hierarchy can be checked with
`node tests/test_map_controls.js` in addition to the Python validation suite.

Tooltip conversion handles daylight saving and date rollover. Source timestamps
and the existing source-year query/annual grouping remain unchanged.
