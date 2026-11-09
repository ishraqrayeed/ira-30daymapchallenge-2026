"""Package the reviewed HTML map for GitHub Pages without source data caches."""

import json
from pathlib import Path
import re
import shutil
import hashlib

ROOT = Path(__file__).resolve().parents[1]

DAY3_FILES = ('poster.html', 'README.md', 'map.qa.json', 'map.results.md',
              'context.qa.json', 'config.json', 'context-config.json',
              'source-manifest.json', 'boundary-source.json',
              'farmgate_15min.geojson', 'farmgate_30min.geojson', 'farmgate_45min.geojson',
              'farmgate_accessibility.geojson', 'farmgate_display_bands.geojson',
              'dhaka_mrt6_stations.csv', 'dhaka_mrt6_stations.geojson',
              'estimated_rail_segments.csv', 'dhaka_city_boundary.geojson',
              'dhaka_city_corporations.geojson', 'dhaka_city_geofence.geojson',
              'dhaka_labels.geojson')


DAY4_FILES = ('README.md', 'map.qa.json', 'map.results.md', 'config.json',
              'source-manifest.json', 'record-review.json', 'visual-review.json', 'day04_audit.json',
              'analysis.json', 'dbscan_parameter_sweep.csv',
              'manhattan_halal_locations.csv', 'manhattan_halal_locations.geojson',
              'manhattan_halal_clusters.geojson', 'manhattan_boundary.geojson',
              'poc.html', 'poc.qa.json')


DAY5_FILES = ('poster.html', 'README.md', 'map.qa.json', 'layout.qa.json',
              'analysis.json', 'source-manifest.json', 'map.results.md')


DAY6_FILES = ('README.md', 'source-manifest.json', 'data-audit.json',
              'survey-review.json', 'label-evidence.json', 'final-polish.qa.json', 'map.qa.json', 'validation.json', 'visual-review.json',
              'web-data.qa.json', 'web.qa.json', 'highres-export.qa.json', 'linkedin-export.qa.json')


DAY6_WEB_FILES = ('web/map-data.json', 'web/style.css', 'web/map-controls.js', 'web/app.js',
                  'web/vendor/leaflet.js', 'web/vendor/leaflet.css', 'web/vendor/LEAFLET-LICENSE.txt')
DAY6_EXPORTS = ('exports/day06_telluride.png', 'exports/day06_telluride_linkedin.png',
                'exports/day06_telluride_3000x3750.png')


def day6_artifacts(root: Path) -> Path | None:
    source = root / 'maps/day06-vintage'
    if not (source / 'exports/day06_telluride.png').exists():
        return None
    qa = json.loads((source / 'validation.json').read_text())
    layout = json.loads((source / 'map.qa.json').read_text())
    if not qa['passed'] or not qa['all_print_layers_vector'] or qa['archival_rasters_used']:
        raise ValueError('Day 6 vector map validation failed')
    if hashlib.sha256((source / 'exports/day06_telluride.png').read_bytes()).hexdigest() != layout['png_sha256']:
        raise ValueError('Day 6 poster changed after QA')
    web = json.loads((source / 'web.qa.json').read_text())
    if not web['automated_checks_passed']:
        raise ValueError('Day 6 interactive checks failed')
    for name, digest in web['asset_sha256'].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Day 6 browser asset changed after QA: {name}')
    for name in ('map.html', *DAY6_FILES, *DAY6_WEB_FILES, *DAY6_EXPORTS):
        if not (source / name).is_file():
            raise ValueError(f'Day 6 artifact missing: {name}')
    return source


def day5_artifacts(root: Path) -> tuple[Path, dict] | None:
    source = root / 'maps/day05-sight'
    if not (source / 'map.html').exists():
        return None
    qa = json.loads((source / 'layout.qa.json').read_text())
    if not qa.get('publication_authorized'):
        raise ValueError('Day 5 publication has not been authorized')
    data = None
    for name in ('map.html', *DAY5_FILES):
        if not (source / name).is_file():
            raise ValueError(f'Day 5 artifact missing: {name}')
    for name, digest in qa['release_sha256'].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Day 5 artifact changed after QA: {name}')
    for name in ('map.html',):
        match = re.search(r'const MAP_DATA=(\{[^\n]+\});', (source / name).read_text())
        if not match:
            raise ValueError(f'Day 5 embedded events missing: {name}')
        embedded = json.loads(match[1])
        if data is not None and embedded != data:
            raise ValueError('Day 5 embedded data disagree')
        data = embedded
        if len(data['shots']) != qa['markers'] or len({s['source_event_id'] for s in data['shots']}) != qa['markers']:
            raise ValueError('Day 5 event count or identifiers disagree')
        if sum(s['is_goal'] for s in data['shots']) != data['summary']['goals']:
            raise ValueError('Day 5 goal count disagrees')
    return source, data


