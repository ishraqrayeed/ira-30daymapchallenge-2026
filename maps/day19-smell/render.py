"""Render the Day 19 poster from public elevation and coastline data."""

import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import patheffects
from matplotlib.colors import to_rgb
from matplotlib.lines import Line2D
from matplotlib.path import Path as PolygonPath
import numpy as np
from PIL import Image, ImageFilter, ImageOps
from pyproj import Transformer
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject

DAY = Path(__file__).resolve().parent
CACHE = DAY.parents[1] / "data/raw/day19-smell"
DEM_HOST = "https://copernicus-dem-30m.s3.amazonaws.com"
DEM_TILES = {
    "S02": "536a97d629f02e6169a1a0993e30981544aabbba64e2b430a35de5dbacec019a",
    "S03": "409a6a4223471c93f6ea968b2aa3bea25b6af43d95ddb51edb59715f1c38218f",
}
LAND = "ne_10m_land.geojson"
LAND_URL = f"https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/{LAND}"
LAND_HASH = "1ac90796408bc6ad6911d69448485d3c4dbf2190370080368a09976e1c9f7416"
CRS = "EPSG:32747"
WEST, EAST, SOUTH, NORTH = 724000, 799000, 9744000, 9820000
CELL = 50
PAPER, INK, RUST = "#f8f1e3", "#362218", "#9c3f26"
SERIF = "STIXGeneral"
CULTIVATION = "#753620"
BAND_COLOR = "#c28561"
BAND_ALPHA = 0.18
STUDY_ELEVATION = (1000, 1500)
SUMMIT = (101.264, -1.697)
VILLAGES = (
    ("Pungut", 101.461833, -2.020972, (10, 7), "left"),
    ("Renah Kayu Embun", 101.3993, -2.1589, (-10, 12), "right"),
    ("Lempur", 101.535356, -2.089992, (10, -3), "left"),
)


# Lizawati et al. (2018), Table 1. GR 01 is also reported by the 2019 harvest study.
# Coordinates are degrees, minutes, seconds. RK S1 has ambiguous latitude and is omitted.
CULTIVATION_SITES = (
    ("GR 01", (2, 16, 42.8), (101, 33, 40.1)),
    ("RK S2", (2, 9, 38.9), (101, 23, 32.3)),
    ("PH S1", (2, 1, 15.5), (101, 27, 42.6)),
    ("SL S1", (1, 55, 27.0), (101, 19, 12.4)),
    ("KA S1", (1, 49, 53.8), (101, 15, 39.5)),
    ("KA S2", (1, 46, 0.0), (101, 18, 2.6)),
)


def decimal_degrees(dms):
    degrees, minutes, seconds = dms
    if not (0 <= minutes < 60 and 0 <= seconds < 60):
        raise ValueError(f"Invalid coordinate: {dms}")
    return degrees + minutes / 60 + seconds / 3600


def study_band(elevation):
    low, high = STUDY_ELEVATION
    return (elevation >= low) & (elevation <= high)


def source_file(name, url, expected):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / name
    if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected:
        return path
    with urlopen(url, timeout=90) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Unexpected SHA-256 for {name}")
    path.write_bytes(data)
    return path


