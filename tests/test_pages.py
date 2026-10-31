"""Check that Pages gets only the intended public artifacts and consistent data."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


class PagesBuild(unittest.TestCase):
    def test_public_package_excludes_raw_data_and_rewrites_report_link(self):
        script = Path(__file__).resolve().parents[1] / 'scripts/build_pages.py'
        spec = importlib.util.spec_from_file_location('build_pages', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'maps/day01-points'
            source.mkdir(parents=True)
            config = {'layers': [{'id': 'crash-points', 'data': [{'severity': 'Fatal'}]}]}
            (source / 'map.html').write_text('const jsonInput = ' + json.dumps(config, indent=2) + ';')
            (source / 'map.qa.json').write_text('{"mapped_incidents":1}')
            (source / 'map.results.md').write_text('[Map](map.html)')
            raw = root / 'data/raw'
            raw.mkdir(parents=True)
            (raw / 'not-for-publication.json').write_text('{"raw": true}')
            output = module.build(root)
            expected = {'index.html', 'day01/index.html', 'day01/map.qa.json',
                        'day01/map.results.md', '.nojekyll'}
            self.assertEqual({str(p.relative_to(output)) for p in output.rglob('*') if p.is_file()}, expected)
            self.assertEqual((output / 'day01/map.results.md').read_text(), '[Map](index.html)')
            (source / 'map.qa.json').write_text('{"mapped_incidents":2}')
            with self.assertRaises(ValueError):
                module.build(root)
