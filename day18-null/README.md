# Day 18 — NULL · The Great American Nothing

*How boring is the drive from St. Louis to Denver?* A 28-second,
north-up animated poster follows the mapped I-70 westbound alignment. The
dot reveals land-cover patches along the route while the camera stays fixed.

## Driving Monotony Index

The index scores consecutive eight-mile pieces from 0 to 100. The final piece
ends at the Denver endpoint. Components use fixed physical or categorical
scales and the following weights.

| Component | Weight | Calculation |
| --- | ---: | --- |
| Straightness | 15% | Endpoint distance divided by path length, scaled from 0 at 0.82 to 100 at 1.00 |
| Flatness | 30% | Inverse of the 75th-percentile percent slope within seven miles, scaled from 100 at 0% to 0 at 6% |
| Landscape repetition | 40% | Percentage of corridor pixels in the most common NLCD class |
| Low scenic variation | 15% | Percentage of consecutive 500 m centerline observations with the same prevailing class within a 1.5 km neighborhood |

A high stretch scores at least 80 throughout and spans at least 15 miles.
The longest spans **80.0 miles**, from near Oakley, Kansas, to 5.2 route miles
east of Burlington, Colorado (journey miles 600–680). This headline uses its own threshold. See the
[before-and-after diagnostic report](DIAGNOSTICS.md) for the distribution,
threshold tradeoffs and sensitivity to scenic smoothing.

The display uses three exclusive bands and requires ten contiguous miles
within a band. Scoring still uses eight-mile sections and the original
1.5 km scenic neighborhood. The browser fades in each qualifying region
when the travel dot reaches its first section.

| Display band | Score | Share classified | Stretches shown | Miles shown |
| --- | ---: | ---: | ---: | ---: |
| Moderate | 55–<70 | 41.56% | 10 | 304.8 |
| High | 70–<85 | 36.76% | 7 | 264.0 |
| Extreme | 85–100 | 5.66% | 1 | 24.0 |

The other 16.02% of the corridor scores below 55. In total, 18 stretches
represent **592.8 miles**, or 69.84% of the route. The longest extreme
stretch spans **24.0 miles**, from 15.2 route miles east of Goodland,
Kansas, to 8.8 route miles west of it. The longest run within the high
display band is 80 miles (journey miles 528–608). The separate headline uses
at least 80 throughout and includes any extreme sections within that run.