def day4_artifacts(root: Path) -> tuple[Path, dict] | None:
    source = root / 'maps/day04-clusters'
    if not (source / 'map.qa.json').exists():
        return None
    qa = json.loads((source / 'map.qa.json').read_text())
    for field in ('all_points_match_dataset', 'all_points_in_manhattan',
                  'explicit_halal_evidence_all_locations',
                  'dbscan_recomputed_projected_metres',
                  'all_envelopes_valid_and_cover_members', 'labels_match_clusters'):
        if not qa[field]:
            raise ValueError(f'Day 4 QA failed: {field}')
    for name, digest in {**qa['artifact_sha256'], 'map.html': qa['html_sha256'],
                         'config.json': qa['config_sha256']}.items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Day 4 changed after QA: {name}')
    match = re.search(r'const MAP_DATA=(\{[^\n]+\});', (source / 'map.html').read_text())
    if not match:
        raise ValueError('Day 4 embedded data missing')
    data = json.loads(match[1])
    if data['stats'] != qa['statistics'] or len(data['points']) != qa['locations']:
        raise ValueError('Day 4 map and QA disagree')
    for name in DAY4_FILES:
        if not (source / name).is_file():
            raise ValueError(f'Day 4 public artifact missing: {name}')
    return source, data


def day3_artifacts(root: Path) -> tuple[Path, dict] | None:
    source = root / 'maps/day03-polygons'
    if not (source / 'map.html').exists():
        return None
    qa = json.loads((source / 'map.qa.json').read_text())
    context = json.loads((source / 'context.qa.json').read_text())
    if not qa['nested'] or not qa['valid_geometries']:
        raise ValueError('Day 3 accessibility QA failed')
    for filename, recorded in [('config.json', qa['config_sha256']),
                               ('context-config.json', context['context_config_sha256']),
                               ('farmgate_accessibility.geojson', context['cumulative_isochrone_sha256'])]:
        if hashlib.sha256((source / filename).read_bytes()).hexdigest() != recorded:
            raise ValueError('Day 3 data or configuration changed after QA')
    for filename in ['map.html', 'poster.html']:
        match = re.search(r'const MAP_DATA=(\{[^\n]+\});', (source / filename).read_text())
        if not match:
            raise ValueError('Day 3 is missing embedded map data')
        data = json.loads(match[1])
        if data['stats'] != qa['statistics'] or data['city_percentage'] != context['percentage_45min']:
            raise ValueError('Day 3 poster and calculated statistics disagree')
    if abs(context['intersection_45min_km2'] / context['city_area_km2'] * 100 - context['percentage_45min']) > 1e-9:
        raise ValueError('Day 3 city percentage balance failed')
    for name in DAY3_FILES:
        if not (source / name).is_file():
            raise ValueError(f'Day 3 public artifact is missing: {name}')
    return source, data


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
    third_day = day3_artifacts(root)
    fourth_day = day4_artifacts(root)
    fifth_day = day5_artifacts(root)
    sixth_day = day6_artifacts(root)
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
    if third_day:
        for name in ('', 'index.html', *DAY3_FILES):
            if (destination / 'day03-polygons' / name).is_symlink():
                raise ValueError(f'Refusing to overwrite a Day 3 symlink: {name}')
    if fourth_day:
        for name in ('', 'index.html', *DAY4_FILES):
            if (destination / 'day04-clusters' / name).is_symlink():
                raise ValueError(f'Refusing to overwrite a Day 4 symlink: {name}')
    if fifth_day:
        for name in ('', 'index.html', 'interactive.html', *DAY5_FILES):
            if (destination / 'day05-sight' / name).is_symlink():
                raise ValueError(f'Refusing to overwrite a Day 5 symlink: {name}')
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
    if third_day:
        source3, _ = third_day
        day3 = destination / 'day03-polygons'
        day3.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source3 / 'map.html', day3 / 'index.html')
        for name in DAY3_FILES:
            if name.endswith('.md'):
                (day3 / name).write_text((source3 / name).read_text().replace('(map.html)', '(index.html)'))
            else:
                shutil.copyfile(source3 / name, day3 / name)
        print('Packaged Day 3 metro accessibility, poster and public polygon data')
    if fourth_day:
        source4, data4 = fourth_day
        day4 = destination / 'day04-clusters'
        day4.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source4 / 'map.html', day4 / 'index.html')
        for name in DAY4_FILES:
            if name.endswith('.md'):
                (day4 / name).write_text((source4 / name).read_text().replace('(map.html)', '(index.html)'))
            else:
                shutil.copyfile(source4 / name, day4 / name)
        print(f"Packaged {len(data4['points'])} Day 4 halal food locations")
    if fifth_day:
        source5, data5 = fifth_day
        day5 = destination / 'day05-sight'
        day5.mkdir(parents=True, exist_ok=True)
        # One compact map; preserve old published URLs as redirects.
        shutil.copyfile(source5 / 'map.html', day5 / 'index.html')
        redirect = '<!doctype html><html lang="en"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=./"><title>What Messi Saw</title><a href="./">Open the map</a></html>\n'
        (day5 / 'interactive.html').write_text(redirect)
        for name in DAY5_FILES:
            if name == 'poster.html':
                (day5 / name).write_text(redirect)
            elif name.endswith('.md'):
                (day5 / name).write_text((source5 / name).read_text().replace('(map.html)', '(index.html)'))
            else:
                shutil.copyfile(source5 / name, day5 / name)
        print(f"Packaged {len(data5['shots'])} Day 5 shots and the approved portrait")
    if sixth_day:
        day6 = destination / 'day06-vintage'
        for name in ('', 'index.html', *DAY6_FILES, *DAY6_WEB_FILES, *DAY6_EXPORTS):
            if (day6 / name).is_symlink():
                raise ValueError(f'Refusing to overwrite a Day 6 symlink: {name}')
        day6.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(sixth_day / 'map.html', day6 / 'index.html')
        for name in (*DAY6_FILES, *DAY6_WEB_FILES, *DAY6_EXPORTS):
            (day6 / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(sixth_day / name, day6 / name)
        print('Packaged Day 6 interactive vector atlas and 11.25 MP print export')
    source7 = root / 'maps/day07-10-minute'
    if (source7 / 'map.html').is_file():
        day7 = destination / 'day07-10-minute'
        for name in ('', 'index.html', 'day7.png', 'README.md'):
            if (day7 / name).is_symlink():
                raise ValueError(f'Refusing to overwrite a Day 7 symlink: {name}')
        day7.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source7 / 'map.html', day7 / 'index.html')
        for name in ('day7.png', 'README.md'):
            shutil.copyfile(source7 / name, day7 / name)
        print('Packaged Day 7 approved screenshot and supplied caption')
    source8 = root / 'maps/day08-utopia'
    if (source8 / 'map.html').is_file():
        qa8 = json.loads((source8 / 'map.qa.json').read_text())
        if not qa8['passed'] or qa8['network_components'] != 1:
            raise ValueError('Day 8 network validation failed')
        day8 = destination / 'day08-utopia'
        files8 = ('map.html', 'poster.png', 'poster.svg', 'poster.html', 'poster-export.json', 'day08-utopia-final.png',
                  'poster-offsets.json', 'poster-layout.qa.json', 'README.md', 'map.qa.json',
                  'source-manifest.json', 'benchmark.json', 'stations.geojson', 'routes.geojson',
                  'existing-stations.geojson', 'existing-routes.geojson', 'context.geojson', 'boundaries.geojson',
                  'study-region.geojson', 'streets.geojson', 'basemap-water.geojson',
                  'basemap-highways.geojson', 'web.qa.json', 'explorer.js')
        for name in ('', 'index.html', *files8):
            if (day8 / name).is_symlink():
                raise ValueError(f'Refusing to overwrite a Day 8 symlink: {name}')
        day8.mkdir(parents=True, exist_ok=True)
        for name in files8:
            shutil.copyfile(source8 / name, day8 / ('index.html' if name == 'map.html' else name))
        print('Packaged Day 8 fictional DFW subway and poster')
    source9 = root / 'maps/day09-urban-rural'
    if (source9 / 'map.html').is_file():
        day9 = destination / 'day09-urban-rural'
        files9 = ('map.html', 'app.js', 'cinematic-core.js', 'style.css', 'README.md',
                  'source-manifest.json', 'qa-review.json', 'elevation-check.json',
                  'data/nasa-blue-marble.jpg', 'data/history.json',
                  'data/history-footprints.geojson', 'data/history-changes.geojson',
                  *(str(p.relative_to(source9)) for p in sorted((source9 / 'data/history').glob('*.png'))))
        for name in ('', 'index.html', 'data', *files9):
            if (day9 / name).is_symlink():
                raise ValueError(f'Refusing to overwrite a Day 9 symlink: {name}')
        for name in files9:
            if not (source9 / name).is_file():
                raise ValueError(f'Day 9 artifact missing: {name}')
        day9.mkdir(parents=True, exist_ok=True)
        for name in files9:
            target9 = day9 / ('index.html' if name == 'map.html' else name)
            target9.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source9 / name, target9)
        print('Packaged Day 9 Cesium landscape and processed GIS layers')
    (destination / ".nojekyll").touch()
    print(f"Packaged {len(points):,} crash events for Pages: {destination}")
    return destination


if __name__ == "__main__":
    build()
