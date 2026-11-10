# Day 03 — Polygons

## Dhaka in 45 Minutes

**How far can you travel from Farmgate?** · Dhaka, Bangladesh

[Interactive map](index.html) · [Static HTML poster](poster.html) ·
[Cumulative polygons](farmgate_accessibility.geojson) · [Stations](dhaka_mrt6_stations.csv) ·
[Calculated results](map.results.md)

The coral metro corridor stretches three teal travel-time zones north and south.
Farmgate is the origin; five additional geographic labels provide orientation.
The single slate geofence is **DNCC + DSCC**, not Dhaka District.

### Data and sources

- **Operating service:** 16 stations, Uttara North–Motijheel. Kamalapur remains
  excluded, following the [project director's 17 October 2026 update](https://www.bssnews.net/news/435899).
- **Stations and rail geometry:** OpenStreetMap snapshot **1 November 2026,
  21:21:36 UTC**, downloaded from [Geofabrik](https://download.geofabrik.de/asia/bangladesh.html)
  on 2 November. Passenger route [15060935](https://www.openstreetmap.org/relation/15060935)
  verifies the station order and supplies operating track geometry.
  [citylines.co](https://www.citylines.co/api/dhaka/raw_source/stations) provides
  a coordinate cross-check; it is not used as the operating-status authority.
- **Farmgate:** [station-building centroid](https://www.openstreetmap.org/way/1125768748),
  **23.759043 N, 90.387088 E**; 75 m from the independent station reference.
  All station-coordinate cross-check distances are below 135 m.
- **Walking network and place labels:** the same OSM snapshot. 31,754 candidate
  walking ways were extracted; routing uses the largest connected pedestrian
  component, with 167,646 nodes. Labels are sourced OSM place nodes, not invented
  neighborhood centers. Water context comes from mapped closed water ways.
- **City geometry:** [Bangladesh COD-AB v03](https://data.humdata.org/dataset/cod-ab-bgd),
  sourced from **Bangladesh Bureau of Statistics**, published by **OCHA/HDX**.
  Select `BD30262500` (DNCC) and `BD30262000` (DSCC), then dissolve their shared
  boundary. Source valid-on date: **21 May 2023**; dataset reviewed **1 June 2025**;
  resource last modified January 2026. It is an administrative extent, not a
  built-up-area or metropolitan-region boundary. The older WHO-hosted ward
  service was investigated but not selected.

OSM-derived data: **ODbL 1.0**, © OpenStreetMap contributors. City boundaries:
**CC BY 3.0 IGO**, BBS / OCHA-HDX. Source URLs, dates and checksums are retained in
[source-manifest.json](source-manifest.json) and [boundary-source.json](boundary-source.json).
Raw PBF/XML/GraphML downloads are ignored by Git and excluded from Pages.

### Travel-time model

1. Use Farmgate as rail time zero. Allocate **31 minutes of running time** among
   the 15 mapped track legs in proportion to their lengths. Add an assumed
   **30-second dwell at each intermediate station**: 31 + 14 × 0.5 = 38 minutes
   end to end. The [published approximately 38-minute all-stations journey](https://online.thedailystar.net/news/bangladesh/transport/news/metro-now-connects-uttara-motijheel-3460821)
   is a calibration reference, not a verified 2026 timetable. Intermediate-leg
   values are estimates; acceleration/deceleration is not modeled separately.
2. Subtract the estimated rail time, **2-minute station-exit allowance** and
   station-to-network connector time from each 15/30/45-minute budget. Walking
   speed is **4.8 km/h**. Only one station has an eligible mapped entrance;
   others use station-center access approximations. Maximum network snap: 76 m.
3. Run shortest-time pedestrian routing from all eligible station seeds and take
   the minimum arrival time. No initial train wait, ticketing/security queue or
   transfer is modeled. Walking alone from Farmgate is included through its seed.
4. Retain partially reachable edge segments, not just whole edges or nodes.
   Buffer reachable links by **60 m**, dissolve, subtract mapped water, and remove
   disconnected components below **2,500 m²**. This is a generalized street
   catchment envelope, not a claim that every enclosed property is accessible.
5. Validate geometries and assert **15 ⊂ 30 ⊂ 45**. Distances, intersections and
   areas use **WGS 84 / UTM 46N (EPSG:32646)**; exports use EPSG:4326.

### Exactly what the clock includes

Time zero is **at Farmgate station**, not a home or another street origin.
- **Included:** estimated in-train running time; 30-second intermediate dwells;
  2-minute station exit; station/entrance-to-pedestrian-network connector walking;
  destination street-network walking at 4.8 km/h.
- **Walk-only option:** exiting Farmgate and walking from its street connector is
  included without taking a train.
- **Excluded:** travel to Farmgate, walking into/through its entry gates,
  ticketing/security, initial train waiting, departure dwell at Farmgate, arrival
  dwell at the exit station, transfers and reboarding. There is no other mode.

This is a modeled station-origin catchment, **not door-to-door journey time**.
The polish pass changes no routing assumptions or cumulative geometry.

### City percentage and display generalization

Original municipal union: **304.5095 km²**. Original 45-minute catchment intersected
with that union: **68.8236 km²**. Ratio: **22.6015%**, displayed as **~23%**.
The denominator includes the full mapped municipal area, including water and
restricted land. This is neither population coverage nor observed travel.
Published municipal summary areas can differ from this boundary dataset.

The city **display geofence** is simplified by 80 m, densified to maximum 100 m
segments, then gently rounded once with Chaikin smoothing. It is a single outline
with no DNCC/DSCC internal border. Statistics use the **original unsmoothed union**.

For visual simplicity, cumulative display polygons fill interior holes below
**50,000 m²** and preserve major mapped water bodies ≥25,000 m² and larger access
gaps. Display edges are simplified by 10 m. They are then differenced into
**exclusive 0–15 / 15–30 / 30–45 minute bands**, with opaque colors matching the
legend. None of these display operations changes routing, cumulative exports or
the percentage. Tooltips explicitly distinguish display bands from cumulative
model statistics.

### Limitations

OSM may omit paths, crossings, entrances and access restrictions. Private/no-foot
ways and explicitly restricted barrier nodes are excluded; remaining walking links
are assumed bidirectional. Untagged restrictions, unsafe crossings and detailed
stairs/lift costs cannot be verified. There is no congestion, queue, initial-wait,
disruption, timetable or field validation model. The 60 m envelope may bridge
small unmapped barriers; filled display holes add further visual generalization.
The city outline is administrative context, not proof of a physical urban edge.

### Reproduce

```sh
python3 -m pip install -r requirements.txt
python3 maps/day03-polygons/download_data.py
python3 maps/day03-polygons/extract_osm.py data/raw/day03-polygons/bangladesh-20261102.osm.pbf
python3 maps/day03-polygons/main.py
python3 scripts/preview_map.py --directory maps/day03-polygons --port 8003
```

A cached source snapshot is required for identical routing results; the downloader
checks its SHA-256 and never silently accepts a changed extract. To rerender only
the styling/context, run `prepare_context.py`, then `render.py`; this preserves all
travel-time calculations. The source municipal subset and label points are saved
with their attribution so that rerendering does not require new network access.
The map page retains source credits; explanatory notes, method/data/poster links
and the expandable methodology are omitted from the visual. Full methods remain
here. No PNG export or external basemap is required. Publication route: `/day03-polygons/`; static view: `/day03-polygons/poster.html`.
