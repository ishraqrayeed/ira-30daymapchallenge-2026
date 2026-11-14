"""Day 14 release checks: preserve other routes and validate the published count."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('day14_pages',ROOT/'scripts/build_pages.py')
pages=importlib.util.module_from_spec(spec)
spec.loader.exec_module(pages)

class Day14Release(unittest.TestCase):
    def test_relative_assets_and_previous_route_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)
            previous=output/'day01-points/index.html'
            previous.parent.mkdir();previous.write_text('Preserve this published day')
            pages.package_day14(ROOT,output)
            target=output/'day14-borgesian'
            self.assertEqual(previous.read_text(),'Preserve this published day')
            self.assertEqual((target/'index.html').read_bytes(),(ROOT/'day14-borgesian/map.html').read_bytes())
            expected={'index.html' if name=='map.html' else name for name in pages.DAY14_FILES}
            self.assertEqual({str(p.relative_to(target)) for p in target.rglob('*') if p.is_file()},expected)
            self.assertFalse(list(target.rglob('*.pbf')))
            self.assertTrue((target/'vendor/maplibre-gl-csp-worker.js').is_file())
            self.assertNotIn('data/raw','\n'.join(expected))

    def test_count_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'day14-borgesian';(source/'data').mkdir(parents=True)
            (source/'map.html').write_text('fixture')
            qa=json.loads((ROOT/'day14-borgesian/data/qa.json').read_text());qa['parks_mapped']+=1
            (source/'data/qa.json').write_text(json.dumps(qa))
            for name in ['parks.geojson','interiors.geojson']:
                (source/'data'/name).write_bytes((ROOT/'day14-borgesian/data'/name).read_bytes())
            with self.assertRaisesRegex(ValueError,'park count or tour bench'):
                pages.package_day14(root,root/'out')

if __name__=='__main__':unittest.main()
