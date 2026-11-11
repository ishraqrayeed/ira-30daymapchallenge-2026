# Day 11 — Sound

## The World in Traffic

**12 cities. 12 streets. 12 soundscapes.** A gallery of circular OpenStreetMap
street networks and authentic city field recordings. Every circle is 2 km across,
north up. Choose a city to listen; choose it again to pause or resume.

```sh
python3 scripts/preview_map.py --directory maps/day11-sound --port 8012
```

Open http://127.0.0.1:8012/map.html. Static HTML, CSS and vanilla JavaScript;
no live basemap, paid key, backend, build step or autoplay. Processed maps and audio
are local. Headphones recommended at a comfortable volume.

[Sources, rights and methods](DATA_SOURCES.md) · [Recording manifest](recordings.json)

## Rebuild

Install Python dependencies from `requirements.txt` in a virtual environment;
install FFmpeg and yt-dlp for audio. From the repository root:

```sh
python3 maps/day11-sound/build_streets.py
python3 maps/day11-sound/process_audio.py
python3 maps/day11-sound/validate.py
```

OSM downloads and source audio are cached in ignored `data/day11-traffic/`.
Reusing the cache reproduces the original snapshot; fresh OSM downloads can differ.
All twelve cities have audio. Johannesburg uses a verified CC0 street recording
by noisymichael. Dhaka's permission is recorded
in the manifest; the eleven other recordings are CC0 or CC BY. Freesound inputs
are published HQ previews, not original masters.
Mumbai and London are shorter than 20 seconds because their source recordings are.
Normalized playback is not a measurement of real-world sound pressure.

The selected-city player supports seeking, pause/resume and mute. A small
waveform and selected-map equalizer use real audio samples, and stop when paused
or under reduced motion. Desktop maps are approximately 13% larger where height permits; compact laptop
layouts scale the grid to the available browser height so the player also fits. See `qa-review.json` for observed checks.

Public route: https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day11-sound/
