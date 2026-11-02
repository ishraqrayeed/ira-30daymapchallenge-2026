# GitHub Pages

- [Portfolio](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/)
- [Day 1 — Points](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day01-points/)
- [Day 2 — Lines](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day02-lines/)
- [Day 3 — Polygons](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day03-polygons/)
- [Day 4 — Clusters](https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day04-clusters/)
- [Repository](https://github.com/ishraqrayeed/ira-30daymapchallenge-2026)

## Publish an update

```sh
bash scripts/publish_github.sh
```

The script checks the map, commits the project changes, pushes to `main`, and
runs the Pages workflow. It waits for the deployment result. If authentication
is needed, sign in as `ishraqrayeed`:

```sh
gh auth login --hostname github.com --web --git-protocol https --scopes repo,workflow
```

`scripts/build_pages.py` packages only the generated HTML and reports in `_site`.
The root is a map index; Day 1 lives at `/day01-points/`. The earlier `/day01/`
address redirects there. Raw data caches are not published.
Day 2 lives at `/day02-lines/`; its HTML includes the terrain and trail data.

After deployment, check the symbols, basemap, Denver-time tooltips, attribution,
and mobile layout at the public URL. Updates are manually triggered, so pushing
an edit alone does not publish it.

Day 3 lives at `/day03-polygons/`, with a static `poster.html` view, public
accessibility polygons, station data, municipal boundaries and methodology notes.

Day 4 lives at `/day04-clusters/`: the minimal interactive Manhattan halal-food
cluster map, with sourced processed data and analysis reports packaged separately.
