# Day 02 — Lines

## Every Line a Climb

How does Rocky Mountain National Park's trail network connect valleys and high
country? A circular terrain map colors hiking trails by elevation. Click or tap
a continuous trail segment for its distance and elevation profile.

[Map](map.html) · [QA](map.qa.json) · [Results](map.results.md)

### Sources

Retrieved October 31, 2026:

- [NPS Public Trails](https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_Trails/FeatureServer/0),
  `UNITCODE = 'ROMO'`: 466 features. Source edit dates range from August 2021 to
  February 2026; these are edit dates, not current access confirmations.
- [NPS official boundary](https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer/2),
  `UNIT_CODE = 'ROMO' AND Status = 'Official'`.
- [USGS 3DEP bare-earth elevation](https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer),
  exported as a 2,400 × 2,400 floating-point grid in NAD83 / UTM zone 13N
  (EPSG:26913), approximately 22 m grid spacing. The service describes data
  published through October 26, 2026; underlying acquisition dates vary.
- **350+ miles** is the park-wide summary from the
  [NPS hiking page](https://www.nps.gov/romo/planyourvisit/hiking.htm?fullweb=1),
  checked October 31, 2026. It is separate from our calculated mapped length.

Federal agency-authored data are generally U.S. public domain; see
[NPS terms](https://www.nps.gov/aboutus/disclaimer.htm) and
[USGS terms](https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits).
Every retrieved trail record is marked `Unrestricted` and `Public Map Display`.
Attribution remains visible. Raw responses, metadata, retrieval time, and SHA-256
hashes are cached under ignored `data/raw/day02-lines/`.

### Method and QA

Keep existing hiking-use records; exclude two with unknown use. Clip to the park
boundary. Dissolve exact overlaps and merge touching pieces with the same name;
retain branches as separate continuous profiles. Preserve distinct nearby paths.
Omit remaining pieces shorter than **0.5 miles (804.672 m)** and remove exact duplicate geometry.
Also omit compact detached pieces with a maximum bounding-box width/height below
600 m and more than 100 m from every other segment passing the length filter.
This removes one 0.505-mile Beaver Meadows / Moraine Park Complex piece; it is a
cartographic omission, not a claim that the trail is invalid. Nearby loops remain.
The cleanup is applied to data, with no filter control in the map.

The resulting **158 segments** contain approximately **314.7 miles** of selected
linework. These are continuous dataset pieces, not complete hikes. The park-wide
NPS figure includes trails beyond this cartographic selection. Short-piece and
other exclusions are recorded in the QA file.
The dissolve removes approximately 0.32 miles of overlapping linework; 203 short
pieces totaling approximately 35.65 miles are omitted after merging and simplification.

Simplify lines within 2 m, densify to at most 35 m spacing, and sample elevations
bilinearly. All samples are valid; sampled elevations span 7,780–14,248 feet.
Lengths are horizontal UTM distances. Profiles follow stored line direction,
which does not indicate a trailhead or a recommended hiking direction. No ascent
total or difficulty rating is inferred.

The same DEM supplies neutral shaded relief and 250 m contours, drawn at 48%
opacity to favor the trail colors. Trails use 2.2 px colored strokes, increasing subtly to 2.35 px at low elevations; the park
boundary uses a quieter 1.15 px dashed stroke with a pale under-stroke and lighter dashes. The circular
frame includes the park with margin; it is not the park boundary. Trail colors
encode altitude, not steepness or vegetation. Elevations and distances are
approximate; see [NPS conditions](https://www.nps.gov/romo/planyourvisit/trail_conditions.htm)
for current access.

### Peak landmarks

The three highest peaks are marked: [Longs Peak](https://en.wikipedia.org/wiki/Longs_Peak),
[Mount Meeker](https://en.wikipedia.org/wiki/Mount_Meeker), and
[Chiefs Head Peak](https://en.wikipedia.org/wiki/Chiefs_Head_Peak). Coordinates
were checked November 1, 2026, and transcribed into `peaks.json` from those
Wikipedia articles (article license: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)).
Coordinates are projected to the trail map's UTM frame and checked against the
circular frame. Small neutral dots mark exact summit positions, with thin leader lines connecting them to their names.
Labels follow pan/zoom and hide near the circle edge.
They provide orientation; trail selection remains the interactive action.

### Reproduce and review

```sh
python3 maps/day02-lines/download_data.py
python3 maps/day02-lines/main.py
python3 scripts/preview_map.py --directory maps/day02-lines --port 8002
```

The opening view uses a centered poster layout with no side columns and a small, attributed NPS park-wide 350+ mile figure. Trail details
open below the map after selection; desktop zoom controls appear on hover or
keyboard focus. The HTML embeds terrain and vector data, without live basemap requests. Drag to
pan; use +/− to zoom and Reset view for the whole park. Keyboard: arrows pan,
+/− zoom, Home resets, Escape clears, and bracket keys browse segments.
Ordinary scrolling moves the page. Hover highlights a segment and shows its
source name, length, and elevation range, including when another trail is selected.
The scale bar measures 5 miles in the opening view and switches to smaller round
distances when zoomed, with its width recalculated to remain accurate.

The user reviewed the local preview and approved publication after adjustments
to trail cleanup, direct selection, and centering. Mobile appearance has not been
independently reviewed. Automated data and interaction checks pass.
