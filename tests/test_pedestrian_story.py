"""Verify the fatal-pedestrian-involvement scope and symbol unit."""

import base64
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest

from src.analysis.crashes import prepare_crashes
from src.analysis.pedestrian_story import select_story_crashes
from test_crashes import feature, payload


class PedestrianStory(unittest.TestCase):
    def test_selection_excludes_serious_only_and_bicycle_only_events(self):
        data = payload(feature('ped-fatal', fatal=1), feature('ped-serious'),
                       feature('bike-fatal', fatal=1, pedestrian=0, bicycle=1),
                       feature('both-fatal', fatal=1, pedestrian=1, bicycle=1))
        points, original = prepare_crashes(data, 2025)
        selected, qa = select_story_crashes(points, original)
        self.assertEqual(set(selected.incident_id), {'ped-fatal', 'both-fatal'})
        self.assertEqual(qa['mapped_incidents'], 2)
        self.assertEqual(qa['excluded_from_story_scope'], 2)
        self.assertEqual(qa['both_modes_crashes'], 1)
        self.assertEqual(qa['counted_unit'], 'Unique crash event, not an individual pedestrian death')
        self.assertEqual(original['mapped_incidents'], 4)

    def test_story_export_embeds_original_icon_and_has_no_mode_selector(self):
        script = Path(__file__).resolve().parents[1] / 'maps/day01-points/main.py'
        spec = importlib.util.spec_from_file_location('day01_story', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.json'
            source.write_text(json.dumps(payload(feature(fatal=1))))
            output = Path(directory) / 'map.html'
            qa = module.render(source, 2025, output, edition='story')
            self.assertEqual(qa['mapped_incidents'], 1)
            html = output.read_text()
            config = json.loads(re.search(r'const jsonInput = (\{[\s\S]*?\n\});', html)[1])
            layer = config['layers'][0]
            self.assertEqual(layer['@@type'], 'IconLayer')
            self.assertEqual(layer['getIcon'], '@@=icon_name')
            self.assertEqual(layer['data'][0]['icon_name'], 'pedestrian')
            self.assertEqual(layer['loadOptions']['image']['type'], 'image')
            self.assertEqual(layer['sizeUnits'], 'pixels')
            self.assertTrue(layer['iconAtlas'].startswith('data:image/svg+xml;base64,'))
            svg = base64.b64decode(layer['iconAtlas'].split(',', 1)[1]).decode()
            self.assertIn('Front-facing pedestrian symbol', svg)
            self.assertNotIn('<image', svg)
            self.assertIn('#963f3b', svg)
            self.assertIn('#f5f1e8', svg)
            self.assertIn('One symbol = one fatal crash', html)
            self.assertIn('fatal pedestrian crashes', html)
            self.assertNotIn('mode-filter', html)
            self.assertNotIn('Pedestrian fatalities', html)

    def test_empty_story_subset_stops(self):
        points, qa = prepare_crashes(payload(feature()), 2025)
        with self.assertRaises(ValueError):
            select_story_crashes(points, qa)
