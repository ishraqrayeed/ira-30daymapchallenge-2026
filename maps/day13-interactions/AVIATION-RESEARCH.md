# Archived aviation research — abandoned November 13, 2026

No aircraft collector is running. These notes and acquisition scripts are retained
for reference; they are not part of the Day 13 game or its Pages package.

# Day 13 — Interactions

Question: how did observed aircraft activity change around the November 13,
2026 national departure stop? Implementation is currently at data acquisition.

## Sources and cache

Raw downloads live in ignored `data/raw/day13-aviation/`, outside the public map.
`manifest.json` records URLs, retrieval timestamps, sizes and SHA-256 checksums.
Partial responses are not usable snapshots.

Current cache: airport CSV and FAA advisory downloaded successfully. OpenSky
global and regional requests timed out (40–180 seconds). A separate file preserves
3,378 complete original rows recovered from the truncated global response at
2026-11-14 00:02:14 UTC (November 13, 19:02:14 EST). It is explicitly marked
`INCOMPLETE`: arbitrary response ordering makes it unsuitable for national counts,
coverage comparisons or a before/during/after timeline. No complete aircraft
snapshot or historical event window has been acquired yet.

- [FAA advisory 111](https://www.fly.faa.gov/adv/adv_otherdis.jsp?advn=111&adv_date=11132026&facId=DCC&title=NATIONAL+GROUND+STOP&titleDate=11/13/2026):
  retrieved directly. Signed November 13 at 20:54 UTC (15:54 EST); message event
  window 13/2053–14/0400, effective window 132054–140430. Orders departing
  traffic to remain ground stopped until further notice; inbound international
  flights managed case by case. These windows do **not** verify actual lifting.
- [OpenSky current state vectors](https://openskynetwork.github.io/opensky-api/rest.html):
  anonymous current snapshots, not historical reconstruction. Authenticated REST
  lookback is at most one hour; older positions require historical Trino access.
  Anonymous allowance is 400 credits/day, four per global snapshot.
- [OpenSky terms](https://opensky-network.org/about/terms-of-use): nonprofit
  research/education limitations, redistribution and identifier disclosure
  restrictions apply. This local research cache is not approved for public raw
  redistribution. Operational API use requires written licensing.
- [OurAirports CSV](https://davidmegginson.github.io/ourairports-data/airports.csv):
  supplementary point metadata, not authoritative airport boundaries. The cache
  contains 86,355 worldwide records, including 32,709 US records (all types and
  statuses, not a count of active commercial airports).

## Repeat a current snapshot

```sh
python3 maps/day13-interactions/scripts/fetch_aircraft.py
```

The script preserves the full source fields and source timestamp, validates JSON,
and writes a QA report. It never requests an anonymous historical timestamp.
Optional bounded collection: `--count 12 --interval 300` (55 minutes between
first and last requests, plus download time). No collector runs automatically.

Counts in raw QA are worldwide or bounding-box observations, **not US totals**.
US geographic filtering, airport polygon acquisition, spatial matching, jump
checks and map implementation remain to be done. Ground flags indicate received
surface reports, not parked inventories or evidence of individual FAA impact.
