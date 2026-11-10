# Day 09 — Las Vegas: The Desert That Became a City

Geographic question: how did the Las Vegas Valley’s developed footprint expand over 45 years? This interactive CesiumJS globe animates ten real GHSL estimates, 1975–2020. It does not generate video.

## Local preview

From the repository root:

```sh
python3 scripts/preview_map.py --directory maps/day09-urban-rural --port 8009 --no-browser
```

Open http://127.0.0.1:8009/map.html. Internet and WebGL are required for Cesium, detailed imagery and terrain. No account, token or paid API is required. Initial loading prepares imagery and all historical textures before controls are enabled; this can take time on a cold connection. The default opens directly over Las Vegas with a draggable 1975 / 2020 divider. Compare and Growth are separate modes. Play Growth runs the seven-second timeline through the ten existing source epochs. Switching modes, playing, replaying and resetting the timeline preserve the current camera; Reset View explicitly restores the original overview. The globe zoom is no longer part of the visible controls. Initial preparation is separate from the seven-second animation.

Choose the swipe comparison or play the timeline. Select five-year epochs manually, adjust expansion speed, toggle the footprint/new cells/terrain, pause, replay or reset. Mouse navigation pauses playback and never restarts it. Recording mode retains title, year, the dynamically computed growth multiplier, source notice and attribution. Space plays/pauses, R replays Growth, Escape exits recording. No video or screenshot export is implemented.

## Data and temporal meaning

[European Commission JRC GHS-BUILT-S R2023A](https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php), 100 m equal-area Mollweide, tile R5_C8, total built-up surface. Source raster values are square meters of built-up surface within each cell. Ten official ZIP tiles total about 95 MB; raw caches are ignored under `data/raw/day09/ghsl/`. Exact download URLs and SHA-256 digests are recorded in `data/history.json` and the cache download manifest. License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), European Union copyright; classification, clipping and display reprojection by this project.

