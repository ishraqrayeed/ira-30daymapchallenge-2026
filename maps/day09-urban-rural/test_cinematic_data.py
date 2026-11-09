"""Independent invariants for real polygon partitions and outward distance bands."""
import json,unittest
from pathlib import Path
import geopandas as gpd
from shapely.ops import unary_union
P=Path(__file__).resolve().parent/'data'
class CinematicDataTests(unittest.TestCase):
 def test_geographic_partition_and_distance_bands(self):
  lands=gpd.read_file(P/'edge-landscapes.geojson').to_crs(32611)
  bands=gpd.read_file(P/'edge-reveal-bands.geojson').to_crs(32611)
  border=unary_union(list(gpd.read_file(P/'edge-boundary.geojson').to_crs(32611).geometry))
  urban=lands[lands.side=='urban'].geometry.iloc[0];desert=lands[lands.side=='desert'].geometry.iloc[0]
  footprint=gpd.read_file(P/'urban-footprint.geojson').to_crs(32611).geometry.iloc[0]
  self.assertLess(urban.symmetric_difference(footprint).area,1)
  self.assertLess(urban.intersection(desert).area,.01)
  self.assertTrue(all(g.is_valid for g in [*lands.geometry,*bands.geometry]))
  for side,land in [('urban',urban),('desert',desert)]:
   rows=bands[bands.side==side];union=unary_union(list(rows.geometry))
   self.assertLess(union.symmetric_difference(land).area,1)
   self.assertLess(abs(sum(rows.area)-union.area),1)
   for _,r in rows.iterrows():
    distance=r.geometry.representative_point().distance(border)
    self.assertGreaterEqual(distance,r.inner_m-2);self.assertLessEqual(distance,r.outer_m+2)
 def test_urban_west_desert_east(self):
  config=json.loads((P/'cinematic.json').read_text())
  self.assertGreater(config['comparison']['west']['developed_pct'],85)
  self.assertLess(config['comparison']['east']['developed_pct'],10)
  self.assertEqual(config['target']['heading'],0)
  self.assertLessEqual(config['target']['pitch'],-80)
  self.assertTrue(config['geometry_qa']['bands_cover_both_landscapes'])
if __name__=='__main__':unittest.main()
