# Day 6 — Vintage · TELLURIDE

*Echoes of a Mining Town*

An original PyQGIS poster of the Town's structure polygons, contemporary OSM
streets, and terrain contours derived from USGS elevation data. **Every visible
map layer is vector.** No archival image, georeferenced historical scan, screenshot
or modern basemap tile is used underneath the features.

- [LinkedIn-ready poster, 1080 × 1350](exports/day06_telluride_linkedin.png)
- [2400 × 3000 master, 300 dpi](exports/day06_telluride.png)
- [Editable QGIS project](qgis/day06_telluride.qgz)
- GeoPackage: `data/processed/telluride_inventory.gpkg`
- [Interactive vector atlas](map.html)
- [Complete field audit](data-audit.json), [survey review](survey-review.json),
  [source manifest](source-manifest.json), [validation](validation.json)

## What the data supports

The source contains **1,131 polygon records**, not a verified count of distinct
historical buildings. All 17 source fields, original geometries and OBJECTIDs are
preserved. Some BLDG_ID values repeat; no records were silently deduplicated.

| Source rating | Records |
| --- | ---: |
| Contributing | 158 |
| Supporting | 120 |
| Local Landmark | 19 |
| Significant Landmark Interior | 2 |
| Noncontributing with qualifications | 31 |
| Noncontributing without qualifications | 71 |
| No rating | 730 |

**299 records have contributing, supporting or landmark ratings.** Six of these
carry a legacy `old structures map` status. The poster highlights the remaining
**293 records** in brick red. Other/unrated records are pale ink; all 25 records
marked `demolished` or `old structures map` use dashed, unfilled outlines.
The enlarged downtown detail shows 919 inventory records, including 292 red
footprints. The town-wide statistic remains 293; the full-town inset contains all
1,131 records and all 293 red footprints. Its red locator box marks the main map extent.

**The pre-1900 count is unknown, not zero.** The GIS has no construction-date field.
Its comment, reviewdate, description and other free-text fields contain no usable
dating information. Source ratings are preservation classifications, not years.
Every record therefore has `date_class = undated` and a null construction year.
The separate `verified_pre1900` layer is empty because no verified date join was
applied; `undated_structures` retains the entire inventory.

The Town's published architectural survey was consulted. Its individual forms
contain construction estimates: the form for **103 W. Colorado Avenue**, resource
5SM.1541, gives an estimated 1886 date (page 3) and discusses subsequent alterations.
However, its parcel number `477901119003` is absent from the GIS PIN values. The
survey log uses site numbers and primary/secondary resources; the GIS does not
provide those site IDs or addresses. A reliable complete building-level crosswalk
is not available in these inputs. No date was copied by proximity, district period,
shared parcel, or a guessed interpretation of BLDG_ID. A full survey crosswalk
would require additional record-by-record verification. This version uses the
requested inventory fallback rather than an unsupported age filter.

## Sources and terms

**Town of Telluride — Historic Structure FeatureServer**

