# Day 12 — Power: The Pulse of Hoover Dam

[Open the map](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day12-power/).

What does the Southwest's hidden electrical infrastructure look like when it wakes up at night?

The full-bleed map opens over Hoover Dam and gently pulls back to the Southwest extent over exactly 10 seconds, then the camera settles. Hoover glows at 0.5–1 seconds, selected corridors illuminate outward over 1–4 seconds, and continuous GPU streaks and warm city lights appear over 2–3.5 seconds. The selected network is fully lit by 4.5 seconds, then motion continues. Pause and Replay control lighting and trails; manual pan/zoom takes over the camera, and Replay restarts the pullback. Reduced-motion visitors receive a static, illuminated map. Kingman retains a subtle city glow without a label.


The light represents an artistic pulse, **not measured electricity flow or verified Hoover delivery paths**. The grid is a September 2024 archive, not a live network. See [data sources and assumptions](DATA_SOURCES.md).

## Local preview

From the repository root:

```sh
python3 scripts/preview_map.py --directory maps/day12-power --port 8013 --no-browser
```

Open http://127.0.0.1:8013/map.html. Assets are local; no API key, tiles, backend, or build step is needed. A WebGL2 browser is required for particles; geographic lines remain available if particle initialization fails.

## Rebuild and review

```sh
python3 -m pip install -r maps/day12-power/requirements.txt
python3 maps/day12-power/prepare_data.py
python3 maps/day12-power/validate_data.py
node maps/day12-power/test_core.cjs
```

Raw downloads are cached under ignored `data/raw/day12/`. Reusing these caches preserves the exact inputs; fresh upstream downloads may change. Processed data and source hashes are in `data/`. Browser checks are at `/qa.html` on the preview server; review desktop, mobile, and reduced motion. This harness is excluded from the Pages package.

MapLibre GL JS 5.6.0 is vendored under its BSD license. The custom WebGL2 layer uses sampled real line geometry, additive bloom-like glows and continuous triangle-strip trails rather than a heavyweight postprocessing pipeline. Desktop renders 180 traveling streaks; phone layouts use 72. The static runtime uses only bundled assets.

To rebuild only the continuous background from existing caches, run `python3 maps/day12-power/prepare_context.py`. Transmission geometries and route samples are unchanged by this refinement. Worldwide land is generalized Natural Earth geometry; regional water and state lines retain whole shapes instead of a rectangular crop.

The final visual treatment restores the thinner 0.8 px active corridors, softer cyan glow, and restrained streaks while keeping the fast illumination. Light streaks move 20× the pre-speedup setting (50× the original soft-line speed).

Final polish: Lake Mead alone has a slightly brighter deep-blue fill; continuous active-line opacity is 18% higher, with thickness, bloom and particles unchanged. The dam marker uses the verified Bureau of Reclamation project reference; the original camera anchor is retained.
