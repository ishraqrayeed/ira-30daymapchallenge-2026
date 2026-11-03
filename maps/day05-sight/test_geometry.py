"""Independent analytic checks and source-to-poster consistency checks."""
import json
import math
import re
import unittest
import statistics
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

from geometry import normalize, sight_geometry, POSTS
from fetch_data import HERE, ROOT


class GeometryTests(unittest.TestCase):
    def test_regulation_landmarks(self):
        self.assertEqual(normalize(88.5,50),(94,34))
        self.assertEqual(normalize(83,21.1),(88.5,13.84))
        self.assertEqual(normalize(100,45.2),POSTS[0])
        self.assertEqual(normalize(100,54.8),POSTS[1])

    def test_analytic_penalty_angle(self):
        distance, angle=sight_geometry(94,34)
        self.assertAlmostEqual(distance,11)
        self.assertAlmostEqual(angle, math.degrees(2*math.atan(3.66/11)),places=10)

    def test_symmetry_and_monotonicity(self):
        self.assertAlmostEqual(sight_geometry(80,14)[1],sight_geometry(80,54)[1])
        self.assertGreater(sight_geometry(90,34)[1],sight_geometry(70,34)[1])
        self.assertGreater(sight_geometry(80,34)[1],sight_geometry(80,54)[1])

    def test_invalid_positions_rejected(self):
        for xy in [(-1,50),(101,50),(50,-1),(50,101)]:
            with self.assertRaises(ValueError): normalize(*xy)
        with self.assertRaises(ValueError): sight_geometry(*POSTS[0])

    def test_every_embedded_event_and_geometry(self):
        page=(HERE/'map.html').read_text()
        embedded=json.loads(re.search(r'const MAP_DATA=(\{[^\n]+\});',page)[1])
        processed=json.loads((ROOT/'data/processed/day05-sight/messi_wc2026_shots.json').read_text())
        self.assertEqual(embedded['shots'],processed)
        self.assertEqual(len(processed),35)
        self.assertEqual(sum(s['is_goal'] for s in processed),8)
        self.assertEqual(sum(s['is_penalty'] for s in processed),2)
        for s in processed:
            x,y=normalize(s['source_x'],s['source_y'])
            self.assertEqual((x,y),(s['shot_x'],s['shot_y']))
            distance,angle=sight_geometry(x,y)
            self.assertAlmostEqual(distance,s['distance_to_goal_m'])
            self.assertAlmostEqual(angle,s['sight_angle_deg'])

    def test_static_poster_has_all_points_rays_and_three_callouts(self):
        class Nodes(HTMLParser):
            def __init__(self): super().__init__();self.markers=[];self.rays=[];self.labels=[]
            def handle_starttag(self,tag,attrs):
                a=dict(attrs);classes=a.get('class','').split()
                if 'marker' in classes:self.markers.append(a)
                if 'sight-line' in classes:self.rays.append(a)
                if 'annotation' in classes:self.labels.append(a)
        page=(HERE/'map.html').read_text();nodes=Nodes();nodes.feed(page)
        self.assertEqual(len(nodes.markers),35)
        self.assertEqual(len({m['data-event'] for m in nodes.markers}),35)
        self.assertEqual(len(nodes.rays),70)
        self.assertEqual(len(nodes.labels),3)
        summary=json.loads((HERE/'analysis.json').read_text())
        self.assertEqual({a['data-event'] for a in nodes.labels},{h['event_id'] for h in summary['heroes']})

    def test_four_metrics_goal_markers_and_export_bounds(self):
        page=(HERE/'map.html').read_text()
        data=json.loads(re.search(r'const MAP_DATA=(\{[^\n]+\});',page)[1])
        svg=ET.fromstring(re.search(r'(<svg.*?</svg>)',page,re.S)[1])
        self.assertEqual(svg.attrib['viewBox'],'0 0 1620 1350')
        metrics=[e for e in svg.iter('text') if e.get('class')=='stat-value']
        self.assertEqual(len(metrics),4)
        centers=[float(e.get('x')) for e in metrics]
        self.assertEqual([b-a for a,b in zip(centers,centers[1:])],[320,320,320])
        attempts=data['shots'];nonpen=[s for s in attempts if not s['is_penalty']]
        expected=[str(len(attempts)),str(sum(s['is_goal'] for s in attempts)),
                  f"{statistics.median(s['sight_angle_deg'] for s in nonpen):.1f}°",
                  f"{statistics.median(s['distance_to_goal_m'] for s in nonpen):.1f}m"]
        self.assertEqual([''.join(e.itertext()) for e in metrics],expected)
        goals=[e for e in svg.iter('g') if {'goal','marker'}<=set(e.get('class','').split())]
        self.assertEqual(len(goals),8)
        self.assertIn('.goal .shot-dot{fill:var(--blue)',page)
        self.assertIn('--green:#efefef',page)
        self.assertNotIn('@@',page)


if __name__=='__main__': unittest.main()