- [Service](https://services.arcgis.com/aXqye4IXyXsdIpPb/ArcGIS/rest/services/Telluride_Historic_Structure/FeatureServer)
- [Discovered polygon layer 23](https://services.arcgis.com/aXqye4IXyXsdIpPb/ArcGIS/rest/services/Telluride_Historic_Structure/FeatureServer/23)
- [ArcGIS item metadata](https://www.arcgis.com/sharing/rest/content/items/e4e2fc4a8a524be3aaa367486f90836a?f=pjson)
- [2013 survey index](https://www.telluride.gov/391/2013-Telluride-Historic-Architectural-Su)
- [2013 survey log](https://www.telluride.gov/DocumentCenter/View/2456/2013-Survey-Log-PDF)
- [103 W. Colorado survey form](https://www.telluride.gov/DocumentCenter/View/2117/ColoradoAvenue103W-REVISED?bidId=)

The service is publicly queryable. Its copyright text and the ArcGIS item's
`licenseInfo` and `accessInformation` are blank: **no explicit open reuse license
was supplied**, and this project does not relabel the Town's data as public domain.
Credit is retained; the original metadata is cached. The survey is a 2013 published
resource; the live GIS is a separate inventory snapshot acquired November 5, 2026.
The GIS does not establish the observation or construction date of each geometry.
Survey PDFs are documentation only and are never loaded into the map.

**OpenStreetMap, processed with OSMnx 1.9.1**

[Official OSM API extract](https://api.openstreetmap.org/api/0.6/map?bbox=-107.845,37.923,-107.794,37.953),
© OpenStreetMap contributors, [ODbL](https://www.openstreetmap.org/copyright).
The earlier draft's Overpass request stalled. The reproducible alternative downloads
original XML from the official OSM API, builds and simplifies it with OSMnx
`graph_from_xml`, selects road highway classes, and removes duplicate bidirectional
edge geometries. The result contains 430 edges. Raw XML preserves original tags;
compound edge tags are semicolon-separated for reliable GeoPackage storage.
These are contemporary roads, not reconstructed historic streets.

**USGS 3DEP**

[Elevation ImageServer](https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer),
[USGS data-use policy](https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits).
USGS-produced data are generally public domain; attribution is retained. The
pipeline requests single-band Float32 bare-earth elevation with raster function
`None`, not a rendered map. The raw export spans approximately 2,638–4,142 m;
50 m contours are generated by GDAL. Service metadata and the exact export URL
are cached. This is a contemporary elevation mosaic, not historical terrain, and
no uniform observation date is claimed.

All download URLs, byte counts and SHA-256 hashes are recorded in the manifest.
Raw and processed caches are ignored by Git. No credentials are needed.

## Processing and design

ArcGIS object IDs are discovered and retrieved in batches of 200, with completeness
and uniqueness assertions. The source CRS is Web Mercator; the server returns
geometries in **EPSG:26913**, NAD83 / UTM zone 13N. OSM geometry is transformed from
EPSG:4326; the USGS raster is requested and checked in EPSG:26913. Source x/y and
area/length attributes are preserved verbatim and are not used instead of geometry.
No footprints were invented or manually traced.

The GeoPackage contains `inventory_source`, `inventory_classified`,
`undated_structures`, `verified_pre1900`, `streets`, and `terrain_contours`.
The original layer preserves source polygons; classification and provenance are
added in a separate layer. No geometry repairs were required. A derived hillshade
is available as an initially hidden QGIS layer; the print uses contours only.

The composition uses ivory #F4F0E6, Baskerville typography, charcoal streets,
light sepia contours, and muted brick red. The map is north-up. The wider canyon
context is contemporary; the historic component is the source inventory's ratings.
The separate earlier Sanborn project under `day06-telluride-vintage/` is preserved
but is not an input, background or fallback for this poster.

## Refined poster

The existing QGIS layout and layers were edited in place. The downtown map is
now 1,250 m wide, about 1.87 times the preceding refinement’s scale, preserving
the diagonal valley and some contour context. A small full-town inset links to
the downtown extent. Contours remain
50 m apart, with stronger 250 m index contours. Brick-red fills and outlines are
slightly richer; no source geometry is enlarged or changed. Three small graphic
swatches replace the text-only legend, and source credits use larger centered type.

The statistic, **293 footprints with historic ratings · town inventory**, is
calculated directly from the full inventory class, not just the downtown crop. Those records contain 279 distinct non-null
BLDG_ID values plus 10 records with null IDs; some IDs repeat. It is a reproducible
polygon count, not a census of distinct physical buildings.

A further survey check found an actual construction period of **1891–1892** for
the First National Bank building at 201 (207) W. Colorado Avenue, resource 5SM.1537
([survey, page 4](https://www.telluride.gov/DocumentCenter/View/2131/ColoradoAvenue201W-5SM1537-REVISED?bidId=)).
Its parcel 477901106001 matches one inventory polygon (OBJECTID 831). This is useful
individual evidence, but one checked resource does not provide an inventory-wide
age classification. The preserved dataset's date fields and rating-based colors
remain unchanged. The Town describes the district's mining-era significance as
1878–1913 ([preservation overview](https://www.telluride.gov/239/Historic-Preservation));
that period is context, not an assigned construction range for each footprint.

## Sparse geographic labels and landmark key

Colorado Avenue, Oak Street, Fir Street and Pine Street are labeled from merged
named geometry in the existing OSMnx roads. The San Miguel River is drawn and
labeled from the named river ways already present in the cached OSM XML; no new
basemap or invented water geometry is used.

Three small numbered markers sit on matched inventory footprints:

1. San Miguel County Courthouse — OBJECTID 1045. Name verified on page 1 of the
   [Town survey](https://www.telluride.gov/DocumentCenter/View/2141/ColoradoAvenue305W-Courthouse-5SM1605-REVISED?bidId=).
   Its page 2 NAD27 UTM reference transforms into this single polygon; footprint
   shape and Colorado Avenue frontage agree with the survey description. The survey
   parcel does not match the GIS PIN, so this is a documented spatial match.
2. New Sheridan Hotel — OBJECTID 446. The survey's parcel 456536411007 uniquely
   matches the GIS PIN; name verified on page 1 of the
   [Town survey](https://www.telluride.gov/DocumentCenter/View/2138/ColoradoAvenue231-235W-5SM1534-REVISED?bidId=).
3. First National Bank of Telluride — OBJECTID 831. The survey's parcel 477901106001
   uniquely matches the GIS PIN; name verified on page 1 of the survey linked above.
   The neat key shortens the name to First National Bank.

[Label evidence](label-evidence.json) records the names, source URLs, page numbers,
join methods and original OBJECTIDs. The original inventory has no name field;
these are explicit survey-based label enrichments. They do not assign construction
dates. `scripts/label_context.py` regenerates a separate
`data/processed/label_context.gpkg` containing street label lines, river geometry
and on-footprint landmark points. The original inventory GeoPackage is unchanged.
The existing QGIS project keeps all these derived labels editable.

## Reproduce on this Mac

```sh
bash maps/day06-vintage/scripts/run.sh --render-only
```

The `--render-only` mode preserves all current datasets and refines the existing
QGIS project before export and validation. The launcher discovers the installed
QGIS.app bundle and runs rendering and validation using its bundled
Python. It sets QGIS, PROJ and GDAL resource paths. Tested here with QGIS 3.44.9,
bundled Python 3.12 / GDAL 3.12, and acquisition Python 3.11 / OSMnx 1.9.1.
If needed, install acquisition dependencies with
`python3 -m pip install -r maps/day06-vintage/scripts/requirements-acquisition.txt`.
For a different bundle, set `QGIS_APP='/path/to/QGIS.app'` before the command.

Render-only reruns reuse the existing project, update the same layout, and do not
rewrite the GeoPackage. The original acquisition/preparation stages remain available
by omitting `--render-only`; they were not run for this refinement. Keep the saved
QGIS project: the renderer deliberately edits it instead of creating a new project.
Move the whole `maps/day06-vintage/` directory to keep relative QGIS paths valid.
Checks compare every source attribute and geometry, feature counts, CRS and extents,
source hashes, null construction dates, valid geometries, project reopening,
vector-only print composition and exact PNG dimensions. The PNG is visually reviewed
in addition to these checks. Publication was requested; the interactive atlas is prepared for GitHub Pages.

```sh
python3 scripts/preview_map.py --directory maps/day06-vintage --port 8007 --no-browser
```

## LinkedIn export

`bash maps/day06-vintage/scripts/run.sh --linkedin-only` exports the current saved
QGIS layout directly at 1080 × 1350 pixels, preserving the 4:5 composition without
cropping or stretching. It leaves the master PNG, QGIS project and original
GeoPackage unchanged. The export is PNG and verified below 5 MB; dimensions and
checksums are recorded in `linkedin-export.qa.json`. The normal rendering pipeline
also regenerates this upload copy. Size follows
[LinkedIn's photo guidance](https://www.linkedin.com/help/linkedin/answer/a527229/share-photos-or-videos?lang=en).

## Larger type for social sharing

[3000 × 3750 poster](exports/day06_telluride_3000x3750.png) is rendered directly
from vectors with larger map labels, landmark key, legend and credits. The editable
QGIS project includes a separate “LinkedIn — larger type” layout. Reproduce with
`bash maps/day06-vintage/scripts/run.sh --highres-only`. The former 80 MP export
is retained locally but is no longer packaged for the website. The webpage omits
portfolio, image-download and methods navigation; visible source attribution remains.

## Final polish

Run `bash maps/day06-vintage/scripts/run.sh --final-polish` to update the current
editable social layout in place and export `exports/day06_telluride.png` at
2400 × 3000. This mode preserves the map extent and source inventory, uses smaller
centered mixed-case street labels with thin ivory buffers and polygon obstacles,
strengthens the existing inset border, and updates the three graphical legend captions.
It does not regenerate the older layouts or the website.

The geometry check finds 293 unique OBJECTIDs and 293 topologically distinct
footprint geometries, with no pairwise intersection area above 0.01 m². These
are inventory footprints, not necessarily 293 distinct physical buildings; building
IDs repeat. Included ratings are Contributing, Supporting, Local Landmark and
Significant Landmark Interior; demolished/legacy statuses are excluded.
All three survey matches and on-footprint marker anchors are rechecked.
See `final-polish.qa.json` for counts, methods and source links.
