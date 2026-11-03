# Day 05 — Senses: Sight

Working title: **What Messi Saw**. Every shot begins with an angle.

## Data research — 2 November 2026

The cached [Noah Bair event files](https://github.com/nlbair/wc2026-events),
revision `4674e5c674a852a60def48456d5bbfec0627932a`, contain 35 Messi shot events
across eight Argentina matches: eight goals, two match penalties, no shootout
attempts. All 35 have x/y coordinates. A separate
[FIFA-report-derived dataset](https://github.com/Alamyy/Worldcup26) agrees with
the attempt count in each match and records eight Messi appearances and goals.

| Opponent | Attempts | Goals |
|---|---:|---:|
| Algeria | 6 | 3 |
| Austria | 7 | 2 |
| Jordan | 2 | 1 |
| Cabo Verde | 9 | 1 |
| Egypt | 5 | 1 |
| Switzerland | 4 | 0 |
| England | 1 | 0 |
| Spain | 1 | 0 |

Four Messi passes carry the explicit intentional-goal-assist qualifier. This
agrees with [FIFA's assist table](https://www.fifa.com/articles/most-assists-top-assisters).
Requested context line: **MESSI · WORLD CUP 2026 / 8 GOALS · 4 ASSISTS · 12 G+A ·
21 CAREER WC GOALS**. The career total combines 13 through 2022 with eight in 2026;
it is not calculated solely from this tournament's events.

## Local preview

```sh
python3 maps/day05-sight/main.py
python3 scripts/preview_map.py --directory maps/day05-sight --port 8005
python3 -m unittest discover -s maps/day05-sight -p 'test_*.py' -v
```

Open http://127.0.0.1:8005/map.html. The self-contained HTML shows all 35 shots,
70 goalpost sight lines, eight goals in sky blue, and three static annotations.
Hover, click, or keyboard-focus a shot for recorded clock, outcome and geometry.
The two penalties share one physical position; concentric rings indicate both.

## Geometry and interpretation

Source coordinates are Opta 0–100, attacking increasing x in every period.
Piecewise interpolation between published
[mplsoccer pitch landmarks](https://mplsoccer.readthedocs.io/en/latest/gallery/pitch_setup/plot_explain_standardizer.html)
converts these to a 105 × 68 m pitch. Both penalties map to (94, 34), exactly
11 m from goal. This avoids the 12.075 m error from naive linear scaling.
Goalposts are (105, 30.34) and (105, 37.66), 7.32 m apart. Distance is to goal
centre; angle uses the dot product of the two post vectors. No geographic CRS is
involved: these are local pitch metres, so no misleading lon/lat GeoJSON is made.

Geometry summaries and hero selection exclude both penalties (33 attempts):

- Median distance: 18.7 m; median goal opening: 19.4°.
- Widest view: 47.9°, 8.1 m, goal v Algeria, recorded 59:42.
- Narrowest source-recorded view: 9.8°, 38.8 m, attempt v Algeria, 36:13.
- Longest goal: 24.6 m, 16.9°, v Jordan, 79:12.

The attempt definition follows the event source. The FIFA-derived cross-check
includes a referee-event classification for the narrowest attempt; it remains
included rather than silently removed. Source clocks are displayed verbatim;
official goal-minute labels sometimes differ. Source SavedShot includes blocked
attempts; blocked qualifiers are used where present. Dates use FIFA's local
match dates, which can differ from the event filenames by one day.

No provider xG or complete shot-end x/y exist in these CSVs. Neither is displayed.
Goal-mouth y/z and pass endpoints are not misused as shot destinations.

## Design and QA

**WHAT MESSI SAW / Every shot begins with an angle.** The dedicated
[portrait poster](poster.html) has a 1080 × 1350 artboard and automatically fits
within the visible browser area at normal zoom, including a 1400 × 900 laptop.
The existing wider [interactive map](map.html) remains available.

The portrait uses neutral page gray `#f7f8f7`, pale sage `#dce3d8`, gray-green markings `#839087`, graphite
construction lines `#4d5c60`, and Argentina blue `#75aadb` for goals. Georgia
serif headline (82 px), angles and statistics (70 px) use regular weight;
technical labels use 22–24 px monospaced type. Context is quieter than numbers.

The display crop is centred on the goal at artboard (540, 425), with equal
20 px/m axis scales: **1.43×** V2's geometry scale. The visible metric extent is
x=67.45–105 m, y=10.2–57.8 m. Cropping changes no recorded location or calculation.
Goal width remains 7.32 m; the posts share one goal line. The farthest shot has
45.7 artboard pixels before the bottom field edge; the goal frame has 61 pixels
of clearance below the statistics. The stronger goal frame is graphite `#354247` with 3 px strokes and outlined
posts; outer visible verticals are 25% quieter. The summary unit is 60% of the
number size. Hero annotations retain short leaders and safe margins.
The narrowest annotation says **OFF TARGET**,
verified against the processed outcome. Three compact annotations, 35 markers
and 70 sight lines remain. No new analysis or hero selection was run.

Six existing automated checks pass. Additional layout checks verify the centred
posts, equal scales, all embedded events, data/code checksums and unclipped point
centres. Chrome review covered the native artboard and approximately 540/360 px
feed presentations; the full poster was then checked at normal browser zoom.
Click inspection and Escape dismissal work. Final layout details are in
[layout QA](layout.qa.json). Source type is intentionally small; the two real
penalty events share a position. No PNG export was added. Days 1–4 are unchanged. The Pages packager includes Day 5 as a separate route.

## Coverage, limitations and release status

This represents horizontal geometric goal opening, not Messi's literal field of
vision. Defenders, goalkeeper, pressure, body orientation and control are absent.
Event precision and standardized pitch dimensions limit accuracy. Angle alone
does not explain shot quality. The three heroes are geometric extremes, not a
claim about the importance of those moments.

The event repository credits WhoScored and Noah Bair but provides no explicit
reuse license. Public release was requested by the user after review. No separate raw-event
download is provided, and no open-data license is claimed for the coordinates. The cross-check's structured
CSV dataset is CC BY 4.0; this does not license original FIFA PDFs or the separate
event coordinates. No football provider was scraped by this project.

Raw source caches and processed CSV/JSON remain under ignored
`data/raw/day05-sight/` and `data/processed/day05-sight/`. See
[source manifest](source-manifest.json), [analysis](analysis.json), and
[automated QA](map.qa.json). The approved portrait is the primary `/day05-sight/` page; the wider map is
available as `interactive.html`. Source-stage analysis metadata is retained
unchanged; publication authorization is recorded separately in layout QA.