**These are modeled estimates, not ten independent satellite observations.** The [GHSL technical documentation](https://human-settlement.emergency.copernicus.eu/documents/GHSL_Data_Package_2023.pdf) describes Landsat-supported anchors 1975/1990/2000/2014 and Sentinel-2 2018, with temporal interpolation/extrapolation to five-year outputs. The app labels intermediate years source-interpolated, 1975/1990/2000 anchor-aligned estimates, and 2020 source-extrapolated from the 2018 anchor. 2025/2030 projections are excluded. The app does not create annual observations or interpolate geographic shapes.

The satellite backdrop is **contemporary, not historical**. It remains unchanged through the timeline. Historical change is communicated only by GHSL overlays. Current building extrusions are deliberately not displayed as historical buildings.

- Global imagery: local [NASA GIBS Blue Marble](https://gibs.earthdata.nasa.gov/), a real satellite composite, reproduced with `download_globe.py`.
- Regional imagery: [Esri World Imagery](https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer). Streamed attribution retained; governed by Esri service terms and contributor licensing, not redistributed offline. Provider availability/terms may change.
- Terrain: [Esri WorldElevation3D Terrain3D](https://elevation3d.arcgis.com/arcgis/rest/services/WorldElevation3D/Terrain3D/ImageServer), real multi-source elevation including USGS. Earlier EPQS spot checks are retained in `elevation-check.json`. This is not a claim of locally processed LiDAR. An ellipsoid is used only at globe scale above 2,000 km to avoid the provider’s polar cap artifact; regional views use actual DEM terrain. Historical ground elevation change is not modeled.
- CesiumJS 1.127.0, Apache 2.0, CDN hosted. No Cesium ion dependency; NASA local globe texture provides a practical global imagery fallback, but detailed terrain and imagery still need network access.

## Reproducible GIS method

Install Python dependencies in a virtual environment: `numpy rasterio geopandas shapely pyproj pillow requests`.

```sh
python3 maps/day09-urban-rural/download_history.py
python3 maps/day09-urban-rural/process_history.py
python3 maps/day09-urban-rural/test_history.py
node maps/day09-urban-rural/test_cinematic.js
```

1. Study rectangle: west −115.50°, south 35.88°, east −114.85°, north 36.45°. Covers the valley and adjacent desert, not the entire Census metropolitan county region.
2. Read only the relevant window directly from each compressed tile. Verify identical native grids across all epochs. Use native **ESRI:54009 equal-area Mollweide** for area; do not resample values for analysis. Retain common valid cells whose centers fall inside a densified projected study rectangle.
3. Classify a cell as developed when built-up surface is **at least 1,000 m² within its 10,000 m² cell (10%)**. Apply exactly the same threshold in all epochs. This is an explicit visualization/analysis threshold, not an official GHSL urban or municipal boundary. Low-density settlements and non-residential structures can be included; roads without substantial built surface can remain gaps.
4. Developed-cell area = classified cell count × 0.01 km². Separately sum source built-up surface. Newly classified cells = current minus prior mask; losses = prior minus current. No cumulative union or forced monotonic correction. This subset has zero decreasing source cells and zero threshold losses; that is a result of these modeled rasters, not independent proof that no demolition occurred.
5. Polygonize masks and changes, simplify by 10 m with topology preservation, export WGS84 GeoJSON. Validate vector area against native raster counts. Browser layers are 1024² RGBA classified textures reprojected with nearest neighbor onto one geographic rectangle, accurately draped over terrain. Display resampling is not used for statistics.
6. Animate opacity only. Shared cells stay muted blue, actual additions briefly turquoise, losses would fade. Unchanged layers remain visible across animation frames to avoid unnecessary imagery state churn. Camera stays fixed throughout expansion. All displayed statistics come from `data/history.json`.

| Epoch | Developed-cell km² | Built-up surface km² |
|---|---:|---:|
| 1975 | 289.36 | 87.10 |
| 1980 | 305.11 | 92.06 |
| 1985 | 320.64 | 97.11 |
| 1990 | 335.45 | 102.27 |
| 1995 | 490.90 | 138.51 |
| 2000 | 568.06 | 182.41 |
| 2005 | 713.31 | 212.33 |
| 2010 | 769.51 | 245.41 |
| 2015 | 807.43 | 277.49 |
| 2020 | 836.62 | 296.58 |

Developed-cell footprint increases 547.26 km² (189.1%). **This is not measured land conversion:** a cell can cross the classification threshold through densification inside an existing neighborhood. Built-up surface is a different metric from the land occupied by classified cells. The temporal allocation comes from GHSL’s model and should not be interpreted as exact construction dates. A single threshold, 100 m mixed cells, study boundary and source uncertainty affect results. No uncertainty intervals are supplied by this local analysis.

## Outputs and hosting

`data/history.json`: computed statistics, provenance, temporal definitions and native-grid QA. `data/history/`: small browser textures (~1.6 MB total compressed). `data/history-footprints.geojson` and `data/history-changes.geojson`: GIS companion polygons; not loaded into browser memory. Older NLCD/OSM and edge-reveal files remain as provenance from the previous Day 9 concept and are not used by this historical app.

```sh
python3 maps/day09-urban-rural/package_site.py
```

Creates an ignored local `build/` with `index.html`, relative assets and `.nojekyll`, compatible with GitHub Pages. Does not deploy. No raw ZIP/TIFF files are packaged. Current QA status and any browser limitations are in `qa-review.json`.

## QGIS swipe alternative

For a desktop comparison, load `data/history-footprints.geojson` twice in QGIS, filter one copy with `"year" = 1975` and the other with `"year" = 2020`, apply the same blue fill, and compare them with the [LeafMap plugin Layer Swipe](https://gishub.org/blog/leafmap-qgis-plugin/). These are development estimates, not historical aerial photographs. The browser version implements the same divider interaction using Cesium imagery-layer splitting.

## Final presentation refinements

Footprint RGB is recolored at runtime to `#304F63` with 45% layer opacity; the original geographic texture masks, GIS outputs, classification and source rasters remain unchanged. Compare uses identical symbology for both periods, corner year labels, a thin ivory divider and a compact handle. Growth shows only actual five-year epochs, a separate year counter and opacity transitions; the contemporary basemap remains unchanged. The displayed **2.9× GROWTH** is dynamically calculated as 836.62 / 289.36, the ratio of 2020 to 1975 developed-cell footprint area, not literal building-covered area. Recording preserves the title, epoch, metric and source disclosure while hiding the control panel. Attribution remains available through Cesium credits in desktop and mobile layouts.
