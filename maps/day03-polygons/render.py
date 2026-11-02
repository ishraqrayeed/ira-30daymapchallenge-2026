"""Build self-contained SVG/HTML: interactive map and static poster view."""
import hashlib
import html
import json
from pathlib import Path
from pyproj import Transformer
from shapely.geometry import shape, box, Point, mapping
from shapely.ops import transform, unary_union
from shapely import make_valid
from prepare_context import fill_small_holes

DAY = Path(__file__).resolve().parent


def parts(geometry):
    if geometry.geom_type in ['Polygon', 'LineString']:
        yield geometry
    elif hasattr(geometry, 'geoms'):
        for child in geometry.geoms:
            yield from parts(child)


def main():
    report = json.loads((DAY / 'map.qa.json').read_text())
    context_qa = json.loads((DAY / 'context.qa.json').read_text())
    design = context_qa['context_config']
    if context_qa['context_config_sha256'] != hashlib.sha256((DAY / 'context-config.json').read_bytes()).hexdigest():
        raise ValueError('Context design is stale')
    colors = {int(k): v for k, v in design['colors'].items()}
    if not report['nested'] or not report['valid_geometries']:
        raise ValueError('Analysis QA blocks rendering')
    if report['config_sha256'] != hashlib.sha256((DAY / 'config.json').read_bytes()).hexdigest():
        raise ValueError('Analysis is stale')
    project = Transformer.from_crs(4326, report['config']['crs'], always_xy=True).transform
    features = json.loads((DAY / 'farmgate_accessibility.geojson').read_text())['features']
    geoms = {f['properties']['minutes']: transform(project, shape(f['geometry'])) for f in features}
    for f in features:
        if abs(geoms[f['properties']['minutes']].area / 1e6 - f['properties']['area_km2']) > 1e-8:
            raise ValueError('GeoJSON area and analysis disagree')
    if context_qa['cumulative_isochrone_sha256'] != hashlib.sha256((DAY / 'farmgate_accessibility.geojson').read_bytes()).hexdigest():
        raise ValueError('City-overlap calculation is stale')
    city = transform(project, shape(json.loads((DAY / 'dhaka_city_geofence.geojson').read_text())['features'][0]['geometry']))
    extent = city.union(geoms[45]).bounds
    xmin, ymin, xmax, ymax = extent
    factor = 1000 / (ymax - ymin)
    width, height = (xmax - xmin) * factor + 90, 1080

    def screen(x, y, z=None):
        return (x - xmin) * factor + 45, (ymax - y) * factor + 40

    def path(geometry, tolerance=0):
        if tolerance:
            geometry = geometry.simplify(tolerance, preserve_topology=True)
        result = []
        for p in parts(transform(screen, geometry)):
            if p.geom_type == 'LineString':
                result.append('M' + 'L'.join(f'{x:.2f},{y:.2f}' for x, y in p.coords))
            else:
                for ring in [p.exterior, *p.interiors]:
                    result.append('M' + 'L'.join(f'{x:.2f},{y:.2f}' for x, y in ring.coords) + 'Z')
        return ''.join(result)

    context = json.loads((DAY / 'map-context.geojson').read_text())['features']
    context = {f['properties']['kind']: transform(project, shape(f['geometry'])) for f in context}
    visible_water = unary_union([p for p in parts(context['water']) if p.area >= design['display_preserve_water_above_m2']]).intersection(box(xmin-1000, ymin-1000, xmax+1000, ymax+1000))
    svg = [f'<svg id="map" viewBox="0 0 {width:.3f} {height}" role="img" aria-labelledby="map-title map-desc">',
           '<title id="map-title">Metro and walking accessibility from Farmgate, Dhaka</title>',
           '<desc id="map-desc">Teal travel-time bands from Farmgate, with a separate smooth outline of Dhaka North and South city corporations. Small gaps are generalized for display. Coral marks operating MRT Line 6. Estimated travel times, not timetable-specific journeys.</desc>',
           f'<path class="city-boundary" d="{path(city)}"><title>Dhaka city · DNCC + DSCC · generalized outline</title></path>',
           f'<path class="water" d="{path(visible_water, 15)}"/>']
    # Display simplification is at most 10 m; union of smaller bands preserves
    # nesting. Area statistics always come from the full analytical geometry.
    display = {}
    for minutes in [15, 30, 45]:
        smaller = display.get(minutes - 15)
        g = fill_small_holes(geoms[minutes], design['display_fill_holes_below_m2']).difference(visible_water)
        g = g.simplify(design['display_isochrone_simplification_m'], preserve_topology=True)
        display[minutes] = g.union(smaller) if smaller is not None else g
    bands = {15: display[15], 30: display[30].difference(display[15]), 45: display[45].difference(display[30])}
    for minutes in [45, 30, 15]:
        svg.append(f'<path class="catchment band-{minutes}" data-minutes="{minutes}" fill="{colors[minutes]}" d="{path(bands[minutes])}" fill-rule="evenodd"><title>Travel-time band ending at {minutes} minutes</title></path>')
    svg.append(f'<path class="metro" d="{path(context["metro"])}"/>')
    stations = json.loads((DAY / 'dhaka_mrt6_stations.geojson').read_text())['features']
    for f in stations:
        s = f['properties']
        x, y = screen(*project(*f['geometry']['coordinates']))
        name = html.escape(s['station_name'])
        origin = s['station_name'] == report['origin']
        svg.append(f'<circle class="station {"origin" if origin else ""}" data-station="{name}" cx="{x:.2f}" cy="{y:.2f}" r="{5 if origin else 2}"><title>{name} · {s["metro_minutes_from_farmgate"]:.1f} estimated metro minutes from Farmgate</title></circle>')
        if origin:
            svg.append(f'<path class="leader" d="M{x-10:.2f},{y:.2f}h-28"/><text class="origin-label" x="{x-48:.2f}" y="{y+5:.2f}" text-anchor="end">FARMGATE</text>')
    anchors = json.loads((DAY / 'dhaka_labels.geojson').read_text())['features']
    for f in anchors:
        name = f['properties']['name']
        if name in ['Farmgate', 'Agargaon']:
            continue
        x, y = screen(*project(*f['geometry']['coordinates']))
        west = name in ['Mirpur', 'Agargaon', 'Dhanmondi']
        svg.append(f'<text class="end-label" x="{x + (-12 if west else 12):.2f}" y="{y-8:.2f}" text-anchor="{"end" if west else "start"}">{html.escape(name)}</text>')
    svg.append('</svg>')
    stats = {s['minutes']: s for s in report['statistics']}
    payload = {'origin': report['origin'], 'thresholds': [15, 30, 45],
               'stats': report['statistics'], 'scale2km': 2000 * factor,
               'width': width, 'height': height, 'stations': [s['properties'] for s in stations],
               'city_percentage': context_qa['percentage_45min'], 'colors': colors, 'display_mode': 'exclusive bands',
               'display_holes_filled_below_m2': design['display_fill_holes_below_m2']}
    template = (DAY / 'template.html').read_text()
    replacements = {'__MAP_SVG__': ''.join(svg), '__CITY_PERCENT__': f'{context_qa["percentage_45min"]:.0f}',
                    '__CITY_AREA__': f'{context_qa["city_area_km2"]:.2f}',
                    '__CITY_PRECISE__': f'{context_qa["percentage_45min"]:.6f}',
                    '__MAP_DATA__': json.dumps(payload, separators=(',', ':')).replace('<', '\\u003c'),
                    '__SNAPSHOT__': report['source']['snapshot']['osmosis_replication_timestamp'][:10]}
    for key, value in replacements.items():
        template = template.replace(key, value)
    for minutes, color in colors.items():
        template = template.replace(f'__COLOR_{minutes}__', color)
    inverse = Transformer.from_crs(32646, 4326, always_xy=True).transform
    display_features = []
    for m in [15, 30, 45]:
        # Nonlinear reprojection can flip point-touching display-ring junctions.
        # A 1 mm export-only inset separates them; analytical polygons, plotted
        # SVG bands and all reported areas remain completely unchanged.
        export_geometry = make_valid(transform(inverse, make_valid(bands[m]).buffer(-.001)))
        if not export_geometry.is_valid or not transform(project, export_geometry).is_valid:
            raise ValueError('Invalid display-band export after projection')
        display_features.append({'type': 'Feature', 'properties': {'minutes': m, 'role': 'exclusive generalized display band',
                                'color': colors[m], 'export_topology_inset_m': .001}, 'geometry': mapping(export_geometry)})
    (DAY / 'farmgate_display_bands.geojson').write_text(json.dumps({'type':'FeatureCollection','features':display_features},separators=(',',':'))+'\n')
    (DAY / 'map.html').write_text(template.replace('__MODE__', 'interactive'))
    (DAY / 'poster.html').write_text(template.replace('__MODE__', 'static').replace('id="method-link" href="#methodology"', 'id="method-link" href="README.md"'))
    rows = '\n'.join(f'| {m} min | {stats[m]["area_km2"]:.3f} | {stats[m]["reachable_stations"]} |' for m in [15, 30, 45])
    (DAY / 'map.results.md').write_text('# Dhaka in 45 Minutes\n\n[Interactive map](map.html) · [Static poster](poster.html) · [Method](README.md)\n\n'
        '| Budget | Modeled street envelope, km² | Metro-reachable stations |\n| --- | ---: | ---: |\n' + rows +
        '\n\nAreas describe a 60 m envelope of reachable pedestrian links, excluding mapped water. '
        'They are not verified building/parcel accessibility. No initial train wait is modeled.\n')
    with (DAY / 'map.results.md').open('a') as output:
        output.write(f'\nMunicipal denominator: **{context_qa["city_area_km2"]:.4f} km²**, original BBS/OCHA DNCC+DSCC union. '
                     f'45-minute intersection: **{context_qa["intersection_45min_km2"]:.4f} km²**; '
                     f'modeled overlap **{context_qa["percentage_45min"]:.4f}%**, displayed approximately. '
                     'The generalized display geofence and hole-filled exclusive bands are not used for these statistics.\n')
    print('Rendered interactive map.html and static poster.html.')


if __name__ == '__main__':
    main()
