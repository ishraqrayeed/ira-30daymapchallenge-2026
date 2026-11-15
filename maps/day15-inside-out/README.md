# Day 15 — Inside Out

## The Road Carved Into the Mountains

**Switchbacks of the Million Dollar Highway**

[Open locally](map.html): a portrait photograph, a south-up GIS centerline, and a
rotatable isolated road ribbon shown together. On narrow screens the three
views stack. Drag to rotate, scroll/pinch to zoom, shift-drag/two fingers to pan;
reset, overhead, and rotate/tilt arrow buttons are available. Dragging uses
damped OrbitControls with a level horizon; rotation underneath the road is allowed.
Arrow keys rotate, +/− zoom, R resets.

[Poster PNG](map.png) · [Blender scene](road.blend) · [QA](qa.json)

## Selected stretch

**900 m of US 550 near Bear Creek**, with an approach, compact alternating bends,
and a short exit. The cut is at chainages 8,800–9,700 m along the original route
from central Ouray. It rises approximately 53 m in the sampled DEM.

| Endpoint | Latitude | Longitude | DEM height |
| --- | ---: | ---: | ---: |
| Approach | 37.9688650 | −107.6592292 | 2,876.40 m |
| Exit | 37.9647639 | −107.6608134 | 2,929.33 m |

The broader leading curve and closely spaced reversing bends form the same
compact sequence as the supplied snowy reference and the selected Instagram
photograph. The alternative above Ironton has two offset pairs rather than this
single aligned sequence. The southern exit extends 50 m beyond the initial candidate. The user selected
the Bear Creek candidate after the
[top-down comparison](review/segment-candidates.png). This is a visual match;
the exact photographic camera position has not been independently geolocated.
No bend is moved or rearranged. All three geographic outputs use `data/route.json`.

## Sources and processing

- **Road:** © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright),
  ODbL. [Overpass API](https://overpass-api.de/api/interpreter), snapshot retrieved
  2026-11-14. Only `ref=US 550` edges enter the graph; the selected stretch follows
  [way 1073455801](https://www.openstreetmap.org/way/1073455801).
- **Elevation:** public-domain USGS [3DEP Bare Earth DEM Dynamic ImageServer](https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer).
  Multi-resolution service exported as a **10 × 10 m**, float32, single-band
  GeoTIFF in NAD83 / UTM zone 13N, **EPSG:26913**. The full-corridor export is
  1,667 × 2,933 pixels. This is export resolution, not uniform native source
  resolution. Service coverage includes DEMs published through 2026-10-26;
  acquisition dates vary. Heights are metres, using 3DEP's CONUS NAVD88 heights.
- **Photograph:** © **Adam Silverman (@wej12)**, photographed 2024-09-27, posted
  2024-10-14. [Original Instagram carousel](https://www.instagram.com/p/DBHaQE2vHJG/).
  The 1,080 × 1,350 portrait image and its watermark are displayed uncropped.
  Attribution was checked against public post metadata. No open photo license
  is asserted. The separately supplied Aaron Woo snowy JPEG was a selection
  reference and is not used as Adam Silverman's image.

Project OSM to EPSG:26913; clip by metric chainage, retaining all 76 original
and interpolated boundary vertices; densify each edge to ≤10 m (117 vertices).
Bilinearly interpolate the pixel-centered DEM. Missing samples, repeated nodes,
side roads, duplicate segments and horizontal self-intersections are absent.
An isolated-sample check found no spikes. A Gaussian filter with sigma 20 m and
radius 60 m suppresses raster-scale roughness on a 5 m chainage grid before
interpolating back to the unchanged alignment; endpoint heights are retained.
The maximum height adjustment is 0.58 m. These are **DEM-derived approximations
of road height**, not surveyed road elevations or a driving-grade profile.

The isolated ribbon is 24 m wide with a 3 m display edge. Neither is a
measurement of the asphalt. Terrain is not rendered. The browser and Blender
read the same clipped route JSON. The perspective default looks along the road
from its northern end, 45° above horizontal, matching the photograph. The GIS
trace is south-up as well, with the north arrow pointing down; reset restores that view. The amber
surface uses broad fill lighting so the connected bends stay legible. Camera and reproducible scene settings are stored in `segment.json`.

## Reproduce

Python 3.11+, Blender 4.5+ (built using 5.3), and Node.js for controller checks.
Run from the repository root. On macOS use
`/Applications/Blender.app/Contents/MacOS/Blender` in place of `blender`.

```sh
python3 -m pip install -r maps/day15-inside-out/requirements.txt
python3 maps/day15-inside-out/download_data.py
python3 maps/day15-inside-out/prepare_data.py
blender --background --python maps/day15-inside-out/build_scene.py
python3 maps/day15-inside-out/validate.py
node maps/day15-inside-out/test_viewer.mjs
python3 scripts/preview_map.py --directory maps/day15-inside-out --port 8015
```

`map.png` is 3200 × 4000, 4:5; `road.blend` packs its fonts. Scripts fall back to
Blender's built-in font if Georgia/Arial are unavailable. Cached raw OSM, raster
and service metadata live in ignored `data/raw/day15-inside-out/`; URLs, export
parameters and checksums are in `sources.json`. Included derived data let both
renderers run without downloads. Three.js r160 and its OrbitControls are vendored under MIT.

Published at https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day15-inside-out/. Browser and poster observations are recorded
in [visual-review.json](visual-review.json).
