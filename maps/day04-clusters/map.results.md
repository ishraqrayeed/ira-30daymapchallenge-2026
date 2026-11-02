# Halal in Manhattan — results

[Interactive map](map.html) · [Full methodology](README.md)

### Data

1. Investigated OSM, NYC DOHMH, NYC DCP, eatHalal, Zabihah, HalalHive and the NYS halal registry. No Google Maps or Yelp scraping.
2. Used OSM/Geofabrik and NYC DOHMH for locations; NYC DCP for Manhattan boundary and neighborhood reference. Business websites assisted identity review only. Explicit halal tag or name required; cuisine never qualifies.
3. **2,011 raw rows:** 222 OSM bounding-box candidates + 1,789 citywide inspection observations.
4. Collapse **1,623 repeated inspection observations**; merge **12 duplicate establishment records** (including four reviewed identity merges).
5. **255 exclusions:** outside Manhattan 242; unusable coordinates 5; non-food 5; inactive 2; potentially closed 1. Broader collection region, not 255 excluded Manhattan businesses.
6. **121 final unique locations.** OSM provenance 108, NYC provenance 24, overlapping 11. Original coordinates; no geocoding. Per-record evidence, source URLs, retrieval dates, normalized names/addresses and provenance retained. Combined derivative downloads: ODbL with OSM/NYC attribution.

### Clustering

7. **EPSG:32618 — WGS 84 / UTM zone 18N; Euclidean metres.** Actual Manhattan point-in-polygon filtering.
8. DBSCAN **epsilon 450 m**.
9. **min_samples 3**, including the point itself: at least two others within 450 m for a core point. Chained groups can span more than epsilon.
10. **14 clusters**, after the user selected a three-location minimum from the 20-model sweep. The previous minimum 5 gave 6 clusters.
11. **92 clustered locations**.
12. **29 noise locations**, all visible.
13. **76.03% clustered**, displayed as **76%**.
14–15. Names assigned after recalculating and inspecting memberships:

| Cluster interpretation | Locations |
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

The five largest clusters receive labels; all fourteen have outlines and popups.
The leading group includes East Village 17, Lower East Side 5, Gramercy 2 and
SoHo–Little Italy–Hudson Square 1. These are descriptive corridor/neighborhood
labels, not administrative borders. Smaller groups now include trios.

16. **HDBSCAN tested:** minimum cluster size 3, minimum samples 3, EOM:
**19 clusters / 105 members / 16 noise**. DBSCAN is retained for its common spatial
scale. OSM-only gives 14 clusters / 108 locations; explicit-tag-only 12 / 101
(largest 24); food-service-only 11 / 110 (largest 18). No significance test is claimed.

### Visualization

17. **HALAL IN MANHATTAN** — *Where halal food clusters across the borough*.
18. Aggregate statistics are omitted from the map page. Calculated results remain **121 locations · 14 clusters · 76% clustered · 29 unclustered**; labels and popups retain individual cluster counts.
19. Charcoal **#141612**, warm dark land **#292A23**, amber **#F2C34D**, cream **#EEE9DA**, noise **#858A7C**. Thin, low-opacity concave envelopes; no heatmap, rainbow colors or conventional street basemap.
20. Created Day 4 collection/cleaning/clustering/sensitivity/geometry/render/QA/reproduction scripts; processed CSV/GeoJSON, parameter sweep, audit, source manifest, POC and self-contained `map.html`. Updated root README, portfolio index, workflow packager note and Pages packager. Days 1–3 map files and shared rendering components are unchanged. No PNG export. Publication route: `/day04-clusters/`. The map page is poster-only with source credits; methods, dataset descriptions, README/limitation links and downloads are removed from the page and retained here.

### Limits on claims

21. This is **not a complete census**. Public-source coverage and naming practices
are spatially biased. Businesses open, close, move or change halal status. Carts
are especially easy to omit or mislocate. Source records are not independent
halal certification or current-operation checks. Nearby identity ambiguities and
source staleness cannot be ruled out after deduplication.
22. Do **not** rank neighborhoods, measure total halal availability, equate noise
with absence, or claim statistically significant clusters of all halal food.
These are descriptive concentrations in this compiled sample, conditional on
source coverage and DBSCAN parameters. HDBSCAN/source sensitivity supports the
leading concentration but does not establish an unbiased citywide distribution.
