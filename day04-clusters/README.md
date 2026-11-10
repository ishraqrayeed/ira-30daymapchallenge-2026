# Day 04 — Clusters

## Halal in Manhattan

**Where does halal food cluster across Manhattan?**

[Interactive map](index.html) · [Analysis POC](poc.html) · [Results](map.results.md) ·
[Locations](manhattan_halal_locations.csv) · [Audit](day04_audit.json)

**121 identifiable halal food locations compiled from public sources.** Not a
census. DBSCAN identifies **14 clusters: 92 locations (76.03%)**; 29 remain
unclustered. The largest spans the East Village / Lower East Side (25). The
poster shows every location and all 14 cluster outlines. Aggregate statistics
are documented here and omitted from the map page.
The interactive page contains the map, title, editorial line, legend and source credits only; methods, audit
and downloads remain in the repository documentation.

### Sources / terms / inclusion

Include food businesses with explicit OSM `diet:halal=yes/only` or a business name
explicitly containing “halal” in OSM / NYC records. Cuisine never qualifies a
location. A source indication is a public claim, not independent certification.
The scope includes restaurants, takeout, mapped carts, groceries and halal meat
shops. Do not describe the total as a restaurant count.

- **OpenStreetMap via Geofabrik:** [fixed New York extract](https://download.geofabrik.de/north-america/us/new-york-261101.osm.pbf),
  source snapshot **1 November 2026, 21:21:36 UTC**, retrieved 2 November.
  Nodes and ways with explicit evidence are extracted; an unhandled halal relation
  blocks extraction instead of being silently omitted. 108 final locations have
  OSM provenance. © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright),
  [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
- **NYC DOHMH restaurant inspections:** [43nn-pn8j](https://data.cityofnewyork.us/Health/DOHMH-New-York-City-Restaurant-Inspection-Results/43nn-pn8j),
  registered names containing HALAL, all boroughs, retrieved 2 November 2026.
  1,789 inspection observations collapse to 166 business IDs. NYC record dates
  are 30 October 2026; non-sentinel inspections span 10 August 2017–28 October 2026. 24 final locations
  have NYC provenance; 11 also have OSM provenance. Records are not proof of
  current operation. `1900-01-01` is a missing-inspection sentinel.
- **NYC DCP shoreline borough boundary:** [gthc-hcne](https://data.cityofnewyork.us/City-Government/Borough-Boundaries/gthc-hcne).
  Use the actual full Manhattan polygon, including smaller islands and Marble
  Hill. “Manhattan” means borough, not strictly the main island.
- **NYC DCP 2020 neighborhood tabulation areas:** [9nt8-h7nd](https://data.cityofnewyork.us/City-Government/2020-Neighborhood-Tabulation-Areas-NTAs-/9nt8-h7nd),
  point-in-polygon reference for interpretation. These statistical areas do not
  definitively represent neighborhood identities. Both boundaries retrieved 2 November.

NYC sources: [NYC Open Data terms](https://cityofnewyork.github.io/opendatatsm/publicpolicies.html).
Combined derivative downloads are offered under ODbL; retain OSM and NYC credits.
[Source manifest](source-manifest.json) records URLs, retrieval times, bytes and
SHA-256. Original source caches remain ignored and are excluded from Pages.

**Investigated, not incorporated:** [eatHalal](https://eathalal.com/restaurants/new-york/manhattan)
([API coming soon](https://eathalal.com/api-access), reuse terms not established);
[Zabihah](https://www.zabihah.com/terms) (automated collection restricted);
[HalalHive](https://www.halalhive.app/faq) (community coverage, open reuse permission
not established); [NYS halal registry](https://apps.agriculture.ny.gov/FS/halal-establishment-registrations.html)
(public declarations with addresses, no native coordinates; requires a separate
matching/geocoding review). Registration itself is not certification. No Google
Maps or Yelp scraping. Failed Overpass queries were replaced with the open PBF.
Business websites were used to check identities, not to add unsourced locations.

### Cleaning / audit

**2,011 raw rows → 388 candidate establishments** after removing **1,623 repeated
inspection observations**. Exclude **255**: 242 outside Manhattan, 5 unusable
coordinates, 5 non-food features, 2 inactive OSM records, 1 potentially closed.
Merge **12 duplicate records → 121 locations**. Collection-region counts are
broader than Manhattan. This is not a loss of 255 Manhattan halal businesses.

Use original coordinates: OSM nodes / way representative points and DOHMH points.
**No geocoding**. Normalize names and addresses, retaining originals and per-source
provenance. Generic matching requires ≤60 m plus the same normalized name, or
matching normalized address and name similarity ≥0.88. Four reviewed identity
merges are in [record-review.json](record-review.json), including a phone-confirmed
B&B / BB Halal duplicate. Distinct nearby businesses and separately mapped Hooda
trucks remain separate. The audit retains close pairs and identity decisions;
source staleness and co-location ambiguity cannot be ruled out.

### Spatial analysis

Actual point-in-polygon filtering, then **WGS 84 / UTM zone 18N (EPSG:32618)**.
DBSCAN uses Euclidean metres: **epsilon 450 m, min_samples 3**, including the point
itself. A core location needs at least two other locations within that radius.
Chained core neighborhoods form clusters; border points may join. Distance is
straight-line, not walking distance, and a cluster may span more than 450 m.
Membership is calculated, never hand-assigned.

The [20-model sweep](dbscan_parameter_sweep.csv) tests 250–700 m and minimum 3–6.
The user selected minimum 3 to include smaller concentrations. At the same 450 m
radius, this yields **14 clusters / 92 members / 29 noise**, compared with
6 / 59 / 62 at minimum 5. This intentionally admits trios and small chains;
it is not a claim that every three-place group is a major food district.
The geographic labels were reviewed again after recomputing membership.

| Post-analysis cluster interpretation | Locations |
| --- | ---: |
| East Village / Lower East Side | 25 |
| Midtown West / Chelsea | 11 |
| Kips Bay / Gramercy | 10 |
| Greenwich Village | 7 |
| Lenox Hill / Sutton Place | 6 |
| Midtown East | 5 |
| Upper East Side / First Avenue | 4 |
| East Harlem South | 4 |
| Harlem South | 4 |
| Morningside Heights / Broadway | 4 |
| Civic Center / Chinatown | 3 |
| Turtle Bay / Murray Hill | 3 |
| Sixth Avenue / Midtown | 3 |
| Yorkville / Carnegie Hill | 3 |

The largest group includes East Village 17, Lower East Side 5, Gramercy 2 and
SoHo–Little Italy–Hudson Square 1. Midtown West / Chelsea spans several reference
areas. Labels describe concentrations, not exact neighborhood boundaries. The
five largest groups are labeled; all 14 have inspectable outlines.

Use **concave hull ratio 0.35**, buffer 140 m, intersect union of member-point
225 m buffers and Manhattan. This keeps outlines clear of point symbols while
limiting empty-space bridges. Exports are unsimplified and cover all members.
These secondary display envelopes are not statistical boundaries or service areas.

**Sensitivity:** HDBSCAN (sklearn; minimum cluster size 3, minimum samples 3, EOM)
returns **19 clusters, 105 members, 16 noise**. Retain DBSCAN's explicit shared spatial
scale. OSM-only gives 14 clusters / 108 locations; explicit halal tags only gives
12 / 101 (largest 24); food-service-only gives 11 / 110 (largest 18).
[Analysis details](analysis.json) include membership Jaccard comparisons, source
sensitivity, HDBSCAN and hull areas. Smaller groups depend strongly on coverage
and model settings.

### Limitations

Not a census. Public mapping and explicit-name selection are spatially biased;
carts and businesses without HALAL in their names are easy to miss. Businesses
open, close, move and change halal status. Current operation and certification
have not been independently verified. Coordinates may be approximate. Do not
rank neighborhoods, infer food availability from gray points, or claim statistical
significance: no random-baseline/significance test is established.

### Reproduce / preview

Install repository requirements. Recompute from the redistributable processed
snapshot without network access:

```sh
python3 maps/day04-clusters/main.py
python3 scripts/preview_map.py --directory maps/day04-clusters --port 8004
```

To rebuild cleaning from source caches, first run `collect_data.py`, then
`main.py --clean`. Source checksum changes require review. Scripts separate
collection, cleaning, parameter exploration (`cluster.py`), interpretation and
geometry (`analyze.py`), rendering and QA. No PNG export or conventional basemap.

QA recomputes projected DBSCAN, checks evidence and Manhattan containment for
every point, verifies memberships/envelopes/counts and checks public artifact
consistency. The Pages packager validates artifact checksums and preserves Days 1–3.
Publication route: `/day04-clusters/`.
