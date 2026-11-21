# Where America Learns to Play

**Day 20 · Hexagons** · Can public records tell families where children under 10 actually play organized soccer?

The current national preview maps US Club Soccer directory addresses, including offices, across all 50 states and D.C. [National map](outputs/clubs/map.html) · [Club directory evaluation and rerun](CLUBS.md)

## Approved Boulder-area pilot

The Fall 2026 pilot links **10 verified program–venue pairs** to **8 venues, 7 program offerings and 4 providers** in Boulder, Broomfield and Lafayette postal addresses. The 14-row evaluation table includes four unmapped observations. The five known providers form a spot check, and the verified data cover part of Colorado’s Front Range. All three resolutions use those same points.

[Static preview](outputs/pilot-preview.svg) · [Pilot CSV](outputs/pilot.csv) · [Review queue](outputs/review.csv) · [Source manifest](source-manifest.json) · [QA counts](outputs/qa.json)

| Resolution | Occupied cells | Providers per occupied cell | Layers |
| --- | ---: | ---: | --- |
| 4 | 1 | 4 | [GeoJSON](outputs/h3-r4.geojson) · [Panel JSON](outputs/h3-r4-panel.json) |
| 5 | 4 | 1–3 | [GeoJSON](outputs/h3-r5.geojson) · [Panel JSON](outputs/h3-r5-panel.json) |
| 6 | 6 | 1–2 | [GeoJSON](outputs/h3-r6.geojson) · [Panel JSON](outputs/h3-r6-panel.json) |

Each hex counts distinct providers. Programs and addressed venues sit beneath their provider in the panel. H3 assigns every venue independently at each resolution. Counts summed across cells can exceed the number of providers in the footprint.

## What the sources supplied

Collection date **2026-11-20**. Directory numbers describe discovery listings. Local rows count reviewed program–venue–season observations, including observations with no venue. “Exclusive” means the pair uses only that program/schedule source group in the audit. Joint provider and league evidence appears under both groups, and address and age references support the underlying joins.

| Source | Records retrieved or reviewed | Unique provider keys | Verified under-10 offerings | Verified pairs | Exclusive pairs |
| --- | ---: | ---: | ---: | ---: | ---: |
| Play Club Soccer | 13 browser-indexed listing extracts | 13 provisional profile keys | 0 | 0 | 0 |
| US Club Soccer | 102 API listings | 102 club IDs | 0 | 0 | 0 |
| US Youth Soccer | 54 association links | 0 club records | 0 | 0 | 0 |
| CSA club and field maps | 0 listings from widget shells | 0 | 0 | 0 | 0 |
| AYSO | 661 embedded locator records | 658 distinct nonempty website keys | 0 | 0 | 0 |
| Broomfield Soccer Club | 2 | 1 | 1 | 1 | 0 |
| CSA public schedules | 2 pilot observations used in verification | 2 | 2 | 2 | 0 |
| Albion | 5 | 1 | 2 | 5 | 5 |
| Kick2Build | 2 | 1 | 2 | 1 | 0 |
| Lafayette Recreation | 3 | 1 | 3 | 3 | 3 |
| YMCA of Northern Colorado | 2 | 1 | 1 | 0 | 0 |
| City of Boulder | 1 | 1 | 1 | 0 | 0 |

