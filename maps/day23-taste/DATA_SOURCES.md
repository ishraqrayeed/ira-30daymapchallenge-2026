# Data sources and methods

## Geographic inputs

- **OpenStreetMap contributors**, Bangladesh snapshot **2026-11-02**, distributed by
  [Geofabrik](https://download.geofabrik.de/asia/bangladesh.html).
  [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
  Regional extraction bounds: 90.383–90.435° E, 23.694–23.735° N. These are processing
  bounds, not a claimed administrative boundary of Old Dhaka. The initial camera
  fits the curated restaurant points, with space reserved for the title and controls.
- **Streets and pedestrian graph:** existing repository extraction of the same PBF,
  cropped to this area. Public pedestrian-accessible highways are retained;
  construction, motorways and explicitly restricted access are excluded. Restricted
  barrier nodes split ways. Explicit `oneway:foot` is honored in graph construction.
  All nodes and edges retain OSM provenance; no connection is inferred from a
  geometric crossing or drawn across missing node references.
- **Water:** pyosmium assembles closed ways and multipolygon relations from the PBF,
  then Shapely clips them to the extraction extent. Buriganga is OSM relation
  [5347205](https://www.openstreetmap.org/relation/5347205), with real shoreline geometry.
- **Neighborhoods:** named OSM place nodes. They are reference labels, not invented
  neighborhood boundaries. Restaurant assignments describe reported localities.
  Empty neighborhood selections remain legitimate: zero curated places is not an
  assertion that the neighborhood has no food businesses.
- **Landmarks:** Lalbagh Fort node 13954132428, Star Mosque way 245019710,
  Ahsan Manzil node 9365643172 and Bahadur Shah Park way 34339923.
  Points taken from mapped features; polygon points represent the feature, not an entrance.

The source manifest contains snapshot/cache checksums and processed-asset hashes.
Coordinates are WGS84 longitude, latitude. Edge lengths use great-circle distance
on consecutive mapped street nodes. No live OSM requests occur in the browser.
`routes.geojson` is initially empty; the worker creates actual graph paths on demand.
Each leg remains separate so disconnected routes cannot silently acquire connectors.

## Restaurant research

The starting references are Goethe-Institut’s
[Old Dhaka Food Map](https://www.goethe.de/ins/bd/en/kul/all/odf.html) and TBS’s
[2023 reported food walk](https://www.tbsnews.net/features/panorama/exploring-past-through-old-dhaka-food-map-665174).
They are research references; their map artwork and photographs are not copied.

Every restaurant lists its own links in `curated.json` and `restaurants.geojson`.
Menu evidence draws on branch-specific delivery menus, local reporting and the
Goethe project. Coordinates for **20** locations come from OSM nodes/buildings;
duplicate nearby records are consolidated by branch identity. The other **two**:

- **Manik Chan Polao:** place coordinates from the map link attached to Dhaka Tribune’s
  [2022 field report](https://www.dhakatribune.com/feature/290134/মানিক-চানের-পোলাও-manik-chan-polao-food-cart).
  The linked place coordinates are distinguished from the camera viewport center.
  This is an outdoor stall, not a claimed permanent storefront. Its latest cited
  [2025 report](https://www.tbsnews.net/features/78-years-flavour-story-manik-chans-polao-old-dhaka-1260066)
  supports Thursday mutton bhuna khichuri and Wednesday mutton biryani; older
  schedules differ, so service hours are omitted.
- **Haji Makhan Biryani:** approximate storefront from place code **7MMGPC76+5WG**
  linked in a [2023 visitor field report](https://www.localguidesconnect.com/t/73-years-old-haji-makhan-biryani-of-old-dhaka/396908),
  corroborated as a food-map establishment by TBS. The point is the decoded code-cell
  center, not a surveyed doorway. Current operation is explicitly uncertain.

The reviewed date is **2026-11-11**. “Source-checked” means documented identity,
location and specialty; it does not mean field-visited, independently inspected or
confirmed open today. Aftab’s specialty source is from 2012, and its status is also
explicitly uncertain. All others carry a check-locally operating-status note.
Restaurant Bengali names are shown only where present in OSM or an identified source.
Transliterations and normalized dish tags are documented, including menu “Chicken
Bhuna Khichuri” indexed as Morog Khichuri. No Beef Khichuri destination is asserted
without adequately resolved branch coordinates; see the unresolved research notes.
Ananda’s bakarkhani evidence is historical customer reporting, not a current menu.

## Reuse and limitations

OSM-derived GeoJSON and graph data retain ODbL attribution; related source caches
and extraction scripts provide the reconstruction path. Short descriptions are
original paraphrases. News photographs and Goethe artwork retain their own copyright
and are **not bundled**. All `photo_url` and `photo_credit` values are null.
MapLibre and Turf carry BSD/MIT license files; Noto Sans Bengali uses the SIL OFL.
The site makes no geolocation request and embeds no analytics or private API keys.
