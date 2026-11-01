"""Check trail selection, geographic cleanup, and elevation sampling."""
import importlib.util
from pathlib import Path
import unittest

import numpy as np
from rasterio.transform import from_origin
from shapely.geometry import LineString

SCRIPT = Path(__file__).resolve().parents[1] / "maps/day02-lines/main.py"
spec = importlib.util.spec_from_file_location("day2", SCRIPT)
day2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(day2)


class Trails(unittest.TestCase):
    def test_select_existing_hiking_use_and_reject_closed_or_unknown(self):
        base = {"TRLUSE": "Hiker/Pedestrian | Pack and Saddle", "TRLSTATUS": "Existing"}
        self.assertTrue(day2.hiking_feature(base))
        for changes in [{"TRLUSE": "Unknown"}, {"TRLSTATUS": "Proposed"},
                        {"OPENTOPUBLIC": "False"}, {"ISEXTANT": "False"}]:
            self.assertFalse(day2.hiking_feature({**base, **changes}))

    def test_overlaps_dissolve_short_connecting_pieces_merge_and_parallel_paths_survive(self):
        parts = [LineString([(0, 0), (90, 0)]), LineString([(90, 0), (180, 0)]),
                 LineString([(50, 0), (150, 0)]), LineString([(0, 5), (180, 5)])]
        result = day2.dissolve_named_parts(parts)
        self.assertEqual(len(result), 2)
        self.assertEqual(sorted(p.length for p in result), [180, 180])
        # Filtering after merging keeps both short pieces as one meaningful line.
        self.assertTrue(all(p.length >= 100 for p in result))

    def test_bilinear_sampling_pixel_centers_and_outside_coverage(self):
        affine = from_origin(0, 40, 10, 10)
        grid = np.array([[2000, 2100, 2200], [2200, 2300, 2400], [2400, 2500, 2600]])
        values = day2.bilinear(grid, affine, np.array([[5, 35], [10, 30]]))
        np.testing.assert_allclose(values, [2000, 2150])
        with self.assertRaises(ValueError):
            day2.bilinear(grid, affine, np.array([[-1, 35]]))


if __name__ == "__main__":
    unittest.main()