- **Play Club Soccer.** Advertised totals were CO 19, CA 203 and FL 92. The three state pages and one overlapping Albion profile supplied 13 manually transcribed discovery records with names, directory cities and selected league hints. Direct HTTP returned a Cloudflare 403 challenge for all five requested pages. The public indexed pages include club profiles and websites, but age descriptions and facilities lack a dependable season-specific program join. Supreme FC’s Florida record has a mismatched name and description. [Colorado](https://playclubsoccer.org/directory/soccer-clubs-in-colorado) · [California](https://playclubsoccer.org/directory/soccer-clubs-in-california) · [Florida](https://playclubsoccer.org/directory/soccer-clubs-in-florida)
- **US Club Soccer.** The WordPress REST index documents the directory’s public GET listing route. Three Colorado pages yielded 42 records, and two each in California and Florida yielded 30 per state. The API reported totals of 42, 711 and 345 respectively. Fields include club ID, name, organization type, website, discovery address, team count and record update date. Team and venue requests for Broomfield and the Albion venue request returned HTTP 403 with a missing session token. The list alone lacks eligibility and venue assignments. [Directory](https://usclubsoccer.org/club-directory/) · [REST schema](https://usclubsoccer.org/wp-json/gotsoccer/v1) · [Terms](https://usclubsoccer.org/terms-of-use/)
- **US Youth Soccer and CSA.** The USYS index links to associations across all 50 states, with split associations in California, New York, Pennsylvania and Texas. It supplies association names and websites. Colorado’s linked club and field maps served JavaScript widget shells without listing records in the cached responses. CSA reports sanctioning 60+ clubs. Separately, some public PlayMetrics schedules were readable through search indexing while direct responses served a JavaScript shell. The schedules can expose team labels, fields, dates and fixture status. [USYS index](https://www.usyouthsoccer.org/state-associations/) · [CSA maps](https://www.coloradosoccer.org/maps) · [CSA membership](https://www.coloradosoccer.org/about) · [Sample schedule](https://playmetricssports.com/g/leagues/1017-2262-661fd0f8/divisions/16222/division_view.html)
- **AYSO.** The public locator HTML embedded one structured list of 661 rows. Parsed contact addresses span 37 states, with four rows whose state could not be parsed. The payload exposes location names, contact addresses, URLs and coordinate fields. Its location ID is always zero, two entries lack websites and some website values repeat. Website keys are a proxy for regions. The pilot discards locator coordinates for mapping because the source does not tie them to an age-eligible offering or facility. The three Colorado rows list Black Hawk, Fountain and Colorado Springs contact cities. [FAQ and access instructions](https://ayso.org/faqs-support/) · [Public region locator](https://www.aysonational.org/RegionLocator)

No stand-alone bulk download was found in the checked entry points. AYSO’s embedded list is the broadest captured listing and the US Club REST route is the most reproducible paginated club source. There were **zero nationally verified venue pairs outside the Colorado pilot**. Website records and dates were collected for local evaluation. No general redistribution grant was established for the directory listings or provider materials. Raw caches stay outside Git, and the workflow retains factual fields and evidence links for this review. Confirm use and redistribution terms before public release.

## Five-provider spot check

| Known provider | Directory recovery | Evidence that maps an under-10 program |
| --- | --- | --- |
| Broomfield Soccer Club | Play Club Soccer, US Club Soccer and CSA schedule | Fall U10 Girls Junior Academy fixture at **Highland Park**, Broomfield. The youngest under-10-eligible birthdates derive from the 2026–27 age matrix. The recreational calendar’s spring heading conflicts with its fall dates and no rec venue was established. |
| Albion SC Boulder County Juniors | Play Club Soccer, US Club Soccer and CSA schedule | Fall Boulder Juniors at **Pleasant View Fields**, **Foothills Community Park** and **Martin Park**. East County Juniors at **Whitetail Park** and **Sports Performance Center**, Lafayette. Both Play Club Soccer Albion profiles link to the Boulder County footprint. The broad Colorado profile overlaps it and Juniors is assigned to the official Boulder County entity once. |
| Kick2Build | CSA schedule | Fall competitive **Boys U9 Akoma** at **Alexander Dawson School Sports Fields**, Lafayette postal address. The provider describes Dawson as its home site and the U9 fixture lists it. The linked competitive registration form is for spring. Sankofa’s fall registration verifies eligible birth years, but its Friday listing, Saturday overview and Boulder contact venue do not resolve a season-specific field. |
| Lafayette Recreation | City youth page | Fall **Tiny Tyke Soccer** (age 3), **Pee Wee Soccer** (ages 4–5) and **Youth Soccer** (K–8) at **City Park Fields** in the city guide. |
| YMCA of Northern Colorado | YMCA and City of Boulder program pages | The city’s Fall 2025 guide confirms preschool through grade 6 for the joint Boulder program and gives a generic field description. YMCA and City count as one program. Lafayette’s registration link returned HTTP 429 and no season-specific venue was recovered. |

CSA’s map widgets returned no usable listings for any of the five, and none matched the retrieved AYSO rows. US Youth Soccer provides the link to CSA. The checked Play Club Soccer and US Club Soccer slices recovered the entries shown above.

The pilot uses city facility pins or address matches after checking facility names and street addresses against published evidence. The two Lafayette facility pages expose the same default pin for different parks, so both were replaced with full-address matches. Candidates for Foothills and Martin Park from Census were empty and the matched Esri street records were used instead. Remaining mapped precision is facility pin, point address or street-level interpolation. Eight venues passed these checks, with zero unresolved geocoding failures among mapped candidates. An address point may sit away from the playing field. Postal city labels follow the evidence, including Dawson’s Lafayette address. Eligibility uses actual birth years, explicit ages or grades, with league labels retained alongside the 2026–27 affiliate matrix interpretation. The East County fall year is inferred from the shared club listing and matching weekdays. Blank registration status means no same-season availability was established at retrieval. [Age matrix](https://www.cjsa.org/wp-content/uploads/sites/276/2025/08/2026-2027-Player-Registration-Matrix.pdf) · [Lafayette fall offerings](https://www.lafayetteco.gov/DocumentCenter/View/46436/2026-Summer-Community-Services-Activity-Guide)

## Rerun

From the repository root, use Python 3.11 and `curl`.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r maps/day20-hexagons/requirements.txt
python maps/day20-hexagons/download_data.py
MPLCONFIGDIR=/tmp/day20-mpl python maps/day20-hexagons/main.py
```

The collector caches a fixed set of public URLs under ignored `data/raw/day20-hexagons/`. It retains response status and checksums and reuses matching cached files. Use `--refresh` to collect a new snapshot, then recheck the manually reviewed evidence in `observations.tsv`, `play-extract.tsv`, `coverage.tsv` and `review.tsv`. Browser-indexed evidence covers the blocked directory extracts plus some schedule and venue corroboration. The cleaner produces the pilot, review file, discovery extract, coverage JSON, six H3 layers, QA and SVG. To serve the static preview locally, run `python -m http.server 8020 --bind 127.0.0.1 --directory maps/day20-hexagons/outputs` and open `http://127.0.0.1:8020/pilot-preview.svg`.

**Recommendation.** The evidence supports a verified Colorado pilot and a broader discovery index. It is insufficient for a nationwide verified under-10 venue map. Pursue **Colorado Soccer Association’s PlayMetrics schedule and field data** next. Ask for a permitted feed or dated export with stable club, team, division, facility and season IDs, then test the same joins with another state association. Alongside that test, retain a municipal recreation and YMCA sample to measure what federation schedules miss.
