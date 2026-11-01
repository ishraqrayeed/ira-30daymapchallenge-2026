"""Package the reviewed HTML map for GitHub Pages without source data caches."""

import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]


def day2_artifacts(root: Path) -> tuple[Path, dict] | None:
    source = root / "maps/day02-lines"
    if not (source / "map.html").exists():
        return None
    match = re.search(r"const MAP_DATA = (\{[^\n]+\});", (source / "map.html").read_text())
    if not match:
        raise ValueError("Day 2 is missing its embedded trail data")
    data = json.loads(match[1])
    qa = json.loads((source / "map.qa.json").read_text())
    trails = data["trails"]
    if not trails or len(trails) != qa["mapped_segments"] or data["totals"] != qa["totals"]:
        raise ValueError("Day 2 map and QA disagree; regenerate both")
    if len({t["id"] for t in trails}) != len(trails):
        raise ValueError("Duplicate Day 2 segment identifiers")
    if sum(len(t["points"]) for t in trails) != qa["elevation_samples"]:
        raise ValueError("Day 2 sample count disagrees with QA")
    return source, data


def build(root: Path = ROOT, destination: Path | None = None) -> Path:
    destination = destination or root / "_site"
    second_day = day2_artifacts(root)
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
    for relative in ["index.html", "day01/index.html", "day01/map.qa.json", "day01/map.results.md",
                     "day01-points/index.html", "day01-points/map.qa.json", "day01-points/map.results.md"]:
        if (destination / relative).is_symlink():
            raise ValueError(f"Refusing to overwrite a symlink: {relative}")
    day = destination / "day01-points"
    if second_day:
        for relative in ["day02-lines", "day02-lines/index.html", "day02-lines/map.qa.json",
                         "day02-lines/map.results.md", "day02-lines/README.md"]:
            if (destination / relative).is_symlink():
                raise ValueError(f"Refusing to overwrite a symlink: {relative}")
    day.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / "templates/portfolio-index.html", destination / "index.html")
    shutil.copyfile(html, day / "index.html")
    shutil.copyfile(qa, day / "map.qa.json")
    report = (source / "map.results.md").read_text().replace("(map.html)", "(index.html)")
    (day / "map.results.md").write_text(report)
    # Preserve previously shared Day 1 URLs, while using the named theme path.
    previous = destination / "day01"
    previous.mkdir(parents=True, exist_ok=True)
    (previous / "index.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0;url=../day01-points/">'
        '<title>Day 1 — Points</title></head><body>'
        '<a href="../day01-points/">Open Day 1 — Points</a></body></html>')
    shutil.copyfile(qa, previous / "map.qa.json")
    (previous / "map.results.md").write_text(report)
    if second_day:
        source2, data2 = second_day
        day2 = destination / "day02-lines"
        day2.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source2 / "map.html", day2 / "index.html")
        shutil.copyfile(source2 / "map.qa.json", day2 / "map.qa.json")
        shutil.copyfile(source2 / "README.md", day2 / "README.md")
        report2 = (source2 / "map.results.md").read_text().replace("(map.html)", "(index.html)")
        (day2 / "map.results.md").write_text(report2)
        print(f'Packaged {len(data2["trails"]):,} Day 2 trail segments')
    (destination / ".nojekyll").touch()
    print(f"Packaged {len(points):,} crash events for Pages: {destination}")
    return destination


if __name__ == "__main__":
    build()
