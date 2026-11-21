# Where America Learns to Play Soccer

Day 20 maps **2,307 geocoded US Club Soccer club listings across all 50 states and D.C.** The mapped locations are directory street addresses, including offices. The map measures the distribution of listed clubs. Playing fields, age eligibility and proximity to a program are outside the directory snapshot.

[Interactive local preview](outputs/clubs/map.html) · [Resolution 3 map layer](outputs/clubs/national-r3.svg) · [State coverage CSV](outputs/clubs/state-coverage.csv)

## Collection and address matches

| Stage | Count |
| --- | ---: |
| Directory API advertised total | 4,625 |
| Records downloaded across 47 pages | 4,625 |
| Distinct directory IDs | 4,622 |
| U.S. records classified as clubs with a positive team count | 4,402 |
| Club records with a usable street address submitted | 3,584 |
| Distinct address submissions | 3,518 |
| Club records mapped from exact address matches | 2,307 |
| Submitted club records without an accepted exact match | 1,277 |
| Club records with no usable street address | 818 |

The 2026-11-20 directory download contained three duplicate records. The state endpoint advertised one more record than the observed distinct IDs in each of California, North Carolina and Texas. The state export retains both counts. Club IDs deduplicate the directory. A positive team count is the automated filter. Geographic and membership coverage reflect this directory and snapshot. [US Club Soccer directory](https://usclubsoccer.org/club-directory/) · [Public API schema](https://usclubsoccer.org/wp-json/gotsoccer/v1) · [Source manifest](source-manifest.json)

The Census Bureau responded to all 3,518 distinct street addresses. Accepted geocodes require an exact TIGER street match in the directory state. Street locations are interpolated along address ranges. P.O. boxes, unrecognized addresses, ties and nonexact matches stay out of the map. The locally generated club CSV records exclusions and retrieval provenance. [Census geocoding documentation](https://geocoding.geo.census.gov/geocoder/Geocoding_Services_API.html) · [Batch manifest](outputs/clubs/geocoding-manifest.json)

Mapped examples include Albion SC Boulder County in Lafayette, Real Colorado in Centennial, and Colorado Storm in Aurora. Colorado Storm is the former Colorado Rapids Youth Soccer Club. Colorado has 30 mapped club listings, Alaska has 5, Hawaii has 18 and D.C. has 4. [Colorado Storm rebrand](https://coloradostorm.com/news/how-we-want-to-attack)

## Reading the map

**Resolution 3** groups the original 2,307 mapped locations into 296 occupied hexes. Counts use distinct directory club IDs. The same counts determine the muted sage-to-pine fills, legend, tooltip and club panel. The panel lists club names, cities and websites when available. The margin note uses the leading state in the mapped club IDs. Texas leads with 411 listed clubs, followed by California with 346 and Florida with 174.

Occupied cells fill to their edges and clip to the Census land outlines. Areas without listings have a smooth ivory fill. The 1.1-pixel coastline and international-border stroke sits above the hex fills, with thinner internal state lines. Alaska and Hawaii appear in compact insets to the right of the contiguous U.S. The original H3 IDs support data joins, and the whole occupied hex is selectable. Thin outlines identify the hovered, focused or selected cell. [Census cartographic boundaries](https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html) · [Land-grid and timing checks](outputs/clubs/land-grid-qa.json)

The intro starts from ten separated local peaks within the first quarter-second. Cells within three H3 rings follow by distance to the nearest eligible peak. Higher counts lead at similar distances. Isolated cells fade in near the end. Each occupied cell gets one brief highlight before it settles into its legend color. Reveal starts are distributed continuously across 2.5 seconds, while the map view stays still. Reduced motion shows the final fills immediately. Use the scroll wheel or pinch to zoom and drag to pan. With the map focused, use + and − to zoom, the arrow keys to pan, and Home to restore the national extent. Tab moves between occupied hexes, and Enter opens the club drawer. The club panel opens over the map and keeps the current view.

[Resolution 3 GeoJSON](outputs/clubs/h3-r3.geojson) · [Resolution 3 click data](outputs/clubs/h3-r3-panel.json)

## City audit

| Listed city | Raw listings | Distinct directory club IDs | Listings with usable street | Distinct listed street addresses | Mapped club IDs | Distinct Census-matched addresses |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Midland, TX | 66 | 66 | 65 | 63 | 48 | 47 |
| Odessa, TX | 72 | 72 | 71 | 68 | 42 | 40 |
| Dallas, TX | 49 | 49 | 48 | 43 | 31 | 30 |

The audit uses the mapped IDs from the hex panels and groups cities by trimmed, case-insensitive name and state. The audit found one lower-case Odessa record, one uppercase Dallas record and one trailing-space variant each for Odessa and Dallas. It found zero repeated directory IDs or normalized club names in these three raw city groups. Distinct listed street addresses use the geocoder inputs, with punctuation, case and common street suffixes normalized. The count groups by street and ZIP and excludes unit designators.

One pair of Midland clubs, two pairs in Odessa and one pair in Dallas share exact Census street matches and coordinates. Midland’s repeated match includes an “Avenue” versus “Ave” spelling. The exact matches are TIGER address-range interpolations; the workflow uses neither ZIP nor city centroid coordinates. Each shared match has different directory IDs and names, with insufficient evidence for a merger. The audited city counts and order remained stable. [Source-page and club-ID trace](outputs/clubs/city-audit.json)

## Rerun

Run from the repository root using Python 3.11. Cached directory and geocoding responses live in the ignored `data/raw/day20-hexagons/` directory. The final command serves the local preview.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r maps/day20-hexagons/requirements.txt
python maps/day20-hexagons/download_data.py --clubs
python maps/day20-hexagons/clubs.py --geocode
python maps/day20-hexagons/render.py
python scripts/preview_map.py --directory maps/day20-hexagons/outputs/clubs
```

On repeat builds, `clubs.py` also runs without `--geocode` when all batch responses are cached. Use `download_data.py --clubs --refresh` for new source responses. The page list describes the reviewed snapshot. If the API reports a different number of pages on refresh, update the numbered entries in `sources.tsv` before rebuilding.

The [approved Boulder pilot](README.md#approved-boulder-area-pilot) remains a separate verified program-and-venue study. Its counts are independent of the directory map.
