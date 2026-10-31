# Map presentation

Day 1 uses a centered serif headline, a rust-colored italic phrase, and original
walking-person symbols over a muted OSM basemap. The subtitle states the count,
geography, and period. One symbol represents one crash; tooltips show Denver time.

- Overlay: `templates/story-panel.html`.
- Symbol: `assets/pedestrian.svg`.
- Renderer: `src/visualization/interactive.py`.
- Shared basemap style: `src/visualization/basemap.py`.

Keep source credits visible in browser screenshots. Review the map at the intended
capture size after all tiles have loaded. Future maps can adapt the layout to
their own story rather than repeat the same visual treatment.
