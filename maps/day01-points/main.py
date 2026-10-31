"""Export the interactive Day 1 map, QA summary, and annual results."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.analysis.crashes import CACHE_PREFIX, prepare_crashes
from src.data.download import write_json


def render(source: Path | list[Path], year: int | tuple[int, int], output: Path, edition: str = 'analysis') -> dict:
    if output.suffix.lower() != ".html":
        raise ValueError("Map output must be an .html file; screenshots are captured in the browser")
    start, end = (year, year) if isinstance(year, int) else year
    period_label = str(start) if start == end else f"{start}–{end}"
    sources = [source] if isinstance(source, Path) else source
    if len(sources) != end - start + 1:
        raise ValueError("Provide one complete snapshot per requested calendar year")
    payload = {"spatialReference": {"wkid": 4326}, "features": []}
    inputs = []
    for source_year, path in zip(range(start, end + 1), sources):
        snapshot = json.loads(path.read_text())
        # Validate each year's declared CRS and dates before combining files.
        prepare_crashes(snapshot, source_year)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path = path.with_name(f"{CACHE_PREFIX}-manifest-{source_year}.json")
        retrieved = "not recorded (imported snapshot)"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            if manifest.get("sha256") != digest or manifest.get("year") != source_year:
                raise ValueError("Input checksum/year does not match its download manifest")
            retrieved = manifest["retrieved_at"]
        inputs.append({"year": source_year, "sha256": digest, "retrieved_at": retrieved})
        payload["features"].extend(snapshot["features"])
    points, stats = prepare_crashes(payload, year)
    if edition == 'story':
        from src.analysis.pedestrian_story import select_story_crashes
        points, stats = select_story_crashes(points, stats)
    stats["inputs"] = inputs
    retrieved = inputs[-1]["retrieved_at"]
    stats["input_sha256"] = inputs[0]["sha256"] if len(inputs) == 1 else {str(i["year"]): i["sha256"] for i in inputs}
    stats["retrieved_at"] = retrieved
    from src.visualization.interactive import export_crash_html
    export_crash_html(points, period_label, output, edition=edition)
    write_json(output.with_suffix(".qa.json"), stats)
    results = output.with_suffix(".results.md")
    results.write_text(
        f"# Day 1 — {period_label} results\n\n[Explore the interactive crash map]({output.name})\n\n"
        f"{stats['mapped_incidents']:,} unique events passed validation: "
        f"{stats['fatal_crashes']:,} fatal crashes and "
        f"{stats['serious_injury_only_crashes']:,} serious-injury crashes without a recorded fatality.\n\n"
        f"Pedestrian involvement: {stats['pedestrian_involved_crashes']:,}; "
        f"bicycle involvement: {stats['bicycle_involved_crashes']:,}; "
        f"both: {stats['both_modes_crashes']:,}. Events involving both modes are counted once overall.\n\n"
        "Severity applies to the crash; involvement flags do not identify who was injured. "
        "These are crash counts, not numbers of injured or killed people. "
        "Source coverage is unverified; these counts are not a complete annual crash total. "
        "No exposure-adjusted risk or statistical hotspot inference is made. See the adjacent QA JSON for exclusions "
        "and the input checksum; see README.md for methods and licensing.\n\n"
        "Severity uses positive injury counts or explicit FATAL/SBI offense labels; "
        "offense labels do not supply missing person counts.\n\n"
        "| Year | Mapped crashes | Fatal | Serious injury only |\n"
        "| --- | ---: | ---: | ---: |\n" +
        "\n".join(f"| {r['year']} | {r['mapped_incidents']} | {r['fatal_crashes']} | {r['serious_injury_only_crashes']} |"
                  for r in stats["annual_counts"]) + "\n")
    if edition == 'story':
        results.write_text(
            f'# Someone Was Walking Here\n\n[Explore the map]({output.name})\n\n'
            f'Fatal crashes involving pedestrians · Denver · {period_label}.\n\n'
            f'{len(points):,} unique mapped fatal crash events involve pedestrians. '
            'One walking-person symbol represents one crash, not one pedestrian death. '
            'The current records do not establish which person died.\n\n'
            'The original walking-person SVG is embedded in the HTML with a light halo. '
            'Occurrence times use America/Denver, labeled MST or MDT. Symbols are '
            'anchored at the recorded location; overlapping events can hide one another.\n\n'
            '| Year | Mapped fatal crashes involving pedestrians |\n| --- | ---: |\n' +
            '\n'.join(f"| {r['year']} | {r['mapped_incidents']} |" for r in stats['annual_counts']) +
            '\n\nSource: City of Denver Open Data Catalog · CC BY 3.0. '
            'AI-assisted analysis and original SVG/cartographic design. '
            'See README.md and the adjacent QA JSON for selection and limitations.\n')
    print(json.dumps(stats, indent=2))
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--start-year", type=int)
    parser.add_argument("--end-year", type=int)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--edition", choices=['story', 'analysis'], default='story')
    # Keep previously documented commands compatible; HTML is always the output.
    parser.add_argument("--interactive", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--html-only", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("map.html"))
    args = parser.parse_args()
    try:
        if (args.start_year is None) != (args.end_year is None):
            raise ValueError("Provide both --start-year and --end-year")
        year = args.year
        if args.start_year is not None:
            if args.input or args.start_year > args.end_year:
                raise ValueError("Year ranges require ordered years and the default annual cache files")
            year = (args.start_year, args.end_year)
            source = [ROOT / f"data/raw/day01/{CACHE_PREFIX}-{y}.json"
                      for y in range(args.start_year, args.end_year + 1)]
        else:
            source = args.input or ROOT / f"data/raw/day01/{CACHE_PREFIX}-{args.year}.json"
        missing = [p for p in (source if isinstance(source, list) else [source]) if not p.exists()]
        if missing:
            raise ValueError(f"Missing snapshots: {', '.join(p.name for p in missing)}. Run download_data.py first.")
        render(source, year, args.output, edition=args.edition)
    except (ValueError, KeyError, RuntimeError) as exc:
        parser.exit(1, f"Map generation stopped: {exc}\n")
