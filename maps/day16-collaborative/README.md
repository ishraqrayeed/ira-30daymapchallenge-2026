# Day 16 — Collaborative: THE INVISIBLE SYMPHONY

## America, Listening to Satellites.

An approximately 6-second interactive documentary (5× playback) of **57,329 actual GPS L1 Doppler samples from
116 NOAA CORS receivers in eleven states**. Observation window: **1 November 2026,
17:59:42–18:59:42 UTC**. This is a geographically selected, availability-limited
sample, not complete national coverage. No deployment has been performed.

[Interactive map](map.html) · [3000 × 2000 poster](exports/day16-invisible-symphony.png)

```sh
python3 scripts/preview_map.py --directory maps/day16-collaborative --port 8016 --no-browser
```

Open http://127.0.0.1:8016/map.html. Play, Pause, Replay, Final view and the scrubber
control the documentary. Click a receiver for every retained observation at that
exact epoch; select a PRN to highlight its links and plot. The chart defaults to a
real observed pass with a sign change. Reduced motion opens paused at the final
frame. All runtime assets are local; no API key or live tiles are required.

## Science

GPS L1 transmits at 1,575.42 MHz. To first order, the received frequency shift is
`Δf = −(f₀/c) × range_rate`, where increasing range is positive. Receivers track
carrier frequency and record the Doppler observable in RINEX. Motion during a
satellite pass changes its projection along the receiver's line of sight.
Clock behavior, atmospheric effects and tracking noise also contribute.

We read actual **D1 observations in RINEX 2.11**, not carrier-phase derivatives.
The IGS convention is positive for approaching satellites. That convention is
independently checked at each station against orbit-derived range rate. All
retained stations use the original D1 sign; **no bias correction or sign reversal
is applied to their measurements**. Cyan is positive, amber negative, and white
is the explicitly defined ±100 Hz interval. The chart explicitly labels raw, sign-verified D1; a physical-sign transform of
`+1 × raw D1` applies to every retained station, without removing clock bias.
White is a display category, not a
measurement uncertainty estimate.

The matching IGS rapid SP3 product supplies GPS positions in Earth-fixed IGc20.
Ten-node local polynomial interpolation covers the observed hour with padding;
light time is iterated and Earth rotation during signal travel is applied for
receiver geometry. Range rate uses a centered 1-second range difference. NGS
ITRF2020 ARP coordinates are propagated from epoch 2020.0 with published
velocities. Antenna phase-center offsets and clock/atmospheric corrections are
not estimated; this is sufficient for the validated Doppler-direction display,
not precision GNSS processing.

Both SP3 and observation epochs are GPS time. The pipeline explicitly subtracts
**18 seconds** to display UTC. It retains exact minute-aligned observations from
18:00–19:00 GPST, without inventing samples. Every active link uses the same
selected epoch. Missing links disappear; measurements are held between samples.

## Selection, filters and validation

The expanded sample contains **116 receivers across 11 states**: AZ, CT, FL, IL,
IN, MA, NY, OK, OR, TN and VA. It preserves the observation date and common hour.
[coverage-summary.json](data/coverage-summary.json) gives computed counts, state
allocations, exclusions and all unrepresented states.

The header audit covers 1,436 stations with published coordinates and 342
additional daily archive entries. D1 candidates were available in only 12 states
under this pipeline. State-first sampling selects at least one candidate per
available state, retains the validated existing receivers, and fills the least
represented states using WGS84 maximin distance. The target is 120 candidates,
with a ceiling of 20 per state; Doppler magnitude is never a selection score.
The checked-in station manifest makes the delivered sample reproducible.

Of 120 candidates, 116 passed. ICT4 (Kansas) has a −362 Hz median orbit residual;
STAY, MCSO and NYLP have too few usable observations in this hour. Previously
excluded ICT5 has a +1,683 Hz common residual. Neither Kansas station is used to
color motion. No clock correction or invented measurements fill these gaps.

Retain GPS PRNs with matching SP3 orbits, finite `|D1| ≤ 10,000 Hz`, and elevation
≥10°. Require per-station Doppler/orbit correlation >0.98, absolute median
residual ≤100 Hz and residual MAD ≤25 Hz. Every retained non-near-zero sample
agrees in sign with geometric range rate. The independent GeoRinex comparison
matches 25 observations exactly; withheld SP3-node interpolation error is ≤0.041 m
(an internal check, not absolute orbit accuracy). See
[scientific-qa.json](data/scientific-qa.json) and [validation.json](data/validation.json).

The 25–35-state target cannot be supported by the inspected November 1 files:
large gaps remain across the Rockies, northern/central Great Plains and parts of
the Southeast. This describes this archive/date/pipeline, not the absence of GNSS
stations or Doppler observations generally. RF collaborator review remains pending.

## What the animation represents

