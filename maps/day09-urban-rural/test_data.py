"""Day 9 analysis invariants and fractional-area regression tests."""
import json, unittest
from pathlib import Path
import numpy as np
from affine import Affine
from shapely.geometry import shape, box, LineString
from shapely.ops import transform, unary_union
from pyproj import Transformer
from process_data import zonal, height_m
P=Path(__file__).resolve().parent
class AnalysisTests(unittest.TestCase):
    def test_fractional_pixels_and_nodata(self):
        a=np.array([[21,52],[255,24]],dtype='uint8')
        dev,valid=zonal(a,Affine(30,0,0,0,-30,60),(15,15,45,45))
        self.assertAlmostEqual(dev,450);self.assertAlmostEqual(valid,675)
    def test_height_units_and_no_level_inference(self):
        self.assertAlmostEqual(height_m('100 ft'),30.48)
        self.assertEqual(height_m('120 m'),120)
        for invalid in ('unknown','12;15','-5','0','3 levels'):self.assertIsNone(height_m(invalid))
    def test_processed_layers(self):
        grid=json.loads((P/'data/grid.geojson').read_text())['features']
        qa=json.loads((P/'data/analysis.json').read_text())
        project=Transformer.from_crs(4326,32611,always_xy=True).transform
        urban=[];dev=valid=0
        self.assertEqual(len(grid),qa['cells']);self.assertEqual(len({f['properties']['id'] for f in grid}),len(grid))
        for f in grid:
            geom=transform(project,shape(f['geometry']));p=f['properties']
            self.assertTrue(geom.is_valid);self.assertAlmostEqual(geom.area,250000,places=2)
            self.assertTrue(0<=p['developed_pct']<=100)
            self.assertAlmostEqual(p['developed_pct'],p['developed_m2']/p['valid_m2']*100,delta=.006)
            self.assertEqual(p['class'],'Urban' if p['intensive_m2']/p['valid_m2']>=.5 else 'Suburban' if p['developed_m2']/p['valid_m2']>=.1 else 'Rural')
            if p['developed_m2']/p['valid_m2']>=.5:
                x,y=map(int,p['id'].split('-'));urban.append(box(x,y,x+500,y+500))
            dev+=p['developed_m2'];valid+=p['valid_m2']
        self.assertAlmostEqual(dev,qa['totals']['developed_m2'],delta=1)
        self.assertAlmostEqual(valid,qa['totals']['valid_m2'])
        union=unary_union(urban)
        expected=max(union.geoms,key=lambda g:g.area).exterior if union.geom_type=='MultiPolygon' else union.exterior
        boundary=transform(project,shape(json.loads((P/'data/boundary.geojson').read_text())['features'][0]['geometry']))
        self.assertLess(LineString(expected.coords).hausdorff_distance(boundary),.001)
        places=json.loads((P/'data/places.geojson').read_text())['features']
        self.assertEqual(len(places),12)
        self.assertEqual(sum(f['properties']['place_type']=='Incorporated city' for f in places),3)
        self.assertTrue(all(shape(f['geometry']).is_valid for f in places))
        buildings=json.loads((P/'data/buildings.geojson').read_text())['features']
        self.assertEqual(len(buildings),qa['buildings'])
        for f in buildings:
            self.assertTrue(shape(f['geometry']).is_valid)
            self.assertAlmostEqual(f['properties']['height_m'],height_m(f['properties']['height_original']),places=3)
if __name__=='__main__':unittest.main()