def terrain():
    shape = ((NORTH - SOUTH) // CELL, (EAST - WEST) // CELL)
    transform = from_origin(WEST, NORTH, CELL, CELL)
    elevation = np.full(shape, np.nan, dtype=np.float32)
    for latitude, checksum in DEM_TILES.items():
        tile = f"Copernicus_DSM_COG_10_{latitude}_00_E101_00_DEM"
        path = source_file(f"{tile}.tif", f"{DEM_HOST}/{tile}/{tile}.tif", checksum)
        with rasterio.open(path) as src:
            reproject(rasterio.band(src, 1), elevation, dst_crs=CRS,
                      dst_transform=transform, dst_nodata=np.nan, init_dest_nodata=False,
                      resampling=Resampling.bilinear)
    if not np.isfinite(elevation).all():
        raise ValueError("Elevation coverage is incomplete")
    print(f"DEM {shape[1]} × {shape[0]}, {elevation.min():.0f}–{elevation.max():.0f} m")
    return elevation


def relief(elevation):
    # Row order runs southward, so reverse the y gradient for north-facing light.
    south_slope, east_slope = np.gradient(elevation, CELL)
    azimuth, altitude = np.radians([315, 43])
    illumination = (
        np.sin(altitude)
        - east_slope * np.cos(altitude) * np.sin(azimuth)
        + south_slope * np.cos(altitude) * np.cos(azimuth)
    ) / np.sqrt(1 + south_slope**2 + east_slope**2)
    weight = np.clip((0.88 - illumination) * 0.66, 0, 0.63)[..., None]
    light = np.array(to_rgb("#faf3e4"))
    dark = np.array(to_rgb("#bfa489"))
    shaded = light + weight * (dark - light)
    band = study_band(elevation)
    shaded[band] = (1 - BAND_ALPHA) * shaded[band] + BAND_ALPHA * np.asarray(to_rgb(BAND_COLOR))
    return shaded


def draw_terrain(fig, elevation):
    ax = fig.add_axes([0.07, 0.188, 0.86, 0.86 * 11 / 15 * (NORTH-SOUTH)/(EAST-WEST)])
    extent = [WEST, EAST, SOUTH, NORTH]
    ax.imshow(relief(elevation), extent=extent, interpolation="bilinear")
    x = np.arange(WEST + CELL / 2, EAST, CELL)
    y = np.arange(NORTH - CELL / 2, SOUTH, -CELL)
    levels = np.arange(100, 3900, 100)
    index = levels % 500 == 0
    ax.contour(x, y, elevation, levels=levels[~index], colors="#955a3e", alpha=0.40, linewidths=0.29)
    ax.contour(x, y, elevation, levels=levels[index], colors="#77422f", alpha=0.68, linewidths=0.49)
    ax.set(xlim=(WEST, EAST), ylim=(SOUTH, NORTH), xticks=[], yticks=[], aspect="equal")
    for spine in ax.spines.values():
        spine.set(color="#b3967e", linewidth=0.6)

    project = Transformer.from_crs(4326, CRS, always_xy=True)
    halo = [patheffects.withStroke(linewidth=3.3, foreground=PAPER)]
    for accession, latitude, longitude in CULTIVATION_SITES:
        px, py = project.transform(decimal_degrees(longitude), -decimal_degrees(latitude))
        if not (WEST < px < EAST and SOUTH < py < NORTH):
            raise ValueError(f"{accession} is outside the map")
        # PH S1 is also the Pungut reference point. The diamond remains visible
        # around its circle, conveying both records at the published location.
        ax.scatter(px, py, marker="D", s=210 if accession == "PH S1" else 115,
                   c=CULTIVATION, edgecolors=PAPER, linewidths=1.4, zorder=4)
        if accession == "GR 01":
            ax.annotate("Lempur cinnamon agroforest", (px, py), xytext=(-12, 0),
                        textcoords="offset points", ha="right", va="center",
                        family=SERIF, style="italic", size=17, color=CULTIVATION,
                        path_effects=halo, zorder=6)

    for name, lon, lat, offset, alignment in VILLAGES:
        px, py = project.transform(lon, lat)
        if not (WEST < px < EAST and SOUTH < py < NORTH):
            raise ValueError(f"{name} is outside the map")
        ax.scatter(px, py, s=78, c=RUST, edgecolors=PAPER, linewidths=1.5, zorder=5)
        ax.annotate(name, (px, py), xytext=offset, textcoords="offset points",
                    va="center", ha=alignment, size=17, weight="semibold",
                    color=INK, path_effects=halo, zorder=6)
    summit = project.transform(*SUMMIT)
    ax.annotate("Mount Kerinci", summit, xytext=(11, 8), textcoords="offset points",
                va="bottom", family=SERIF, style="italic", size=16, color=INK, path_effects=halo)
    ax.text(0.952, 0.91, "N", transform=ax.transAxes, color=INK, ha="center", size=9,
            weight="semibold", path_effects=halo)
    ax.annotate("", xy=(0.952, 0.90), xytext=(0.952, 0.862), xycoords="axes fraction",
                arrowprops={"arrowstyle": "-|>", "color": INK, "lw": 0.9})
    # A 10,000 m UTM grid distance, placed inside the lower left of the terrain panel.
    sx, sy = WEST + 2500, SOUTH + 2700
    for dx, color in ((0, INK), (5000, PAPER)):
        ax.plot([sx + dx, sx + dx + 5000], [sy, sy], color=color, linewidth=2.6,
                solid_capstyle="butt", path_effects=[patheffects.withStroke(linewidth=3.5, foreground=INK)])
    ax.text(sx, sy + 700, "0", size=8, color=INK, path_effects=halo)
    ax.text(sx + 10000, sy + 700, "10 km", size=8, ha="right", color=INK, path_effects=halo)


def draw_locator(fig):
    land = json.loads(source_file(LAND, LAND_URL, LAND_HASH).read_text())
    ax = fig.add_axes([0.071, 0.057, 0.177, 0.122])
    for feature in land["features"]:
        geometry = feature["geometry"]
        polygons = geometry["coordinates"]
        if geometry["type"] == "Polygon":
            polygons = [polygons]
        for polygon in polygons:
            ring = np.asarray(polygon[0])
            if ring[:, 0].max() < 94 or ring[:, 0].min() > 107:
                continue
            if ring[:, 1].max() < -7 or ring[:, 1].min() > 6.5:
                continue
            is_sumatra = PolygonPath(ring).contains_point((101.43, -2.03))
            ax.fill(*ring.T, color="#d9c5aa" if is_sumatra else "#eae0ce",
                    ec="#a4846b" if is_sumatra else "#c8b8a0", lw=0.32)
    ax.set(xlim=(94, 107), ylim=(-7, 6.5), aspect="equal")
    ax.axis("off")
    ax.scatter(101.43, -2.03, s=26, color=RUST, edgecolor=PAPER, linewidth=0.7, zorder=3)
    ax.text(101.86, -2.13, "Kerinci", size=8, color=INK, weight="semibold", va="center")
    ax.text(97.7, -2.9, "SUMATRA", size=7.7, color=INK, ha="center")


def draw_illustration(fig):
    art = fig.add_axes([0.609, 0.065, 0.333, 0.145], zorder=8)
    with Image.open(DAY / "assets/cinnamon.png") as source:
        illustration = source.convert("RGBA")
    pad = 32
    alpha = ImageOps.expand(illustration.getchannel("A"), border=pad)
    shadow = Image.new("RGBA", alpha.size, "#60432f")
    shadow.putalpha(alpha.filter(ImageFilter.GaussianBlur(13)).point(lambda a: round(a * 0.22)))
    canvas = Image.new("RGBA", (alpha.width + 8, alpha.height + 15))
    canvas.alpha_composite(shadow, (8, 15))
    canvas.alpha_composite(illustration, (pad, pad))
    art.imshow(np.asarray(canvas), interpolation="antialiased")
    art.axis("off")


def render():
    plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42})
    fig = plt.figure(figsize=(11, 15), facecolor=PAPER)
    fig.text(0.07, 0.957, "DAY 19  /  SENSES: SMELL", color=RUST, size=10, weight="semibold")
    fig.text(0.93, 0.957, "#30DayMapChallenge 2026", color=RUST, size=10, ha="right")
    fig.text(0.067, 0.892, "Where Cinnamon Grows", family=SERIF, size=66, color=INK)
    fig.text(0.072, 0.86, "The Kerinci Highlands, Sumatra", family=SERIF,
             style="italic", size=23, color="#79523b")
    fig.text(0.073, 0.840, "From mountain slopes to spice markets.", color=RUST, size=13)
    draw_terrain(fig, terrain())
    draw_locator(fig)

    fig.text(0.269, 0.169, "Cinnamon in the Highlands", color=INK, family=SERIF,
             size=21, va="center")
    fig.text(0.269, 0.147, "Study sites at 1,000–1,500 m elevation.", color=INK, size=12)
    band_swatch = ((1 - BAND_ALPHA) * np.asarray(to_rgb("#faf3e4"))
                   + BAND_ALPHA * np.asarray(to_rgb(BAND_COLOR)))
    for y, marker, color, label in (
        (0.126, "D", CULTIVATION, "Cultivated cinnamon · field records"),
        (0.106, "o", RUST, "Documented cinnamon study villages"),
        (0.086, "s", band_swatch, "Study elevation band (terrain only)"),
    ):
        fig.add_artist(Line2D([0.275], [y], marker=marker, markersize=8, color=color,
                              markeredgecolor="#a17961" if marker == "s" else PAPER,
                              transform=fig.transFigure))
        fig.text(0.290, y, label, color=INK, va="center", size=11.5)
    fig.text(0.269, 0.063, "100 m contours  /  Index contours every 500 m", color="#79523b", size=8)
    draw_illustration(fig)

    fig.add_artist(Line2D([0.07, 0.93], [0.05, 0.05], lw=0.5, color="#b3967e",
                          transform=fig.transFigure))
    fig.text(0.07, 0.036, "Villages · Antony et al.   /   Cultivation · Lizawati et al. (2018), Table 1   /   Locator · Natural Earth",
             size=7.6, color=INK)
    fig.text(0.07, 0.016, "Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018\n"
             "provided under COPERNICUS by the European Union and ESA; all rights reserved.",
             size=6.6, color=INK, linespacing=1.4)
    output = DAY / "exports"
    output.mkdir(exist_ok=True)
    fig.savefig(output / "where-cinnamon-grows.png", dpi=360)
    fig.savefig(output / "where-cinnamon-grows.pdf", dpi=360, metadata={"Title": "Where Cinnamon Grows"})
    plt.close(fig)


if __name__ == "__main__":
    render()
