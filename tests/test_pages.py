"""Check that Pages gets only the intended public artifacts and consistent data."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


class PagesBuild(unittest.TestCase):
    def test_day3_release_preserves_previous_maps_and_excludes_caches(self):
        repository = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location('release_pages', repository / 'scripts/build_pages.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            output = module.build(repository, Path(directory))
            day3 = output / 'day03-polygons'
            self.assertEqual({p.name for p in day3.iterdir()}, {'index.html', *module.DAY3_FILES})
            self.assertIn('Dhaka in 45 Minutes', (output / 'index.html').read_text())
            for day in ['day01-points', 'day02-lines']:
                self.assertEqual((output / day / 'index.html').read_bytes(),
                                 (repository / 'maps' / day / 'map.html').read_bytes())
            self.assertNotIn('data/raw', '\n'.join(str(p) for p in output.rglob('*')))
            self.assertNotIn('(map.html)', (day3 / 'README.md').read_text())

    def test_public_package_excludes_raw_data_and_rewrites_report_link(self):
        script = Path(__file__).resolve().parents[1] / 'scripts/build_pages.py'
        spec = importlib.util.spec_from_file_location('build_pages', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'maps/day01-points'
            source.mkdir(parents=True)
            templates = root / 'templates'
            templates.mkdir()
            (templates / 'portfolio-index.html').write_text('<a href="./day01-points/">Day 1 — Points</a>')
            config = {'layers': [{'id': 'crash-points', 'data': [{'severity': 'Fatal'}]}]}
            (source / 'map.html').write_text('const jsonInput = ' + json.dumps(config, indent=2) + ';')
            (source / 'map.qa.json').write_text('{"mapped_incidents":1}')
            (source / 'map.results.md').write_text('[Map](map.html)')
            raw = root / 'data/raw'
            raw.mkdir(parents=True)
            (raw / 'not-for-publication.json').write_text('{"raw": true}')
            output = module.build(root)
            expected = {'index.html', 'day01/index.html', 'day01/map.qa.json',
                        'day01/map.results.md', 'day01-points/index.html',
                        'day01-points/map.qa.json', 'day01-points/map.results.md', '.nojekyll'}
            self.assertEqual({str(p.relative_to(output)) for p in output.rglob('*') if p.is_file()}, expected)
            self.assertEqual((output / 'day01/map.results.md').read_text(), '[Map](index.html)')
            self.assertIn('href="./day01-points/"', (output / 'index.html').read_text())
            self.assertNotIn('const jsonInput', (output / 'index.html').read_text())
            self.assertEqual((output / 'day01-points/index.html').read_text(), (source / 'map.html').read_text())
            self.assertIn('0;url=../day01-points/', (output / 'day01/index.html').read_text())
            second = root / 'maps/day02-lines'
            second.mkdir()
            data2 = {'trails': [{'id': 'a', 'points': [[0, 0, 8000, 0], [1, 1, 8100, .1]]}],
                     'totals': {'segments': 1, 'miles': .1}}
            (second / 'map.html').write_text('const MAP_DATA = ' + json.dumps(data2) + ';')
            qa2 = {'mapped_segments': 1, 'elevation_samples': 2, 'totals': data2['totals']}
            (second / 'map.qa.json').write_text(json.dumps(qa2))
            (second / 'map.results.md').write_text('[Map](map.html)')
            (second / 'README.md').write_text('Sources and methods')
            module.build(root)
            self.assertTrue((output / 'day02-lines/index.html').is_file())
            self.assertEqual((output / 'day02-lines/map.results.md').read_text(), '[Map](index.html)')
            self.assertEqual((output / 'day01-points/index.html').read_text(), (source / 'map.html').read_text())
            (second / 'map.qa.json').write_text(json.dumps({**qa2, 'mapped_segments': 2}))
            with self.assertRaises(ValueError):
                module.build(root)
            (second / 'map.qa.json').write_text(json.dumps(qa2))
            (source / 'map.qa.json').write_text('{"mapped_incidents":2}')
            with self.assertRaises(ValueError):
                module.build(root)
