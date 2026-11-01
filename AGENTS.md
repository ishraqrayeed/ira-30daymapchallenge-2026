# Working in this repository

Read `README.md`, `docs/WORKFLOW.md`, and the target day's README before starting.
`PLAN.md` lists the official themes; `docs/DESIGN.md` records the current visual
direction. Work on the requested day only.

- Start with a geographic question and a story. Give each map personality while
  keeping the interpretation supported by the data. Treat fatal crashes respectfully.
- Use public/open data with source attribution, terms, coverage dates, and QA.
  Distinguish crash events, people, involvement flags, and injury outcomes.
- Primary output is interactive HTML. The user takes browser screenshots; do not
  add a separate PNG export. Keep the map itself minimal and documentation concise.
- Reuse the rendering, basemap, and data utilities where appropriate. Day 1's
  walking symbols and headline are specific to its story, not a universal template.
- Preview over local HTTP with `scripts/preview_map.py`. OSM requests from direct
  `file://` previews have previously been blocked. Keep attribution visible.
- Preserve published day URLs. Add each finished day to the portfolio index and
  Pages packager; do not overwrite an earlier day's map to publish a new one.
- Test data selection and interactive behavior. Visually review desktop and mobile;
  export validation alone cannot confirm that browser symbols rendered correctly.
- Keep source caches, credentials, and `.local-notes/` out of Git. Record brief AI
  assistance disclosure in the day's documentation, not in the map overlay.
- Publish only when requested. Draft social posts when asked; do not post them.
- Check actual Git/network access before deployment. This environment has previously
  blocked Git metadata writes and outbound requests. A DNS failure is not evidence
  of invalid GitHub credentials. If blocked, finish local work and provide the
  existing terminal publishing command rather than claiming deployment succeeded.

Current checkpoint: Day 1, **Someone Was Walking Here**, is finished and the user
reports publishing it. Day 2, **Every Line a Climb**, is implemented: a circular
Rocky Mountain National Park trail map, approved for publication. Preserve both
days; do not restart Day 1 or recreate its old map. See `docs/WORKFLOW.md`.
