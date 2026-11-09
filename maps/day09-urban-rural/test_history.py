"""Validate source-derived metrics, geometry, and display masks independently of Cesium."""
import json,unittest
from pathlib import Path
import numpy as np
from PIL import Image
import geopandas as gpd
P=Path(__file__).resolve().parent
D=json.loads((P/'data/history.json').read_text())
def mask(row,key):return np.array(Image.open(P/row['texture'][key]))[:,:,3]>0
class HistoryTests(unittest.TestCase):
 def test_source_epochs_and_area_balance(self):
  self.assertEqual(D['epochs'],list(range(1975,2021,5)))
  baseline=D['series'][0]['developed_km2'];previous=baseline
  for r in D['series']:
   self.assertAlmostEqual(r['developed_km2'],r['selected_cells']*.01,places=6)
   self.assertAlmostEqual(r['developed_mi2'],r['developed_km2']/2.589988110336,places=3)
   self.assertAlmostEqual(r['change_from_first_km2'],r['developed_km2']-baseline,places=4)
   self.assertAlmostEqual(r['change_from_first_pct'],100*(r['developed_km2']/baseline-1),places=3)
   self.assertAlmostEqual(r['developed_km2']-previous,r['gain_km2']-r['loss_km2'],places=4);previous=r['developed_km2']
 def test_masks_preserve_geographic_changes(self):
  previous=None
  for r in D['series']:
   full=mask(r,'footprint');stable=mask(r,'stable');gain=mask(r,'gain');loss=mask(r,'loss')
   self.assertTrue(np.array_equal(full,stable|gain))
   if previous is not None:
    self.assertTrue(np.array_equal(previous,stable|loss))
    self.assertFalse(np.any(stable&gain));self.assertFalse(np.any(full&loss))
   self.assertTrue(np.array_equal(gain,mask(r,'highlight')));previous=full
 def test_vector_geography_and_native_area(self):
  g=gpd.read_file(P/'data/history-footprints.geojson');self.assertTrue(g.is_valid.all());self.assertEqual(len(g),10)
  self.assertTrue((g.total_bounds>=np.array([-115.6,35.8,-115.6,35.8])).all())
  areas=g.to_crs('ESRI:54009').area/1e6
  for actual,expected in zip(areas,D['series']):self.assertAlmostEqual(actual,expected['developed_km2'],places=3)
if __name__=='__main__':unittest.main()
