# Shared day design

Status: initial visual direction approved by the user; iterative refinements are
being developed in Day 1. The original [synthetic preview](template-preview.html)
remains a design reference, not a data result.

## Common structure

1. Day/theme, geography, title, and one-sentence framing.
2. A clear legend; keep detailed metrics in the documentation.
3. A full-screen map with a minimal headline, severity legend, and source credits.
4. An evidence-based finding, methods, limitations, and reproduction commands.
5. Source, date coverage, retrieval date, license, CRS, tools, and AI disclosure.
6. A shareable HTML map and source code. Capture social images in the browser.

No separate PNG generation is required under the user's revised workflow.
Day 30 remains a physical drawing, photographed or scanned by the user.

## Visual language

Warm paper (#f5f1e8), dark ink (#24343c), teal (#087f8c), and rust (#bb3f30).
Consistent typography, spacing, attribution, and severity hierarchy. Day-specific
palettes and layers can vary with the analysis.

## Reuse

The current minimal map overlay is in `templates/interactive-panel.html` and its
export helper is in `src/visualization/interactive.py`. Analysis stays separate
from presentation. Future days can reuse the design without copying whole apps.
Large GPS datasets will need aggregation or tiled delivery instead of embedding
millions of raw points. The HTML loads rendering JavaScript and basemap tiles online.

## Hosting

GitHub Pages is the planned host; see [hosting notes](HOSTING.md). No public site
or remote repository has been created in this workspace yet.

Latest user direction: remove on-map counts, explanatory paragraphs, and AI
disclosure. Retain attribution; document methods and AI assistance in README files.

Current Day 1 refinements: a narrower title card near the top edge; a scope subtitle;
a quieter grayscale basemap; 4.5-pixel serious-injury and 7.5-pixel fatal markers;
a thin light outline; and an involvement selector instead of an additional shape
encoding. Keep actual provider credit and the severe-crash scope in the footer.
