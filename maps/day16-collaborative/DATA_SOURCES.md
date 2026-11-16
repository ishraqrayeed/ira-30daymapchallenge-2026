# Data sources

- **NOAA National Geodetic Survey CORS observations:**
  https://geodesy.noaa.gov/CORS/data.shtml — public archive distributed through
  https://noaa-cors-pds.s3.amazonaws.com/. Selected day: 2026/305 (1 November).
  Daily files: `rinex/2026/305/ssss/ssss3050.26o.gz` or compact `.26d.gz`.
  RINEX headers verify D1 availability. NOAA's distribution terms state no warranty
  and use at the user's risk. No authentication is required.
- **NGS published station metadata:** `coord/coord_20/ssss_20.coord.txt` and
  `station_log/ssss.log.txt` in the same bucket. Coordinate inventory:
  `coord/coord_20/itrf2020_geo.comp.txt`. Published ARP positions and velocities in
  ITRF2020; header approximate coordinates are not substituted for these.
- **IGS rapid GPS orbit:**
  `rinex/2026/305/IGS0OPSRAP_20263050000_01D_15M_ORB.SP3.gz` in NOAA's bucket.
  32 GPS PRNs; 15-minute positions, GPS time, IGc20 Earth-fixed frame. The product
  is a real postprocessed rapid orbit, not a TLE or invented constellation.
  See https://igs.org/products/ and https://igs.org/data/ for IGS use/citation policies.
- **RINEX sign convention:** IGS RINEX specification §3.4, positive Doppler for
  approaching satellites: https://files.igs.org/pub/data/format/rinex303_update1.pdf.
  The files here are v2.11 D1; the convention is independently verified numerically.
- **Boundaries:** US Census 2024 1:5,000,000 cartographic states,
  https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_state_5m.zip.
  Federal public data, selected to the lower 48 plus DC. Generalized cartographic
  boundaries are not survey-grade legal boundaries.

No observations are live. Station availability and receiver equipment change;
source dates, exact station choices, exclusions and hashes are retained in `data/`.
Software: MapLibre GL JS 5.6.0 (BSD), Three.js (MIT), Barlow fonts (OFL); licenses
are bundled in `vendor/`. Original raw source caches are excluded from Git.
