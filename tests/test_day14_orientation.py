"""Bench models face nearby path geometry without overwriting source directions."""
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('orient_benches',Path(__file__).resolve().parents[1]/'day14-borgesian/orient_benches.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def feature(kind,coords,direction=None):
    p={'kind':kind,'osm':kind+'/1'}
    if direction is not None:p['direction']=direction
    return {'type':'Feature','properties':p,'geometry':{'type':'Point' if kind=='bench' else 'LineString','coordinates':coords}}

class BenchFacing(unittest.TestCase):
    def test_faces_trail_and_preserves_source_coordinate(self):
        trail=feature('path',[[-104.970,39.699],[-104.970,39.701]])
        bench=feature('bench',[-104.9699,39.7]);module.orient_benches([trail,bench])
        self.assertAlmostEqual(bench['properties']['display_direction'],270,places=2)
        self.assertEqual(bench['geometry']['coordinates'],[-104.9699,39.7])
        self.assertEqual(bench['properties']['direction_basis'],'nearest trail')

    def test_recorded_direction_and_distance_cutoff(self):
        trail=feature('path',[[-104.970,39.699],[-104.970,39.701]])
        bench=feature('bench',[-104.9699,39.7],'E');far=feature('bench',[-104.96,39.7])
        module.orient_benches([trail,bench,far])
        self.assertEqual(bench['properties']['display_direction'],90)
        self.assertEqual(bench['properties']['direction_basis'],'osm')
        self.assertEqual(far['properties']['direction_basis'],'display fallback')

    def test_on_path_is_perpendicular_to_local_tangent(self):
        trail=feature('path',[[-104.970,39.699],[-104.970,39.701]])
        bench=feature('bench',[-104.97,39.7]);module.orient_benches([trail,bench])
        self.assertEqual(bench['properties']['direction_basis'],'nearest trail')
        self.assertAlmostEqual(bench['properties']['display_direction'],270,places=2)