The polygons show connected areas of predominant NLCD cover, generalized
with a 4.5 km neighborhood. Each raster cell can belong only to the region
containing its nearest sampled route station, within 20 miles of I-70.
The script keeps connected patches of at least 12 km² with at least 4 km²
inside the qualifying run’s seven-mile sampling corridor, then dissolves
and simplifies with an 850 m topology-preserving tolerance. Details below 3 km²
for fragments and 1.5 km² for interior holes are omitted. Geometry operations use CONUS Albers
(EPSG:5070). Both source rasters are sampled on a 500 m grid.
[USGS 2021 NLCD](https://www.mrlc.gov/data/nlcd-2021-land-cover-conus) ·
[USGS 3DEP elevation service](https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer)

## Corridor checks and fuel analysis

The 848.77-mile route passes 152 qualifying westbound fuel access points. The
longest interval is **34.64 miles**, from the 24/7 Travel access near Colby to
an unnamed mapped fuel station near Goodland, Kansas. The two stations
qualify with modeled one-way access legs of 0.38–0.40 miles.

`python day18-null/validate.py` checks the browser measurements and compares
the route’s state sections against independent mileage references. Kansas
measures 423.78 miles versus 424.15 in the federal route log. The measured
Missouri and Colorado sections are 249.65 and 175.34 miles. The reference
sections are 251.66 and 175.59 miles and use slightly different endpoints.
[FHWA route log](https://ops-dr.fhwa.dot.gov/freight/freight_analysis/perform_meas/fpmtraveltime/traveltimebrochure.pdf) ·
[CDOT eastern milepoint](https://www.codot.gov/projects/archives/i-70-crack-seal-kansas-flagler) ·
[CDOT Denver milepoint](https://www.codot.gov/travel/i70mountain/i70denver)

## Run

From the repository root:

```sh
python3 scripts/preview_map.py --directory day18-null
```

Playback starts automatically unless reduced motion is enabled. Drag the distance slider to inspect a point or choose **Explore map** to pan, zoom, and inspect revealed polygons and fuel markers. All browser assets are local to this folder. The Pages packager
copies `map.html` as the Day 18 landing page.

To rebuild the data:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r day18-null/requirements.txt
python day18-null/prepare.py --fetch
python day18-null/monotony.py
python day18-null/validate.py
```

The script caches state PBF files and Census responses in ignored
`data/raw/day18/`. Geofabrik’s latest extracts change. The input replication
timestamps and SHA-256 checksums are in [asset QA](assets/qa.json).

## Sources and method

- **Route, roads, buildings, and fuel** — OpenStreetMap via the [Geofabrik US state extracts](https://download.geofabrik.de/north-america/us.html). A directed graph connects adjacent OSM nodes on ways referenced as I-70. The route uses WGS84 ellipsoidal segment distances and begins near the Missouri side of the Stan Musial Veterans Memorial Bridge. It ends on Central 70 in Denver at 39.77992° N, 104.98693° W. Columbia includes the unreferenced but connected [OSM motorway way 1524427900](https://www.openstreetmap.org/way/1524427900).
- **Topeka** — The visualization follows the pre-closure I-70 alignment through the Polk–Quincy reconstruction, using the [archived OSM trace](source/topeka-preclosure.json) from May 31, 2026. Its shared end nodes join the newer extract, and fuel access calculations exclude ramp attachment to the archival section. KDOT designated I-470 as the through-traffic detour during construction. [KDOT closure notice](https://www.ksdot.gov/Home/Components/News/News/6289/385?widgetId=3472)
- **Fuel access** — Candidate OSM `amenity=fuel` points and closed ways within 4.75 km of the route are snapped to the nearest eligible street segment within 90 m. The connector length counts toward both directions of travel. NetworkX follows directed edges from a westbound off-ramp to the station and back to a downstream westbound on-ramp. Each leg must be at most two miles, and the merge must be less than four mainline miles beyond the exit. Routes respect mapped direction and basic vehicle/access tags, and exclude motorway travel between ramps. Each fuel feature contributes its lowest-cost qualifying exit/merge pair. If several features select one exit, the lowest-cost one represents that exit. Gaps use the distance between consecutive exit attachment nodes, excluding the partial intervals at the start and end.
- **Population** — [2020 TIGERweb Census tracts](https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/Tracts_Blocks/MapServer/0) supply `POP100`, land area, and water area. An 8 km circle sampled every 4 km along the route uses area-weighted gross tract density in CONUS Albers (EPSG:5070). This assumes uniform density within a tract. The map’s cyan lighting uses a 3.3 km grid sampled from the same tract densities. State outlines use the repository’s processed [2024 Census cartographic boundaries](https://www2.census.gov/geo/tiger/GENZ2024/shp/).
- **Rendering** — MapLibre draws the fixed north-up map and interpolates the travel dot along the mapped I-70 alignment.

Fuel coverage varies with mapping completeness and driveway geometry. The
graph does not apply turn restrictions, conditional access, opening hours, or
live closures. The result describes the longest gap under the stated model
between **qualifying mapped services**. Low Census density reflects a sparse
settlement pattern rather than an absence of people.

OpenStreetMap data © OpenStreetMap contributors, [ODbL](https://www.openstreetmap.org/copyright).
Census geography and counts are public-domain federal data.

## Atlas callouts

The timed notes pair route measurements with geographic landmarks. The
Rocheport marker uses the published Katy Trail trailhead coordinates. The
Kansas City marker locates River Market near the downtown I-70 curve. The
three monotony callouts use averages of the component scores across the
corresponding display stretch. NLCD cover classes describe grassland and
cultivated crops at this scale. Crop species and livestock are outside
the dataset.
[Missouri State Parks](https://mostateparks.com/key-location/rocheport-trailhead) ·
[Visit KC River Market map](https://www.visitkc.com/uploads/2025/12/RiverMarketMap.pdf)
