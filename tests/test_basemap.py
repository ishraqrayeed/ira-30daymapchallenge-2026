"""Check browser tile configuration and visible source attribution."""

import unittest

from src.visualization.basemap import web_style


class Basemap(unittest.TestCase):
    def test_osm_style_uses_correct_tile_order_and_attribution(self):
        style = web_style()
        source = style['sources']['osm-streets']
        self.assertEqual(source['tiles'], ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'])
        self.assertIn('openstreetmap.org/copyright', source['attribution'])