The main map has real receiver coordinates. Its skyward Bézier arcs follow
calculated satellite azimuths, but endpoint distance and curvature are schematic;
they are neither ground tracks nor true three-dimensional lines of sight. The
Earth inset follows the same selected station/PRN as the chart, with the
receiver, selected satellite, actual orbit trace, line of sight, and projected
range-rate arrow. Earth is a WGS84 ellipsoid at true Earth-to-orbit scale; marker
sizes and arrow length are enlarged for visibility. Satellite geometry is
computed from SP3 every five seconds and interpolated for smooth display. D1
values stay at the last actual observed sample; the chart labels its UTC epoch.

The introductory reveals hold the first observation epoch. From internal timeline positions 9–28,
the hour advances through its 61 measured epochs. Glow, arc shape and moving
light trails are artistic; particle speed is not radio propagation speed.
The final scene holds the last data epoch while a separate artistic clock
keeps a gentle pulse shimmer; it never restarts the documentary. Pause freezes
that shimmer, and reduced motion stays static. Desktop illustrates at most **72 links**, mobile 48, chosen first for state
representation and then geographic spacing. All 61 epochs have 72 desktop links.
A receiver selection prioritizes its observations within the same cap; all its
retained values are available in the details panel. Satellite selection highlights
that PRN and dims the other links. Nothing is synthesized to fill geographic or temporal gaps.

Day 12's local MapLibre architecture, layered additive glow, deterministic GPU
ribbons and triangle-strip light trails are reused and adapted for measured link
colors. Previous days were not edited. The earlier terrain experiment is preserved
locally under ignored `archive/terrain-study/` and is not the current deliverable.

## Reproduce

From the repository root, with Python 3.11:

```sh
python3 -m venv .venv
.venv/bin/pip install -r maps/day16-collaborative/requirements.txt
.venv/bin/python maps/day16-collaborative/scripts/acquire.py
.venv/bin/python maps/day16-collaborative/scripts/preprocess.py
.venv/bin/python maps/day16-collaborative/scripts/validate.py
node maps/day16-collaborative/scripts/test_core.cjs
.venv/bin/python maps/day16-collaborative/scripts/coverage_report.py
```

The commands above use the delivered station manifest. To audit and resample, run
`select_stations.py`, `extend_coverage.py --apply`, then `balance_coverage.py` before
acquisition and processing. New quality exclusions can change the resulting sample.

Raw daily files, compact RINEX, original headers and metadata are cached under
ignored `data/raw/day16-symphony/`. Reusing caches preserves exact inputs; fresh
metadata may change. [sources.json](data/sources.json) records URLs, retrieval time
and SHA-256 hashes. Browser data are compact arrays with an explicit `record_fields`
schema; original D1 values are preserved. Orbit/geometry code is in
[scripts/preprocess.py](scripts/preprocess.py).

For browser review/export, install Playwright and Chromium, start the local HTTP
preview, then run `node maps/day16-collaborative/scripts/review.cjs`. Set
`PLAYWRIGHT_BROWSERS_PATH` if using a nondefault browser cache. The script verifies
controls and reduced motion and captures the final 3000 × 2000 PNG. Optional video:
record the browser at 30 fps after Replay; about 6 seconds contains the full story at the default 5× speed.

See [DATA_SOURCES.md](DATA_SOURCES.md) for terms and exact product identifiers.

## Cinematic presentation

The 65/35 desktop composition keeps the US map dominant, with the selected
satellite pass and measured Doppler graph on the right. Mobile stacks these views.
Section headings, repeated frequency explanations and the upper-right paragraph
are removed. A single dynamic motion label and measured value accompany the pass.
Methods, geometry qualifications and sign conventions remain available in **Info**
and this README. The footer contains only a compact legend and source line.

The pass canvas is approximately 35% taller at each reviewed desktop size:
238 px at 1920×1080, 164 px at 1600×900 and 173 px at 1366×768. The rendering sample is capped independently of the larger station dataset;
station selection exposes all values.
The data, orbital calculations and sign transformations are unchanged.

The selected LFLO × G04 series contains 61 measured epochs, a real positive-to-negative
D1 transition and near-zero observations. The enlarged pass view shows a fixed
receiver on the WGS84 Earth horizon, the actual SP3-derived trajectory, a geometric
line of sight and an arrow along the satellite's calculated motion direction.
A fixed, side-on camera changes only when the selected pair or viewport changes.
The view is cropped for clarity; Earth/orbit length scale remains consistent.
The satellite icon and arrow size are exaggerated, not the orbit altitude.

Five-second calculated orbit positions are interpolated for motion. Numeric Doppler
values, labels and link colors are held at the most recent real one-minute sample;
the graph cursor may move between samples. Dots and the selected observation marker
always represent actual measurements. The graph explicitly says **Measured GPS L1
Doppler (D1), Hz**. The physical-sign transform remains +1 for retained stations;
this does not remove clock or atmospheric contributions.

See `data/story-validation.json` for the selected pass and `browser-qa.json` for
control, synchronization, ambient-motion, reduced-motion and layout checks at
1920×1080, 1600×900, 1366×768 and mobile portrait. No previous day's source changed.

Playback uses a shared 5× clock for station reveals, orbital motion, measured
epoch selection and the graph. The internal scrubber spans the original 0–28
story units; elapsed time displays wall-clock seconds. Final ambient shimmer
retains its original gentle speed.
