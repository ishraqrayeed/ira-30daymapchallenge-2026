"""OpenStreetMap raster style for browser-rendered deck.gl maps."""

TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
SERVICE_URL = "https://www.openstreetmap.org/copyright"
CREDIT = "© OpenStreetMap contributors · openstreetmap.org/copyright"


def web_style() -> dict:
    """A raster style using OpenStreetMap tiles; no commercial-provider token."""
    return {
        "version": 8,
        "sources": {"osm-streets": {
            "type": "raster", "tiles": [TILE_URL], "tileSize": 256,
            "minzoom": 0, "maxzoom": 19,
            "attribution": '<a href="https://www.openstreetmap.org/copyright">© OpenStreetMap contributors</a>',
        }},
        "layers": [
            {"id": "paper", "type": "background", "paint": {"background-color": "#f5f1e8"}},
            {"id": "osm-streets", "type": "raster", "source": "osm-streets",
             "paint": {"raster-opacity": 0.6, "raster-saturation": -0.85,
                       "raster-contrast": -0.1}},
        ],
    }
