# Day 19 — Senses: Smell

## Where Cinnamon Grows

Where does the familiar scent of a cinnamon stick begin? In Sumatra’s Kerinci
Highlands, the layers of a rolled quill echo the closely spaced contours of the
mountains.

[Sharing PNG](exports/where-cinnamon-grows.png) · [Print PDF](exports/where-cinnamon-grows.pdf)

## Where cultivation is documented

Diamonds show six field observations of cultivated Indonesian cinnamon from
[Lizawati et al., *Genetic diversity of cinnamon plants (Cinnamomum burmanii BL.) at various altitude based on morphological character*, Table 1, IOP Conf. Ser. Mater. Sci. Eng. 434 (2018) 012129, CC BY 3.0](https://doi.org/10.1088/1757-899X/434/1/012129).
The map includes the six unambiguous Kerinci and Sungai Penuh coordinates from
the table. RK S1 was omitted because its printed latitude minutes are ambiguous.
The reported field elevations span 898–1,488 m and include records below the
separate Antony et al. study band.

| Accession | Location | WGS84 latitude, longitude | Reported elevation |
| --- | --- | --- | ---: |
| GR 01 | Lempur Mudik community cinnamon agroforest | −2.278556, 101.561139 | 1,076 m |
| RK S2 | Renah Kayu Embun | −2.160806, 101.392306 | 1,335 m |
| PH S1 | Pungut Hilir | −2.020972, 101.461833 | 919 m |
| SL S1 | Lubuk Nagodang | −1.924167, 101.320111 | 898 m |
| KA S1 | Batu Ampar | −1.831611, 101.260972 | 1,377 m |
| KA S2 | Tanjung Bungo | −1.766667, 101.300722 | 1,488 m |

The [2019 harvest study](https://doi.org/10.3390/su11236709) identifies the same
GR 01 coordinate as its community agroforest field site. PH S1 also anchors
the Pungut study village marker, so the poster shows both symbols at that point.
These are historical observations without complete geographic coverage.

The public sources reviewed provide [seed-block locations and areas](https://online-journal.unja.ac.id/JIITUJ/article/download/19331/13756),
[a planning suitability study](https://repository.ipb.ac.id/handle/123456789/43978),
and [general plantation land cover](https://geoservices.big.go.id/rbi/rest/services/BASEMAP/Rupabumi_Indonesia/MapServer/222).
No verifiable cinnamon parcel boundaries were found. Mixed cinnamon agroforests
and general agriculture cannot be reliably distinguished by those land-cover
classes, so the map uses published observations instead of a suitability proxy.

## Study villages

[Antony et al., Figure 1 and §2.1](https://doi.org/10.1111/sum.12974)
identify three villages and report a sampling elevation of 1,000–1,500 m.
The paper provides village names and a map at regional scale. The dots
are reference points for the named villages. The elevation range refers to the
study plots, whose individual coordinates and boundaries are unavailable.

| Poster label | WGS84 latitude, longitude | Placement |
| --- | --- | --- |
| Lempur | −2.089992, 101.535356 | Lempur Mudik village office, Gunung Raya, from [Indonesia’s BIG gazetteer](https://sinar.big.go.id/pencarian/detail/16099). Independent [cinnamon fieldwork in Lempur Mudik](https://doi.org/10.3390/su11236709) situates the crop in this part of the wider Lempur area. |
| Pungut | −2.020972, 101.461833 | Pungut Hilir, Air Hangat Timur. The reference point is from a separate cinnamon survey that explicitly identifies Pungut Hilir, Table 1, accession PH S1. [2018 cinnamon diversity survey](https://doi.org/10.1088/1757-899X/434/1/012129) |
| Renah Kayu Embun | −2.158900, 101.399300 | Village school in Kumun Debai, Kota Sungai Penuh, from [the Indonesian education ministry’s school registry](https://referensi.data.kemdikbud.go.id/tabs.php?npsn=70007580). |

Figure 1 abbreviates Lempur and Pungut. The links to Lempur Mudik and Pungut
Hilir are interpretations supported by local cinnamon fieldwork. The paper
does not resolve the administrative subdivisions or precise plot positions.
In particular, the Lempur village office is northeast of the Renah Kayu Embun
school, while Figure 1 places the Lempur sampling symbol southeast of RKE.

## Sources and reproduction

- Terrain comes from the [Copernicus GLO-30 Public 2021 release on AWS](https://registry.opendata.aws/copernicus-dem/).
  The original DSM is approximately 30 m, based on 2011–2015 acquisitions.
  The renderer checks SHA-256 for both tiles and reprojects to WGS 84 / UTM
  zone 47S (EPSG:32747) at 50 m before calculating 100 m contours and
  northwest hillshade. The tint uses cells with elevations from 1,000 to
  1,500 m inclusive. It only illustrates the elevation of the Antony et al.
  sampling sites. The 10 km scale bar uses the projected grid.
  [Copernicus DEM license](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM/resources/license/License-COPDEM-30.pdf)
- Locator coastline comes from [Natural Earth 1:10m land, v5.1.2](https://github.com/nvkelso/natural-earth-vector/tree/v5.1.2),
  public domain. The summit label uses the [Smithsonian Global Volcanism Program](https://volcano.si.edu/volcano.cfm?vn=261170).
- ImageGen produced the cinnamon quill illustration. The transparent source asset is
  included in `assets/`. Cartography comes from the geographic sources above.
- Terrain credit: produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and
  © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the
  European Union and ESA; all rights reserved.

From the repository root with Python 3.11:

```sh
python3 -m pip install -r maps/day19-smell/requirements.txt
python3 maps/day19-smell/render.py
```

The first run downloads the DEM and coastline into ignored `data/raw/day19-smell/`.
Output is an 11 × 15 inch PDF with vector contours and embedded type, plus
a 3960 × 5400 PNG at 360 dpi. The renderer checks that the projected grid contains
no missing cells and that all village and cultivation references fall within the
panel. The expanded terrain frame covers 75 × 76 km and includes the southern
Lempur agroforest. The final grid is 1,500 × 1,520 cells with 842,246 cells inside
the study elevation band.
