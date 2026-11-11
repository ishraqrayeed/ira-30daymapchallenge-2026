# The World in Traffic — data and listening notes

## Geographic question

How do the street patterns and everyday traffic environments of twelve cities differ?
Each map is a local portrait, not an entire city or a measure of congestion. Each
recording captures one place and moment, not a city's definitive sound.

## Streets

© OpenStreetMap contributors, [ODbL](https://www.openstreetmap.org/copyright).
OSMnx 1.9.1 queries Overpass for the `drive_service` network within a 1,300 m
bounding distance. When Overpass is overloaded, the script downloads four small
quadrants from the official OSM map API, applies the equivalent road-tag filter,
and constructs the network with OSMnx `graph_from_xml`. Both routes keep
disconnected components and simplified edge geometry.
This includes drivable public streets and service roads according to OSM tags;
it excludes private roads and pedestrian-only paths under OSMnx's filter.
Completeness and access tagging vary by city. Road type is not a traffic count.

Python projects each network to its local UTM zone, transforms the documented
WGS84 center into that CRS, and intersects every edge with a 1,000 m radius circle.
A 0.6 m topology-preserving line simplification reduces SVG size. Every SVG uses
the same 300 × 300 viewBox and 0.15 SVG units per meter: a 2 km diameter, north up.
Bidirectional graph edges can share the same physical street geometry. SVG clipping
provides a final exact circular visual mask. Primary through tertiary roads and
links are slightly thicker than minor roads; no invented lines are added.

Centers and their interpretation are in [recordings.json](recordings.json).
Named recording areas are used where possible. Otherwise a representative busy
location is used. None of these centers claims to be an exact microphone position.
NYC's creator recalls Times Square but explicitly expresses uncertainty.
[GIS QA](streets/qa.json) records projection, radius, retrieval time, feature count
and output hash for each city. Raw GraphML and Overpass responses are cached under
ignored `data/day11-traffic/`; processed SVGs are bundled and make no live requests.

## Audio provenance and rights

[recordings.json](recordings.json) is the authoritative track-by-track manifest:
creator, title, source and license links, original duration, recording date when
known, upload date separately, description, coordinate availability, excerpt,
gain and SHA-256 hashes. Unknown recording dates and coordinates remain null.

Eleven city recordings come from Freesound under CC0 1.0 or CC BY 4.0. Source pages
were checked for location descriptions and license labels. The app credits each
creator and links the source and applicable license. These are recordist-reported
locations, not independently authenticated recording sessions.

Freesound original-file downloads require login. This build uses each recording's
explicitly published high-quality MP3 preview instead, retaining that limitation
and the actual preview URL in the manifest. It does not claim lossless originals.
No authentication or download restriction is bypassed.

Dhaka uses the user-selected [Dhanmondi 27 recording by AnantaArtBD](https://www.youtube.com/watch?v=7LrWGGJFEJo).
The user explicitly confirmed permission to extract and redistribute its audio on
2026-11-11. It is credited as **Used with permission**, not as Creative Commons.
That permission is not a license grant to downstream users. The map center is
representative of the named Dhanmondi 27 area; exact recording coordinates and date
are unknown. The intended excerpt begins at 2:30 in the supplied video.

## Processing and interpretation

`process_audio.py` uses Python, NumPy/SciPy and FFmpeg. It extracts up to 25 seconds,
resamples to 44.1 kHz stereo, applies one constant gain targeting −24 dBFS RMS,
limits peak level to −3 dBFS and amplification to +12 dB, adds 40 ms edge fades,
and encodes 128 kbps MP3. Mumbai (15 s) and London (17.44 s) preserve the shorter
available recording rather than manufacturing extra material. No synthesis,
layering of cities, denoising, time stretching or artificial traffic is used.
The excerpt plays once; it is not looped.

Playback levels are adjusted for comfortable listening. They do **not** support
scientific comparisons of sound pressure levels, noise exposure or city loudness.
Source microphones, placement, dates and mastering differ. Tokyo includes a
pedestrian signal and other street activity; other clips can include voices,
birds, wind or other incidental sounds alongside traffic.

The small waveform is drawn from actual Web Audio time-domain samples of the
currently playing file. It is flat while paused, muted or under reduced motion.
It is an audio signal visualization, not a decibel meter.

## Final global selection and source availability

The active order is Dhaka, New York City, Mumbai, London; Tokyo, Cairo, Bangkok,
Sydney; Istanbul, São Paulo, Johannesburg, Mexico City. Retired city assets are
kept only in an ignored local archive.

Sydney uses [City Street Weekend.aif](https://freesound.org/people/thefilmbakery/sounds/137835/)
by thefilmbakery ([CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)):
a Sydney shopping/cafe street with a bus and passing traffic. The recording street
and date are unknown; the map uses a documented representative center near Sydney
Town Hall. The first 25 seconds of its published HQ preview are processed with the
same conservative gain and encoding used for the other cities.

Johannesburg uses [Johannesburg_CBD](https://freesound.org/people/noisymichael/sounds/725158/)
by noisymichael ([CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)).
The binaural street walk includes traffic and taxi horns alongside hawkers and
generators; the creator condensed the original walk. The first 25 seconds are
processed through the existing pipeline. The representative map center is Gandhi
Square in the CBD, not a known microphone location or a reconstructed walking route.
The recording date and exact coordinates are unknown; its upload date is retained
separately. All twelve active cities now have verified reusable or permissioned audio.

The refined road style uses minor roads #B9BFBB at 0.9 SVG units and major roads
#87928F at 1.35 units. The ten retained cities' path coordinates are unchanged.
A selected-map equalizer and player waveform use actual Web Audio time-domain
samples. The player reports native media duration and current time, and its range
control seeks within that file. No animation runs while playback is paused,
muted, ended or unavailable, or when reduced motion is requested.
