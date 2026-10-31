"""Shareable deck.gl maps with a minimal headline, legend, and source credit."""

from html import escape
import base64
from pathlib import Path
from string import Template

import geopandas as gpd
import pydeck as pdk

from src.analysis.crashes import DETAIL_COLUMNS
from src.visualization.basemap import web_style

TEMPLATES = Path(__file__).resolve().parents[2] / 'templates'
PANEL = TEMPLATES / 'interactive-panel.html'


def export_crash_html(points: gpd.GeoDataFrame, year: int | str, output: Path, edition: str = 'analysis') -> None:
    """Embed validated event details; load the OSM basemap only in the browser."""
    geo = points.to_crs(4326)
    records = []
    for row in geo.itertuples():
        records.append({
            'position': [row.geometry.x, row.geometry.y],
            'incident_id': row.incident_id, 'icon_name': 'pedestrian',
            'severity': row.severity, 'involvement': row.involvement, 'year': row.year,
            'pedestrian': bool(row.pedestrian), 'bicycle': bool(row.bicycle),
            'occurrence_denver': row.occurrence_denver, 'severity_basis': row.severity_basis,
            **{column: getattr(row, column) for column in DETAIL_COLUMNS},
            'color': [187, 63, 48, 230] if row.fatal else [8, 127, 140, 210],
            'radius': 7.5 if row.fatal else 4.5,
        })
    records.sort(key=lambda record: record['severity'] == 'Fatal')
    # Fixed pixel sizes preserve severity contrast at overview and street scales.
    # White outlines separate nearby points from each other and from the basemap.
    icon = ''
    if edition == 'story':
        artwork = TEMPLATES.parent / 'assets/pedestrian.svg'
        icon = 'data:image/svg+xml;base64,' + base64.b64encode(artwork.read_bytes()).decode('ascii')
        layer = pdk.Layer('IconLayer', records, id='crash-points', pickable=True,
                         icon_atlas=f'"{icon}"',
                         icon_mapping={'pedestrian': {'x': 0, 'y': 0, 'width': 64, 'height': 80,
                                                      'anchorX': 32, 'anchorY': 40, 'mask': False}},
                         get_icon='icon_name', get_position='position', get_size=22,
                         get_color=[255, 255, 255, 255],
                         load_options={'image': {'type': 'image', 'decode': True}},
                         size_units='"pixels"', size_min_pixels=16, size_max_pixels=28,
                         billboard=True, alpha_cutoff=0.1)
    else:
        layer = pdk.Layer('ScatterplotLayer', records, id='crash-points', pickable=True,
                      get_position='position', get_fill_color='color', get_radius='radius', radius_units='"pixels"',
                      radius_min_pixels=1, radius_max_pixels=9,
                      stroked=True, get_line_color=[255, 255, 255, 235],
                      line_width_min_pixels=0.65, line_width_max_pixels=0.65)
    if edition == 'story':
        # Focus the opening camera on urban Denver; retain every record for panning.
        view = pdk.ViewState(latitude=39.738, longitude=-104.972, zoom=11.4,
                             pitch=0, bearing=0)
    else:
        bounds = geo.total_bounds.tolist()
        view = pdk.data_utils.compute_view([[bounds[0], bounds[1]], [bounds[2], bounds[3]]])
        view.zoom += 0.8
    # Custom non-Mapbox raster URLs use the bundled renderer without a token.
    tooltip = {
        'text': '{occurrence_denver}' if edition == 'story' else '{occurrence_denver}\n{involvement} involved\n{severity}',
        'style': {'backgroundColor': '#24343c', 'color': '#ffffff',
                  'fontSize': '12px', 'lineHeight': '1.5', 'maxWidth': '370px',
                  'padding': '14px', 'borderRadius': '6px'},
    }
    deck = pdk.Deck(layers=[layer], initial_view_state=view, map_provider='mapbox',
                    map_style=web_style(), tooltip=tooltip)
    html = deck.to_html(as_string=True, notebook_display=False)
    # Escape script delimiters in source descriptions while preserving JS data.
    serialized = deck.to_json()
    safe_json = serialized.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    html = html.replace(serialized, safe_json)
    title = escape(f'Someone Was Walking Here — Denver {year}' if edition == 'story'
                   else f'Denver pedestrian- and bicycle-involved severe crashes — {year}')
    html = html.replace('<title>pydeck</title>', f'<title>{title}</title>')
    html = html.replace('</head>', '<meta name="viewport" content="width=device-width, initial-scale=1">'
                        '<meta name="referrer" content="strict-origin-when-cross-origin"></head>')
    panel_file = TEMPLATES / 'story-panel.html' if edition == 'story' else PANEL
    panel = Template(panel_file.read_text()).substitute(period=escape(str(year)), icon=icon, count=f'{len(geo):,}')
    html = html.replace('</body>', panel + '</body>')
    # The exported loader constructs deckInstance before installing controls.
    if edition == 'analysis':
        controls = (TEMPLATES / 'map-controls.js').read_text()
        before, after = html.rsplit('</script>', 1)
        html = before + '\n' + controls + '\n</script>' + after
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html)
