"""Package the reviewed HTML map for GitHub Pages without source data caches."""

import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]


def build(root: Path = ROOT, destination: Path | None = None) -> Path:
    destination = destination or root / "_site"
    source = root / "maps/day01-points"
    html = source / "map.html"
    qa = source / "map.qa.json"
    text = html.read_text()
    match = re.search(r"const jsonInput = (\{[\s\S]*?\n\});", text)
    if not match:
        raise ValueError("Generated map is missing deck.gl configuration; regenerate it first")
    config = json.loads(match[1])
    points = next(layer["data"] for layer in config["layers"] if layer["id"] == "crash-points")
    summary = json.loads(qa.read_text())
    if not points or len(points) != summary["mapped_incidents"]:
        raise ValueError("Map and QA counts disagree; regenerate both before publishing")
    for relative in ["index.html", "day01/index.html", "day01/map.qa.json", "day01/map.results.md"]:
        if (destination / relative).is_symlink():
            raise ValueError(f"Refusing to overwrite a symlink: {relative}")
    day = destination / "day01"
    day.mkdir(parents=True, exist_ok=True)
    # With only Day 1 complete, the site root opens that map directly.
    shutil.copyfile(html, destination / "index.html")
    shutil.copyfile(html, day / "index.html")
    shutil.copyfile(qa, day / "map.qa.json")
    report = (source / "map.results.md").read_text().replace("(map.html)", "(index.html)")
    (day / "map.results.md").write_text(report)
    (destination / ".nojekyll").touch()
    print(f"Packaged {len(points):,} crash events for Pages: {destination}")
    return destination


if __name__ == "__main__":
    build()
