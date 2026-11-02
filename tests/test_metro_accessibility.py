"""Check routing boundaries, municipal denominator and independent display bands."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from pyproj import Transformer
from shapely.geometry import shape, Polygon, LineString
from shapely.ops import transform, unary_union

ROOT = Path(__file__).resolve().parents[1]
DAY = ROOT / 'maps/day03-polygons'
sys.path.insert(0, str(DAY))
import analyze
import prepare_context


class MetroAccessibility(unittest.TestCase):
    def test_partial_edge_budget_from_both_ends(self):
        line = LineString([(0, 0), (800, 0)])
        pieces = analyze.reachable_edge(line, 5, 100, 10, 80)
        self.assertEqual(sum(p.length for p in pieces), 400)
        pieces = analyze.reachable_edge(line, 5, 5, 8, 80)
        self.assertEqual(sum(p.length for p in pieces), 480)
        self.assertEqual(len(pieces), 2)
        self.assertEqual(analyze.reachable_edge(line, 20, 30, 15, 80), [])

    def test_small_display_holes_fill_but_large_access_gap_remains(self):
        polygon = Polygon([(0,0),(1000,0),(1000,1000),(0,1000)],
                          [[(20,20),(40,20),(40,40),(20,40)],
                           [(200,200),(600,200),(600,600),(200,600)]])
        result = prepare_context.fill_small_holes(polygon, 50000)
        self.assertEqual(len(result.interiors), 1)
        self.assertAlmostEqual(result.area - polygon.area, 400)
        self.assertEqual(len(polygon.interiors), 2, 'Analytical geometry is not mutated')

    def test_metric_areas_nesting_and_original_city_denominator(self):
        project = Transformer.from_crs(4326,32646,always_xy=True).transform
        features = json.loads((DAY/'farmgate_accessibility.geojson').read_text())['features']
        polygons = {f['properties']['minutes']: transform(project,shape(f['geometry'])) for f in features}
        for feature in features:
            self.assertTrue(polygons[feature['properties']['minutes']].is_valid)
            self.assertAlmostEqual(polygons[feature['properties']['minutes']].area/1e6, feature['properties']['area_km2'], places=8)
        self.assertLess(polygons[15].difference(polygons[30]).area,.01)
        self.assertLess(polygons[30].difference(polygons[45]).area,.01)
        municipalities = json.loads((DAY/'dhaka_city_corporations.geojson').read_text())['features']
        self.assertEqual({f['properties']['adm3_pcode'] for f in municipalities},{'BD30262500','BD30262000'})
        city = unary_union([transform(project,shape(f['geometry'])) for f in municipalities])
        report = json.loads((DAY/'context.qa.json').read_text())
        self.assertAlmostEqual(city.area/1e6, report['city_area_km2'], places=8)
        self.assertAlmostEqual(polygons[45].intersection(city).area/city.area*100,report['percentage_45min'],places=8)
        self.assertFalse(report['display_geofence_statistics_used'])
        self.assertFalse(report['routing_model_modified'])

    def test_exclusive_bands_valid_and_legend_colors_match(self):
        project = Transformer.from_crs(4326,32646,always_xy=True).transform
        features = json.loads((DAY/'farmgate_display_bands.geojson').read_text())['features']
        polygons = [transform(project,shape(f['geometry'])) for f in features]
        self.assertTrue(all(p.is_valid for p in polygons))
        self.assertLess(sum(p.area for p in polygons)-unary_union(polygons).area,.01)
        html = (DAY/'map.html').read_text()
        for f in features:
            self.assertIn('fill="'+f['properties']['color']+'"',html)
            self.assertIn('--swatch:'+f['properties']['color'],html)
        self.assertNotIn('Modeled street catchment<br>within 45 minutes',html)
        self.assertNotIn('__CITY_',html)
        labels=json.loads((DAY/'dhaka_labels.geojson').read_text())['features']
        self.assertEqual(len(labels),7)
        self.assertTrue(all(f['properties']['source'].startswith('https://www.openstreetmap.org/') for f in labels))


if __name__=='__main__':
    unittest.main()
